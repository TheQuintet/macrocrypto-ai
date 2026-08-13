"""
Repository for storing and retrieving macroeconomic regime data.

Handles:
- Macro regime periods
- BTC performance by regime
- Current regime
"""

import logging
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.macro_regime import MacroRegime
from app.models.regime_performance import RegimePerformance
from app.models.current_regime import CurrentRegime

logger = logging.getLogger(__name__)


class RegimeRepository:
    """
    Handles database operations for macroeconomic regimes.
    """

    def __init__(self, db: Session):
        self.db = db

    # --------------------------------------------------
    # MACRO REGIMES
    # --------------------------------------------------

    def create_regime(
        self,
        regime_type: str,
        start_date: date,
        end_date: date | None = None,
        duration_days: int | None = None,
    ) -> MacroRegime:
        """
        Create a macroeconomic regime record.
        """

        regime = MacroRegime(
            regime_type=regime_type,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(regime)
        self.db.commit()
        self.db.refresh(regime)

        logger.info(
            "Stored macro regime: %s (%s - %s)",
            regime_type,
            start_date,
            end_date,
        )

        return regime

    def get_current_regime(
        self,
    ) -> MacroRegime | None:
        """
        Return the currently active macro regime.
        """

        return (
            self.db.query(MacroRegime)
            .filter(
                MacroRegime.end_date.is_(None)
            )
            .order_by(
                MacroRegime.start_date.desc()
            )
            .first()
        )

    def get_latest_regime(
        self,
    ) -> MacroRegime | None:
        """
        Return the most recently created regime.
        """

        return (
            self.db.query(MacroRegime)
            .order_by(
                MacroRegime.start_date.desc()
            )
            .first()
        )

    def close_regime(
        self,
        regime: MacroRegime,
        end_date: date,
    ) -> MacroRegime:
        """
        Close an active regime.
        """

        regime.end_date = end_date

        if regime.start_date:
            regime.duration_days = (
                end_date - regime.start_date
            ).days
            if end_date >= regime.start_date:
                regime.duration_days = (end_date - regime.start_date).days
            else:
                regime.duration_days = 0

        self.db.commit()
        self.db.refresh(regime)

        return regime

    # --------------------------------------------------
    # REGIME PERFORMANCE
    # --------------------------------------------------

    def create_performance(
        self,
        regime_id: int,
        avg_return: float | None = None,
        max_drawdown: float | None = None,
        volatility: float | None = None,
        sharpe_ratio: float | None = None,
        btc_price_start: float | None = None,
        btc_price_end: float | None = None,
    ) -> RegimePerformance:
        """
        Store BTC performance statistics for a regime.
        """

        performance = RegimePerformance(
            regime_id=regime_id,
            avg_return=avg_return,
            max_drawdown=max_drawdown,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            btc_price_start=btc_price_start,
            btc_price_end=btc_price_end,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(performance)
        self.db.commit()
        self.db.refresh(performance)

        logger.info(
            "Stored BTC performance for regime_id=%s",
            regime_id,
        )

        return performance

    def get_performance(
        self,
        regime_id: int,
    ) -> RegimePerformance | None:
        """
        Return performance statistics for a regime.
        """

        return (
            self.db.query(RegimePerformance)
            .filter(
                RegimePerformance.regime_id == regime_id
            )
            .order_by(
                RegimePerformance.created_at.desc()
            )
            .first()
        )

    # --------------------------------------------------
    # CURRENT REGIME
    # --------------------------------------------------

    def set_current_regime(
        self,
        regime_type: str,
        expires_at: datetime | None = None,
    ) -> CurrentRegime:
        """
        Store the currently identified macro regime.
        """

        current = CurrentRegime(
            regime_type=regime_type,
            identified_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )

        self.db.add(current)
        self.db.commit()
        self.db.refresh(current)

        logger.info(
            "Current macro regime updated: %s",
            regime_type,
        )

        return current

    def get_current_regime_snapshot(
        self,
    ) -> CurrentRegime | None:
        """
        Return the most recently identified current regime.
        """

        return (
            self.db.query(CurrentRegime)
            .order_by(
                CurrentRegime.identified_at.desc()
            )
            .first()
        )