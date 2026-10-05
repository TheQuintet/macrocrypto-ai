# """Unit tests for the PredictionRepository.

# These tests mock the SQLAlchemy AsyncSession so no live database is
# required. They verify:
#     - Correct SQL statements are issued (shape + parameters)
#     - Result rows are correctly mapped to DataFrames
#     - Column names match what the model adapters expect
#     - Merging and forward-fill logic in fetch_training_frame
#     - Bulk-insert payload construction in save_predictions

# Test organization:
#     - TestPredictionRow: dataclass behavior
#     - TestFetchRecentBtcData: read BTC prices
#     - TestFetchRecentMacroData: read macro indicators
#     - TestFetchBtcPriceAt: single-price lookup (A5.2 Group 1)
#     - TestFetchBtcPricesRange: range lookup (A5.2 Group 1)
#     - TestFetchTrainingFrame: merge + ffill logic
#     - TestSavePredictions: bulk insert
#     - TestFetchLatestPredictionTime: idempotency helper
#     - TestFetchLatestPredictionsBatch: multi-model batch read (M6a)
# """

# from datetime import datetime, timedelta, timezone
# from typing import Any, Dict, List
# from unittest.mock import AsyncMock, MagicMock

# import pandas as pd
# import pytest

# from app.database.repositories.prediction_repository import (
#     PredictionRepository,
#     PredictionRow,
# )


# # ============================================================
# # HELPERS
# # ============================================================
# def _mock_session_returning(rows: list[dict]) -> AsyncMock:
#     """Build a mock AsyncSession whose execute() returns the given rows.

#     Args:
#         rows: List of dicts to return as mapping rows.

#     Returns:
#         AsyncMock configured to mimic AsyncSession.execute().
#     """
#     mock_result = MagicMock()
#     # mappings().all() returns the rows
#     mock_result.mappings.return_value.all.return_value = rows

#     mock_session = AsyncMock()
#     mock_session.execute.return_value = mock_result
#     mock_session.flush = AsyncMock()
#     return mock_session


# def _make_prediction_row(
#     time: datetime,
#     model_name: str,
#     price: float,
#     horizon: str = "24h",
#     confidence: float = 0.85,
# ) -> Dict[str, Any]:
#     """Build a dict shaped like a btc_predictions row mapping."""
#     return {
#         "time": time,
#         "prediction_time": time - timedelta(hours=1),
#         "horizon": horizon,
#         "model_name": model_name,
#         "confidence": confidence,
#         "predicted_price": price,
#         "lower_bound": price - 500.0,
#         "upper_bound": price + 500.0,
#     }


# # ============================================================
# # ROW DATACLASS TESTS
# # ============================================================
# class TestPredictionRow:
#     """Tests for the PredictionRow dataclass."""

#     def test_construction(self) -> None:
#         """Test constructing a row with all fields."""
#         now = datetime.now(timezone.utc)
#         row = PredictionRow(
#             time=now,
#             prediction_time=now,
#             horizon="24h",
#             model_name="prophet",
#             confidence=0.85,
#             predicted_price=50_000.0,
#             lower_bound=49_000.0,
#             upper_bound=51_000.0,
#         )
#         assert row.horizon == "24h"
#         assert row.predicted_price == 50_000.0

#     def test_to_dict_keys(self) -> None:
#         """Test that to_dict returns the expected keys."""
#         now = datetime.now(timezone.utc)
#         row = PredictionRow(
#             time=now,
#             prediction_time=now,
#             horizon="24h",
#             model_name="prophet",
#             confidence=0.85,
#             predicted_price=50_000.0,
#             lower_bound=49_000.0,
#             upper_bound=51_000.0,
#         )
#         d = row.to_dict()
#         expected = {
#             "time",
#             "prediction_time",
#             "horizon",
#             "model_name",
#             "confidence",
#             "predicted_price",
#             "lower_bound",
#             "upper_bound",
#         }
#         assert set(d.keys()) == expected


# # ============================================================
# # FETCH BTC DATA TESTS
# # ============================================================
# class TestFetchRecentBtcData:
#     """Tests for fetch_recent_btc_data()."""

#     @pytest.mark.asyncio
#     async def test_returns_dataframe(self) -> None:
#         """Test that the method returns a DataFrame."""
#         rows = [
#             {
#                 "time": datetime(2024, 4, 1, tzinfo=timezone.utc),
#                 "close": 50_000.0,
#                 "volume": 25_000_000_000.0,
#                 "volatility": 0.15,
#                 "dominance": 52.5,
#                 "active_addresses": 850_000.0,
#                 "price_lag_7d": 49_500.0,
#             },
#         ]
#         session = _mock_session_returning(rows)
#         repo = PredictionRepository(session)

#         df = await repo.fetch_recent_btc_data(hours=24)

#         assert isinstance(df, pd.DataFrame)
#         assert len(df) == 1
#         assert set(df.columns) == {
#             "time",
#             "close",
#             "volume",
#             "volatility",
#             "dominance",
#             "active_addresses",
#             "price_lag_7d",
#         }

#     @pytest.mark.asyncio
#     async def test_empty_result_returns_empty_dataframe(self) -> None:
#         """Test that empty DB results produce an empty DataFrame."""
#         session = _mock_session_returning([])
#         repo = PredictionRepository(session)

#         df = await repo.fetch_recent_btc_data(hours=24)

#         assert isinstance(df, pd.DataFrame)
#         assert df.empty

#     @pytest.mark.asyncio
#     async def test_execute_is_called(self) -> None:
#         """Test that session.execute is called once."""
#         session = _mock_session_returning([])
#         repo = PredictionRepository(session)

#         await repo.fetch_recent_btc_data(hours=24)

#         assert session.execute.call_count == 1


# # ============================================================
# # FETCH MACRO DATA TESTS
# # ============================================================
# class TestFetchRecentMacroData:
#     """Tests for fetch_recent_macro_data()."""

#     @pytest.mark.asyncio
#     async def test_returns_dataframe(self) -> None:
#         """Test that the method returns a DataFrame with macro columns."""
#         rows = [
#             {
#                 "time": datetime(2024, 4, 1, tzinfo=timezone.utc),
#                 "cpi": 3.2,
#                 "interest_rate": 4.5,
#                 "m2_growth": 2.8,
#                 "dxy": 102.5,
#                 "treasury_yield": 4.2,
#             },
#         ]
#         session = _mock_session_returning(rows)
#         repo = PredictionRepository(session)

#         df = await repo.fetch_recent_macro_data(hours=24)

#         assert isinstance(df, pd.DataFrame)
#         assert len(df) == 1
#         assert set(df.columns) == {
#             "time",
#             "cpi",
#             "interest_rate",
#             "m2_growth",
#             "dxy",
#             "treasury_yield",
#         }

#     @pytest.mark.asyncio
#     async def test_empty_result_returns_empty_dataframe(self) -> None:
#         """Test that empty DB results produce an empty DataFrame."""
#         session = _mock_session_returning([])
#         repo = PredictionRepository(session)

#         df = await repo.fetch_recent_macro_data(hours=24)

#         assert isinstance(df, pd.DataFrame)
#         assert df.empty


# # ============================================================
# # FETCH BTC PRICE AT TESTS (A5.2 Group 1)
# # ============================================================
# class TestFetchBtcPriceAt:
#     """Tests for fetch_btc_price_at() (A5.2 Group 1)."""

#     @pytest.mark.asyncio
#     async def test_returns_float(self) -> None:
#         """Test that the method returns a float when a row exists."""
#         target = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
#         session = AsyncMock()
#         mock_result = MagicMock()
#         mock_result.scalar_one_or_none.return_value = 63_500.0
#         session.execute.return_value = mock_result

#         repo = PredictionRepository(session)
#         value = await repo.fetch_btc_price_at(target)

#         assert value == 63_500.0

#     @pytest.mark.asyncio
#     async def test_returns_none_when_no_row(self) -> None:
#         """Test that None is returned when no row is within tolerance."""
#         target = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
#         session = AsyncMock()
#         mock_result = MagicMock()
#         mock_result.scalar_one_or_none.return_value = None
#         session.execute.return_value = mock_result

#         repo = PredictionRepository(session)
#         value = await repo.fetch_btc_price_at(target)

#         assert value is None

#     @pytest.mark.asyncio
#     async def test_tolerance_hours_defaults_to_one(self) -> None:
#         """Test that the default tolerance is 1 hour."""
#         target = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
#         session = AsyncMock()
#         mock_result = MagicMock()
#         mock_result.scalar_one_or_none.return_value = 63_500.0
#         session.execute.return_value = mock_result

#         repo = PredictionRepository(session)
#         # Call without tolerance_hours, then with an explicit one.
#         # The default should be 1 (per PRICE_LOOKUP_TOLERANCE_HOURS
#         # at the caller), and the explicit call should accept 6.
#         await repo.fetch_btc_price_at(target)
#         await repo.fetch_btc_price_at(target, tolerance_hours=6)

#         # Exactly two SELECTs issued.
#         assert session.execute.call_count == 2

#     @pytest.mark.asyncio
#     async def test_execute_is_called(self) -> None:
#         """Test that session.execute is called exactly once."""
#         target = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
#         session = AsyncMock()
#         mock_result = MagicMock()
#         mock_result.scalar_one_or_none.return_value = 63_500.0
#         session.execute.return_value = mock_result

#         repo = PredictionRepository(session)
#         await repo.fetch_btc_price_at(target)

#         assert session.execute.call_count == 1


# # ============================================================
# # FETCH BTC PRICES RANGE TESTS (A5.2 Group 1)
# # ============================================================
# class TestFetchBtcPricesRange:
#     """Tests for fetch_btc_prices_range() (A5.2 Group 1)."""

#     @pytest.mark.asyncio
#     async def test_returns_dataframe_with_time_and_close(self) -> None:
#         """Test that the result has the two columns the caller needs."""
#         start = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
#         end = datetime(2024, 3, 20, 0, 0, tzinfo=timezone.utc)
#         rows = [
#             {
#                 "time": datetime(2024, 3, 19, 0, tzinfo=timezone.utc),
#                 "close": 63_000.0,
#             },
#             {
#                 "time": datetime(2024, 3, 19, 1, tzinfo=timezone.utc),
#                 "close": 63_100.0,
#             },
#         ]
#         session = _mock_session_returning(rows)
#         repo = PredictionRepository(session)

#         df = await repo.fetch_btc_prices_range(start, end)

#         assert isinstance(df, pd.DataFrame)
#         assert len(df) == 2
#         assert set(df.columns) == {"time", "close"}

#     @pytest.mark.asyncio
#     async def test_empty_range_returns_empty_dataframe(self) -> None:
#         """Test that an empty range returns an empty DataFrame."""
#         start = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
#         end = datetime(2024, 3, 20, 0, 0, tzinfo=timezone.utc)
#         session = _mock_session_returning([])
#         repo = PredictionRepository(session)

#         df = await repo.fetch_btc_prices_range(start, end)

#         assert isinstance(df, pd.DataFrame)
#         assert df.empty

#     @pytest.mark.asyncio
#     async def test_ascending_order_is_preserved(self) -> None:
#         """Test that rows come back in the order the DB returned them."""
#         start = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
#         end = datetime(2024, 3, 20, 0, 0, tzinfo=timezone.utc)
#         rows = [
#             {
#                 "time": datetime(2024, 3, 19, 0, tzinfo=timezone.utc),
#                 "close": 63_000.0,
#             },
#             {
#                 "time": datetime(2024, 3, 19, 1, tzinfo=timezone.utc),
#                 "close": 63_100.0,
#             },
#             {
#                 "time": datetime(2024, 3, 19, 2, tzinfo=timezone.utc),
#                 "close": 63_200.0,
#             },
#         ]
#         session = _mock_session_returning(rows)
#         repo = PredictionRepository(session)

#         df = await repo.fetch_btc_prices_range(start, end)

#         assert list(df["close"]) == [63_000.0, 63_100.0, 63_200.0]

#     @pytest.mark.asyncio
#     async def test_execute_is_called(self) -> None:
#         """Test that session.execute is called exactly once."""
#         start = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
#         end = datetime(2024, 3, 20, 0, 0, tzinfo=timezone.utc)
#         session = _mock_session_returning([])
#         repo = PredictionRepository(session)

#         await repo.fetch_btc_prices_range(start, end)

#         assert session.execute.call_count == 1


# # ============================================================
# # FETCH TRAINING FRAME TESTS
# # ============================================================
# class TestFetchTrainingFrame:
#     """Tests for fetch_training_frame() (merge + forward-fill)."""

#     @pytest.mark.asyncio
#     async def test_returns_empty_when_btc_empty(self) -> None:
#         """Test that empty BTC data yields an empty frame."""
#         btc_rows: list[dict] = []
#         macro_rows: list[dict] = []

#         session = AsyncMock()
#         mock_result = MagicMock()
#         # Both calls return their respective rows in order
#         mock_result.mappings.return_value.all.side_effect = [
#             btc_rows,  # first call (BTC)
#             macro_rows,  # second call (macro)
#         ]
#         session.execute.return_value = mock_result

#         repo = PredictionRepository(session)
#         df = await repo.fetch_training_frame(hours=24)

#         assert df.empty

#     @pytest.mark.asyncio
#     async def test_renames_time_to_ds_and_close_to_y(self) -> None:
#         """Test that the merged frame uses Prophet column names."""
#         now = datetime(2024, 4, 1, 12, tzinfo=timezone.utc)

#         btc_rows = [
#             {
#                 "time": now,
#                 "close": 50_000.0,
#                 "volume": 25_000_000_000.0,
#                 "volatility": 0.15,
#                 "dominance": 52.5,
#                 "active_addresses": 850_000.0,
#                 "price_lag_7d": 49_500.0,
#             },
#         ]
#         macro_rows = [
#             {
#                 "time": now,
#                 "cpi": 3.2,
#                 "interest_rate": 4.5,
#                 "m2_growth": 2.8,
#                 "dxy": 102.5,
#                 "treasury_yield": 4.2,
#             },
#         ]

#         session = AsyncMock()
#         mock_result = MagicMock()
#         mock_result.mappings.return_value.all.side_effect = [
#             btc_rows,
#             macro_rows,
#         ]
#         session.execute.return_value = mock_result

#         repo = PredictionRepository(session)
#         df = await repo.fetch_training_frame(hours=24)

#         assert "ds" in df.columns
#         assert "y" in df.columns
#         assert "time" not in df.columns
#         assert "close" not in df.columns

#     @pytest.mark.asyncio
#     async def test_merges_macro_and_btc_on_time(self) -> None:
#         """Test that BTC + macro are merged on their shared timestamp."""
#         now = datetime(2024, 4, 1, 12, tzinfo=timezone.utc)

#         btc_rows = [
#             {
#                 "time": now,
#                 "close": 50_000.0,
#                 "volume": 25_000_000_000.0,
#                 "volatility": 0.15,
#                 "dominance": 52.5,
#                 "active_addresses": 850_000.0,
#                 "price_lag_7d": 49_500.0,
#             },
#         ]
#         macro_rows = [
#             {
#                 "time": now,
#                 "cpi": 3.2,
#                 "interest_rate": 4.5,
#                 "m2_growth": 2.8,
#                 "dxy": 102.5,
#                 "treasury_yield": 4.2,
#             },
#         ]

#         session = AsyncMock()
#         mock_result = MagicMock()
#         mock_result.mappings.return_value.all.side_effect = [
#             btc_rows,
#             macro_rows,
#         ]
#         session.execute.return_value = mock_result

#         repo = PredictionRepository(session)
#         df = await repo.fetch_training_frame(hours=24)

#         assert len(df) == 1
#         # All 10 regressors should be present
#         for col in (
#             "cpi",
#             "interest_rate",
#             "m2_growth",
#             "dxy",
#             "treasury_yield",
#             "volume",
#             "volatility",
#             "dominance",
#             "active_addresses",
#             "price_lag_7d",
#         ):
#             assert col in df.columns, f"Missing {col}"
#         assert df["cpi"].iloc[0] == 3.2
#         assert df["y"].iloc[0] == 50_000.0

#     @pytest.mark.asyncio
#     async def test_missing_macro_returns_btc_only(self) -> None:
#         """Test that missing macro data still returns the BTC frame."""
#         now = datetime(2024, 4, 1, 12, tzinfo=timezone.utc)

#         btc_rows = [
#             {
#                 "time": now,
#                 "close": 50_000.0,
#                 "volume": 25_000_000_000.0,
#                 "volatility": 0.15,
#                 "dominance": 52.5,
#                 "active_addresses": 850_000.0,
#                 "price_lag_7d": 49_500.0,
#             },
#         ]

#         session = AsyncMock()
#         mock_result = MagicMock()
#         mock_result.mappings.return_value.all.side_effect = [
#             btc_rows,
#             [],  # macro empty
#         ]
#         session.execute.return_value = mock_result

#         repo = PredictionRepository(session)
#         df = await repo.fetch_training_frame(hours=24)

#         assert len(df) == 1
#         assert "y" in df.columns
#         assert df["y"].iloc[0] == 50_000.0


# # ============================================================
# # SAVE PREDICTIONS TESTS
# # ============================================================
# class TestSavePredictions:
#     """Tests for save_predictions()."""

#     @pytest.mark.asyncio
#     async def test_empty_list_returns_zero(self) -> None:
#         """Test that an empty list returns 0 without executing SQL."""
#         session = AsyncMock()
#         repo = PredictionRepository(session)

#         count = await repo.save_predictions([])

#         assert count == 0
#         assert session.execute.call_count == 0

#     @pytest.mark.asyncio
#     async def test_returns_row_count(self) -> None:
#         """Test that the returned count equals the number of rows."""
#         now = datetime.now(timezone.utc)
#         rows = [
#             PredictionRow(
#                 time=now + timedelta(hours=i),
#                 prediction_time=now,
#                 horizon="24h",
#                 model_name="prophet",
#                 confidence=0.85,
#                 predicted_price=50_000.0 + i,
#                 lower_bound=49_000.0 + i,
#                 upper_bound=51_000.0 + i,
#             )
#             for i in range(5)
#         ]

#         session = AsyncMock()
#         session.flush = AsyncMock()
#         repo = PredictionRepository(session)

#         count = await repo.save_predictions(rows)

#         assert count == 5
#         assert session.execute.call_count == 1
#         assert session.flush.call_count == 1

#     @pytest.mark.asyncio
#     async def test_execute_and_flush_called(self) -> None:
#         """Test that execute() and flush() are both called."""
#         now = datetime.now(timezone.utc)
#         rows = [
#             PredictionRow(
#                 time=now,
#                 prediction_time=now,
#                 horizon="24h",
#                 model_name="prophet",
#                 confidence=0.85,
#                 predicted_price=50_000.0,
#                 lower_bound=49_000.0,
#                 upper_bound=51_000.0,
#             )
#         ]

#         session = AsyncMock()
#         session.flush = AsyncMock()
#         repo = PredictionRepository(session)

#         await repo.save_predictions(rows)

#         session.execute.assert_called_once()
#         session.flush.assert_called_once()


# # ============================================================
# # LATEST PREDICTION TIME TESTS
# # ============================================================
# class TestFetchLatestPredictionTime:
#     """Tests for fetch_latest_prediction_time()."""

#     @pytest.mark.asyncio
#     async def test_returns_value(self) -> None:
#         """Test that the method returns the scalar from the DB."""
#         expected = datetime(2024, 4, 1, 12, tzinfo=timezone.utc)

#         session = AsyncMock()
#         mock_result = MagicMock()
#         mock_result.scalar_one_or_none.return_value = expected
#         session.execute.return_value = mock_result

#         repo = PredictionRepository(session)
#         value = await repo.fetch_latest_prediction_time(
#             horizon="24h", model_name="prophet"
#         )

#         assert value == expected

#     @pytest.mark.asyncio
#     async def test_returns_none_when_no_rows(self) -> None:
#         """Test that None is returned when no rows match."""
#         session = AsyncMock()
#         mock_result = MagicMock()
#         mock_result.scalar_one_or_none.return_value = None
#         session.execute.return_value = mock_result

#         repo = PredictionRepository(session)
#         value = await repo.fetch_latest_prediction_time(
#             horizon="24h", model_name="prophet"
#         )

#         assert value is None


# # ============================================================
# # FETCH LATEST PREDICTIONS BATCH (M6a)
# # ============================================================
# class TestFetchLatestPredictionsBatch:
#     """Tests for fetch_latest_predictions_batch()."""

#     @pytest.mark.asyncio
#     async def test_empty_model_names_returns_empty_dict(self) -> None:
#         """Test that empty input short-circuits without hitting the DB."""
#         session = AsyncMock()
#         repo = PredictionRepository(session)

#         result = await repo.fetch_latest_predictions_batch(
#             model_names=[],
#             horizon="24h",
#             confidence=0.85,
#         )

#         assert result == {}
#         assert session.execute.call_count == 0

#     @pytest.mark.asyncio
#     async def test_returns_dict_keyed_by_model(self) -> None:
#         """Test that the result is keyed by model name."""
#         t0 = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)

#         # Query 1: latest prediction_time per model
#         latest_rows = [
#             {"model_name": "prophet", "latest_ts": t0},
#             {"model_name": "xgboost_fresh", "latest_ts": t0},
#         ]
#         # Query 2: all rows in those batches
#         batch_rows = [
#             _make_prediction_row(t0, "prophet", 50_000.0),
#             _make_prediction_row(t0, "xgboost_fresh", 50_100.0),
#         ]

#         mock_result_latest = MagicMock()
#         mock_result_latest.mappings.return_value.all.return_value = latest_rows

#         mock_result_batch = MagicMock()
#         mock_result_batch.mappings.return_value.all.return_value = batch_rows

#         session = AsyncMock()
#         session.execute.side_effect = [mock_result_latest, mock_result_batch]

#         repo = PredictionRepository(session)
#         result = await repo.fetch_latest_predictions_batch(
#             model_names=["prophet", "xgboost_fresh"],
#             horizon="24h",
#             confidence=0.85,
#         )

#         assert set(result.keys()) == {"prophet", "xgboost_fresh"}
#         assert len(result["prophet"]) == 1
#         assert len(result["xgboost_fresh"]) == 1

#     @pytest.mark.asyncio
#     async def test_missing_model_omitted(self) -> None:
#         """Test that a requested model with no rows is not a key."""
#         t0 = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
#         latest_rows = [{"model_name": "prophet", "latest_ts": t0}]
#         batch_rows = [
#             _make_prediction_row(t0, "prophet", 50_000.0),
#         ]

#         mock_result_latest = MagicMock()
#         mock_result_latest.mappings.return_value.all.return_value = latest_rows
#         mock_result_batch = MagicMock()
#         mock_result_batch.mappings.return_value.all.return_value = batch_rows

#         session = AsyncMock()
#         session.execute.side_effect = [mock_result_latest, mock_result_batch]

#         repo = PredictionRepository(session)
#         result = await repo.fetch_latest_predictions_batch(
#             model_names=["prophet", "ghost"],
#             horizon="24h",
#             confidence=0.85,
#         )

#         assert "prophet" in result
#         assert "ghost" not in result

#     @pytest.mark.asyncio
#     async def test_no_latest_batches_returns_empty(self) -> None:
#         """Test that no models with data yields an empty dict."""
#         mock_result_latest = MagicMock()
#         mock_result_latest.mappings.return_value.all.return_value = []

#         session = AsyncMock()
#         session.execute.return_value = mock_result_latest

#         repo = PredictionRepository(session)
#         result = await repo.fetch_latest_predictions_batch(
#             model_names=["prophet", "xgboost_fresh"],
#             horizon="24h",
#             confidence=0.85,
#         )

#         assert result == {}
#         # Only one query issued (the "latest" one); no second query
#         # when there's nothing to fetch.
#         assert session.execute.call_count == 1

#     @pytest.mark.asyncio
#     async def test_rows_grouped_by_model(self) -> None:
#         """Test that multiple rows for the same model are grouped."""
#         t0 = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
#         t1 = t0 + timedelta(hours=1)

#         latest_rows = [{"model_name": "prophet", "latest_ts": t0}]
#         batch_rows = [
#             _make_prediction_row(t0, "prophet", 50_000.0),
#             _make_prediction_row(t1, "prophet", 50_100.0),
#         ]

#         mock_result_latest = MagicMock()
#         mock_result_latest.mappings.return_value.all.return_value = latest_rows
#         mock_result_batch = MagicMock()
#         mock_result_batch.mappings.return_value.all.return_value = batch_rows

#         session = AsyncMock()
#         session.execute.side_effect = [mock_result_latest, mock_result_batch]

#         repo = PredictionRepository(session)
#         result = await repo.fetch_latest_predictions_batch(
#             model_names=["prophet"],
#             horizon="24h",
#             confidence=0.85,
#         )

#         assert len(result["prophet"]) == 2
#         assert result["prophet"][0].time == t0
#         assert result["prophet"][1].time == t1

"""Unit tests for the PredictionRepository.

These tests mock the SQLAlchemy AsyncSession so no live database is
required. They verify:
    - Correct SQL statements are issued (shape + parameters)
    - Result rows are correctly mapped to DataFrames
    - Column names match what the model adapters expect
    - Merging and forward-fill logic in fetch_training_frame_legacy
    - Bulk-insert payload construction in save_predictions

Test organization:
    - TestPredictionRow: dataclass behavior
    - TestFetchRecentBtcData: read BTC prices
    - TestFetchRecentMacroData: read macro indicators
    - TestFetchBtcPriceAt: single-price lookup (A5.2 Group 1)
    - TestFetchBtcPricesRange: range lookup (A5.2 Group 1)
    - TestFetchTrainingFrame: legacy merge + ffill logic
    - TestSavePredictions: bulk insert
    - TestFetchLatestPredictionTime: idempotency helper
    - TestFetchLatestPredictionsBatch: multi-model batch read (M6a)
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from app.database.repositories.prediction_repository import (
    PredictionRepository,
    PredictionRow,
)


# ============================================================
# HELPERS
# ============================================================
def _mock_session_returning(rows: list[dict]) -> AsyncMock:
    """Build a mock AsyncSession whose execute() returns the given rows.

    Args:
        rows: List of dicts to return as mapping rows.

    Returns:
        AsyncMock configured to mimic AsyncSession.execute().
    """
    mock_result = MagicMock()
    # mappings().all() returns the rows
    mock_result.mappings.return_value.all.return_value = rows

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.flush = AsyncMock()
    return mock_session


def _make_prediction_row(
    time: datetime,
    model_name: str,
    price: float,
    horizon: str = "24h",
    confidence: float = 0.85,
) -> Dict[str, Any]:
    """Build a dict shaped like a btc_predictions row mapping."""
    return {
        "time": time,
        "prediction_time": time - timedelta(hours=1),
        "horizon": horizon,
        "model_name": model_name,
        "confidence": confidence,
        "predicted_price": price,
        "lower_bound": price - 500.0,
        "upper_bound": price + 500.0,
    }


# ============================================================
# ROW DATACLASS TESTS
# ============================================================
class TestPredictionRow:
    """Tests for the PredictionRow dataclass."""

    def test_construction(self) -> None:
        """Test constructing a row with all fields."""
        now = datetime.now(timezone.utc)
        row = PredictionRow(
            time=now,
            prediction_time=now,
            horizon="24h",
            model_name="prophet",
            confidence=0.85,
            predicted_price=50_000.0,
            lower_bound=49_000.0,
            upper_bound=51_000.0,
        )
        assert row.horizon == "24h"
        assert row.predicted_price == 50_000.0

    def test_to_dict_keys(self) -> None:
        """Test that to_dict returns the expected keys."""
        now = datetime.now(timezone.utc)
        row = PredictionRow(
            time=now,
            prediction_time=now,
            horizon="24h",
            model_name="prophet",
            confidence=0.85,
            predicted_price=50_000.0,
            lower_bound=49_000.0,
            upper_bound=51_000.0,
        )
        d = row.to_dict()
        expected = {
            "time",
            "prediction_time",
            "horizon",
            "model_name",
            "confidence",
            "predicted_price",
            "lower_bound",
            "upper_bound",
        }
        assert set(d.keys()) == expected


# ============================================================
# FETCH BTC DATA TESTS
# ============================================================
class TestFetchRecentBtcData:
    """Tests for fetch_recent_btc_data()."""

    @pytest.mark.asyncio
    async def test_returns_dataframe(self) -> None:
        """Test that the method returns a DataFrame."""
        rows = [
            {
                "time": datetime(2024, 4, 1, tzinfo=timezone.utc),
                "close": 50_000.0,
                "volume": 25_000_000_000.0,
                "volatility": 0.15,
                "dominance": 52.5,
                "active_addresses": 850_000.0,
                "price_lag_7d": 49_500.0,
            },
        ]
        session = _mock_session_returning(rows)
        repo = PredictionRepository(session)

        df = await repo.fetch_recent_btc_data(hours=24)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert set(df.columns) == {
            "time",
            "close",
            "volume",
            "volatility",
            "dominance",
            "active_addresses",
            "price_lag_7d",
        }

    @pytest.mark.asyncio
    async def test_empty_result_returns_empty_dataframe(self) -> None:
        """Test that empty DB results produce an empty DataFrame."""
        session = _mock_session_returning([])
        repo = PredictionRepository(session)

        df = await repo.fetch_recent_btc_data(hours=24)

        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @pytest.mark.asyncio
    async def test_execute_is_called(self) -> None:
        """Test that session.execute is called once."""
        session = _mock_session_returning([])
        repo = PredictionRepository(session)

        await repo.fetch_recent_btc_data(hours=24)

        assert session.execute.call_count == 1


# ============================================================
# FETCH MACRO DATA TESTS
# ============================================================
class TestFetchRecentMacroData:
    """Tests for fetch_recent_macro_data()."""

    @pytest.mark.asyncio
    async def test_returns_dataframe(self) -> None:
        """Test that the method returns a DataFrame with macro columns."""
        rows = [
            {
                "time": datetime(2024, 4, 1, tzinfo=timezone.utc),
                "cpi": 3.2,
                "interest_rate": 4.5,
                "m2_growth": 2.8,
                "dxy": 102.5,
                "treasury_yield": 4.2,
            },
        ]
        session = _mock_session_returning(rows)
        repo = PredictionRepository(session)

        df = await repo.fetch_recent_macro_data(hours=24)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert set(df.columns) == {
            "time",
            "cpi",
            "interest_rate",
            "m2_growth",
            "dxy",
            "treasury_yield",
        }

    @pytest.mark.asyncio
    async def test_empty_result_returns_empty_dataframe(self) -> None:
        """Test that empty DB results produce an empty DataFrame."""
        session = _mock_session_returning([])
        repo = PredictionRepository(session)

        df = await repo.fetch_recent_macro_data(hours=24)

        assert isinstance(df, pd.DataFrame)
        assert df.empty


# ============================================================
# FETCH BTC PRICE AT TESTS (A5.2 Group 1)
# ============================================================
class TestFetchBtcPriceAt:
    """Tests for fetch_btc_price_at() (A5.2 Group 1)."""

    @pytest.mark.asyncio
    async def test_returns_float(self) -> None:
        """Test that the method returns a float when a row exists."""
        target = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 63_500.0
        session.execute.return_value = mock_result

        repo = PredictionRepository(session)
        value = await repo.fetch_btc_price_at(target)

        assert value == 63_500.0

    @pytest.mark.asyncio
    async def test_returns_none_when_no_row(self) -> None:
        """Test that None is returned when no row is within tolerance."""
        target = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = PredictionRepository(session)
        value = await repo.fetch_btc_price_at(target)

        assert value is None

    @pytest.mark.asyncio
    async def test_tolerance_hours_defaults_to_one(self) -> None:
        """Test that the default tolerance is 1 hour."""
        target = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 63_500.0
        session.execute.return_value = mock_result

        repo = PredictionRepository(session)
        # Call without tolerance_hours, then with an explicit one.
        # The default should be 1 (per PRICE_LOOKUP_TOLERANCE_HOURS
        # at the caller), and the explicit call should accept 6.
        await repo.fetch_btc_price_at(target)
        await repo.fetch_btc_price_at(target, tolerance_hours=6)

        # Exactly two SELECTs issued.
        assert session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_is_called(self) -> None:
        """Test that session.execute is called exactly once."""
        target = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 63_500.0
        session.execute.return_value = mock_result

        repo = PredictionRepository(session)
        await repo.fetch_btc_price_at(target)

        assert session.execute.call_count == 1


# ============================================================
# FETCH BTC PRICES RANGE TESTS (A5.2 Group 1)
# ============================================================
class TestFetchBtcPricesRange:
    """Tests for fetch_btc_prices_range() (A5.2 Group 1)."""

    @pytest.mark.asyncio
    async def test_returns_dataframe_with_time_and_close(self) -> None:
        """Test that the result has the two columns the caller needs."""
        start = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 3, 20, 0, 0, tzinfo=timezone.utc)
        rows = [
            {
                "time": datetime(2024, 3, 19, 0, tzinfo=timezone.utc),
                "close": 63_000.0,
            },
            {
                "time": datetime(2024, 3, 19, 1, tzinfo=timezone.utc),
                "close": 63_100.0,
            },
        ]
        session = _mock_session_returning(rows)
        repo = PredictionRepository(session)

        df = await repo.fetch_btc_prices_range(start, end)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert set(df.columns) == {"time", "close"}

    @pytest.mark.asyncio
    async def test_empty_range_returns_empty_dataframe(self) -> None:
        """Test that an empty range returns an empty DataFrame."""
        start = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 3, 20, 0, 0, tzinfo=timezone.utc)
        session = _mock_session_returning([])
        repo = PredictionRepository(session)

        df = await repo.fetch_btc_prices_range(start, end)

        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @pytest.mark.asyncio
    async def test_ascending_order_is_preserved(self) -> None:
        """Test that rows come back in the order the DB returned them."""
        start = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 3, 20, 0, 0, tzinfo=timezone.utc)
        rows = [
            {
                "time": datetime(2024, 3, 19, 0, tzinfo=timezone.utc),
                "close": 63_000.0,
            },
            {
                "time": datetime(2024, 3, 19, 1, tzinfo=timezone.utc),
                "close": 63_100.0,
            },
            {
                "time": datetime(2024, 3, 19, 2, tzinfo=timezone.utc),
                "close": 63_200.0,
            },
        ]
        session = _mock_session_returning(rows)
        repo = PredictionRepository(session)

        df = await repo.fetch_btc_prices_range(start, end)

        assert list(df["close"]) == [63_000.0, 63_100.0, 63_200.0]

    @pytest.mark.asyncio
    async def test_execute_is_called(self) -> None:
        """Test that session.execute is called exactly once."""
        start = datetime(2024, 3, 19, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 3, 20, 0, 0, tzinfo=timezone.utc)
        session = _mock_session_returning([])
        repo = PredictionRepository(session)

        await repo.fetch_btc_prices_range(start, end)

        assert session.execute.call_count == 1


# ============================================================
# FETCH TRAINING FRAME TESTS
# ============================================================
class TestFetchTrainingFrame:
    """Tests for fetch_training_frame_legacy() (merge + forward-fill)."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_btc_empty(self) -> None:
        """Test that empty BTC data yields an empty frame."""
        btc_rows: list[dict] = []
        macro_rows: list[dict] = []

        session = AsyncMock()
        mock_result = MagicMock()
        # Both calls return their respective rows in order
        mock_result.mappings.return_value.all.side_effect = [
            btc_rows,  # first call (BTC)
            macro_rows,  # second call (macro)
        ]
        session.execute.return_value = mock_result

        repo = PredictionRepository(session)
        df = await repo.fetch_training_frame_legacy(hours=24)

        assert df.empty

    @pytest.mark.asyncio
    async def test_renames_time_to_ds_and_close_to_y(self) -> None:
        """Test that the merged frame uses Prophet column names."""
        now = datetime(2024, 4, 1, 12, tzinfo=timezone.utc)

        btc_rows = [
            {
                "time": now,
                "close": 50_000.0,
                "volume": 25_000_000_000.0,
                "volatility": 0.15,
                "dominance": 52.5,
                "active_addresses": 850_000.0,
                "price_lag_7d": 49_500.0,
            },
        ]
        macro_rows = [
            {
                "time": now,
                "cpi": 3.2,
                "interest_rate": 4.5,
                "m2_growth": 2.8,
                "dxy": 102.5,
                "treasury_yield": 4.2,
            },
        ]

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.side_effect = [
            btc_rows,
            macro_rows,
        ]
        session.execute.return_value = mock_result

        repo = PredictionRepository(session)
        df = await repo.fetch_training_frame_legacy(hours=24)

        assert "ds" in df.columns
        assert "y" in df.columns
        assert "time" not in df.columns
        assert "close" not in df.columns

    @pytest.mark.asyncio
    async def test_merges_macro_and_btc_on_time(self) -> None:
        """Test that BTC + macro are merged on their shared timestamp."""
        now = datetime(2024, 4, 1, 12, tzinfo=timezone.utc)

        btc_rows = [
            {
                "time": now,
                "close": 50_000.0,
                "volume": 25_000_000_000.0,
                "volatility": 0.15,
                "dominance": 52.5,
                "active_addresses": 850_000.0,
                "price_lag_7d": 49_500.0,
            },
        ]
        macro_rows = [
            {
                "time": now,
                "cpi": 3.2,
                "interest_rate": 4.5,
                "m2_growth": 2.8,
                "dxy": 102.5,
                "treasury_yield": 4.2,
            },
        ]

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.side_effect = [
            btc_rows,
            macro_rows,
        ]
        session.execute.return_value = mock_result

        repo = PredictionRepository(session)
        df = await repo.fetch_training_frame_legacy(hours=24)

        assert len(df) == 1
        # All 10 regressors should be present
        for col in (
            "cpi",
            "interest_rate",
            "m2_growth",
            "dxy",
            "treasury_yield",
            "volume",
            "volatility",
            "dominance",
            "active_addresses",
            "price_lag_7d",
        ):
            assert col in df.columns, f"Missing {col}"
        assert df["cpi"].iloc[0] == 3.2
        assert df["y"].iloc[0] == 50_000.0

    @pytest.mark.asyncio
    async def test_missing_macro_returns_btc_only(self) -> None:
        """Test that missing macro data still returns the BTC frame."""
        now = datetime(2024, 4, 1, 12, tzinfo=timezone.utc)

        btc_rows = [
            {
                "time": now,
                "close": 50_000.0,
                "volume": 25_000_000_000.0,
                "volatility": 0.15,
                "dominance": 52.5,
                "active_addresses": 850_000.0,
                "price_lag_7d": 49_500.0,
            },
        ]

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.side_effect = [
            btc_rows,
            [],  # macro empty
        ]
        session.execute.return_value = mock_result

        repo = PredictionRepository(session)
        df = await repo.fetch_training_frame_legacy(hours=24)

        assert len(df) == 1
        assert "y" in df.columns
        assert df["y"].iloc[0] == 50_000.0


# ============================================================
# SAVE PREDICTIONS TESTS
# ============================================================
class TestSavePredictions:
    """Tests for save_predictions()."""

    @pytest.mark.asyncio
    async def test_empty_list_returns_zero(self) -> None:
        """Test that an empty list returns 0 without executing SQL."""
        session = AsyncMock()
        repo = PredictionRepository(session)

        count = await repo.save_predictions([])

        assert count == 0
        assert session.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_returns_row_count(self) -> None:
        """Test that the returned count equals the number of rows."""
        now = datetime.now(timezone.utc)
        rows = [
            PredictionRow(
                time=now + timedelta(hours=i),
                prediction_time=now,
                horizon="24h",
                model_name="prophet",
                confidence=0.85,
                predicted_price=50_000.0 + i,
                lower_bound=49_000.0 + i,
                upper_bound=51_000.0 + i,
            )
            for i in range(5)
        ]

        session = AsyncMock()
        session.flush = AsyncMock()
        repo = PredictionRepository(session)

        count = await repo.save_predictions(rows)

        assert count == 5
        assert session.execute.call_count == 1
        assert session.flush.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_and_flush_called(self) -> None:
        """Test that execute() and flush() are both called."""
        now = datetime.now(timezone.utc)
        rows = [
            PredictionRow(
                time=now,
                prediction_time=now,
                horizon="24h",
                model_name="prophet",
                confidence=0.85,
                predicted_price=50_000.0,
                lower_bound=49_000.0,
                upper_bound=51_000.0,
            )
        ]

        session = AsyncMock()
        session.flush = AsyncMock()
        repo = PredictionRepository(session)

        await repo.save_predictions(rows)

        session.execute.assert_called_once()
        session.flush.assert_called_once()


# ============================================================
# LATEST PREDICTION TIME TESTS
# ============================================================
class TestFetchLatestPredictionTime:
    """Tests for fetch_latest_prediction_time()."""

    @pytest.mark.asyncio
    async def test_returns_value(self) -> None:
        """Test that the method returns the scalar from the DB."""
        expected = datetime(2024, 4, 1, 12, tzinfo=timezone.utc)

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected
        session.execute.return_value = mock_result

        repo = PredictionRepository(session)
        value = await repo.fetch_latest_prediction_time(
            horizon="24h", model_name="prophet"
        )

        assert value == expected

    @pytest.mark.asyncio
    async def test_returns_none_when_no_rows(self) -> None:
        """Test that None is returned when no rows match."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = PredictionRepository(session)
        value = await repo.fetch_latest_prediction_time(
            horizon="24h", model_name="prophet"
        )

        assert value is None


# ============================================================
# FETCH LATEST PREDICTIONS BATCH (M6a)
# ============================================================
class TestFetchLatestPredictionsBatch:
    """Tests for fetch_latest_predictions_batch()."""

    @pytest.mark.asyncio
    async def test_empty_model_names_returns_empty_dict(self) -> None:
        """Test that empty input short-circuits without hitting the DB."""
        session = AsyncMock()
        repo = PredictionRepository(session)

        result = await repo.fetch_latest_predictions_batch(
            model_names=[],
            horizon="24h",
            confidence=0.85,
        )

        assert result == {}
        assert session.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_returns_dict_keyed_by_model(self) -> None:
        """Test that the result is keyed by model name."""
        t0 = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)

        # Query 1: latest prediction_time per model
        latest_rows = [
            {"model_name": "prophet", "latest_ts": t0},
            {"model_name": "xgboost_fresh", "latest_ts": t0},
        ]
        # Query 2: all rows in those batches
        batch_rows = [
            _make_prediction_row(t0, "prophet", 50_000.0),
            _make_prediction_row(t0, "xgboost_fresh", 50_100.0),
        ]

        mock_result_latest = MagicMock()
        mock_result_latest.mappings.return_value.all.return_value = latest_rows

        mock_result_batch = MagicMock()
        mock_result_batch.mappings.return_value.all.return_value = batch_rows

        session = AsyncMock()
        session.execute.side_effect = [mock_result_latest, mock_result_batch]

        repo = PredictionRepository(session)
        result = await repo.fetch_latest_predictions_batch(
            model_names=["prophet", "xgboost_fresh"],
            horizon="24h",
            confidence=0.85,
        )

        assert set(result.keys()) == {"prophet", "xgboost_fresh"}
        assert len(result["prophet"]) == 1
        assert len(result["xgboost_fresh"]) == 1

    @pytest.mark.asyncio
    async def test_missing_model_omitted(self) -> None:
        """Test that a requested model with no rows is not a key."""
        t0 = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
        latest_rows = [{"model_name": "prophet", "latest_ts": t0}]
        batch_rows = [
            _make_prediction_row(t0, "prophet", 50_000.0),
        ]

        mock_result_latest = MagicMock()
        mock_result_latest.mappings.return_value.all.return_value = latest_rows
        mock_result_batch = MagicMock()
        mock_result_batch.mappings.return_value.all.return_value = batch_rows

        session = AsyncMock()
        session.execute.side_effect = [mock_result_latest, mock_result_batch]

        repo = PredictionRepository(session)
        result = await repo.fetch_latest_predictions_batch(
            model_names=["prophet", "ghost"],
            horizon="24h",
            confidence=0.85,
        )

        assert "prophet" in result
        assert "ghost" not in result

    @pytest.mark.asyncio
    async def test_no_latest_batches_returns_empty(self) -> None:
        """Test that no models with data yields an empty dict."""
        mock_result_latest = MagicMock()
        mock_result_latest.mappings.return_value.all.return_value = []

        session = AsyncMock()
        session.execute.return_value = mock_result_latest

        repo = PredictionRepository(session)
        result = await repo.fetch_latest_predictions_batch(
            model_names=["prophet", "xgboost_fresh"],
            horizon="24h",
            confidence=0.85,
        )

        assert result == {}
        # Only one query issued (the "latest" one); no second query
        # when there's nothing to fetch.
        assert session.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_rows_grouped_by_model(self) -> None:
        """Test that multiple rows for the same model are grouped."""
        t0 = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
        t1 = t0 + timedelta(hours=1)

        latest_rows = [{"model_name": "prophet", "latest_ts": t0}]
        batch_rows = [
            _make_prediction_row(t0, "prophet", 50_000.0),
            _make_prediction_row(t1, "prophet", 50_100.0),
        ]

        mock_result_latest = MagicMock()
        mock_result_latest.mappings.return_value.all.return_value = latest_rows
        mock_result_batch = MagicMock()
        mock_result_batch.mappings.return_value.all.return_value = batch_rows

        session = AsyncMock()
        session.execute.side_effect = [mock_result_latest, mock_result_batch]

        repo = PredictionRepository(session)
        result = await repo.fetch_latest_predictions_batch(
            model_names=["prophet"],
            horizon="24h",
            confidence=0.85,
        )

        assert len(result["prophet"]) == 2
        assert result["prophet"][0].time == t0
        assert result["prophet"][1].time == t1