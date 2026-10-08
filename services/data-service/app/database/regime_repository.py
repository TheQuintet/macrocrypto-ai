"""
Repository for storing and retrieving macroeconomic regime data.

Handles:
- Macro regime periods
- BTC performance by regime
- Current regime
"""

import logging
from datetime import date, datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.macro_regime import MacroRegime
from app.models.regime_performance import RegimePerformance
from app.models.current_regime import CurrentRegime
from app.config import settings

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
            if end_date >= regime.start_date:
                regime.duration_days = (
                    end_date - regime.start_date
                ).days
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
        confidence: float,
        visual_indicator: str,
        expires_at: datetime | None = None,
    ) -> CurrentRegime:
        """
        Store the currently identified macro regime.

        Args:
            regime_type:
                Classified macroeconomic regime.

            confidence:
                Classification confidence expressed as
                a percentage from 0 to 100.

            visual_indicator:
                Presentation-level market indicator.
                Supported values are configured in settings.

            expires_at:
                Optional expiration timestamp.
        """

        # ----------------------------------------------
        # Validate confidence
        # ----------------------------------------------

        if not 0 <= confidence <= 100:
            raise ValueError(
                "Confidence must be between 0 and 100"
            )

        # ----------------------------------------------
        # Validate visual indicator
        # ----------------------------------------------

        valid_visual_indicators = set(
            settings.REGIME_VISUAL_INDICATORS.values()
        )

        if visual_indicator not in valid_visual_indicators:
            raise ValueError(
                "Visual indicator must be one of: "
                + ", ".join(sorted(valid_visual_indicators))
            )

        # ----------------------------------------------
        # Create current regime record
        # ----------------------------------------------

        current = CurrentRegime(
            regime_type=regime_type,
            confidence=confidence,
            visual_indicator=visual_indicator,
            identified_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )

        self.db.add(current)
        self.db.commit()
        self.db.refresh(current)

        logger.info(
            "Current macro regime updated: %s "
            "(confidence=%.1f%%, visual_indicator=%s)",
            regime_type,
            confidence,
            visual_indicator,
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

    # --------------------------------------------------
    # REGIME BACKFILL SUPPORT
    # --------------------------------------------------

    def count_regimes(self) -> int:
        """
        Return the total number of rows in macro_regimes.

        Used by the scheduler to decide whether an initial
        backfill is needed (count == 0) or whether the table
        is already populated.
        """

        return (
            self.db.query(MacroRegime)
            .count()
        )

    def get_regimes_in_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[MacroRegime]:
        """
        Return all macro regimes that overlap [start_date, end_date].

        "Overlap" is inclusive on both ends:

            regime.start_date <= end_date
            AND (regime.end_date IS NULL OR regime.end_date >= start_date)

        An open regime (end_date IS NULL) is treated as extending
        to infinity, so it overlaps any range whose end_date is
        after the regime's start_date.

        Used by RegimeBackfillService for idempotency: a candidate
        backfilled run is skipped if it is fully covered by an
        existing regime.
        """

        return (
            self.db.query(MacroRegime)
            .filter(
                MacroRegime.start_date <= end_date,
                or_(
                    MacroRegime.end_date.is_(None),
                    MacroRegime.end_date >= start_date,
                ),
            )
            .order_by(MacroRegime.start_date.asc())
            .all()
        )

    def create_regime_many(
        self,
        rows: list[dict],
    ) -> int:
        """
        Batch-insert macro regime rows.

        Each row is a dict with keys:
            regime_type    (str)
            start_date     (date)
            end_date       (date | None)
            duration_days  (int | None)

        Does NOT commit. The caller owns the transaction so that a
        delete + insert sequence can be atomic.

        Returns the number of rows added to the session.

        Idempotency is the caller's responsibility: this method
        does not check for existing rows. Use get_regimes_in_range
        for that check, then insert only the missing runs.
        """

        if not rows:
            return 0

        now = datetime.now(timezone.utc)

        regimes = [
            MacroRegime(
                regime_type=row["regime_type"],
                start_date=row["start_date"],
                end_date=row.get("end_date"),
                duration_days=row.get("duration_days"),
                created_at=now,
            )
            for row in rows
        ]

        self.db.add_all(regimes)
        self.db.flush()

        logger.info(
            "Staged %d macro regime row(s) for insertion",
            len(regimes),
        )

        return len(regimes)

    def delete_open_regime(self) -> int:
        """
        Delete any macro_regimes row with end_date IS NULL.

        Used by the backfill as a defensive step before writing the
        full historical sequence. On an empty table this is a no-op;
        on a table that already has a placeholder open row (from the
        old RegimeService path, or from a partially-completed
        backfill), it removes the conflicting row.

        Does NOT commit. The caller owns the transaction.

        Returns the number of rows deleted.
        """

        deleted = (
            self.db.query(MacroRegime)
            .filter(MacroRegime.end_date.is_(None))
            .delete(synchronize_session=False)
        )

        if deleted:
            logger.info(
                "Deleted %d open macro_regimes row(s)",
                deleted,
            )

        return deleted