"""
Service for identifying and storing macroeconomic regimes.

The service analyzes stored macroeconomic indicators
and determines the prevailing macroeconomic regime.

Supported regimes:

- high_inflation
- low_inflation
- rising_rates
- falling_rates
- recession
- growth

The service also calculates:
- Classification confidence as a percentage (0-100)
- Visual market indicator (bull/bear/recession)
"""

import logging
from datetime import date, timedelta

from app.config import settings
from app.database.regime_repository import RegimeRepository

logger = logging.getLogger(__name__)


class RegimeService:
    """
    Identifies macroeconomic regimes from stored indicators.
    """

    VALID_REGIMES = {
        "high_inflation",
        "low_inflation",
        "rising_rates",
        "falling_rates",
        "recession",
        "growth",
    }

    VISUAL_INDICATORS = {
        "high_inflation": "bear",
        "low_inflation": "bull",
        "rising_rates": "bear",
        "falling_rates": "bull",
        "recession": "recession",
        "growth": "bull",
    }

    def __init__(
        self,
        db,
    ):
        self.db = db
        self.repository = RegimeRepository(db)

    # --------------------------------------------------
    # REGIME CLASSIFICATION
    # --------------------------------------------------

    def determine_regime(
        self,
        indicators: list,
    ) -> str:
        """
        Determine the current macroeconomic regime.

        Classification rules:

        - High Inflation: CPI > configured threshold
        - Low Inflation: CPI < configured threshold
        - Rising Rates: interest rates increased over 3 months
        - Falling Rates: interest rates decreased over 3 months
        - Recession: GDP negative growth for 2 consecutive quarters
        - Growth: GDP positive growth > configured threshold

        When multiple conditions overlap, rules are evaluated
        in a deterministic priority order.
        """

        values = {}

        for indicator in indicators:
            name = indicator.indicator_name.lower()

            values.setdefault(name, []).append(
                indicator
            )

        # --------------------------------------------------
        # SORT HISTORICAL DATA
        # --------------------------------------------------

        for name in values:
            values[name] = sorted(
                values[name],
                key=lambda item: item.time,
                reverse=True,
            )

        # --------------------------------------------------
        # CPI / INFLATION
        # --------------------------------------------------

        cpi_records = values.get(
            "cpi",
            [],
        )

        cpi_inflation = None

        if len(cpi_records) >= 2:

            latest_cpi = cpi_records[0]

            target_time = (
                latest_cpi.time
                - timedelta(
                    days=settings.DAYS_IN_YEAR
                )
            )

            historical_cpi = min(
                cpi_records[1:],
                key=lambda item: abs(
                    (
                        item.time
                        - target_time
                    ).total_seconds()
                ),
            )

            if (
                latest_cpi.value is not None
                and historical_cpi.value is not None
                and historical_cpi.value > 0
            ):
                cpi_inflation = (
                    (
                        latest_cpi.value
                        - historical_cpi.value
                    )
                    / historical_cpi.value
                ) * 100

        # --------------------------------------------------
        # FEDERAL FUNDS RATE
        # --------------------------------------------------

        rate_records = values.get(
            "federal_funds_rate",
            [],
        )

        rate_change_3m = None

        if len(rate_records) >= 2:

            latest_rate = rate_records[0]

            if latest_rate.value is not None:

                target_time = (
                    latest_rate.time
                    - timedelta(
                        days=settings.DAYS_IN_3_MONTHS
                    )
                )

                historical_rate = min(
                    rate_records[1:],
                    key=lambda item: abs(
                        (
                            item.time
                            - target_time
                        ).total_seconds()
                    ),
                )

                if historical_rate.value is not None:
                    rate_change_3m = (
                        latest_rate.value
                        - historical_rate.value
                    )

        # --------------------------------------------------
        # GDP
        # --------------------------------------------------

        gdp_records = values.get(
            "gdp",
            [],
        )

        # --------------------------------------------------
        # RECESSION
        # --------------------------------------------------

        negative_gdp_quarters = 0

        for record in gdp_records[:2]:

            if (
                record.change_percent is not None
                and record.change_percent < 0
            ):
                negative_gdp_quarters += 1

        if negative_gdp_quarters >= 2:
            return "recession"

        # --------------------------------------------------
        # HIGH INFLATION
        # --------------------------------------------------

        if (
            cpi_inflation is not None
            and cpi_inflation
            > settings.INFLATION_THRESHOLD
        ):
            return "high_inflation"

        # --------------------------------------------------
        # LOW INFLATION
        # --------------------------------------------------

        if (
            cpi_inflation is not None
            and cpi_inflation
            < settings.LOW_INFLATION_THRESHOLD
        ):
            return "low_inflation"

        # --------------------------------------------------
        # RISING RATES
        # --------------------------------------------------

        if (
            rate_change_3m is not None
            and rate_change_3m > 0
        ):
            return "rising_rates"

        # --------------------------------------------------
        # FALLING RATES
        # --------------------------------------------------

        if (
            rate_change_3m is not None
            and rate_change_3m < 0
        ):
            return "falling_rates"

        # --------------------------------------------------
        # GROWTH
        # --------------------------------------------------

        if gdp_records:

            latest_gdp = gdp_records[0]

            if (
                latest_gdp.change_percent is not None
                and latest_gdp.change_percent
                > settings.GDP_GROWTH_THRESHOLD
            ):
                return "growth"

        # --------------------------------------------------
        # DEFAULT
        # --------------------------------------------------

        return "growth"

    # --------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------

    def calculate_confidence(
        self,
        indicators: list,
        regime_type: str,
    ) -> float:
        """
        Calculate classification confidence as a percentage.

        This is a deterministic confidence score, not a
        statistical probability.

        Confidence is based on the strength and availability
        of the evidence supporting the identified regime.

        Returns:
            Float between 0 and 100.
        """

        if not indicators:
            return 0.0

        values = {}

        for indicator in indicators:
            name = indicator.indicator_name.lower()

            values.setdefault(name, []).append(
                indicator
            )

        # Sort newest first.
        for name in values:
            values[name] = sorted(
                values[name],
                key=lambda item: item.time,
                reverse=True,
            )

        # --------------------------------------------------
        # RECESSION
        # --------------------------------------------------

        if regime_type == "recession":

            gdp_records = values.get(
                "gdp",
                [],
            )

            negative_quarters = sum(
                1
                for record in gdp_records[:2]
                if (
                    record.change_percent is not None
                    and record.change_percent < 0
                )
            )

            if negative_quarters >= 2:
                return 100.0

            return 50.0

        # --------------------------------------------------
        # CPI REGIMES
        # --------------------------------------------------

        if regime_type in {
            "high_inflation",
            "low_inflation",
        }:

            cpi_records = values.get(
                "cpi",
                [],
            )

            if len(cpi_records) < 2:
                return 50.0

            latest_cpi = cpi_records[0]

            target_time = (
                latest_cpi.time
                - timedelta(
                    days=settings.DAYS_IN_YEAR
                )
            )

            historical_cpi = min(
                cpi_records[1:],
                key=lambda item: abs(
                    (
                        item.time
                        - target_time
                    ).total_seconds()
                ),
            )

            if (
                latest_cpi.value is None
                or historical_cpi.value is None
                or historical_cpi.value <= 0
            ):
                return 50.0

            inflation = (
                (
                    latest_cpi.value
                    - historical_cpi.value
                )
                / historical_cpi.value
            ) * 100

            if regime_type == "high_inflation":

                threshold = (
                    settings.INFLATION_THRESHOLD
                )

                if inflation > threshold:
                    return min(
                        100.0,
                        50.0
                        + (
                            inflation
                            - threshold
                        ) * 10,
                    )

            if regime_type == "low_inflation":

                threshold = (
                    settings.LOW_INFLATION_THRESHOLD
                )

                if inflation < threshold:
                    return min(
                        100.0,
                        50.0
                        + (
                            threshold
                            - inflation
                        ) * 10,
                    )

            return 50.0

        # --------------------------------------------------
        # INTEREST RATE REGIMES
        # --------------------------------------------------

        if regime_type in {
            "rising_rates",
            "falling_rates",
        }:

            rate_records = values.get(
                "federal_funds_rate",
                [],
            )

            if len(rate_records) < 2:
                return 50.0

            latest_rate = rate_records[0]

            if latest_rate.value is None:
                return 50.0

            target_time = (
                latest_rate.time
                - timedelta(
                    days=settings.DAYS_IN_3_MONTHS
                )
            )

            historical_rate = min(
                rate_records[1:],
                key=lambda item: abs(
                    (
                        item.time
                        - target_time
                    ).total_seconds()
                ),
            )

            if historical_rate.value is None:
                return 50.0

            rate_change = (
                latest_rate.value
                - historical_rate.value
            )

            if regime_type == "rising_rates" and rate_change > 0:
                return min(
                    100.0,
                    50.0 + abs(rate_change) * 10,
                )

            if regime_type == "falling_rates" and rate_change < 0:
                return min(
                    100.0,
                    50.0 + abs(rate_change) * 10,
                )

            return 50.0

        # --------------------------------------------------
        # GROWTH
        # --------------------------------------------------

        if regime_type == "growth":

            gdp_records = values.get(
                "gdp",
                [],
            )

            if not gdp_records:
                return 50.0

            latest_gdp = gdp_records[0]

            if latest_gdp.change_percent is None:
                return 50.0

            growth = latest_gdp.change_percent
            threshold = settings.GDP_GROWTH_THRESHOLD

            if growth > threshold:
                return min(
                    100.0,
                    50.0
                    + (
                        growth
                        - threshold
                    ) * 10,
                )

            # Growth is the fallback classification.
            return 50.0

        return 50.0

    # --------------------------------------------------
    # VISUAL INDICATOR
    # --------------------------------------------------

    def get_visual_indicator(
        self,
        regime_type: str,
    ) -> str:
        """
        Map the macroeconomic regime to a visual market
        indicator used by the API/UI.

        Returns:
            bull, bear, or recession.
        """

        return self.VISUAL_INDICATORS.get(
            regime_type,
            "recession",
        )

    # --------------------------------------------------
    # REGIME UPDATE
    # --------------------------------------------------

    def update_current_regime(
        self,
        indicators: list,
    ):
        """
        Determine and persist the current macroeconomic regime.

        When the regime changes, the previous regime is closed
        and its BTC performance is calculated.
        """

        if not indicators:
            logger.warning(
                "No indicators available for regime detection"
            )
            return None

        regime_type = self.determine_regime(
            indicators
        )

        if regime_type not in self.VALID_REGIMES:
            logger.error(
                "Invalid regime detected: %s",
                regime_type,
            )
            return None

        confidence = self.calculate_confidence(
            indicators,
            regime_type,
        )

        visual_indicator = self.get_visual_indicator(
            regime_type
        )

        current_regime = (
            self.repository.get_current_regime()
        )

        today = date.today()

        # --------------------------------------------------
        # NO ACTIVE REGIME
        # --------------------------------------------------

        if current_regime is None:

            regime = self.repository.create_regime(
                regime_type=regime_type,
                start_date=today,
            )

            self.repository.set_current_regime(
                regime_type=regime_type,
                confidence=confidence,
                visual_indicator=visual_indicator,
            )

            logger.info(
                "Initial macro regime created: "
                "regime=%s, confidence=%.2f%%, indicator=%s",
                regime_type,
                confidence,
                visual_indicator,
            )

            return regime

        # --------------------------------------------------
        # REGIME UNCHANGED
        # --------------------------------------------------

        if (
            current_regime.regime_type
            == regime_type
        ):
            logger.info(
                "Macro regime unchanged: %s",
                regime_type,
            )

            return current_regime

        # --------------------------------------------------
        # REGIME CHANGED
        # --------------------------------------------------

        logger.info(
            "Macro regime changed: %s -> %s",
            current_regime.regime_type,
            regime_type,
        )

        self.repository.close_regime(
            current_regime,
            today,
        )

        # --------------------------------------------------
        # CALCULATE PERFORMANCE OF COMPLETED REGIME
        # --------------------------------------------------

        try:
            from app.services.regime_performance_service import (
                RegimePerformanceService,
            )

            performance_service = (
                RegimePerformanceService(self.db)
            )

            performance = (
                performance_service
                .calculate_regime_performance(
                    current_regime
                )
            )

            if performance:
                logger.info(
                    "Previous regime performance calculated: "
                    "regime_id=%s",
                    current_regime.id,
                )
            else:
                logger.info(
                    "Not enough BTC price data to calculate "
                    "performance for regime_id=%s",
                    current_regime.id,
                )

        except Exception:
            logger.exception(
                "Failed to calculate performance for "
                "completed regime_id=%s",
                current_regime.id,
            )

        # --------------------------------------------------
        # CREATE NEW REGIME
        # --------------------------------------------------

        new_regime = self.repository.create_regime(
            regime_type=regime_type,
            start_date=today,
        )

        self.repository.set_current_regime(
            regime_type=regime_type,
            confidence=confidence,
            visual_indicator=visual_indicator,
        )

        logger.info(
            "New macro regime created: "
            "regime=%s, confidence=%.2f%%, indicator=%s",
            regime_type,
            confidence,
            visual_indicator,
        )

        return new_regime

    # --------------------------------------------------
    # UPDATE REGIME FROM DATABASE
    # --------------------------------------------------

    async def update_regime(
        self,
    ):
        """
        Read historical macroeconomic indicators
        and update the current regime.

        Historical records are intentionally preserved
        because regime classification requires:

        - 3-month interest-rate comparisons
        - 2 consecutive GDP quarters
        - 12-month CPI comparison
        """

        from app.models.macro_indicator import MacroIndicator

        indicators = (
            self.db.query(MacroIndicator)
            .order_by(
                MacroIndicator.time.desc()
            )
            .all()
        )

        if not indicators:
            logger.warning(
                "No macroeconomic indicators found"
            )
            return None

        return self.update_current_regime(
            indicators
        )

    # --------------------------------------------------
    # PUBLIC REGIME PROCESSOR
    # --------------------------------------------------

    async def process_regime(
        self,
    ):
        """
        Process the current macroeconomic regime.

        This is the public entry point used by the
        periodic economic scheduler.
        """

        logger.info(
            "Starting macroeconomic regime processing"
        )

        result = await self.update_regime()

        if result:
            logger.info(
                "Macroeconomic regime processing completed: %s",
                result.regime_type,
            )
        else:
            logger.warning(
                "No macroeconomic regime was created or updated"
            )

        return result

    # --------------------------------------------------
    # SERVICE LIFECYCLE
    # --------------------------------------------------

    async def close(
        self,
    ):
        """
        Close service resources.

        Database lifecycle is managed externally.
        """

        return None