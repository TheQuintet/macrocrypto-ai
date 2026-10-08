"""
FeaturesParquetWriter — writes the hourly parquet for Option B.

Produces five artifacts in app/data/processed_v2_builder/:

    train_scaled.parquet
    val_scaled.parquet
    test_scaled.parquet
    live_frontier_scaled.parquet
    feature_scaler.pkl

Input pipeline:

    build_features(include_target=False)        # 52 columns
        |
        v
    SplitProcessor.process(df)                  # adds target_next_price,
        |                                       # splits, applies purges
        v
    rename target_next_price -> y               # 53 columns
        |
        v
    FeatureScaler.fit_transform(train)          # scales training set
    FeatureScaler.transform(val/test/frontier)  # uses fitted params
        |
        v
    five files on disk

Design notes
------------

1. Parquet contract is 53 columns, matching features_db.

   The frozen daily parquet in app/data/processed/ has 47
   columns; that is a separate, isolated, frozen artifact. See
   docs/data-service-schemas.md §3 and the B4 plan for detail.

2. include_target=False on the input.

   SplitProcessor internally uses TargetGenerator to derive the
   target column. If we passed include_target=True, the frame
   would already have `y` and the resulting parquet would carry
   both `y` and `target_next_price` (54 columns). Passing
   include_target=False lets SplitProcessor own the target
   computation, then we rename back to `y` to satisfy the
   features_db contract.

3. SplitProcessor and FeatureScaler are shared with the daily
   pipeline and are not modified.

   We pass explicitly-constructed SplitConfig and ScalerConfig
   with hourly values, rather than relying on the defaults
   (which are daily-oriented).

4. FeatureScaler is fit on the train split only.

   Per D8 and the B5 Q8 answer. Val, test, and frontier are
   transformed with the train-fitted parameters.

5. feature_scaler.pkl is the fitted FeatureScaler wrapper.

   Pickled as-is. The AI Service's FeatureLoader can unpickle
   the object and use .transform() on new data.

6. Write directory is created if missing.

   app/data/processed_v2_builder/ is the Option B output dir per
   D20. It is NOT app/data/processed/ (which is frozen, D13).
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.ml.feature_scaler import FeatureScaler
from app.ml.scaler_config import ScalerConfig
from app.ml.split_processor import SplitProcessor
from app.ml.splitting_config import SplitConfig
from app.services.feature_builder_service import (
    FeatureBuilderService,
)


logger = logging.getLogger(__name__)


# Output directory. Relative to the data-service working
# directory. Matches D20 (processed_v2_builder/).
PARQUET_OUTPUT_DIR = Path("app/data/processed_v2_builder")


# The 14 tracker columns. Listed here so ScalerConfig can
# exclude them explicitly (they are integers and must not be
# scaled).
_TRACKER_COLUMNS = (
    "btc_dominance_days_since_last_observation",
    "gold_spot_days_since_last_observation",
    "dxy_days_since_last_observation",
    "ten_year_treasury_days_since_last_observation",
    "vix_days_since_last_observation",
    "nasdaq_composite_days_since_last_observation",
    "equity_corr_days_since_last_observation",
    "high_yield_credit_stress_proxy_days_since_last_observation",
    "active_addresses_days_since_last_observation",
    "cpi_days_since_release",
    "federal_funds_rate_days_since_release",
    "gdp_days_since_release",
    "m2_money_supply_days_since_release",
    "unemployment_days_since_release",
)


# The four flags. Also excluded from scaling.
_FLAG_COLUMNS = (
    "high_yield_spread_is_missing",
    "active_addresses_is_imputed",
    "unemployment_is_imputed",
    "warmup_complete",
)


def _hourly_split_config() -> SplitConfig:
    """
    SplitConfig with hourly-appropriate purge/embargo windows.

    purge_window=2160 (90 days of hours) covers the longest
    rolling feature window (btc_sma_90 at 2160 hours).

    embargo_window=168 (7 days of hours) between val and test.

    Per D11 and schemas doc §7.
    """
    return SplitConfig(
        purge_window=2160,
        embargo_window=168,
    )


def _hourly_scaler_config() -> ScalerConfig:
    """
    ScalerConfig with hourly-appropriate exclusions.

    target_column="y"            — matches features_db contract
    date_column="ds"             — ditto
    explicit_exclusions:
        warmup_complete          — flag, not a feature
        high_yield_spread        — spec says do not scale
        all 14 trackers          — integers
        all 4 flags              — integers
    """
    return ScalerConfig(
        target_column="y",
        date_column="ds",
        exclude_suffixes=[
            "_timestamp",
            "_is_missing",
            "_is_imputed",
        ],
        explicit_exclusions=[
            "warmup_complete",
            "high_yield_spread",
            *_TRACKER_COLUMNS,
            *_FLAG_COLUMNS,
        ],
    )


class FeaturesParquetWriter:
    """
    Produce the Option B hourly parquet set.

    Usage:

        db = SessionLocal()
        writer = FeaturesParquetWriter(db)
        writer.write_all(start, end)

    The output directory and five files are described in the
    module docstring.
    """

    def __init__(
        self,
        db: Session,
        output_dir: Path | None = None,
    ):
        self.db = db
        self.builder = FeatureBuilderService(db)
        self.output_dir = output_dir or PARQUET_OUTPUT_DIR

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def write_all(
        self,
        start: datetime,
        end: datetime,
    ) -> dict[str, Any]:
        """
        Build, split, scale, and write the five artifacts for
        [start, end).

        Args:
            start: inclusive UTC, hour-aligned.
            end:   exclusive UTC, hour-aligned.

        Returns a summary dict:

            {
              "train_rows":           int,
              "val_rows":             int,
              "test_rows":            int,
              "frontier_rows":        int,
              "purged_embargo_rows":  int,
              "output_dir":           str,
            }

        Raises:
            ValueError: on invalid range, empty training split,
                or any NaN in the training feature columns.
        """
        self._validate_range(start, end)

        logger.info(
            "FeaturesParquetWriter: building for [%s, %s)",
            start.isoformat(),
            end.isoformat(),
        )

        # 1. Build the 52-column frame (no y; SplitProcessor
        #    adds target_next_price).
        df = self.builder.build_features(
            start, end, include_target=False
        )

        if df.empty:
            raise ValueError(
                f"build_features returned no rows for "
                f"[{start.isoformat()}, {end.isoformat()})"
            )

        # The `ds` index is a column again for SplitProcessor
        # (it works on regular frames).
        df = df.reset_index()

        logger.info(
            "Built %d feature row(s) across %d column(s) "
            "before split",
            len(df),
            df.shape[1],
        )

        # 2. Split. SplitProcessor drops warmup_complete==0,
        #    drops NaN active_addresses, adds target_next_price,
        #    pulls out the live frontier, and applies purge /
        #    embargo buffers.
        processor = SplitProcessor(_hourly_split_config())
        result = processor.process(df)

        train = result["train"]
        val = result["val"]
        test = result["test"]
        frontier = result["frontier"]

        logger.info(
            "Split: train=%d val=%d test=%d frontier=%d "
            "(purged+embargoed=%d)",
            len(train),
            len(val),
            len(test),
            len(frontier),
            result["purged_embargo_rows"],
        )

        if train.empty:
            raise ValueError(
                "Training split is empty after split/purge. "
                "The requested range is too short."
            )

        # 3. Rename target_next_price -> y and restore `ds` as
        #    the index. After rename, each frame has 53 columns
        #    (52 features + y) plus observation_date as a column.
        train = self._post_split_fixup(train)
        val = self._post_split_fixup(val)
        test = self._post_split_fixup(test)
        frontier = self._post_split_fixup(frontier)

        # 4. Fit the scaler on train, transform all four splits.
        scaler = FeatureScaler(_hourly_scaler_config())
        train_scaled = scaler.fit_transform(train)
        val_scaled = scaler.transform(val)
        test_scaled = scaler.transform(test)

        # Frontier may be empty (last row) — guard the empty
        # case; the daily pipeline does not call transform on an
        # empty frame.
        if not frontier.empty:
            frontier_scaled = scaler.transform(frontier)
        else:
            logger.warning(
                "Live frontier is empty; writing an empty parquet"
            )
            frontier_scaled = frontier.copy()

        # 5. Write five artifacts.
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._write_parquet(train_scaled, "train_scaled.parquet")
        self._write_parquet(val_scaled, "val_scaled.parquet")
        self._write_parquet(test_scaled, "test_scaled.parquet")
        self._write_parquet(
            frontier_scaled, "live_frontier_scaled.parquet"
        )
        self._write_scaler(scaler, "feature_scaler.pkl")

        summary = {
            "train_rows": len(train_scaled),
            "val_rows": len(val_scaled),
            "test_rows": len(test_scaled),
            "frontier_rows": len(frontier_scaled),
            "purged_embargo_rows": result["purged_embargo_rows"],
            "output_dir": str(self.output_dir),
        }

        logger.info(
            "FeaturesParquetWriter: done. Wrote %s",
            summary,
        )

        return summary

    # ----------------------------------------------------------
    # Internals
    # ----------------------------------------------------------

    @staticmethod
    def _validate_range(start: datetime, end: datetime) -> None:
        for name, dt in (("start", start), ("end", end)):
            if dt.tzinfo is None:
                raise ValueError(
                    f"{name} must be timezone-aware (UTC)"
                )
            if dt.utcoffset() != timedelta(0):
                raise ValueError(
                    f"{name} must be UTC; got offset "
                    f"{dt.utcoffset()}"
                )
            if (
                dt.minute != 0
                or dt.second != 0
                or dt.microsecond != 0
            ):
                raise ValueError(
                    f"{name} must be hour-aligned; got "
                    f"{dt.isoformat()}"
                )
        if end <= start:
            raise ValueError(
                f"end ({end.isoformat()}) must be after "
                f"start ({start.isoformat()})"
            )

    @staticmethod
    def _post_split_fixup(df):
        """
        Post-process a split frame:
            - rename target_next_price -> y
            - restore `ds` as the index

        SplitProcessor uses observation_date as the date column
        (via TargetGenerator's shift on btc_price) and adds a
        target_next_price column. features_db uses ds and y.
        """
        if df.empty:
            # Nothing to rename; return as-is.
            return df

        renamed = df.rename(
            columns={"target_next_price": "y"}
        )

        # `ds` came from build_features' index; split_processor
        # passed it through as a regular column. Move it back
        # to the index.
        if "ds" in renamed.columns:
            renamed = renamed.set_index("ds")

        return renamed

    def _write_parquet(self, df, filename: str) -> None:
        """
        Write a DataFrame to parquet. Logs the shape for
        operator visibility.
        """
        path = self.output_dir / filename
        df.to_parquet(path, index=True)
        logger.info(
            "Wrote %s (%d rows, %d cols)",
            path,
            len(df),
            df.shape[1],
        )

    def _write_scaler(self, scaler: FeatureScaler, filename: str) -> None:
        """
        Pickle the fitted FeatureScaler wrapper.

        The AI Service's FeatureLoader reads the file and uses
        the wrapper's .transform() method on new data.
        """
        path = self.output_dir / filename
        with open(path, "wb") as f:
            pickle.dump(scaler, f)
        logger.info(
            "Wrote %s (feature_columns=%d)",
            path,
            len(scaler.feature_columns),
        )