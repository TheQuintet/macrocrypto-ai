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
"""

import logging
from datetime import date, timedelta

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

        - High Inflation: CPI > 3%
        - Low Inflation: CPI < 2%
        - Rising Rates: interest rates increased over 3 months
        - Falling Rates: interest rates decreased over 3 months
        - Recession: GDP negative growth for 2 consecutive quarters
        - Growth: GDP positive growth > 2%

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
                - timedelta(days=365)
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
                    - timedelta(days=90)
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
            and cpi_inflation > 3.0
        ):
            return "high_inflation"

        # --------------------------------------------------
        # LOW INFLATION
        # --------------------------------------------------

        if (
            cpi_inflation is not None
            and cpi_inflation < 2.0
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
                and latest_gdp.change_percent > 2.0
            ):
                return "growth"

        # --------------------------------------------------
        # DEFAULT
        # --------------------------------------------------

        return "growth"

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
                regime_type=regime_type
            )

            logger.info(
                "Initial macro regime created: %s",
                regime_type,
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
            regime_type=regime_type
        )

        logger.info(
            "New macro regime created: %s",
            regime_type,
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