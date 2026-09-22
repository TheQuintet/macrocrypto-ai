"""BTC-vs-macro correlation calculation.

Computes the Pearson correlation between BTC price and each
macroeconomic indicator over rolling windows, then persists the
results via CorrelationRepository.

Design:
    - Two layers:
        1. Pure functions: `pearson_correlation`, `classify_strength`,
           `classify_direction`, `derive_significance`,
           `confidence_from_p_value`. No I/O. Trivially testable.
        2. Orchestrator: `CorrelationCalculator`. Fetches source
           data, resamples it, runs the pure functions, writes rows.
    - Async (repository calls are async)
    - Fails softly: one bad (indicator, window) pair does not abort
      the rest. Skips and errors are captured in the result.
    - Does not commit — the caller controls the transaction

Data flow:
    1. Fetch hourly BTC close prices for max(WINDOWS) + 1 days
    2. Resample to daily close (last close per UTC day)
    3. Fetch daily macro data (already one row per day per indicator)
    4. For each (indicator, window):
        a. If the indicator's source column is None → skip
        b. Take the last `window` days of BTC daily
        c. Take the same time range of macro daily
        d. Inner-join on date → two aligned series
        e. Compute Pearson correlation and its p-value
        f. Classify strength and direction
        g. Build a CorrelationRow

Source column mapping:
    The `INDICATOR_SOURCE_COLUMNS` mapping is the single point of
    truth for indicator → source column. `gdp` and `unemployment`
    currently map to None because the Data Ingestion Service does
    not yet write those columns to `macro_indicators`. When it does,
    change those two entries here — nothing else in the codebase
    needs to change.

Strength/direction thresholds:
    A1.3 owns the exact thresholds. The implementations of
    `classify_strength` and `classify_direction` in this module are
    the canonical source for the thresholds. Callers should not
    reimplement the classification.

Presentation layer (A1.3):
    `strength_color` and `direction_arrow` translate the labels
    produced by `classify_strength` and `classify_direction` into
    the visual hints the API and export layers expose (colors and
    arrows). Both functions reject unknown labels with a ValueError
    so a mismatch between classification and presentation cannot be
    silently wrong.

Statistical significance (A1.4):
    `pearson_correlation` now returns a three-tuple
    (coefficient, p_value, sample_size). The p-value comes from
    scipy.stats.pearsonr, which implements the standard t-based
    two-tailed significance test for Pearson correlation.

    `derive_significance(p_value)` applies the significance rule
    (p_value < SIGNIFICANCE_THRESHOLD, where the threshold defaults
    to 0.05). `confidence_from_p_value(p_value)` converts a
    p-value to a confidence level as a percentage
    ((1 - p_value) * 100). Both are pure functions so the API layer
    uses the same rules as the storage layer.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from app.database.repositories.correlation_repository import (
    CorrelationRepository,
    CorrelationRow,
)
from app.database.repositories.prediction_repository import (
    PredictionRepository,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# Rolling windows (in days) that we compute correlations over.
# Matches the CHECK constraint in migration 008.
WINDOWS: Tuple[int, ...] = (30, 90, 365)

# Minimum overlapping daily samples required to compute a correlation.
# Below this, the estimate is too noisy to be useful.
MIN_SAMPLES = 3

# Indicator labels (product-facing) mapped to their source column in
# the `macro_indicators` table.
#
# A value of None means "the source does not yet provide data for
# this indicator". The calculator skips unconfigured indicators with
# a log line. When the Data Ingestion Service adds a source column,
# update this mapping — nothing else needs to change.
INDICATOR_SOURCE_COLUMNS: Dict[str, Optional[str]] = {
    "inflation": "cpi",
    "rates": "interest_rate",
    "gdp": None,
    "unemployment": None,
}

# Strength thresholds. A1.3 owns these values; this module is the
# canonical implementation. STRONG_THRESHOLD is the absolute
# coefficient above which a correlation is labelled "strong". Below
# MEDIUM_THRESHOLD it is "weak"; in between it is "medium".
STRONG_THRESHOLD = 0.7
MEDIUM_THRESHOLD = 0.3

# Statistical significance threshold (A1.4). A correlation is
# considered statistically significant when its two-tailed p-value
# is below this value. The conventional threshold in the social and
# physical sciences is 0.05 (95% confidence).
SIGNIFICANCE_THRESHOLD = 0.05


# ============================================================
# RESULT DATACLASS
# ============================================================
@dataclass
class CalculationResult:
    """Structured result of one correlation calculation run.

    Attributes:
        calculated_at: The timestamp this run wrote to the DB.
        rows_built: Number of CorrelationRow objects constructed.
        rows_written: Number of rows persisted by the repository.
        skipped: List of dicts, each with `indicator`, `window`, and
            `reason`, describing pairs that were skipped.
        errors: List of dicts, each with `indicator`, `window`, and
            `error`, describing pairs that raised an exception.
        elapsed_seconds: Wall-clock duration of the run.
    """

    calculated_at: datetime
    rows_built: int = 0
    rows_written: int = 0
    skipped: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict."""
        return {
            "calculated_at": self.calculated_at.isoformat(),
            "rows_built": self.rows_built,
            "rows_written": self.rows_written,
            "skipped": self.skipped,
            "errors": self.errors,
            "elapsed_seconds": self.elapsed_seconds,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"CalculationResult("
            f"built={self.rows_built}, "
            f"written={self.rows_written}, "
            f"skipped={len(self.skipped)}, "
            f"errors={len(self.errors)})"
        )


# ============================================================
# PURE FUNCTIONS
# ============================================================
def pearson_correlation(
    x: Sequence[float],
    y: Sequence[float],
) -> Tuple[Optional[float], Optional[float], int]:
    """Compute the Pearson correlation coefficient and its p-value.

    Uses scipy.stats.pearsonr for the underlying computation. scipy
    implements the standard t-based two-tailed significance test
    with (n - 2) degrees of freedom, which is the reference
    implementation for this calculation. Rolling our own via the
    regularized incomplete beta function is a foot-gun; small
    errors compound and the edge cases (very small n, coefficient
    close to ±1) are exactly where the math is trickiest.

    Guards before calling scipy:
        - x and y must be the same length
        - n must be at least MIN_SAMPLES
        - no NaN or inf values
        - neither series may have zero variance (scipy would raise
          a ConstantInputWarning and return NaN; we short-circuit
          to return None instead)

    Args:
        x: First series. Must be the same length as y.
        y: Second series.

    Returns:
        Tuple of (coefficient, p_value, sample_size).

        `coefficient` and `p_value` are None when the correlation
        is undefined:
            - x and y have different lengths
            - either series has fewer than MIN_SAMPLES entries
            - either series has zero variance (all values equal)
            - either series contains NaN or infinite values

        `sample_size` is the number of values that were considered,
        or 0 when the inputs could not be aligned.

    Examples:
        >>> pearson_correlation([1, 2, 3, 4], [2, 4, 6, 8])[:2]
        (1.0, 0.0)
        >>> pearson_correlation([1, 2, 3, 4], [4, 3, 2, 1])[:2]
        (-1.0, 0.0)
        >>> pearson_correlation([1, 2], [1, 2])
        (None, None, 2)
    """
    # ---- 1. Length check ----
    if x is None or y is None:
        return (None, None, 0)

    if len(x) != len(y):
        return (None, None, 0)

    n = len(x)

    if n < MIN_SAMPLES:
        return (None, None, n)

    # ---- 2. Convert to numpy float arrays ----
    arr_x = np.asarray(x, dtype=float)
    arr_y = np.asarray(y, dtype=float)

    # ---- 3. Guard against non-finite values ----
    if not np.all(np.isfinite(arr_x)) or not np.all(np.isfinite(arr_y)):
        return (None, None, n)

    # ---- 4. Zero-variance guard ----
    # scipy.stats.pearsonr raises a ConstantInputWarning and returns
    # NaN for a constant series. We short-circuit and return None so
    # the caller can classify this as "correlation undefined".
    std_x = np.std(arr_x)
    std_y = np.std(arr_y)

    if std_x == 0.0 or std_y == 0.0:
        return (None, None, n)

    # ---- 5. Delegate to scipy ----
    result = scipy_stats.pearsonr(arr_x, arr_y)
    coefficient = float(result.statistic)
    p_value = float(result.pvalue)

    # Clip the coefficient to [-1, 1] to absorb floating-point drift.
    # scipy's value can be very slightly outside this range.
    coefficient = max(-1.0, min(1.0, coefficient))

    return (coefficient, p_value, n)


def classify_strength(coefficient: float) -> str:
    """Classify a correlation coefficient as strong, medium, or weak.

    Thresholds (on |coefficient|):
        - strong: > STRONG_THRESHOLD (0.7)
        - medium: >= MEDIUM_THRESHOLD (0.3) and <= STRONG_THRESHOLD
        - weak:   < MEDIUM_THRESHOLD (0.3)

    A1.3 owns the exact thresholds. This function is the canonical
    implementation; callers should not reimplement the classification.

    Args:
        coefficient: Pearson correlation coefficient in [-1, 1].

    Returns:
        One of "strong", "medium", "weak".
    """
    magnitude = abs(coefficient)

    if magnitude > STRONG_THRESHOLD:
        return "strong"
    if magnitude >= MEDIUM_THRESHOLD:
        return "medium"
    return "weak"


def classify_direction(coefficient: float) -> str:
    """Classify the direction of a correlation coefficient.

    Rules:
        - coefficient >= 0 → "positive"
        - coefficient < 0 → "negative"

    A1.3 owns the exact semantics. This function is the canonical
    implementation; callers should not reimplement the classification.

    Args:
        coefficient: Pearson correlation coefficient in [-1, 1].

    Returns:
        One of "positive", "negative".
    """
    return "positive" if coefficient >= 0 else "negative"


def strength_color(strength: str) -> str:
    """Translate a strength label into its display color.

    Mapping (per A1.3):
        - "strong" → "green"
        - "medium" → "yellow"
        - "weak"   → "red"

    The input must be a label produced by `classify_strength`. This
    function raises ValueError for anything else, so a mismatch
    between classification and presentation cannot silently produce
    a wrong color.

    Args:
        strength: One of "strong", "medium", "weak".

    Returns:
        One of "green", "yellow", "red".

    Raises:
        ValueError: If strength is not a recognized label.
    """
    if strength == "strong":
        return "green"
    if strength == "medium":
        return "yellow"
    if strength == "weak":
        return "red"

    raise ValueError(
        f"Unknown strength label '{strength}'. "
        f"Expected one of 'strong', 'medium', 'weak'."
    )


def direction_arrow(direction: str) -> str:
    """Translate a direction label into its display arrow.

    Mapping (per A1.3):
        - "positive" → "↑"
        - "negative" → "↓"

    The input must be a label produced by `classify_direction`. This
    function raises ValueError for anything else, so a mismatch
    between classification and presentation cannot silently produce
    a wrong arrow.

    Args:
        direction: One of "positive", "negative".

    Returns:
        One of "↑", "↓".

    Raises:
        ValueError: If direction is not a recognized label.
    """
    if direction == "positive":
        return "↑"
    if direction == "negative":
        return "↓"

    raise ValueError(
        f"Unknown direction label '{direction}'. "
        f"Expected one of 'positive', 'negative'."
    )


def derive_significance(p_value: Optional[float]) -> bool:
    """Return True when a p-value is statistically significant.

    A correlation is significant when its two-tailed p-value is
    strictly below SIGNIFICANCE_THRESHOLD (0.05 by default). A
    p-value of None (not yet computed, or the correlation was
    undefined) is treated as not significant — there is no evidence
    of a relationship when we cannot compute the p-value.

    Args:
        p_value: Two-tailed p-value in [0, 1], or None.

    Returns:
        True if the p-value is below the significance threshold,
        False otherwise.
    """
    if p_value is None:
        return False
    return p_value < SIGNIFICANCE_THRESHOLD


def confidence_from_p_value(
    p_value: Optional[float],
) -> Optional[float]:
    """Convert a p-value to a confidence level in percent.

    confidence = (1 - p_value) * 100

    Examples:
        - p_value = 0.05 → 95.0 (the conventional 95% confidence
          level)
        - p_value = 0.01 → 99.0
        - p_value = 0.5  → 50.0
        - p_value = None → None

    Args:
        p_value: Two-tailed p-value in [0, 1], or None.

    Returns:
        Confidence level as a percentage, or None when p_value is
        None.
    """
    if p_value is None:
        return None
    return (1.0 - p_value) * 100.0


def resample_btc_to_daily(btc_df: pd.DataFrame) -> pd.DataFrame:
    """Resample an hourly BTC frame to one close per UTC day.

    Takes the last close within each UTC calendar day. The result
    has columns `date` (a `datetime.date`) and `close`. Returns an
    empty frame when the input is empty or missing required columns.

    Args:
        btc_df: DataFrame with columns `time` (or `ds`) and `close`
            (or `y`). The output of
            PredictionRepository.fetch_recent_btc_data uses
            `time` and `close`; the output of fetch_training_frame
            uses `ds` and `y`.

    Returns:
        DataFrame with columns `date`, `close`, sorted ascending by
        date. Empty when the input has no usable rows.
    """
    if btc_df is None or btc_df.empty:
        return pd.DataFrame(columns=["date", "close"])

    # Accept either of the two column naming conventions.
    time_col = "time" if "time" in btc_df.columns else "ds"
    close_col = "close" if "close" in btc_df.columns else "y"

    if time_col not in btc_df.columns or close_col not in btc_df.columns:
        return pd.DataFrame(columns=["date", "close"])

    df = btc_df[[time_col, close_col]].copy()
    df[time_col] = pd.to_datetime(df[time_col], utc=True)
    df["date"] = df[time_col].dt.date

    # Group by UTC calendar day, take the last close of the day.
    daily = (
        df.groupby("date", as_index=False)[close_col]
        .last()
        .rename(columns={close_col: "close"})
        .sort_values("date")
        .reset_index(drop=True)
    )

    return daily


# ============================================================
# CALCULATOR
# ============================================================
class CorrelationCalculator:
    """Orchestrates one correlation calculation run.

    Fetches BTC and macro data from the source tables via
    PredictionRepository, resamples BTC to daily, computes the
    Pearson correlation for each (indicator, window) pair, and
    writes the results via CorrelationRepository.

    The calculator does not commit — the caller controls the
    transaction via session_scope().

    Example:
        async with session_scope() as session:
            calc = CorrelationCalculator(
                correlation_repo=CorrelationRepository(session),
                prediction_repo=PredictionRepository(session),
            )
            result = await calc.run()
    """

    def __init__(
        self,
        correlation_repo: CorrelationRepository,
        prediction_repo: PredictionRepository,
        windows: Tuple[int, ...] = WINDOWS,
    ) -> None:
        """Initialize the calculator.

        Args:
            correlation_repo: A CorrelationRepository bound to a
                session.
            prediction_repo: A PredictionRepository bound to the
                same session (used to fetch source data).
            windows: Rolling windows in days to compute. Defaults
                to (30, 90, 365).

        Raises:
            ValueError: If windows is empty or contains non-positive
                values.
        """
        if not windows:
            raise ValueError("windows must not be empty")

        if any(w <= 0 for w in windows):
            raise ValueError(
                f"windows must all be positive, got {windows}"
            )

        self.correlation_repo = correlation_repo
        self.prediction_repo = prediction_repo
        self.windows = tuple(windows)

        logger.info(
            f"CorrelationCalculator initialized "
            f"(windows={self.windows})"
        )

    # ============================================================
    # PUBLIC API
    # ============================================================
    async def run(self) -> CalculationResult:
        """Run one full correlation calculation.

        Fetches source data once, computes every (indicator, window)
        pair, and persists the built rows. Skips and errors are
        captured in the result — this method does not raise on
        data-related failures.

        Returns:
            CalculationResult with what was built, written, skipped,
            and errored.
        """
        start = datetime.now(timezone.utc)
        calculated_at = start

        result = CalculationResult(calculated_at=calculated_at)

        # ---- 1. Fetch source data ----
        # Fetch enough BTC history to cover the longest window plus a
        # small buffer. `max(self.windows) + 1` days, expressed in hours.
        max_window = max(self.windows)
        btc_hours = (max_window + 1) * 24
        macro_hours = (max_window + 1) * 24

        try:
            btc_df = await self.prediction_repo.fetch_recent_btc_data(
                hours=btc_hours
            )
        except Exception as e:
            logger.error(f"Failed to fetch BTC data: {e}", exc_info=True)
            result.elapsed_seconds = (
                datetime.now(timezone.utc) - start
            ).total_seconds()
            return result

        try:
            macro_df = await self.prediction_repo.fetch_recent_macro_data(
                hours=macro_hours
            )
        except Exception as e:
            logger.error(f"Failed to fetch macro data: {e}", exc_info=True)
            result.elapsed_seconds = (
                datetime.now(timezone.utc) - start
            ).total_seconds()
            return result

        if btc_df is None or btc_df.empty:
            logger.warning(
                "BTC data is empty — no correlations can be computed"
            )
            result.elapsed_seconds = (
                datetime.now(timezone.utc) - start
            ).total_seconds()
            return result

        # ---- 2. Resample BTC to daily ----
        btc_daily = resample_btc_to_daily(btc_df)

        if btc_daily.empty:
            logger.warning(
                "BTC daily resample produced no rows — nothing to compute"
            )
            result.elapsed_seconds = (
                datetime.now(timezone.utc) - start
            ).total_seconds()
            return result

        logger.info(
            f"Prepared BTC daily series: {len(btc_daily)} days "
            f"(range: {btc_daily['date'].iloc[0]} → "
            f"{btc_daily['date'].iloc[-1]})"
        )

        # ---- 3. Resample macro to daily (already daily in source) ----
        macro_daily = self._prepare_macro_daily(macro_df)

        # ---- 4. Compute per (indicator, window) ----
        rows: List[CorrelationRow] = []

        for indicator, source_col in INDICATOR_SOURCE_COLUMNS.items():
            for window in self.windows:
                try:
                    row = self._compute_one(
                        indicator=indicator,
                        source_col=source_col,
                        window_days=window,
                        btc_daily=btc_daily,
                        macro_daily=macro_daily,
                        calculated_at=calculated_at,
                        skipped=result.skipped,
                    )
                    if row is not None:
                        rows.append(row)
                except Exception as e:
                    logger.error(
                        f"Failed to compute correlation for "
                        f"{indicator}/{window}d: {e}",
                        exc_info=True,
                    )
                    result.errors.append(
                        {
                            "indicator": indicator,
                            "window_days": window,
                            "error": str(e),
                        }
                    )

        result.rows_built = len(rows)

        # ---- 5. Persist ----
        if rows:
            try:
                written = await self.correlation_repo.save_rows(rows)
                result.rows_written = written
            except Exception as e:
                logger.error(
                    f"Failed to persist correlation rows: {e}",
                    exc_info=True,
                )
                result.errors.append(
                    {
                        "indicator": "*",
                        "window_days": 0,
                        "error": f"save_rows failed: {e}",
                    }
                )

        result.elapsed_seconds = (
            datetime.now(timezone.utc) - start
        ).total_seconds()

        logger.info(
            f"Correlation calculation complete: "
            f"{result.rows_built} built, {result.rows_written} written, "
            f"{len(result.skipped)} skipped, {len(result.errors)} errors, "
            f"in {result.elapsed_seconds:.3f}s"
        )

        return result

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================
    def _prepare_macro_daily(
        self, macro_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Normalize the macro frame to one row per date.

        The source already stores macro data daily, but it arrives
        with a `time` column. We convert it to a `date` column so
        the join with BTC daily is a simple equality on date.

        Args:
            macro_df: DataFrame from fetch_recent_macro_data.

        Returns:
            DataFrame with columns: date, and one column per macro
            indicator present in the input. Sorted ascending by
            date.
        """
        if macro_df is None or macro_df.empty:
            return pd.DataFrame()

        df = macro_df.copy()
        df["date"] = pd.to_datetime(df["time"], utc=True).dt.date

        # Drop the time column — we only need date + indicators.
        df = df.drop(columns=["time"], errors="ignore")

        # If a single date has multiple rows (should not happen for
        # daily macro, but be defensive), keep the last per date.
        indicator_cols = [
            c for c in df.columns if c != "date"
        ]
        if indicator_cols:
            df = (
                df.groupby("date", as_index=False)[indicator_cols]
                .last()
                .sort_values("date")
                .reset_index(drop=True)
            )

        return df

    def _compute_one(
        self,
        indicator: str,
        source_col: Optional[str],
        window_days: int,
        btc_daily: pd.DataFrame,
        macro_daily: pd.DataFrame,
        calculated_at: datetime,
        skipped: List[Dict[str, Any]],
    ) -> Optional[CorrelationRow]:
        """Compute one (indicator, window) correlation row.

        On any skip condition, appends an entry to `skipped` and
        returns None. On success, returns a CorrelationRow.

        Args:
            indicator: Product-facing indicator label.
            source_col: Source column name, or None if the source
                does not yet provide data for this indicator.
            window_days: Window length in days.
            btc_daily: BTC daily frame with columns date, close.
            macro_daily: Macro daily frame with a column per source.
            calculated_at: Timestamp to write on every row.
            skipped: List to append skip reasons to.

        Returns:
            A CorrelationRow on success, or None when skipped.
        """
        # ---- 1. Source column configured? ----
        if source_col is None:
            reason = (
                f"source column not configured for indicator "
                f"'{indicator}' — the macro_indicators table does not "
                f"yet have this column; update "
                f"INDICATOR_SOURCE_COLUMNS when it does"
            )
            logger.info(
                f"Skipping {indicator}/{window_days}d: {reason}"
            )
            skipped.append(
                {
                    "indicator": indicator,
                    "window_days": window_days,
                    "reason": "source_column_not_configured",
                }
            )
            return None

        # ---- 2. BTC window available? ----
        if len(btc_daily) < window_days:
            reason = (
                f"insufficient btc history: have {len(btc_daily)} days, "
                f"need {window_days}"
            )
            logger.info(
                f"Skipping {indicator}/{window_days}d: {reason}"
            )
            skipped.append(
                {
                    "indicator": indicator,
                    "window_days": window_days,
                    "reason": "insufficient_btc_history",
                }
            )
            return None

        # ---- 3. Macro column present? ----
        if macro_daily is None or macro_daily.empty:
            logger.info(
                f"Skipping {indicator}/{window_days}d: no macro data"
            )
            skipped.append(
                {
                    "indicator": indicator,
                    "window_days": window_days,
                    "reason": "no_macro_data",
                }
            )
            return None

        if source_col not in macro_daily.columns:
            logger.info(
                f"Skipping {indicator}/{window_days}d: macro column "
                f"'{source_col}' not present in fetched data"
            )
            skipped.append(
                {
                    "indicator": indicator,
                    "window_days": window_days,
                    "reason": f"macro_column_missing:{source_col}",
                }
            )
            return None

        # ---- 4. Slice the last `window_days` days of BTC ----
        btc_window = btc_daily.tail(window_days).copy()

        # ---- 5. Inner-join BTC and macro on date ----
        merged = btc_window.merge(
            macro_daily[["date", source_col]],
            on="date",
            how="inner",
        )

        if len(merged) < MIN_SAMPLES:
            logger.info(
                f"Skipping {indicator}/{window_days}d: only "
                f"{len(merged)} overlapping days after join "
                f"(need >= {MIN_SAMPLES})"
            )
            skipped.append(
                {
                    "indicator": indicator,
                    "window_days": window_days,
                    "reason": "insufficient_overlap",
                }
            )
            return None

        # ---- 6. Drop rows with NaN in either series ----
        merged = merged.dropna(subset=["close", source_col])

        if len(merged) < MIN_SAMPLES:
            logger.info(
                f"Skipping {indicator}/{window_days}d: only "
                f"{len(merged)} non-NaN days after dropna"
            )
            skipped.append(
                {
                    "indicator": indicator,
                    "window_days": window_days,
                    "reason": "insufficient_after_dropna",
                }
            )
            return None

        # ---- 7. Compute Pearson (coefficient + p-value) ----
        coefficient, p_value, n = pearson_correlation(
            merged["close"].tolist(),
            merged[source_col].tolist(),
        )

        if coefficient is None:
            logger.info(
                f"Skipping {indicator}/{window_days}d: correlation "
                f"undefined (zero variance or non-finite values)"
            )
            skipped.append(
                {
                    "indicator": indicator,
                    "window_days": window_days,
                    "reason": "correlation_undefined",
                }
            )
            return None

        # ---- 8. Classify ----
        strength = classify_strength(coefficient)
        direction = classify_direction(coefficient)

        logger.info(
            f"Computed {indicator}/{window_days}d: "
            f"r={coefficient:+.4f} ({strength}, {direction}), "
            f"p={p_value:.4f}, n={n}"
        )

        return CorrelationRow(
            indicator_name=indicator,
            window_days=window_days,
            calculated_at=calculated_at,
            correlation_coefficient=coefficient,
            strength=strength,
            direction=direction,
            p_value=p_value,
        )

    # ============================================================
    # DUNDER METHODS
    # ============================================================
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"CorrelationCalculator("
            f"windows={self.windows}, "
            f"indicators={list(INDICATOR_SOURCE_COLUMNS.keys())})"
        )