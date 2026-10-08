"""
FeatureBuilderService — the single source of truth for features_db.

build_features(start, end) returns a pandas DataFrame containing
the 53-column contract v2 feature vector for every hour in
[start, end), indexed by `ds` (UTC, hourly).

Consumers:

    - FeaturesDBWriter       — persists the full 53-column frame
                               to the features_db table.
    - FeaturesParquetWriter  — projects the frame through
                               SplitProcessor + FeatureScaler and
                               writes the 53-column hourly parquet
                               to processed_v2_builder/.

Both consumers call build_features(). No other module computes
features. This is the D22 guarantee: "feature_builder_service
and features_parquet_writer must produce identical values for
the same range; both must call
feature_builder_service.build_features() — never duplicate
logic."

Design notes
------------

1. Target semantics (D9).

   y at ds = btc_prices_hourly.close at ds + 1h.

   include_target=True:
       - computes y
       - returns 53 columns
       - drops the trailing row where y is NaN (the "frontier"
         hour, whose successor close is not yet knowable)

   include_target=False:
       - omits y
       - returns 52 columns
       - keeps every row in [start, end)

2. Three macro source rules (schemas doc §5).

   - Source 1 — macro_indicator_vintages (5 PIT series):
       cpi, federal_funds_rate, gdp, m2_money_supply,
       unemployment.
       Merged with pd.merge_asof: for each ds, pick the vintage
       row with the largest release_date <= ds. Tie-break on
       largest observation_date.

   - Source 2 — macro_indicators_hourly (2 direct series):
       dxy, ten_year_treasury (renamed from treasury_yield).
       No PIT merge; the hourly writer already materialized them
       and carried them forward. But note: the tracker for these
       two is computed from RAW macro_indicators (their real
       observation times), not from the hourly table.

   - Source 3 — raw macro_indicators (7 market features, ffill):
       active_addresses (limit 120h), gold_spot, vix,
       high_yield_spread, nasdaq_composite, equity_corr,
       high_yield_credit_stress_proxy.
       Each ffilled; separate is_imputed/missing flags where the
       schema requires them.

3. Trackers in HOURS with _days_since_* names (D8).

   All 14 observation/recency trackers store hours, not days.
   Column names keep the _days_since_* suffix per the AI
   Service contract. This is a semantic change from the daily
   parquet, which stored days: the same interval is 24x larger
   here.

   Each tracker is computed as:

       floor((ds - last_observed_at) / 1 hour)

   where `last_observed_at` is the maximum raw observation time
   for the feature, at or before ds. The raw source table gives
   this directly:

       - btc_dominance       -> btc_dominance.time
       - active_addresses    -> macro_indicators.time
       - gold_spot           -> macro_indicators.time
       - dxy                 -> macro_indicators.time
       - ten_year_treasury   -> macro_indicators.time
       - vix                 -> macro_indicators.time
       - nasdaq_composite    -> macro_indicators.time
       - equity_corr         -> macro_indicators.time
       - high_yield_credit_stress_proxy -> macro_indicators.time
       - cpi / federal_funds_rate / gdp / m2_money_supply /
         unemployment        -> macro_indicator_vintages.release_date
                                (anchored at midnight UTC)

4. Governance flags computed here, not in SplitProcessor.

   active_addresses_is_imputed, unemployment_is_imputed, and
   high_yield_spread_is_missing are all computed in this
   service, because they are columns of features_db (schema
   §3) and must exist for every row, independent of whether
   SplitProcessor is used downstream.

   Semantics:

   active_addresses_is_imputed:
       1  when ds - last_obs > 0 AND ds - last_obs <= 120h
          (value came from ffill, within the limit)
       0  when ds - last_obs == 0 (fresh observation)
       0  when ds - last_obs > 120h (value is NaN, not imputed)
       0  when last_obs is None (no prior observation at all;
          nothing to impute from)

   unemployment_is_imputed:
       1  when the PIT merge produced NaN for this ds
          (no release exists at or before ds)
       0  otherwise

       Note: this is a small divergence from the daily pipeline,
       which always produces 0 because the PIT merge always
       matched in practice. The daily behavior makes the flag
       meaningless. The hourly implementation marks pre-release
       hours as imputed.

   high_yield_spread_is_missing:
       1  when the value is still NaN after ffill
       0  otherwise

5. Read-only.

   build_features() only reads. It never writes to the database
   or to disk. Persistence is the caller's responsibility.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Literal

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------


# Volatility annualization for hourly data. A "1-day" log return
# at hourly resolution is 24 samples; the annualization factor is
# sqrt(365 * 24). Matches D11 and schemas doc §5 rows 26-27.
_HOURLY_ANNUALIZATION = float(np.sqrt(365.0 * 24.0))

# Ffill limit for active_addresses, per schemas doc §5 row 6.
_ACTIVE_ADDRESSES_FFILL_LIMIT_HOURS = 120

# The 5 PIT-prone vintage series, keyed by the indicator_name
# used in the vintages table and (after PIT merge) in features_db.
_VINTAGE_SERIES = (
    "cpi",
    "federal_funds_rate",
    "gdp",
    "m2_money_supply",
    "unemployment",
)

# The 7 ffilled raw-macro features, keyed by indicator_name in
# raw macro_indicators. active_addresses is handled separately
# because it has a ffill limit and an is_imputed flag.
_RAW_MACRO_FFILL = (
    "gold_spot",
    "vix",
    "high_yield_spread",
    "nasdaq_composite",
    "equity_corr",
    "high_yield_credit_stress_proxy",
)


# The 14 tracker columns, mapped to their raw source table and
# source key. Used by _attach_observation_trackers to issue one
# query per tracker.
#
# "raw"        -> macro_indicators, filtered by indicator_name
# "dominance"  -> btc_dominance
# "release"    -> macro_indicator_vintages, filtered by indicator_name
_TRACKER_SOURCES = {
    # tracker column name -> (source kind, source key)
    "btc_dominance_days_since_last_observation": (
        "dominance", None,
    ),
    "gold_spot_days_since_last_observation": (
        "raw", "gold_spot",
    ),
    "dxy_days_since_last_observation": (
        "raw", "dxy",
    ),
    "ten_year_treasury_days_since_last_observation": (
        "raw", "ten_year_treasury",
    ),
    "vix_days_since_last_observation": (
        "raw", "vix",
    ),
    "nasdaq_composite_days_since_last_observation": (
        "raw", "nasdaq_composite",
    ),
    "equity_corr_days_since_last_observation": (
        "raw", "equity_corr",
    ),
    "high_yield_credit_stress_proxy_days_since_last_observation": (
        "raw", "high_yield_credit_stress_proxy",
    ),
    "active_addresses_days_since_last_observation": (
        "raw", "active_addresses",
    ),
    "cpi_days_since_release": (
        "release", "cpi",
    ),
    "federal_funds_rate_days_since_release": (
        "release", "federal_funds_rate",
    ),
    "gdp_days_since_release": (
        "release", "gdp",
    ),
    "m2_money_supply_days_since_release": (
        "release", "m2_money_supply",
    ),
    "unemployment_days_since_release": (
        "release", "unemployment",
    ),
}


# The full 53-column list, in schema order. build_features()
# returns exactly these columns (minus y when
# include_target=False) in this order.
FEATURES_DB_COLUMNS = (
    "ds",
    "y",
    "btc_price",
    "btc_volume",
    "btc_dominance",
    "active_addresses",
    "gold_spot",
    "dxy",
    "ten_year_treasury",
    "vix",
    "high_yield_spread",
    "nasdaq_composite",
    "equity_corr",
    "high_yield_credit_stress_proxy",
    "cpi",
    "federal_funds_rate",
    "gdp",
    "m2_money_supply",
    "unemployment",
    "btc_log_return_1d",
    "btc_log_return_7d",
    "btc_log_return_30d",
    "btc_sma_7",
    "btc_sma_30",
    "btc_sma_90",
    "btc_volatility_7d",
    "btc_volatility_30d",
    "btc_gold_ratio",
    "btc_nasdaq_ratio",
    "high_yield_spread_is_missing",
    "active_addresses_is_imputed",
    "unemployment_is_imputed",
    "warmup_complete",
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
    "eng_price_lag_1d",
    "eng_price_lag_7d",
    "eng_price_lag_30d",
    "eng_returns_1d",
    "eng_returns_7d",
    "eng_returns_30d",
)


# The set of tracker columns, for the integer-cast loop in
# _finalize. Kept as a module-level constant so the cast doesn't
# have to string-match every column name every call.
_TRACKER_COLUMNS = frozenset(_TRACKER_SOURCES.keys())


# ------------------------------------------------------------------
# Service
# ------------------------------------------------------------------


class FeatureBuilderService:
    """
    Reads raw tables and returns features_db-shaped DataFrames.

    Stateless except for the injected Session. No writes, no
    side effects beyond logging.
    """

    def __init__(self, db: Session):
        self.db = db

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def build_features(
        self,
        start: datetime,
        end: datetime,
        *,
        resolution: Literal["hourly"] = "hourly",
        include_target: bool = True,
    ) -> pd.DataFrame:
        """
        Build the feature vector for every hour in [start, end).

        Args:
            start: inclusive UTC datetime, must be hour-aligned.
            end:   exclusive UTC datetime, must be hour-aligned.
            resolution: currently only "hourly" is supported.
            include_target:
                True  -> 53 columns, including y; drops the
                         trailing row whose y is NaN.
                False -> 52 columns, no y; keeps every row.

        Returns:
            DataFrame indexed by `ds` (UTC, hourly), with the
            columns listed in FEATURES_DB_COLUMNS (minus y when
            include_target=False).

        Raises:
            ValueError: if start or end is not hour-aligned, if
                start >= end, or if the requested resolution is
                not supported.
        """
        if resolution != "hourly":
            raise ValueError(
                f"Unsupported resolution: {resolution!r}. "
                f"Only 'hourly' is supported."
            )

        self._validate_range(start, end)

        logger.info(
            "Building features for [%s, %s) (include_target=%s)",
            start.isoformat(),
            end.isoformat(),
            include_target,
        )

        # The spine is the set of hours we build a row for. Every
        # other frame is attached onto it.
        spine = pd.DataFrame(
            {
                "ds": pd.date_range(
                    start, end, freq="h", inclusive="left"
                )
            }
        )

        # 1. BTC hourly (price, volume, dominance, active_addresses)
        spine = self._attach_btc_hourly(spine)

        # 2. Direct hourly macro (dxy, ten_year_treasury)
        spine = self._attach_hourly_macro(spine)

        # 3. Raw macro features (gold_spot, vix, etc.) with ffill
        spine = self._attach_raw_macro_ffill(spine)

        # 4. Vintage series (PIT merge)
        spine, release_at = self._attach_vintages_pit(spine)

        # 5. Trackers, in hours
        spine = self._attach_trackers(spine, release_at)

        # 6. Technical indicators and ratios
        spine = self._attach_technicals(spine)

        # 7. Governance flags
        spine = self._attach_flags(spine)

        # 8. Engineered features
        spine = self._attach_engineered(spine)

        # 9. Target (y), if requested
        if include_target:
            spine = self._attach_target(spine)

        # 10. Column ordering and dtype normalization
        spine = self._finalize(spine, include_target=include_target)

        logger.info(
            "Built %d feature row(s) across %d column(s)",
            len(spine),
            spine.shape[1],
        )

        return spine

    # ----------------------------------------------------------
    # Range validation
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

    # ----------------------------------------------------------
    # Step 1 — BTC hourly
    # ----------------------------------------------------------

    def _attach_btc_hourly(self, spine: pd.DataFrame) -> pd.DataFrame:
        """
        Attach btc_price, btc_volume, btc_dominance,
        active_addresses from btc_prices_hourly.
        """
        start = spine["ds"].iloc[0]
        end = spine["ds"].iloc[-1] + timedelta(hours=1)

        rows = self.db.execute(
            text(
                """
                SELECT
                    time AS ds,
                    close AS btc_price,
                    volume AS btc_volume,
                    dominance AS btc_dominance,
                    active_addresses
                FROM btc_prices_hourly
                WHERE time >= :start AND time < :end
                ORDER BY time
                """
            ),
            {"start": start, "end": end},
        ).mappings().all()

        if not rows:
            logger.warning(
                "No btc_prices_hourly rows in [%s, %s)",
                start.isoformat(),
                end.isoformat(),
            )
            df = pd.DataFrame(
                columns=[
                    "ds",
                    "btc_price",
                    "btc_volume",
                    "btc_dominance",
                    "active_addresses",
                ]
            )
        else:
            df = pd.DataFrame(rows)

        df["ds"] = pd.to_datetime(df["ds"], utc=True)

        return spine.merge(df, on="ds", how="left")

    # ----------------------------------------------------------
    # Step 2 — direct hourly macro
    # ----------------------------------------------------------

    def _attach_hourly_macro(self, spine: pd.DataFrame) -> pd.DataFrame:
        """
        Attach dxy and ten_year_treasury from
        macro_indicators_hourly.
        """
        start = spine["ds"].iloc[0]
        end = spine["ds"].iloc[-1] + timedelta(hours=1)

        rows = self.db.execute(
            text(
                """
                SELECT
                    time AS ds,
                    dxy AS dxy,
                    treasury_yield AS ten_year_treasury
                FROM macro_indicators_hourly
                WHERE time >= :start AND time < :end
                ORDER BY time
                """
            ),
            {"start": start, "end": end},
        ).mappings().all()

        if not rows:
            logger.warning(
                "No macro_indicators_hourly rows in [%s, %s)",
                start.isoformat(),
                end.isoformat(),
            )
            df = pd.DataFrame(
                columns=["ds", "dxy", "ten_year_treasury"]
            )
        else:
            df = pd.DataFrame(rows)

        df["ds"] = pd.to_datetime(df["ds"], utc=True)

        return spine.merge(df, on="ds", how="left")

    # ----------------------------------------------------------
    # Step 3 — raw macro features, ffilled
    # ----------------------------------------------------------

    def _attach_raw_macro_ffill(self, spine: pd.DataFrame) -> pd.DataFrame:
        """
        Attach the 7 ffilled raw macro features.

        Reads from raw macro_indicators, pivots wide, reindexes
        onto the hourly spine, and ffills.

        active_addresses gets special handling: it is already
        present from step 1 (via btc_prices_hourly), and only
        NULLs from that step are filled from the raw source with
        a 120h limit. The pre-ffill pattern is retained as a
        helper column so is_imputed can be computed in step 7.
        """
        start = spine["ds"].iloc[0]
        end = spine["ds"].iloc[-1] + timedelta(hours=1)

        # Over-fetch by 168h so early spine rows can see the last
        # observation before `start`.
        lookback_start = start - timedelta(hours=168)

        all_names = list(_RAW_MACRO_FFILL) + ["active_addresses"]
        placeholders = ", ".join(
            f":name_{i}" for i in range(len(all_names))
        )
        params: dict = {"start": lookback_start, "end": end}
        for i, name in enumerate(all_names):
            params[f"name_{i}"] = name

        rows = self.db.execute(
            text(
                f"""
                SELECT time, indicator_name, value
                FROM macro_indicators
                WHERE indicator_name IN ({placeholders})
                  AND time >= :start AND time < :end
                ORDER BY time
                """
            ),
            params,
        ).mappings().all()

        if not rows:
            logger.warning(
                "No raw macro_indicators rows in [%s, %s)",
                lookback_start.isoformat(),
                end.isoformat(),
            )
            return spine

        raw = pd.DataFrame(rows)
        raw["time"] = pd.to_datetime(raw["time"], utc=True)

        wide = raw.pivot_table(
            index="time",
            columns="indicator_name",
            values="value",
            aggfunc="last",
        )

        # Reindex onto the spine and ffill.
        wide = wide.reindex(spine["ds"], method=None)

        # Keep a copy of the pre-ffill pattern for active_addresses
        # and high_yield_spread. Used by step 7.
        spine = spine.copy()
        spine["_active_addresses_observed_now"] = wide.get(
            "active_addresses"
        )
        spine["_high_yield_spread_observed_now"] = wide.get(
            "high_yield_spread"
        )

        wide = wide.ffill()

        # Replace the active_addresses column with the raw-ffilled
        # value only where step 1 produced NULL.
        if "active_addresses" in wide.columns:
            spine["active_addresses"] = spine[
                "active_addresses"
            ].fillna(wide["active_addresses"])

        # The other raw-macro features go straight from the wide
        # ffill frame.
        for col in _RAW_MACRO_FFILL:
            if col in wide.columns:
                spine[col] = wide[col].values
            else:
                spine[col] = np.nan

        return spine

    # ----------------------------------------------------------
    # Step 4 — vintages PIT merge
    # ----------------------------------------------------------

    def _attach_vintages_pit(
        self, spine: pd.DataFrame
    ) -> tuple[pd.DataFrame, dict[str, pd.Series]]:
        """
        Attach the 5 PIT-merged vintage series.

        For each ds, the value of each series is the one from
        the vintage row with the largest release_date <= ds.
        Tie-break: largest observation_date.

        release_date is a DATE; anchor it at 00:00:00 UTC for
        the merge, per the Chat 5 Q4 decision.

        Also returns a {series: release_at_series} dict, keyed
        by indicator_name, so step 5 can compute the release
        trackers without re-querying.
        """
        start = spine["ds"].iloc[0]
        end = spine["ds"].iloc[-1] + timedelta(hours=1)

        spine = spine.copy().sort_values("ds").reset_index(drop=True)
        release_at: dict[str, pd.Series] = {}

        for indicator_name in _VINTAGE_SERIES:
            rows = self.db.execute(
                text(
                    """
                    SELECT
                        observation_date,
                        release_date,
                        value
                    FROM macro_indicator_vintages
                    WHERE indicator_name = :name
                      AND release_date <= :end_date
                    ORDER BY release_date, observation_date
                    """
                ),
                {
                    "name": indicator_name,
                    "end_date": end.date(),
                },
            ).mappings().all()

            if not rows:
                logger.warning(
                    "No vintage rows for %s (release_date <= %s)",
                    indicator_name,
                    end.date(),
                )
                spine[indicator_name] = np.nan
                release_at[indicator_name] = pd.Series(
                    pd.NaT, index=spine.index, dtype="datetime64[ns, UTC]"
                )
                continue

            vdf = pd.DataFrame(rows)
            vdf["release_at"] = pd.to_datetime(
                vdf["release_date"], utc=True
            )
            vdf = (
                vdf.sort_values(
                    ["release_at", "observation_date"]
                )
                .drop_duplicates(
                    subset=["release_at"], keep="last"
                )
                .sort_values("release_at")
                .reset_index(drop=True)
            )

            merged = pd.merge_asof(
                spine[["ds"]],
                vdf[["release_at", "value"]].rename(
                    columns={"value": indicator_name}
                ),
                left_on="ds",
                right_on="release_at",
                direction="backward",
            )

            spine[indicator_name] = merged[indicator_name].values
            release_at[indicator_name] = pd.Series(
                merged["release_at"].values, index=spine.index
            ).dt.tz_convert("UTC")

        return spine, release_at

    # ----------------------------------------------------------
    # Step 5 — trackers (hours since last real observation)
    # ----------------------------------------------------------

    def _attach_trackers(
        self,
        spine: pd.DataFrame,
        release_at: dict[str, pd.Series],
    ) -> pd.DataFrame:
        """
        Attach the 14 tracker columns, in HOURS.

        For observation trackers (9), issues one query per
        tracker that returns "max(time) at or before ds" for the
        feature's raw source. The query uses generate_series so
        one round-trip returns the entire range.

        For release trackers (5), uses the release_at series
        computed in step 4. No additional queries.
        """
        spine = spine.copy()
        start = spine["ds"].iloc[0]
        end = spine["ds"].iloc[-1] + timedelta(hours=1)

        for tracker_col, (kind, key) in _TRACKER_SOURCES.items():
            if kind == "release":
                # Use the release_at series from step 4.
                release_series = release_at.get(key)
                if release_series is None:
                    spine[tracker_col] = 0
                    continue
                delta = spine["ds"] - release_series.values
                hours = (
                    delta.dt.total_seconds() / 3600.0
                ).fillna(0.0)
                # Floor to integer. Negative values (shouldn't
                # happen after a PIT merge) clamp to 0.
                spine[tracker_col] = (
                    np.floor(hours).clip(lower=0).astype("int64")
                )
                continue

            # Observation tracker: query the raw source for the
            # latest observation time at or before each ds.
            last_obs = self._query_last_observation(
                kind=kind,
                key=key,
                start=start,
                end=end,
                spine_ds=spine["ds"],
            )

            delta = spine["ds"] - last_obs
            hours = (delta.dt.total_seconds() / 3600.0)
            # Where there's no prior observation, tracker = 0
            # (matching the daily pipeline's convention of 0 for
            # "no observation yet").
            spine[tracker_col] = (
                np.floor(hours.fillna(0.0))
                .clip(lower=0)
                .astype("int64")
            )

        return spine

    def _query_last_observation(
        self,
        *,
        kind: str,
        key: str | None,
        start: datetime,
        end: datetime,
        spine_ds: pd.Series,
    ) -> pd.Series:
        """
        Return a Series aligned with spine_ds containing, for
        each ds, the max observation time at or before ds for
        the given raw source.

        kind:
            "raw"       -> macro_indicators WHERE indicator_name=key
            "dominance" -> btc_dominance

        Returns a Series of UTC datetimes (NaT when no prior
        observation exists). The spine_ds is used only for its
        index; the SQL results are matched by ds.
        """
        if kind == "dominance":
            sql = text(
                """
                WITH spine AS (
                    SELECT generate_series(
                        :start, :end_inclusive, interval '1 hour'
                    ) AS ds
                )
                SELECT
                    s.ds AS ds,
                    (
                        SELECT max(time) FROM btc_dominance b
                        WHERE b.time <= s.ds
                    ) AS last_obs
                FROM spine s
                ORDER BY s.ds
                """
            )
            params = {
                "start": start,
                "end_inclusive": end - timedelta(hours=1),
            }
        elif kind == "raw":
            sql = text(
                """
                WITH spine AS (
                    SELECT generate_series(
                        :start, :end_inclusive, interval '1 hour'
                    ) AS ds
                )
                SELECT
                    s.ds AS ds,
                    (
                        SELECT max(time) FROM macro_indicators m
                        WHERE m.indicator_name = :name
                          AND m.time <= s.ds
                    ) AS last_obs
                FROM spine s
                ORDER BY s.ds
                """
            )
            params = {
                "name": key,
                "start": start,
                "end_inclusive": end - timedelta(hours=1),
            }
        else:
            raise ValueError(f"Unknown tracker kind: {kind!r}")

        rows = self.db.execute(sql, params).all()

        if not rows:
            return pd.Series(
                pd.NaT,
                index=spine_ds.index,
                dtype="datetime64[ns, UTC]",
            )

        result = pd.DataFrame(rows, columns=["ds", "last_obs"])
        result["ds"] = pd.to_datetime(result["ds"], utc=True)
        # last_obs may be NULL; pandas converts to NaT.
        result["last_obs"] = pd.to_datetime(result["last_obs"], utc=True)

        # Align onto the spine.
        merged = (
            pd.DataFrame({"ds": spine_ds.values})
            .merge(result, on="ds", how="left")
        )

        return merged["last_obs"].reset_index(drop=True)

    # ----------------------------------------------------------
    # Step 6 — technical indicators and ratios
    # ----------------------------------------------------------

    def _attach_technicals(self, spine: pd.DataFrame) -> pd.DataFrame:
        """
        Attach the 10 technical columns. Matches schemas doc §5
        rows 20-29. All rolling windows are in HOURS: 7d=168,
        30d=720, 90d=2160 (D11).
        """
        spine = spine.copy().sort_values("ds").reset_index(drop=True)
        close = spine["btc_price"]

        # Log returns
        spine["btc_log_return_1d"] = np.log(close / close.shift(24))
        spine["btc_log_return_7d"] = np.log(close / close.shift(168))
        spine["btc_log_return_30d"] = np.log(close / close.shift(720))

        # SMAs
        spine["btc_sma_7"] = close.rolling(168, min_periods=168).mean()
        spine["btc_sma_30"] = close.rolling(720, min_periods=720).mean()
        spine["btc_sma_90"] = close.rolling(
            2160, min_periods=2160
        ).mean()

        # Rolling volatility of 1-day log returns
        vol_input = spine["btc_log_return_1d"]
        spine["btc_volatility_7d"] = (
            vol_input.rolling(168, min_periods=168).std(ddof=1)
            * _HOURLY_ANNUALIZATION
        )
        spine["btc_volatility_30d"] = (
            vol_input.rolling(720, min_periods=720).std(ddof=1)
            * _HOURLY_ANNUALIZATION
        )

        # Cross-asset ratios
        spine["btc_gold_ratio"] = spine["btc_price"] / spine["gold_spot"]
        spine["btc_nasdaq_ratio"] = (
            spine["btc_price"] / spine["nasdaq_composite"]
        )

        return spine

    # ----------------------------------------------------------
    # Step 7 — governance flags
    # ----------------------------------------------------------

    def _attach_flags(self, spine: pd.DataFrame) -> pd.DataFrame:
        """
        Attach the 4 governance flags.

        active_addresses_is_imputed:
            1  where ds - last_obs in (0, 120] (came from ffill)
            0  where ds - last_obs == 0 (fresh observation)
            0  where last_obs is None or gap > 120h

        unemployment_is_imputed:
            1  where the PIT merge produced NaN (no release before ds)
            0  otherwise

        high_yield_spread_is_missing:
            1  where the value is still NaN after ffill
            0  otherwise

        warmup_complete:
            1  where btc_sma_90 is not NaN
            0  otherwise
        """
        spine = spine.copy()

        # active_addresses_is_imputed.
        # The tracker column already stores hours since last obs.
        # Imputed when >0 and <= 120. Note this ignores the case
        # where the value is NaN (gap > 120h): in that case the
        # tracker is 0 (default) and the flag is 0. Matches the
        # semantics you confirmed.
        aa_tracker = spine[
            "active_addresses_days_since_last_observation"
        ]
        aa_is_observed_now = spine[
            "active_addresses"
        ].notna() & (aa_tracker == 0)
        # A row is imputed if the value is present but the
        # tracker says we're not on the observation hour.
        spine["active_addresses_is_imputed"] = (
            spine["active_addresses"].notna()
            & (~aa_is_observed_now)
            & (aa_tracker <= _ACTIVE_ADDRESSES_FFILL_LIMIT_HOURS)
        ).astype("int64")

        # unemployment_is_imputed: 1 where PIT merge produced NaN.
        spine["unemployment_is_imputed"] = (
            spine["unemployment"].isna().astype("int64")
        )

        # high_yield_spread_is_missing: 1 where NaN after ffill.
        spine["high_yield_spread_is_missing"] = (
            spine["high_yield_spread"].isna().astype("int64")
        )

        # warmup_complete.
        spine["warmup_complete"] = (
            spine["btc_sma_90"].notna().astype("int64")
        )

        # Drop helper columns added by step 3.
        spine = spine.drop(
            columns=[
                "_active_addresses_observed_now",
                "_high_yield_spread_observed_now",
            ],
            errors="ignore",
        )

        return spine

    # ----------------------------------------------------------
    # Step 8 — engineered features
    # ----------------------------------------------------------

    def _attach_engineered(self, spine: pd.DataFrame) -> pd.DataFrame:
        """
        Attach the 6 engineered features. Matches schemas doc §5
        rows 48-53.
        """
        spine = spine.copy()
        close = spine["btc_price"]

        spine["eng_price_lag_1d"] = close.shift(24)
        spine["eng_price_lag_7d"] = close.shift(168)
        spine["eng_price_lag_30d"] = close.shift(720)

        spine["eng_returns_1d"] = spine["btc_log_return_1d"]
        spine["eng_returns_7d"] = spine["btc_log_return_7d"]
        spine["eng_returns_30d"] = spine["btc_log_return_30d"]

        return spine

    # ----------------------------------------------------------
    # Step 9 — target
    # ----------------------------------------------------------

    def _attach_target(self, spine: pd.DataFrame) -> pd.DataFrame:
        """
        Attach y = close at ds + 1h, then drop the trailing row
        where y is NaN.
        """
        spine = spine.copy().sort_values("ds").reset_index(drop=True)
        spine["y"] = spine["btc_price"].shift(-1)

        before = len(spine)
        spine = spine[spine["y"].notna()].reset_index(drop=True)
        after = len(spine)
        if before != after:
            logger.debug(
                "Dropped %d trailing frontier row(s) with NaN y",
                before - after,
            )

        return spine

    # ----------------------------------------------------------
    # Step 10 — column ordering and dtype normalization
    # ----------------------------------------------------------

    def _finalize(
        self,
        spine: pd.DataFrame,
        *,
        include_target: bool,
    ) -> pd.DataFrame:
        """
        Order columns per FEATURES_DB_COLUMNS and cast to the
        schema's types.
        """
        spine = spine.copy()

        expected = [
            c
            for c in FEATURES_DB_COLUMNS
            if include_target or c != "y"
        ]
        for col in expected:
            if col not in spine.columns:
                spine[col] = np.nan

        spine = spine.set_index("ds")
        spine = spine[expected[1:]]

        # Cast integer columns.
        for col in spine.columns:
            if (
                col in _TRACKER_COLUMNS
                or col.endswith("_is_missing")
                or col.endswith("_is_imputed")
                or col == "warmup_complete"
            ):
                spine[col] = spine[col].fillna(0).astype("int64")

        return spine


# ------------------------------------------------------------------
# Module-level convenience
# ------------------------------------------------------------------


def build_features(
    db: Session,
    start: datetime,
    end: datetime,
    *,
    include_target: bool = True,
) -> pd.DataFrame:
    """
    Convenience wrapper. Equivalent to
    FeatureBuilderService(db).build_features(start, end,
    include_target=include_target).
    """
    return FeatureBuilderService(db).build_features(
        start, end, include_target=include_target
    )