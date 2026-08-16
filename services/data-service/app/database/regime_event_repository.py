"""
Repository for macro event analysis.
"""

import logging
from datetime import date

from sqlalchemy.orm import Session

from app.models.regime_event_analysis import RegimeEventAnalysis


logger = logging.getLogger(__name__)


class RegimeEventRepository:
    """
    Handles persistence and retrieval of macro event analysis.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_event_analysis(
        self,
        regime_id: int,
        event_type: str,
        event_date: date,
        btc_price_before: float,
        btc_price_after: float,
        btc_return: float,
    ) -> RegimeEventAnalysis:

        analysis = RegimeEventAnalysis(
            regime_id=regime_id,
            event_type=event_type,
            event_date=event_date,
            btc_price_before=btc_price_before,
            btc_price_after=btc_price_after,
            btc_return=btc_return,
        )

        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        logger.info(
            "Stored event analysis: %s on %s, regime_id=%s",
            event_type,
            event_date,
            regime_id,
        )

        return analysis

    def get_by_regime(
        self,
        regime_id: int,
    ) -> list[RegimeEventAnalysis]:

        return (
            self.db.query(RegimeEventAnalysis)
            .filter(
                RegimeEventAnalysis.regime_id == regime_id
            )
            .order_by(
                RegimeEventAnalysis.event_date.desc()
            )
            .all()
        )

    def get_all(
        self,
    ) -> list[RegimeEventAnalysis]:

        return (
            self.db.query(RegimeEventAnalysis)
            .order_by(
                RegimeEventAnalysis.event_date.desc()
            )
            .all()
        )