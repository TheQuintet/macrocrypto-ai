"""
Service for identifying historical macroeconomic periods
similar to the current macroeconomic environment.

Similarity is calculated using normalized Euclidean distance.
BTC performance is included when historical BTC data is available.
"""

import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.btc_price import BTCPrice
from app.models.macro_indicator import MacroIndicator


logger = logging.getLogger(__name__)


class SimilarPeriodService:
    """
    Identifies historical periods with macroeconomic conditions
    similar to the current environment.
    """

    INDICATORS = (
        "cpi",
        "federal_funds_rate",
        "m2_money_supply",
        "dxy",
        "ten_year_treasury",
        "gdp",
        "unemployment",
    )

    DEFAULT_LIMIT = 5
    MIN_LIMIT = 3
    MAX_LIMIT = 5

    # Historical snapshots are created monthly.
    SNAPSHOT_INTERVAL_DAYS = 30

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # CURRENT CONDITIONS
    # ============================================================

    def get_current_conditions(self) -> dict[str, float]:
        """
        Return the latest available value for every configured
        macroeconomic indicator.
        """

        if self.db is None:
            return {}

        rows = (
            self.db.query(MacroIndicator)
            .filter(
                MacroIndicator.indicator_name.in_(
                    self.INDICATORS
                )
            )
            .order_by(MacroIndicator.time.desc())
            .all()
        )

        latest = {}

        for row in rows:
            if row.indicator_name not in latest:
                latest[row.indicator_name] = row.value

        missing = [
            indicator
            for indicator in self.INDICATORS
            if indicator not in latest
        ]

        if missing:
            raise ValueError(
                "Missing current indicator data: "
                + ", ".join(missing)
            )

        return latest

    # ============================================================
    # HISTORICAL SNAPSHOTS
    # ============================================================

    def get_historical_snapshots(
        self,
    ) -> dict[datetime, dict[str, float]]:
        """
        Build historical macroeconomic snapshots.

        A snapshot is created approximately every 30 days.

        For each snapshot date, the latest available observation
        for each indicator at or before that date is used.

        This handles different FRED publication frequencies.
        """

        if self.db is None:
            return {}

        rows = (
            self.db.query(MacroIndicator)
            .filter(
                MacroIndicator.indicator_name.in_(
                    self.INDICATORS
                )
            )
            .order_by(MacroIndicator.time.asc())
            .all()
        )

        if not rows:
            return {}

        observations = defaultdict(list)

        for row in rows:
            if row.value is not None:
                observations[row.indicator_name].append(row)

        all_dates = [
            row.time
            for row in rows
            if row.time is not None
        ]

        if not all_dates:
            return {}

        first_date = min(all_dates)
        last_date = max(all_dates)

        snapshots = {}

        snapshot_date = first_date

        while snapshot_date <= last_date:
            values = {}

            for indicator in self.INDICATORS:
                candidates = [
                    row
                    for row in observations.get(indicator, [])
                    if row.time <= snapshot_date
                ]

                if not candidates:
                    continue

                latest = candidates[-1]
                values[indicator] = latest.value

            # Only retain complete macroeconomic vectors.
            if all(
                indicator in values
                for indicator in self.INDICATORS
            ):
                snapshots[snapshot_date] = values

            snapshot_date += timedelta(
                days=self.SNAPSHOT_INTERVAL_DAYS
            )

        return snapshots

    # ============================================================
    # NORMALIZATION
    # ============================================================

    def calculate_statistics(
        self,
        snapshots,
    ) -> dict[str, dict[str, float]]:
        """
        Calculate mean and standard deviation for each indicator.

        Supports both:

        1. Production format:
           {
               datetime: {
                   "cpi": 3.0,
                   ...
               }
           }

        2. Test/legacy format:
           [
               {
                   "macro_conditions": {
                       "cpi": 3.0,
                       ...
                   }
               }
           ]
        """

        # Normalize input into a list of macro condition dictionaries.
        if isinstance(snapshots, dict):
            snapshot_values = list(snapshots.values())
        elif isinstance(snapshots, list):
            snapshot_values = []

            for snapshot in snapshots:
                if "macro_conditions" in snapshot:
                    snapshot_values.append(
                        snapshot["macro_conditions"]
                    )
                else:
                    snapshot_values.append(snapshot)
        else:
            return {}

        statistics = {}

        for indicator in self.INDICATORS:
            values = [
                snapshot[indicator]
                for snapshot in snapshot_values
                if indicator in snapshot
                and snapshot[indicator] is not None
            ]

            if not values:
                continue

            mean = sum(values) / len(values)

            variance = sum(
                (value - mean) ** 2
                for value in values
            ) / len(values)

            statistics[indicator] = {
                "mean": mean,
                "stddev": math.sqrt(variance),
            }

        return statistics

    def _normalize(
        self,
        value: float,
        mean: float,
        stddev: float,
    ) -> float:
        """
        Normalize one value into a z-score.

        This helper exists for unit-testability and backwards
        compatibility with the A3.17 test suite.
        """

        if stddev == 0:
            return 0.0

        return (value - mean) / stddev

    def normalize(
        self,
        values: dict[str, float],
        statistics,
    ) -> dict[str, float]:
        """
        Convert indicator values to z-scores.

        Supports statistics represented either as:

            {"cpi": {"mean": 3.0, "stddev": 1.0}}

        or:

            {"cpi": (3.0, 1.0)}
        """

        normalized = {}

        for indicator in self.INDICATORS:
            if indicator not in values:
                continue

            if indicator not in statistics:
                continue

            stats = statistics[indicator]

            # Support dictionary format.
            if isinstance(stats, dict):
                mean = stats["mean"]
                stddev = stats["stddev"]

            # Support tuple/list format used by tests.
            elif isinstance(stats, (tuple, list)):
                mean = stats[0]
                stddev = stats[1]

            else:
                continue

            normalized[indicator] = self._normalize(
                value=values[indicator],
                mean=mean,
                stddev=stddev,
            )

        return normalized

    # ============================================================
    # DISTANCE
    # ============================================================

    def _calculate_distance(
        self,
        current: dict[str, float],
        historical: dict[str, float],
        statistics,
    ) -> tuple[float, dict[str, float]]:
        """
        Calculate normalized Euclidean distance.

        Returns:

            (
                distance,
                per_indicator_normalized_differences
            )
        """

        current_normalized = self.normalize(
            current,
            statistics,
        )

        historical_normalized = self.normalize(
            historical,
            statistics,
        )

        differences = {}

        for indicator in current_normalized:
            if indicator not in historical_normalized:
                continue

            differences[indicator] = abs(
                current_normalized[indicator]
                - historical_normalized[indicator]
            )

        distance = math.sqrt(
            sum(
                difference ** 2
                for difference in differences.values()
            )
        )

        return distance, differences

    def calculate_euclidean_distance(
        self,
        current: dict[str, float],
        historical: dict[str, float],
    ) -> float:
        """
        Calculate Euclidean distance between normalized
        macroeconomic vectors.

        This method expects already-normalized vectors.
        """

        common_indicators = [
            indicator
            for indicator in self.INDICATORS
            if indicator in current
            and indicator in historical
        ]

        return math.sqrt(
            sum(
                (
                    current[indicator]
                    - historical[indicator]
                ) ** 2
                for indicator in common_indicators
            )
        )

    # ============================================================
    # SIMILARITY REASONING
    # ============================================================

    def _build_reason(
        self,
        differences: dict[str, float],
    ) -> str:
        """
        Build a human-readable similarity explanation.

        The three indicators with the smallest normalized
        differences are used.
        """

        if not differences:
            return "No matching macroeconomic conditions available."

        sorted_differences = sorted(
            differences.items(),
            key=lambda item: item[1],
        )

        closest = sorted_differences[:3]

        names = [
            indicator
            for indicator, _ in closest
        ]

        return (
            "Similar macro conditions primarily driven by: "
            + ", ".join(names)
        )

    def build_similarity_reason(
        self,
        current: dict[str, float],
        historical: dict[str, float],
    ) -> dict:
        """
        Explain why a historical period is similar.

        Returns the three indicators with the smallest
        normalized differences.
        """

        differences = []

        common_indicators = [
            indicator
            for indicator in self.INDICATORS
            if indicator in current
            and indicator in historical
        ]

        for indicator in common_indicators:
            difference = abs(
                current[indicator]
                - historical[indicator]
            )

            differences.append(
                {
                    "indicator": indicator,
                    "normalized_difference": round(
                        difference,
                        4,
                    ),
                }
            )

        differences.sort(
            key=lambda item: item["normalized_difference"]
        )

        closest = differences[:3]

        reason_input = {
            item["indicator"]: item["normalized_difference"]
            for item in closest
        }

        return {
            "summary": self._build_reason(reason_input),
            "matching_indicators": closest,
        }

    # ============================================================
    # BTC PERFORMANCE
    # ============================================================

    def get_btc_performance(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict | None:
        """
        Calculate BTC performance during a historical period.

        Returns None if BTC data is unavailable.
        """

        if self.db is None:
            return None

        prices = (
            self.db.query(BTCPrice)
            .filter(
                BTCPrice.time >= start_date,
                BTCPrice.time < end_date,
            )
            .order_by(BTCPrice.time.asc())
            .all()
        )

        if len(prices) < 2:
            return None

        valid_prices = [
            price.price
            for price in prices
            if price.price is not None
            and price.price > 0
        ]

        if len(valid_prices) < 2:
            return None

        start_price = valid_prices[0]
        end_price = valid_prices[-1]

        return {
            "price_start": start_price,
            "price_end": end_price,
            "return_percent": (
                (end_price - start_price)
                / start_price
            ) * 100,
            "observations": len(valid_prices),
        }

    # ============================================================
    # SNAPSHOT HELPERS
    # ============================================================

    def _prepare_snapshots(
        self,
        snapshots,
    ) -> dict[datetime, dict[str, float]]:
        """
        Convert test-style historical snapshots into the internal
        datetime -> macro_conditions representation.
        """

        if isinstance(snapshots, dict):
            return snapshots

        prepared = {}

        if not isinstance(snapshots, list):
            return prepared

        for snapshot in snapshots:
            period = snapshot.get("period", {})
            macro_conditions = snapshot.get(
                "macro_conditions",
                {},
            )

            start_date = period.get("start_date")

            if start_date is None:
                continue

            if isinstance(start_date, datetime):
                snapshot_date = start_date
            else:
                snapshot_date = datetime.combine(
                    start_date,
                    datetime.min.time(),
                )

            prepared[snapshot_date] = macro_conditions

        return prepared

    # ============================================================
    # MAIN ENGINE
    # ============================================================

    def find_similar_periods(
        self,
        limit: int = DEFAULT_LIMIT,
    ) -> dict:
        """
        Identify the most similar historical macroeconomic periods.
        """

        if not self.MIN_LIMIT <= limit <= self.MAX_LIMIT:
            raise ValueError(
                f"limit must be between "
                f"{self.MIN_LIMIT} and {self.MAX_LIMIT}"
            )

        # --------------------------------------------------------
        # Current conditions
        # --------------------------------------------------------

        try:
            current = self.get_current_conditions()
        except ValueError:
            return {
                "current_conditions": {},
                "method": "normalized_euclidean_distance",
                "similar_periods": [],
                "period_count": 0,
                "message": (
                    "Current macroeconomic conditions are "
                    "unavailable."
                ),
            }

        if not current:
            return {
                "current_conditions": {},
                "method": "normalized_euclidean_distance",
                "similar_periods": [],
                "period_count": 0,
                "message": (
                    "Current macroeconomic conditions are "
                    "unavailable."
                ),
            }

        # --------------------------------------------------------
        # Historical snapshots
        # --------------------------------------------------------

        raw_snapshots = self.get_historical_snapshots()

        snapshots = self._prepare_snapshots(
            raw_snapshots
        )

        if len(snapshots) < 2:
            return {
                "current_conditions": current,
                "method": "normalized_euclidean_distance",
                "similar_periods": [],
                "period_count": 0,
                "message": (
                    "Insufficient historical macroeconomic "
                    "snapshots for similarity matching."
                ),
            }

        # --------------------------------------------------------
        # Statistics
        # --------------------------------------------------------

        statistics = self.calculate_statistics(
            snapshots
        )

        if not statistics:
            return {
                "current_conditions": current,
                "method": "normalized_euclidean_distance",
                "similar_periods": [],
                "period_count": 0,
                "message": (
                    "No statistical data available for "
                    "similarity matching."
                ),
            }

        # --------------------------------------------------------
        # Normalize current conditions
        # --------------------------------------------------------

        current_normalized = self.normalize(
            current,
            statistics,
        )

        if not current_normalized:
            return {
                "current_conditions": current,
                "method": "normalized_euclidean_distance",
                "similar_periods": [],
                "period_count": 0,
                "message": (
                    "No common indicators available for "
                    "similarity matching."
                ),
            }

        candidates = []

        # --------------------------------------------------------
        # Compare historical periods
        # --------------------------------------------------------

        dates = sorted(snapshots.keys())

        for snapshot_date in dates:

            historical_values = snapshots[
                snapshot_date
            ]

            historical_normalized = self.normalize(
                historical_values,
                statistics,
            )

            common_indicators = [
                indicator
                for indicator in current_normalized
                if indicator in historical_normalized
            ]

            if not common_indicators:
                continue

            distance, differences = (
                self._calculate_distance(
                    current,
                    historical_values,
                    statistics,
                )
            )

            similarity_score = (
                1.0 / (1.0 + distance)
            )

            reasoning = self.build_similarity_reason(
                current_normalized,
                historical_normalized,
            )

            # ----------------------------------------------------
            # Determine period dates
            # ----------------------------------------------------

            period_start = snapshot_date

            period_end = (
                snapshot_date
                + timedelta(
                    days=self.SNAPSHOT_INTERVAL_DAYS
                )
            )

            # ----------------------------------------------------
            # BTC performance
            # ----------------------------------------------------

            btc_performance = self.get_btc_performance(
                period_start,
                period_end,
            )

            # ----------------------------------------------------
            # Build candidate
            # ----------------------------------------------------

            candidates.append(
                {
                    "period_start": (
                        period_start.date().isoformat()
                    ),
                    "period_end": (
                        period_end.date().isoformat()
                    ),
                    "distance": round(
                        distance,
                        6,
                    ),
                    "similarity_score": round(
                        similarity_score,
                        6,
                    ),
                    "reason": reasoning["summary"],
                    "matching_indicators": (
                        reasoning["matching_indicators"]
                    ),
                    "macro_conditions": (
                        historical_values
                    ),
                    "btc_performance": (
                        btc_performance
                    ),
                }
            )

        # --------------------------------------------------------
        # Sort by similarity
        # --------------------------------------------------------

        candidates.sort(
            key=lambda item: item["distance"]
        )

        # --------------------------------------------------------
        # Remove the latest/current observation
        # --------------------------------------------------------

        if dates:
            current_date = max(dates)

            current_date_string = (
                current_date.date().isoformat()
            )

            candidates = [
                candidate
                for candidate in candidates
                if candidate["period_start"]
                != current_date_string
            ]

        # --------------------------------------------------------
        # Return top N
        # --------------------------------------------------------

        selected = candidates[:limit]

        return {
            "current_conditions": current,
            "method": "normalized_euclidean_distance",
            "period_count": len(selected),
            "similar_periods": selected,
        }