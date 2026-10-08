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

    # --------------------------------------------------
    # IDEMPOTENCY / BATCH SUPPORT
    # --------------------------------------------------

    def exists(
        self,
        regime_id: int,
        event_type: str,
        event_date: date,
    ) -> bool:
        """
        Return True if an analysis row already exists for the
        given (regime_id, event_type, event_date) triple.

        The regime_event_analysis table has no unique constraint
        on this triple (schema is frozen), so idempotency is the
        caller's responsibility. The service checks this before
        inserting; create_event_analysis_many does NOT check.
        """

        return (
            self.db.query(RegimeEventAnalysis)
            .filter(
                RegimeEventAnalysis.regime_id == regime_id,
                RegimeEventAnalysis.event_type == event_type,
                RegimeEventAnalysis.event_date == event_date,
            )
            .first()
            is not None
        )

    def create_event_analysis_many(
        self,
        rows: list[dict],
    ) -> int:
        """
        Batch-insert regime_event_analysis rows.

        Each row is a dict with keys:
            regime_id         (int)
            event_type        (str)
            event_date        (date)
            btc_price_before  (float)
            btc_price_after   (float)
            btc_return        (float)

        Does NOT commit. The caller owns the transaction. This
        differs from create_event_analysis, which commits
        internally — that contract is preserved for existing
        callers.

        Idempotency is the caller's responsibility: this method
        does not check for existing rows. Use exists() for that,
        then insert only the missing triples.

        Returns the number of rows added to the session.
        """

        if not rows:
            return 0

        analyses = [
            RegimeEventAnalysis(
                regime_id=row["regime_id"],
                event_type=row["event_type"],
                event_date=row["event_date"],
                btc_price_before=row["btc_price_before"],
                btc_price_after=row["btc_price_after"],
                btc_return=row["btc_return"],
            )
            for row in rows
        ]

        self.db.add_all(analyses)
        self.db.flush()

        logger.info(
            "Staged %d regime_event_analysis row(s) for insertion",
            len(analyses),
        )

        return len(analyses)