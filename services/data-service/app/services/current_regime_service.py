"""
Service for managing the currently identified macroeconomic regime.

This service is responsible for:

- Calculating confidence in the classified regime.
- Determining the visual indicator for the regime.
- Persisting the current regime snapshot.
- Providing a single service boundary between regime
  classification and current-regime persistence.

Regime classification itself remains the responsibility of
RegimeService.
"""

import logging
from datetime import datetime, timezone

from app.config import settings
from app.database.regime_repository import RegimeRepository
from app.services.regime_service import RegimeService

logger = logging.getLogger(__name__)


class CurrentRegimeService:
    """
    Service for calculating and storing the current
    macroeconomic regime snapshot.
    """

    VALID_REGIMES = {
        "high_inflation",
        "low_inflation",
        "rising_rates",
        "falling_rates",
        "recession",
        "growth",
    }

    def __init__(self, db):
        self.db = db
        self.repository = RegimeRepository(db)
        self.regime_service = RegimeService(db)

    # ============================================================
    # CONFIDENCE CALCULATION
    # ============================================================

    def calculate_confidence(
        self,
        regime_type: str,
        indicators: list,
    ) -> float:
        """
        Calculate confidence in the identified regime.

        Confidence is based on the classification evidence
        available for the regime.

        Configurable weights:

        - CPI evidence: configured CPI weight
        - Interest-rate evidence: configured rate weight
        - GDP evidence: configured GDP weight

        Confidence is calculated as:

            supporting evidence / applicable evidence * 100

        This ensures that unavailable indicators do not
        artificially reduce confidence.

        Parameters
        ----------
        regime_type:
            Regime already determined by RegimeService.

        indicators:
            Historical macroeconomic indicator records.

        Returns
        -------
        float
            Confidence percentage between 0 and 100.
        """

        if regime_type not in self.VALID_REGIMES:
            raise ValueError(
                f"Invalid regime type: {regime_type}"
            )

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

        applicable_weight = 0.0
        supporting_weight = 0.0

        # --------------------------------------------------------
        # CPI EVIDENCE
        # --------------------------------------------------------

        cpi_supported = False
        cpi_available = False

        cpi_records = values.get("cpi", [])

        if len(cpi_records) >= 2:

            latest_cpi = cpi_records[0]

            if latest_cpi.value is not None:

                target_time = (
                    latest_cpi.time
                    - (
                        latest_cpi.time
                        - latest_cpi.time
                    )
                )

                # Reuse the same one-year period defined by
                # the regime classification configuration.
                from datetime import timedelta

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
                    historical_cpi.value is not None
                    and historical_cpi.value > 0
                ):
                    cpi_inflation = (
                        (
                            latest_cpi.value
                            - historical_cpi.value
                        )
                        / historical_cpi.value
                    ) * 100

                    cpi_available = True

                    if regime_type == "high_inflation":
                        cpi_supported = (
                            cpi_inflation
                            > settings.INFLATION_THRESHOLD
                        )

                    elif regime_type == "low_inflation":
                        cpi_supported = (
                            cpi_inflation
                            < settings.LOW_INFLATION_THRESHOLD
                        )

        if cpi_available:
            weight = (
                settings.REGIME_CONFIDENCE_CPI_WEIGHT
            )

            applicable_weight += weight

            if cpi_supported:
                supporting_weight += weight

        # --------------------------------------------------------
        # INTEREST RATE EVIDENCE
        # --------------------------------------------------------

        rate_supported = False
        rate_available = False

        rate_records = values.get(
            "federal_funds_rate",
            [],
        )

        if len(rate_records) >= 2:

            latest_rate = rate_records[0]

            if latest_rate.value is not None:

                from datetime import timedelta

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

                    rate_change = (
                        latest_rate.value
                        - historical_rate.value
                    )

                    rate_available = True

                    if regime_type == "rising_rates":
                        rate_supported = (
                            rate_change > 0
                        )

                    elif regime_type == "falling_rates":
                        rate_supported = (
                            rate_change < 0
                        )

        if rate_available:
            weight = (
                settings.REGIME_CONFIDENCE_RATE_WEIGHT
            )

            applicable_weight += weight

            if rate_supported:
                supporting_weight += weight

        # --------------------------------------------------------
        # GDP EVIDENCE
        # --------------------------------------------------------

        gdp_supported = False
        gdp_available = False

        gdp_records = values.get(
            "gdp",
            [],
        )

        if gdp_records:

            latest_gdp = gdp_records[0]

            if latest_gdp.change_percent is not None:

                gdp_available = True

                if regime_type == "growth":
                    gdp_supported = (
                        latest_gdp.change_percent
                        > settings.GDP_GROWTH_THRESHOLD
                    )

                elif regime_type == "recession":

                    negative_quarters = 0

                    for record in gdp_records[:2]:

                        if (
                            record.change_percent
                            is not None
                            and record.change_percent < 0
                        ):
                            negative_quarters += 1

                    gdp_supported = (
                        negative_quarters >= 2
                    )

        if gdp_available:
            weight = (
                settings.REGIME_CONFIDENCE_GDP_WEIGHT
            )

            applicable_weight += weight

            if gdp_supported:
                supporting_weight += weight

        # --------------------------------------------------------
        # NO APPLICABLE EVIDENCE
        # --------------------------------------------------------

        if applicable_weight <= 0:
            logger.warning(
                "No applicable evidence available for "
                "regime confidence: %s",
                regime_type,
            )

            return 0.0

        confidence = (
            supporting_weight
            / applicable_weight
        ) * 100

        # Ensure numerical result stays within valid range.
        confidence = max(
            0.0,
            min(
                100.0,
                confidence,
            ),
        )

        return round(
            confidence,
            2,
        )

    # ============================================================
    # VISUAL INDICATOR
    # ============================================================

    def get_visual_indicator(
        self,
        regime_type: str,
    ) -> str:
        """
        Return the configured visual indicator for a regime.

        Examples:

        - Growth -> bull
        - Falling rates -> bull
        - High inflation -> bear
        - Rising rates -> bear
        - Recession -> recession
        """

        if regime_type not in self.VALID_REGIMES:
            raise ValueError(
                f"Invalid regime type: {regime_type}"
            )

        return settings.REGIME_VISUAL_INDICATORS.get(
            regime_type,
            "neutral",
        )

    # ============================================================
    # CURRENT REGIME UPDATE
    # ============================================================

    def update_current_regime(
        self,
        regime_type: str,
        indicators: list,
        expires_at: datetime | None = None,
    ):
        """
        Calculate confidence and visual indicator and
        persist the current regime snapshot.
        """

        if regime_type not in self.VALID_REGIMES:
            raise ValueError(
                f"Invalid regime type: {regime_type}"
            )

        confidence = self.calculate_confidence(
            regime_type=regime_type,
            indicators=indicators,
        )

        visual_indicator = self.get_visual_indicator(
            regime_type
        )

        current_regime = (
            self.repository.set_current_regime(
                regime_type=regime_type,
                confidence=confidence,
                visual_indicator=visual_indicator,
                expires_at=expires_at,
            )
        )

        logger.info(
            "Current regime updated: "
            "regime=%s confidence=%.2f visual=%s",
            regime_type,
            confidence,
            visual_indicator,
        )

        return current_regime

    # ============================================================
    # PROCESS CURRENT REGIME
    # ============================================================

    async def process_current_regime(
        self,
        indicators: list | None = None,
    ):
        """
        Determine, calculate, and persist the current regime.

        When indicators are not supplied, historical indicators
        are loaded from the database.
        """

        if indicators is None:

            from app.models.macro_indicator import (
                MacroIndicator,
            )

            indicators = (
                self.db.query(MacroIndicator)
                .order_by(
                    MacroIndicator.time.desc()
                )
                .all()
            )

        if not indicators:
            logger.warning(
                "No macroeconomic indicators available "
                "for current regime processing"
            )

            return None

        # First determine the regime using the existing
        # classification engine.
        regime_type = (
            self.regime_service.determine_regime(
                indicators
            )
        )

        # Then calculate confidence and visual indicator.
        return self.update_current_regime(
            regime_type=regime_type,
            indicators=indicators,
        )

    # ============================================================
    # SERVICE LIFECYCLE
    # ============================================================

    async def close(self):
        """
        Close service resources.

        Database lifecycle is managed externally.
        """

        return None