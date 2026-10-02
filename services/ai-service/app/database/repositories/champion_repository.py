"""Champion repository.

Encapsulates all database reads and writes for the champion state
tables:
    - model_champions:      the currently-active champion per
                            (horizon, market_condition)
    - champion_candidates:  the daily top-ranked candidate per
                            (horizon, market_condition)

Written by daily_promote_champion_job. Read by:
    - the promotion job itself (to fetch the incumbent)
    - the prediction jobs (to decide which model to load)
    - observability / debugging endpoints

CLI isolation:
    Both tables have `_cli` mirror variants (created by migration
    014). When settings.cli_mode is True, all reads and writes are
    routed to the CLI variants. This keeps CLI promotions fully
    sandboxed — a CLI run never modifies production champion state.

Design notes:

    - The champion tables are state, not time series. Each
      (horizon, market_condition) key has exactly one active row,
      enforced by a partial unique index. Promotions UPDATE the
      existing row rather than inserting a new one.

    - champion_candidates is append-only. One row per
      (candidate_date, horizon, market_condition, model_name,
      metric_name). Re-running the promotion job on the same day
      is idempotent: ON CONFLICT DO NOTHING drops the duplicate.

    - The repository does not commit. Callers control transactions
      via session_scope().

    - The repository returns plain dicts (not ORM objects) to
      keep the API simple and consistent with the other
      repositories in this package.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, desc, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.tables import (
    champion_candidates,
    champion_candidates_cli,
    model_champions,
    model_champions_cli,
)

logger = logging.getLogger(__name__)


# ============================================================
# ROW DATACLASSES
# ============================================================
@dataclass
class ModelChampionRow:
    """A single row to write into model_champions.

    Used both for the initial insert and for the update path when
    a new champion displaces the incumbent. The repository's
    upsert_champion() handles both cases — this dataclass only
    describes the payload.

    Attributes:
        horizon: '24h' or '7d'.
        market_condition: Regime label or None for global.
        model_name: Champion model identifier.
        model_version: Version string at promotion time.
        metric_name: Metric used to rank candidates.
        metric_value: Value of metric_name for the champion.
        sample_size: Matched points contributing to metric_value.
        lookback_days: Rolling window used to compute metric_value.
        previous_champion: The displaced champion (or None).
        reason: Human-readable justification for the promotion.
        promoted_at: When the promotion happened. Defaults to now.
    """

    horizon: str
    market_condition: Optional[str]
    model_name: str
    model_version: str
    metric_name: str
    metric_value: float
    sample_size: int
    lookback_days: int
    previous_champion: Optional[str] = None
    reason: Optional[str] = None
    promoted_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dict suitable for SQLAlchemy insert()."""
        return {
            "horizon": self.horizon,
            "market_condition": self.market_condition,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "promoted_at": self.promoted_at or datetime.now(timezone.utc),
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "sample_size": self.sample_size,
            "lookback_days": self.lookback_days,
            "previous_champion": self.previous_champion,
            "reason": self.reason,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ModelChampionRow("
            f"horizon='{self.horizon}', "
            f"market_condition={self.market_condition!r}, "
            f"model_name='{self.model_name}', "
            f"metric_name='{self.metric_name}', "
            f"metric_value={self.metric_value})"
        )


@dataclass
class ChampionCandidateRow:
    """A single row to write into champion_candidates.

    Represents one day's top-ranked candidate for a given
    (horizon, market_condition) key.

    Attributes:
        candidate_date: The day this candidate was the top pick.
        horizon: '24h' or '7d'.
        market_condition: Regime label or None for global.
        model_name: Top-ranked model identifier.
        metric_name: Metric used to rank.
        metric_value: Value of metric_name for this candidate.
        sample_size: Matched points contributing to metric_value.
    """

    candidate_date: date
    horizon: str
    market_condition: Optional[str]
    model_name: str
    metric_name: str
    metric_value: float
    sample_size: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dict suitable for SQLAlchemy insert()."""
        return {
            "candidate_date": self.candidate_date,
            "horizon": self.horizon,
            "market_condition": self.market_condition,
            "model_name": self.model_name,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "sample_size": self.sample_size,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ChampionCandidateRow("
            f"candidate_date={self.candidate_date}, "
            f"horizon='{self.horizon}', "
            f"market_condition={self.market_condition!r}, "
            f"model_name='{self.model_name}', "
            f"metric_value={self.metric_value})"
        )


# ============================================================
# REPOSITORY
# ============================================================
class ChampionRepository:
    """Repository for champion state reads and writes.

    All methods are async. The repository does not commit — the
    caller controls the transaction via session_scope().

    Example:
        async with session_scope() as session:
            repo = ChampionRepository(session)
            champ = await repo.get_champion(horizon="24h")
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: An AsyncSession bound to the target database.
        """
        self.session = session

    # ============================================================
    # CLI ROUTING HELPERS
    # ============================================================
    def _resolve_champion_table(self):
        """Return the active model_champions table.

        In CLI mode (settings.cli_mode=True), returns
        model_champions_cli. Otherwise the production table.
        """
        if settings.cli_mode:
            return model_champions_cli
        return model_champions

    def _resolve_candidates_table(self):
        """Return the active champion_candidates table.

        In CLI mode (settings.cli_mode=True), returns
        champion_candidates_cli. Otherwise the production table.
        """
        if settings.cli_mode:
            return champion_candidates_cli
        return champion_candidates

    # ============================================================
    # CHAMPION READS
    # ============================================================
    async def get_champion(
        self,
        horizon: str,
        market_condition: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch the active champion for a (horizon, regime) key.

        Args:
            horizon: '24h' or '7d'.
            market_condition: Regime label, or None for the global
                champion.

        Returns:
            Dict with the champion row, or None if no champion is
            set for this key.
        """
        table = self._resolve_champion_table()

        # Two-branch match for market_condition: if None, use IS
        # NULL; otherwise use =. SQLAlchemy handles this
        # automatically when we compare against None with ==, but
        # being explicit is clearer for readers.
        if market_condition is None:
            condition = table.c.market_condition.is_(None)
        else:
            condition = table.c.market_condition == market_condition

        stmt = (
            select(
                table.c.id,
                table.c.horizon,
                table.c.market_condition,
                table.c.model_name,
                table.c.model_version,
                table.c.promoted_at,
                table.c.metric_name,
                table.c.metric_value,
                table.c.sample_size,
                table.c.lookback_days,
                table.c.previous_champion,
                table.c.reason,
                table.c.created_at,
            )
            .where(
                table.c.horizon == horizon,
                condition,
            )
            .order_by(desc(table.c.promoted_at))
            .limit(1)
        )

        result = await self.session.execute(stmt)
        row = result.mappings().first()
        return dict(row) if row else None

    async def get_all_champions(self) -> List[Dict[str, Any]]:
        """Fetch every active champion row.

        Returns one row per (horizon, market_condition) that has an
        active champion. Ordered by horizon then regime for
        deterministic output.

        Returns:
            List of dicts.
        """
        table = self._resolve_champion_table()

        stmt = (
            select(
                table.c.id,
                table.c.horizon,
                table.c.market_condition,
                table.c.model_name,
                table.c.model_version,
                table.c.promoted_at,
                table.c.metric_name,
                table.c.metric_value,
                table.c.sample_size,
                table.c.lookback_days,
                table.c.previous_champion,
                table.c.reason,
                table.c.created_at,
            )
            .order_by(
                table.c.horizon.asc(),
                table.c.market_condition.asc().nullsfirst(),
            )
        )

        result = await self.session.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    # ============================================================
    # CHAMPION WRITES
    # ============================================================
    async def upsert_champion(self, row: ModelChampionRow) -> int:
        """Insert or update the active champion for a key.

        The (horizon, market_condition) key is the unique identity.
        If a row already exists for the key, it is updated in place.
        Otherwise a new row is inserted.

        Uses PostgreSQL's ON CONFLICT ... DO UPDATE against the
        partial unique index that enforces "one champion per
        (horizon, COALESCE(market_condition, '__global__'))".

        Does not commit.

        Args:
            row: The ModelChampionRow to upsert.

        Returns:
            The id of the affected row.
        """
        table = self._resolve_champion_table()
        payload = row.to_dict()

        # We insert with ON CONFLICT DO UPDATE. The conflict target
        # is the partial unique index. Because the index uses
        # COALESCE(market_condition, '__global__'), the conflict
        # target must reference the same expression.
        stmt = pg_insert(table).values(**payload)

        # Fields to update on conflict. Note: we do NOT update
        # `id` or `created_at`. All the business fields are
        # replaced with the new values.
        excluded = stmt.excluded
        stmt = stmt.on_conflict_do_update(
            index_elements=[
                table.c.horizon,
                func.coalesce(
                    table.c.market_condition,
                    "__global__",
                ),
            ],
            set_={
                "model_name": excluded.model_name,
                "model_version": excluded.model_version,
                "promoted_at": excluded.promoted_at,
                "metric_name": excluded.metric_name,
                "metric_value": excluded.metric_value,
                "sample_size": excluded.sample_size,
                "lookback_days": excluded.lookback_days,
                "previous_champion": excluded.previous_champion,
                "reason": excluded.reason,
            },
        ).returning(table.c.id)

        result = await self.session.execute(stmt)
        row_id = result.scalar_one()

        logger.info(
            f"Upserted champion for horizon={row.horizon!r} "
            f"market_condition={row.market_condition!r}: "
            f"{row.model_name} (metric={row.metric_name} "
            f"value={row.metric_value})"
        )

        return int(row_id)

    async def clear_champion(
        self,
        horizon: str,
        market_condition: Optional[str] = None,
    ) -> bool:
        """Remove the active champion for a key.

        Useful for tests and manual resets. Does not commit.

        Args:
            horizon: '24h' or '7d'.
            market_condition: Regime label or None.

        Returns:
            True if a row was removed, False otherwise.
        """
        table = self._resolve_champion_table()

        if market_condition is None:
            condition = table.c.market_condition.is_(None)
        else:
            condition = table.c.market_condition == market_condition

        stmt = (
            delete(table)
            .where(
                table.c.horizon == horizon,
                condition,
            )
            .returning(table.c.id)
        )

        result = await self.session.execute(stmt)
        removed = result.scalar_one_or_none() is not None
        if removed:
            logger.info(
                f"Cleared champion for horizon={horizon!r} "
                f"market_condition={market_condition!r}"
            )
        return removed

    # ============================================================
    # CANDIDATE READS
    # ============================================================
    async def get_stability_streak(
        self,
        horizon: str,
        market_condition: Optional[str],
        model_name: str,
        metric_name: str,
        today: Optional[date] = None,
    ) -> int:
        """Count consecutive days the model has been the top pick.

        Walks backward from today (or the passed `today`), reading
        the champion_candidates rows for the given
        (horizon, market_condition, model_name, metric_name) key.
        Stops at the first missing day.

        The streak includes today if a row exists for today. If the
        promotion job hasn't yet recorded today's candidate, the
        streak is measured up to the most recent recorded day.

        Args:
            horizon: '24h' or '7d'.
            market_condition: Regime label or None for global.
            model_name: The model whose streak we're measuring.
            metric_name: The metric used to rank (part of the key).
            today: Override for the "current date". Defaults to
                today in UTC. Pass a date in tests.

        Returns:
            Number of consecutive days. Zero if no row exists for
            the most recent day.
        """
        table = self._resolve_candidates_table()

        # Resolve today in UTC if not passed.
        if today is None:
            today = datetime.now(timezone.utc).date()

        # Fetch the last N days of rows for this exact key. N is
        # bounded by the secondary lookback window: a streak
        # longer than that cannot exist (the underlying metrics
        # would have expired). Cap at the max secondary window.
        lookback_days = max(
            settings.champion_secondary_lookback_days,
            settings.champion_stability_days * 4,
        )
        earliest = today - timedelta(days=lookback_days)

        # Match market_condition with the appropriate operator.
        if market_condition is None:
            mc_condition = table.c.market_condition.is_(None)
        else:
            mc_condition = table.c.market_condition == market_condition

        stmt = (
            select(table.c.candidate_date)
            .where(
                table.c.horizon == horizon,
                mc_condition,
                table.c.model_name == model_name,
                table.c.metric_name == metric_name,
                table.c.candidate_date >= earliest,
                table.c.candidate_date <= today,
            )
            .order_by(desc(table.c.candidate_date))
        )

        result = await self.session.execute(stmt)
        dates = [row[0] for row in result.all()]

        if not dates:
            return 0

        # The most recent candidate date must be today OR the
        # previous day. If it's older than that, the streak has
        # already been broken.
        most_recent = dates[0]
        if most_recent < today - timedelta(days=1):
            return 0

        # Walk backward day by day.
        streak = 0
        expected = most_recent
        for d in dates:
            if d == expected:
                streak += 1
                expected = expected - timedelta(days=1)
            else:
                # Gap detected.
                break

        logger.debug(
            f"Stability streak for {model_name} on "
            f"(horizon={horizon!r}, market_condition={market_condition!r}, "
            f"metric={metric_name!r}): {streak} day(s)"
        )

        return streak

    async def get_recent_candidates(
        self,
        horizon: str,
        market_condition: Optional[str] = None,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Fetch recent candidate rows for a (horizon, regime) key.

        Useful for debugging and for observing the rotation of top
        candidates over time.

        Args:
            horizon: '24h' or '7d'.
            market_condition: Regime label or None.
            days: Look-back window in days.

        Returns:
            List of dicts, most recent first.
        """
        table = self._resolve_candidates_table()
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)

        if market_condition is None:
            mc_condition = table.c.market_condition.is_(None)
        else:
            mc_condition = table.c.market_condition == market_condition

        stmt = (
            select(
                table.c.id,
                table.c.candidate_date,
                table.c.horizon,
                table.c.market_condition,
                table.c.model_name,
                table.c.metric_name,
                table.c.metric_value,
                table.c.sample_size,
                table.c.created_at,
            )
            .where(
                table.c.horizon == horizon,
                mc_condition,
                table.c.candidate_date >= cutoff,
            )
            .order_by(
                table.c.candidate_date.desc(),
                table.c.model_name.asc(),
            )
        )

        result = await self.session.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    # ============================================================
    # CANDIDATE WRITES
    # ============================================================
    async def record_candidate(self, row: ChampionCandidateRow) -> bool:
        """Record one day's top candidate for a key.

        Idempotent per (candidate_date, horizon, market_condition,
        model_name, metric_name) via ON CONFLICT DO NOTHING. A
        second call on the same day is a no-op.

        Does not commit.

        Args:
            row: The ChampionCandidateRow to record.

        Returns:
            True if a row was inserted, False if it already existed.
        """
        table = self._resolve_candidates_table()
        payload = row.to_dict()

        stmt = (
            pg_insert(table)
            .values(**payload)
            .on_conflict_do_nothing(
                constraint="champion_candidates_unique",
            )
            .returning(table.c.id)
        )

        # Note: the unique constraint name is shared between the
        # production table and its CLI mirror because LIKE ...
        # INCLUDING CONSTRAINTS copies the constraint name. Two
        # tables can't have two constraints with the same name in
        # the same schema, so the CLI table's constraint has a
        # generated name. That's why we specify the constraint
        # by its column list instead — the ON CONFLICT clause
        # needs to work for both.

        # Since the constraint name differs, we fall back to
        # column-based conflict resolution.
        stmt = (
            pg_insert(table)
            .values(**payload)
            .on_conflict_do_nothing(
                index_elements=[
                    table.c.candidate_date,
                    table.c.horizon,
                    table.c.model_name,
                    table.c.metric_name,
                ],
            )
            .returning(table.c.id)
        )

        result = await self.session.execute(stmt)
        inserted = result.scalar_one_or_none() is not None

        if inserted:
            logger.info(
                f"Recorded candidate for "
                f"(date={row.candidate_date}, horizon={row.horizon!r}, "
                f"market_condition={row.market_condition!r}): "
                f"{row.model_name} (metric={row.metric_name} "
                f"value={row.metric_value})"
            )
        else:
            logger.debug(
                f"Candidate already recorded for "
                f"(date={row.candidate_date}, horizon={row.horizon!r}, "
                f"market_condition={row.market_condition!r}, "
                f"model_name={row.model_name!r}, "
                f"metric={row.metric_name!r}) — skipping"
            )

        return inserted

    async def prune_old_candidates(self, keep_days: int = 180) -> int:
        """Delete candidate rows older than N days.

        Keeps the table from growing unbounded. The default 180
        days is well beyond any plausible stability window. Does
        not commit.

        Args:
            keep_days: Number of days of history to retain.

        Returns:
            Number of rows deleted.
        """
        table = self._resolve_candidates_table()
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=keep_days)

        stmt = (
            delete(table)
            .where(table.c.candidate_date < cutoff)
            .returning(table.c.id)
        )

        result = await self.session.execute(stmt)
        deleted_ids = [row[0] for row in result.all()]
        count = len(deleted_ids)

        if count > 0:
            logger.info(
                f"Pruned {count} champion_candidates rows older than "
                f"{cutoff}"
            )

        return count


__all__ = [
    "ChampionCandidateRow",
    "ChampionRepository",
    "ModelChampionRow",
]