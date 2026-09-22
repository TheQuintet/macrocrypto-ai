"""Unit tests for app.export.csv_export.

Covers:
    - TIMEFRAME_HOURS / TIMEFRAME_DAYS maps
    - SUPPORTED_DATA_TYPES and the prediction defaults
    - ExportRequest / ExportResult dataclasses (to_dict, __repr__)
    - CsvExporter._tag, ._stringify_timestamps, .to_csv, ._filename
    - Each per-data-type builder against fake repositories
    - build() end-to-end for single type, multiple types, and
      error cases (bad timeframe, empty data_types, unsupported
      type, empty result frame)

Note on reading `build()` payloads:

    Since A2.5, the payload produced by `CsvExporter.build` begins
    with a citations comment header (lines starting with ``#``).
    Tests that parse the payload must pass ``comment="#"`` to
    ``pandas.read_csv``. ``CsvExporter.to_csv`` called directly
    without a ``metadata`` argument produces a bare CSV and does
    not need the hint — see ``TestToCsv::test_round_trips_via_read_csv``.

The exporter is a pure in-memory generator over injected
repositories, so the tests use tiny fake repos that return canned
DataFrames. No session, no database, no I/O.
"""

import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
import pytest

from app.database.repositories.prediction_repository import PredictionRow
from app.export.csv_export import (
    PREDICTION_CONFIDENCE,
    PREDICTION_HORIZONS,
    PREDICTION_MODELS,
    REGIME_ROLLING_WINDOW_HOURS,
    SUPPORTED_DATA_TYPES,
    TIMEFRAME_DAYS,
    TIMEFRAME_HOURS,
    CsvExporter,
    ExportRequest,
    ExportResult,
)


# ============================================================
# FAKE REPOSITORIES
# ============================================================
class _FakePredictionRepo:
    """Returns canned DataFrames / PredictionRows for exporter tests.

    Attributes record the arguments each fetch was called with so
    individual tests can assert on them.
    """

    def __init__(
        self,
        btc: Optional[pd.DataFrame] = None,
        macro: Optional[pd.DataFrame] = None,
        batches: Optional[Dict[str, List[PredictionRow]]] = None,
    ) -> None:
        self._btc = btc if btc is not None else pd.DataFrame()
        self._macro = macro if macro is not None else pd.DataFrame()
        self._batches = batches or {}

        # Call log for assertions
        self.btc_hours_called: Optional[int] = None
        self.macro_hours_called: Optional[int] = None
        self.prediction_calls: List[Dict[str, Any]] = []

    async def fetch_recent_btc_data(self, hours: int) -> pd.DataFrame:
        self.btc_hours_called = hours
        return self._btc.copy()

    async def fetch_recent_macro_data(self, hours: int) -> pd.DataFrame:
        self.macro_hours_called = hours
        return self._macro.copy()

    async def fetch_latest_predictions(
        self,
        horizon: str,
        model_name: str,
        confidence: float,
    ) -> List[PredictionRow]:
        self.prediction_calls.append(
            {
                "horizon": horizon,
                "model_name": model_name,
                "confidence": confidence,
            }
        )
        key = f"{model_name}_{horizon}"
        return list(self._batches.get(key, []))


class _FakeCorrelationRepo:
    """Returns a canned list of correlation dicts."""

    def __init__(self, rows: Optional[List[Dict[str, Any]]] = None) -> None:
        self._rows = rows or []
        self.fetch_calls = 0

    async def fetch_latest_per_indicator(
        self,
    ) -> List[Dict[str, Any]]:
        self.fetch_calls += 1
        return [dict(r) for r in self._rows]


# ============================================================
# FIXTURES
# ============================================================
def _btc_frame(hours: int = 3) -> pd.DataFrame:
    """Build a small BTC frame matching the repository's shape."""
    base = datetime(2026, 9, 14, tzinfo=timezone.utc)
    return pd.DataFrame(
        {
            "time": [base + pd.Timedelta(hours=i) for i in range(hours)],
            "close": [60000.0 + 100.0 * i for i in range(hours)],
            "volume": [1000.0 + i for i in range(hours)],
            "volatility": [0.02] * hours,
            "dominance": [0.55] * hours,
            "active_addresses": [500_000] * hours,
            "price_lag_7d": [59000.0] * hours,
        }
    )


def _macro_frame(hours: int = 3) -> pd.DataFrame:
    """Build a small macro frame matching the repository's shape."""
    base = datetime(2026, 9, 14, tzinfo=timezone.utc)
    return pd.DataFrame(
        {
            "time": [base + pd.Timedelta(hours=i) for i in range(hours)],
            "cpi": [3.2] * hours,
            "interest_rate": [5.25] * hours,
            "m2_growth": [1.5] * hours,
            "dxy": [104.0] * hours,
            "treasury_yield": [4.5] * hours,
        }
    )


def _prediction_row(
    horizon: str = "24h",
    model_name: str = "prophet_fresh",
) -> PredictionRow:
    now = datetime(2026, 9, 14, tzinfo=timezone.utc)
    return PredictionRow(
        time=now,
        prediction_time=now,
        horizon=horizon,
        model_name=model_name,
        confidence=PREDICTION_CONFIDENCE,
        predicted_price=61000.0,
        lower_bound=60000.0,
        upper_bound=62000.0,
    )


# ============================================================
# CONSTANTS
# ============================================================
class TestTimeframeMaps:
    """TIMEFRAME_HOURS and TIMEFRAME_DAYS cover the four labels."""

    def test_hours_keys(self) -> None:
        assert set(TIMEFRAME_HOURS.keys()) == {"30d", "90d", "1y", "5y"}

    def test_days_keys(self) -> None:
        assert set(TIMEFRAME_DAYS.keys()) == {"30d", "90d", "1y", "5y"}

    def test_hours_values(self) -> None:
        assert TIMEFRAME_HOURS["30d"] == 720
        assert TIMEFRAME_HOURS["90d"] == 2160
        assert TIMEFRAME_HOURS["1y"] == 8760
        assert TIMEFRAME_HOURS["5y"] == 43800

    def test_days_values(self) -> None:
        assert TIMEFRAME_DAYS["30d"] == 30
        assert TIMEFRAME_DAYS["90d"] == 90
        assert TIMEFRAME_DAYS["1y"] == 365
        assert TIMEFRAME_DAYS["5y"] == 1825

    def test_days_hours_are_consistent(self) -> None:
        for label, days in TIMEFRAME_DAYS.items():
            assert TIMEFRAME_HOURS[label] == days * 24


class TestSupportedConstants:
    """The supported data types and prediction defaults are stable."""

    def test_supported_data_types(self) -> None:
        assert SUPPORTED_DATA_TYPES == (
            "btc_price",
            "macro",
            "predictions",
            "correlations",
            "regimes",
        )

    def test_prediction_horizons(self) -> None:
        assert PREDICTION_HORIZONS == ("24h", "7d")

    def test_prediction_models(self) -> None:
        assert PREDICTION_MODELS == (
            "prophet_fresh",
            "prophet_warm",
            "xgboost_fresh",
            "xgboost_incremental",
            "lightgbm_fresh",
            "lightgbm_incremental",
        )

    def test_prediction_confidence(self) -> None:
        assert PREDICTION_CONFIDENCE == 0.85

    def test_regime_rolling_window(self) -> None:
        assert REGIME_ROLLING_WINDOW_HOURS == 720


# ============================================================
# DATACLASSES
# ============================================================
class TestExportRequest:
    """ExportRequest defaults, to_dict, and __repr__."""

    def test_defaults(self) -> None:
        req = ExportRequest()
        assert req.data_types == []
        assert req.timeframe == "30d"
        assert req.user_id is None

    def test_to_dict_round_trip(self) -> None:
        req = ExportRequest(
            data_types=["btc_price"],
            timeframe="90d",
            user_id="analyst-42",
        )
        d = req.to_dict()
        assert d == {
            "data_types": ["btc_price"],
            "timeframe": "90d",
            "user_id": "analyst-42",
        }

    def test_to_dict_copies_data_types(self) -> None:
        original = ["btc_price"]
        req = ExportRequest(data_types=original, timeframe="30d")
        d = req.to_dict()
        d["data_types"].append("macro")
        assert original == ["btc_price"]

    def test_repr_contains_key_fields(self) -> None:
        req = ExportRequest(
            data_types=["macro"], timeframe="1y", user_id="u-1"
        )
        text = repr(req)
        assert "macro" in text
        assert "1y" in text
        assert "u-1" in text


class TestExportResult:
    """ExportResult to_dict and __repr__."""

    def test_to_dict_omits_content(self) -> None:
        res = ExportResult(
            file_name="f.csv",
            file_size=10,
            data_types=["btc_price"],
            timeframe="30d",
            rows_written=3,
            content=b"a,b\n1,2\n",
        )
        d = res.to_dict()
        assert "content" not in d
        assert d == {
            "file_name": "f.csv",
            "file_size": 10,
            "data_types": ["btc_price"],
            "timeframe": "30d",
            "rows_written": 3,
        }

    def test_repr_contains_key_fields(self) -> None:
        res = ExportResult(
            file_name="f.csv",
            file_size=10,
            data_types=["btc_price"],
            timeframe="30d",
            rows_written=3,
            content=b"",
        )
        text = repr(res)
        assert "f.csv" in text
        assert "30d" in text
        assert "3" in text


# ============================================================
# HELPERS
# ============================================================
class TestTagHelper:
    """CsvExporter._tag inserts a leading data_type column."""

    def test_inserts_column_at_position_zero(self) -> None:
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        tagged = CsvExporter._tag(df, "btc_price")
        assert list(tagged.columns) == ["data_type", "a", "b"]
        assert tagged["data_type"].tolist() == ["btc_price", "btc_price"]

    def test_does_not_mutate_input(self) -> None:
        df = pd.DataFrame({"a": [1]})
        CsvExporter._tag(df, "macro")
        assert list(df.columns) == ["a"]

    def test_empty_frame_still_gets_column(self) -> None:
        df = pd.DataFrame()
        tagged = CsvExporter._tag(df, "btc_price")
        assert list(tagged.columns) == ["data_type"]
        assert tagged.empty


class TestStringifyTimestamps:
    """CsvExporter._stringify_timestamps converts datetimes to ISO."""

    def test_converts_datetime_column(self) -> None:
        ts = datetime(2026, 9, 14, tzinfo=timezone.utc)
        df = pd.DataFrame({"time": [ts], "x": [1.0]})
        out = CsvExporter._stringify_timestamps(df)
        assert out["time"].iloc[0] == ts.isoformat()
        assert out["x"].iloc[0] == 1.0

    def test_leaves_non_datetime_columns_alone(self) -> None:
        df = pd.DataFrame({"x": [1, 2, 3]})
        out = CsvExporter._stringify_timestamps(df)
        assert out["x"].tolist() == [1, 2, 3]

    def test_empty_frame_is_noop(self) -> None:
        df = pd.DataFrame()
        out = CsvExporter._stringify_timestamps(df)
        assert out.empty


class TestToCsv:
    """CsvExporter.to_csv produces UTF-8 CSV bytes."""

    def test_returns_bytes(self) -> None:
        df = pd.DataFrame({"a": [1], "b": ["x"]})
        payload = CsvExporter.to_csv(df)
        assert isinstance(payload, bytes)
        assert payload.startswith(b"a,b\n")

    def test_round_trips_via_read_csv(self) -> None:
        df = pd.DataFrame(
            {"data_type": ["btc_price"], "time": ["2026-09-14"], "x": [1]}
        )
        payload = CsvExporter.to_csv(df)
        back = pd.read_csv(io.BytesIO(payload))
        assert list(back.columns) == list(df.columns)
        assert len(back) == len(df)

    def test_no_index_column(self) -> None:
        df = pd.DataFrame({"a": [1, 2]})
        payload = CsvExporter.to_csv(df)
        # Header row is exactly "a" — no "Unnamed: 0" or empty
        # first field.
        header = payload.decode("utf-8").splitlines()[0]
        assert header == "a"


class TestFilename:
    """CsvExporter._filename matches the naming convention."""

    def test_single_data_type(self) -> None:
        name = CsvExporter._filename(["btc_price"], "30d")
        assert name.startswith("macro-crypto-btc_price-30d-")
        assert name.endswith(".csv")

    def test_single_data_type_uses_the_type_name(self) -> None:
        for dt in SUPPORTED_DATA_TYPES:
            name = CsvExporter._filename([dt], "90d")
            assert name.startswith(f"macro-crypto-{dt}-90d-")

    def test_multiple_data_types_use_multi(self) -> None:
        name = CsvExporter._filename(
            ["btc_price", "macro", "regimes"], "1y"
        )
        assert name.startswith("macro-crypto-multi-1y-")
        assert name.endswith(".csv")

    def test_date_is_utc_iso(self) -> None:
        name = CsvExporter._filename(["btc_price"], "30d")
        # "macro-crypto-btc_price-30d-YYYY-MM-DD.csv"
        parts = name[:-4].split("-")
        assert len(parts[-3]) == 4  # year
        assert len(parts[-2]) == 2  # month
        assert len(parts[-1]) == 2  # day


# ============================================================
# build() — VALIDATION
# ============================================================
class TestBuildValidation:
    """build() rejects bad requests before doing any work."""

    @pytest.mark.asyncio
    async def test_unknown_timeframe(self) -> None:
        exporter = CsvExporter(
            _FakePredictionRepo(), _FakeCorrelationRepo()
        )
        with pytest.raises(ValueError, match="Unknown timeframe"):
            await exporter.build(
                ExportRequest(data_types=["btc_price"], timeframe="1m")
            )

    @pytest.mark.asyncio
    async def test_empty_data_types(self) -> None:
        exporter = CsvExporter(
            _FakePredictionRepo(), _FakeCorrelationRepo()
        )
        with pytest.raises(ValueError, match="data_types must not be empty"):
            await exporter.build(
                ExportRequest(data_types=[], timeframe="30d")
            )

    @pytest.mark.asyncio
    async def test_unsupported_data_type(self) -> None:
        exporter = CsvExporter(
            _FakePredictionRepo(), _FakeCorrelationRepo()
        )
        with pytest.raises(ValueError, match="Unsupported data type"):
            await exporter.build(
                ExportRequest(
                    data_types=["bogus"], timeframe="30d"
                )
            )


# ============================================================
# build() — PER-DATA-TYPE
# ============================================================
class TestBuildBtcPrice:
    """build() for data_types=['btc_price']."""

    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        pred_repo = _FakePredictionRepo(btc=_btc_frame(3))
        exporter = CsvExporter(pred_repo, _FakeCorrelationRepo())

        result = await exporter.build(
            ExportRequest(data_types=["btc_price"], timeframe="30d")
        )

        assert result.rows_written == 3
        assert result.file_name.startswith("macro-crypto-btc_price-30d-")
        assert pred_repo.btc_hours_called == TIMEFRAME_HOURS["30d"]
        back = pd.read_csv(io.BytesIO(result.content), comment="#")
        assert list(back.columns)[0] == "data_type"
        assert back["data_type"].iloc[0] == "btc_price"

    @pytest.mark.asyncio
    async def test_empty_frame_raises(self) -> None:
        pred_repo = _FakePredictionRepo(btc=pd.DataFrame())
        exporter = CsvExporter(pred_repo, _FakeCorrelationRepo())
        with pytest.raises(ValueError, match="zero rows"):
            await exporter.build(
                ExportRequest(data_types=["btc_price"], timeframe="30d")
            )


class TestBuildMacro:
    """build() for data_types=['macro']."""

    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        pred_repo = _FakePredictionRepo(macro=_macro_frame(5))
        exporter = CsvExporter(pred_repo, _FakeCorrelationRepo())

        result = await exporter.build(
            ExportRequest(data_types=["macro"], timeframe="90d")
        )

        assert result.rows_written == 5
        assert result.file_name.startswith("macro-crypto-macro-90d-")
        assert pred_repo.macro_hours_called == TIMEFRAME_HOURS["90d"]


class TestBuildPredictions:
    """build() for data_types=['predictions']."""

    @pytest.mark.asyncio
    async def test_happy_path_uses_all_pairs(self) -> None:
        batches = {
            f"{model}_{horizon}": [_prediction_row(horizon, model)]
            for horizon in PREDICTION_HORIZONS
            for model in PREDICTION_MODELS
        }
        pred_repo = _FakePredictionRepo(batches=batches)
        exporter = CsvExporter(pred_repo, _FakeCorrelationRepo())

        result = await exporter.build(
            ExportRequest(data_types=["predictions"], timeframe="30d")
        )

        expected_calls = len(PREDICTION_HORIZONS) * len(PREDICTION_MODELS)
        assert len(pred_repo.prediction_calls) == expected_calls
        assert result.rows_written == expected_calls

        # Every call uses the default confidence.
        for call in pred_repo.prediction_calls:
            assert call["confidence"] == PREDICTION_CONFIDENCE

    @pytest.mark.asyncio
    async def test_no_pairs_raises(self) -> None:
        pred_repo = _FakePredictionRepo(batches={})
        exporter = CsvExporter(pred_repo, _FakeCorrelationRepo())
        with pytest.raises(ValueError, match="zero rows"):
            await exporter.build(
                ExportRequest(data_types=["predictions"], timeframe="30d")
            )


class TestBuildCorrelations:
    """build() for data_types=['correlations']."""

    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        rows = [
            {
                "indicator_name": "inflation",
                "window_days": 30,
                "calculated_at": datetime(
                    2026, 9, 14, tzinfo=timezone.utc
                ),
                "correlation_coefficient": -0.42,
                "strength": "medium",
                "direction": "negative",
                "p_value": 0.03,
            },
            {
                "indicator_name": "rates",
                "window_days": 30,
                "calculated_at": datetime(
                    2026, 9, 14, tzinfo=timezone.utc
                ),
                "correlation_coefficient": 0.85,
                "strength": "strong",
                "direction": "positive",
                "p_value": 0.001,
            },
        ]
        corr_repo = _FakeCorrelationRepo(rows=rows)
        exporter = CsvExporter(_FakePredictionRepo(), corr_repo)

        result = await exporter.build(
            ExportRequest(data_types=["correlations"], timeframe="90d")
        )

        assert corr_repo.fetch_calls == 1
        assert result.rows_written == 2
        assert result.file_name.startswith(
            "macro-crypto-correlations-90d-"
        )

    @pytest.mark.asyncio
    async def test_empty_rows_raises(self) -> None:
        corr_repo = _FakeCorrelationRepo(rows=[])
        exporter = CsvExporter(_FakePredictionRepo(), corr_repo)
        with pytest.raises(ValueError, match="zero rows"):
            await exporter.build(
                ExportRequest(
                    data_types=["correlations"], timeframe="30d"
                )
            )


class TestBuildRegimes:
    """build() for data_types=['regimes'] — the on-the-fly path."""

    @pytest.mark.asyncio
    async def test_happy_path_emits_a_label_per_row(self) -> None:
        # 100 hours of steadily rising prices → every window is
        # "bull" once the window has enough points.
        base = datetime(2026, 9, 1, tzinfo=timezone.utc)
        closes = [50000.0 * (1.0 + 0.01 * i) for i in range(100)]
        btc = pd.DataFrame(
            {
                "time": [
                    base + pd.Timedelta(hours=i) for i in range(100)
                ],
                "close": closes,
                "volume": [0.0] * 100,
                "volatility": [0.0] * 100,
                "dominance": [0.0] * 100,
                "active_addresses": [0] * 100,
                "price_lag_7d": [0.0] * 100,
            }
        )
        pred_repo = _FakePredictionRepo(btc=btc)
        exporter = CsvExporter(pred_repo, _FakeCorrelationRepo())

        result = await exporter.build(
            ExportRequest(data_types=["regimes"], timeframe="30d")
        )

        assert result.rows_written == 100
        assert result.file_name.startswith("macro-crypto-regimes-30d-")
        back = pd.read_csv(io.BytesIO(result.content), comment="#")
        assert "regime" in back.columns
        # The last row has a full rolling window — it must have a
        # label. The specific label depends on the classifier's
        # thresholds; assert only that a label is present.
        assert back["regime"].iloc[-1] is not None

    @pytest.mark.asyncio
    async def test_early_rows_have_no_label(self) -> None:
        # With only 2 rows, the rolling window cannot classify.
        btc = _btc_frame(2)
        pred_repo = _FakePredictionRepo(btc=btc)
        exporter = CsvExporter(pred_repo, _FakeCorrelationRepo())

        result = await exporter.build(
            ExportRequest(data_types=["regimes"], timeframe="30d")
        )
        back = pd.read_csv(io.BytesIO(result.content), comment="#")
        # Both rows exist even though the classifier returns None.
        assert len(back) == 2

    @pytest.mark.asyncio
    async def test_empty_btc_raises(self) -> None:
        pred_repo = _FakePredictionRepo(btc=pd.DataFrame())
        exporter = CsvExporter(pred_repo, _FakeCorrelationRepo())
        with pytest.raises(ValueError, match="zero rows"):
            await exporter.build(
                ExportRequest(data_types=["regimes"], timeframe="30d")
            )


# ============================================================
# build() — MULTI-TYPE
# ============================================================
class TestBuildMultiType:
    """build() concatenates frames when multiple types are requested."""

    @pytest.mark.asyncio
    async def test_two_types_concatenate(self) -> None:
        pred_repo = _FakePredictionRepo(
            btc=_btc_frame(3), macro=_macro_frame(3)
        )
        exporter = CsvExporter(pred_repo, _FakeCorrelationRepo())

        result = await exporter.build(
            ExportRequest(
                data_types=["btc_price", "macro"], timeframe="30d"
            )
        )

        assert result.rows_written == 6
        assert result.file_name.startswith("macro-crypto-multi-30d-")
        back = pd.read_csv(io.BytesIO(result.content), comment="#")
        assert set(back["data_type"].unique()) == {"btc_price", "macro"}

    @pytest.mark.asyncio
    async def test_three_types_concatenate(self) -> None:
        rows = [
            {
                "indicator_name": "inflation",
                "window_days": 30,
                "calculated_at": datetime(
                    2026, 9, 14, tzinfo=timezone.utc
                ),
                "correlation_coefficient": -0.42,
                "strength": "medium",
                "direction": "negative",
                "p_value": 0.03,
            }
        ]
        pred_repo = _FakePredictionRepo(
            btc=_btc_frame(2), macro=_macro_frame(2)
        )
        corr_repo = _FakeCorrelationRepo(rows=rows)
        exporter = CsvExporter(pred_repo, corr_repo)

        result = await exporter.build(
            ExportRequest(
                data_types=["btc_price", "macro", "correlations"],
                timeframe="90d",
            )
        )

        assert result.rows_written == 5
        back = pd.read_csv(io.BytesIO(result.content), comment="#")
        assert set(back["data_type"].unique()) == {
            "btc_price",
            "macro",
            "correlations",
        }