"""
Service layer for the BTC macroeconomic regime API.

This service aggregates:
- Historical macroeconomic regimes
- BTC performance metrics
- Current regime
- Similar historical periods
- Macro event analysis

The service is intentionally kept separate from the FastAPI
route layer so that API-specific aggregation logic is not mixed
with HTTP handling.
"""

from datetime import date
import logging
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.models.macro_regime import MacroRegime
from app.models.current_regime import CurrentRegime
from app.models.regime_performance import RegimePerformance

logger = logging.getLogger(__name__)

class RegimeAPIService:
    """
    Business logic for the BTC macroeconomic regime API.
    """

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # HISTORICAL REGIMES
    # ============================================================

    def get_historical_regimes(
        self,
        regime_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve historical macroeconomic regimes.

        Optional filters:
        - regime_type
        - start_date
        - end_date
        """

        query = self.db.query(MacroRegime)

        # --------------------------------------------------------
        # Regime type filter
        # --------------------------------------------------------

        if regime_type:
            query = query.filter(
                MacroRegime.regime_type == regime_type
            )

        # --------------------------------------------------------
        # Date range filters
        # --------------------------------------------------------

        if start_date:
            query = query.filter(
                MacroRegime.start_date >= start_date
            )

        if end_date:
            query = query.filter(
                MacroRegime.start_date <= end_date
            )

        regimes = (
            query
            .order_by(
                MacroRegime.start_date.desc()
            )
            .all()
        )

        results: list[dict[str, Any]] = []

        for regime in regimes:

            performance = (
                self.db.query(RegimePerformance)
                .filter(
                    RegimePerformance.regime_id
                    == regime.id
                )
                .order_by(
                    RegimePerformance.created_at.desc()
                )
                .first()
            )

            results.append(
                {
                    "id": regime.id,
                    "regime_type": regime.regime_type,
                    "start_date": regime.start_date,
                    "end_date": regime.end_date,
                    "duration_days": getattr(
                        regime,
                        "duration_days",
                        None,
                    ),
                    "performance": (
                        self._serialize_performance(
                            performance
                        )
                        if performance
                        else None
                    ),
                }
            )

        return results

    # ============================================================
    # CURRENT REGIME
    # ============================================================

    def get_current_regime(
        self,
    ) -> Optional[dict[str, Any]]:
        """
        Retrieve the most recently identified current regime.
        """

        current_regime = (
            self.db.query(CurrentRegime)
            .order_by(
                CurrentRegime.identified_at.desc()
            )
            .first()
        )

        if current_regime is None:
            return None

        return {
            "id": current_regime.id,
            "regime_type": current_regime.regime_type,
            "confidence": getattr(
                current_regime,
                "confidence",
                None,
            ),
            "visual_indicator": getattr(
                current_regime,
                "visual_indicator",
                None,
            ),
            "identified_at": current_regime.identified_at,
            "expires_at": current_regime.expires_at,
        }

    # ============================================================
    # PERFORMANCE
    # ============================================================

    def get_latest_performance(
        self,
        regime_id: int,
    ) -> Optional[dict[str, Any]]:
        """
        Retrieve the latest performance record for a regime.
        """

        performance = (
            self.db.query(RegimePerformance)
            .filter(
                RegimePerformance.regime_id == regime_id
            )
            .order_by(
                RegimePerformance.created_at.desc()
            )
            .first()
        )

        if performance is None:
            return None

        return self._serialize_performance(
            performance
        )

    # ============================================================
    # SIMILAR PERIODS
    # ============================================================

    # ============================================================
    # SIMILAR PERIODS
    # ============================================================

    def get_similar_periods(
        self,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Retrieve similar historical periods using the
        existing SimilarPeriodService implementation.

        The underlying service returns a response containing:
        - current_conditions
        - method
        - period_count
        - similar_periods

        The BTC regime API only exposes the actual
        similar_periods collection.
        """

        try:
            from app.services.similar_period_service import (
                SimilarPeriodService,
            )

            service = SimilarPeriodService(self.db)

            result = service.find_similar_periods(
                limit=limit
            )

            if result is None:
                return []

            if isinstance(result, dict):
                return result.get(
                    "similar_periods",
                    [],
                )

            return []

        except Exception:
            logger.exception(
                "Failed to retrieve similar historical periods"
            )
            return []

    # ============================================================
    # EVENT ANALYSIS
    # ============================================================

    def get_event_analysis(
        self,
        regime_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve persisted macro event analysis.

        If regime_id is provided, return events for that regime.
        Otherwise return all event analysis records.
        """

        try:
            from app.services.regime_event_service import (
                RegimeEventService,
            )

            service = RegimeEventService(self.db)

            events = service.get_event_analysis(
                regime_id=regime_id
            )

            return [
                {
                    "id": event.id,
                    "regime_id": event.regime_id,
                    "event_type": event.event_type,
                    "event_date": event.event_date,
                    "btc_price_before": event.btc_price_before,
                    "btc_price_after": event.btc_price_after,
                    "btc_return": event.btc_return,
                    "created_at": event.created_at,
                }
                for event in events
            ]

        except Exception:
            logger.exception(
                "Failed to retrieve macro event analysis"
            )
            return []

    # ============================================================
    # COMPLETE BTC REGIME RESPONSE
    # ============================================================

    def get_btc_regime_data(
        self,
        regime_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        similar_limit: int = 5,
    ) -> dict[str, Any]:
        """
        Build the complete response required by:

            GET /api/v1/regimes/btc

        Includes:
        - Historical regimes
        - Performance metrics
        - Current regime
        - Similar historical periods
        - Macro event analysis
        """

        historical_regimes = (
            self.get_historical_regimes(
                regime_type=regime_type,
                start_date=start_date,
                end_date=end_date,
            )
        )

        current_regime = (
            self.get_current_regime()
        )

        similar_periods = (
            self.get_similar_periods(
                limit=similar_limit
            )
        )

        event_analysis = (
            self.get_event_analysis()
        )

        return {
            "current_regime": current_regime,
            "historical_regimes": historical_regimes,
            "similar_periods": similar_periods,
            "event_analysis": event_analysis,
        }

    # ============================================================
    # SERIALIZATION HELPERS
    # ============================================================

    @staticmethod
    def _serialize_performance(
        performance: RegimePerformance,
    ) -> dict[str, Any]:
        """
        Convert a RegimePerformance ORM object into
        a JSON-compatible dictionary.
        """

        return {
            "avg_return": performance.avg_return,
            "max_drawdown": performance.max_drawdown,
            "volatility": performance.volatility,
            "sharpe_ratio": performance.sharpe_ratio,
            "btc_price_start": performance.btc_price_start,
            "btc_price_end": performance.btc_price_end,
        }