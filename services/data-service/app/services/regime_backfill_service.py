"""
Historical backfill for the macro_regimes table.

The live path never wrote to macro_regimes — CurrentRegimeService
updates current_regime but not the historical table. This service
reconstructs the full historical regime timeline by replaying
RegimeService.determine_regime over the raw macro_indicators
history, in a point-in-time-correct walk-forward loop.

Reads:
    macro_indicators  (raw; indicator_name IN
                       {'cpi','federal_funds_rate','gdp'})

Writes:
    macro_regimes     (one row per contiguous regime run)
    current_regime    (reconciled to the final run's label)

Design notes:
    - Reuses RegimeService.determine_regime; does not reimplement
      classification.
    - Only the three indicators the classifier actually reads are
      loaded. vix/dxy/etc. are not passed.
    - Walk-forward stepping is event-driven: the algorithm only
      reclassifies at timestamps where one of the three indicators
      changed. Between such timestamps the classifier's output is
      constant by construction.
    - Idempotent by-skip: runs already covered by existing
      macro_regimes rows are dropped before insert. A re-run on a
      fully-populated table is a complete no-op.
    - Guarded by a Postgres advisory lock so the CLI and the
      scheduler cannot overlap.

The last backfilled run is written with end_date = None, matching
the invariant RegimeRepository.get_current_regime() relies on.
"""

import logging
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.regime_repository import RegimeRepository
from app.models.macro_indicator import MacroIndicator
from app.services.regime_service import RegimeService

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------------

# The earliest date for which we attempt a backfill. Matches the
# start of Binance hourly history (2017-08-17), which is the
# earliest point for which the raw data window is meaningful.
# This is a soft floor: if macro_indicators has rows before this
# date, they are ignored.
DEFAULT_REGIME_BACKFILL_START = date(2017, 8, 17)

# Indicator names the classifier reads. Adding anything else here
# would silently change classification behavior — do not.
_CLASSIFIER_INDICATORS = ("cpi", "federal_funds_rate", "gdp")

# Advisory lock key. 0x726567696d65 == b"regime".
# Non-blocking; released on session close.
_ADVISORY_LOCK_KEY = 0x726567696D65


# ------------------------------------------------------------------
# SERVICE
# ------------------------------------------------------------------

class RegimeBackfillService:
    """
    Reconstructs the macro_regimes history from raw
    macro_indicators.

    Usage:
        service = RegimeBackfillService(db)
        result = await service.backfill_regimes(
            start_date=date(2017, 8, 17),
        )
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = RegimeRepository(db)
        self.regime_service = RegimeService(db)

    # ----------------------------------------------------------
    # PUBLIC ENTRY POINT
    # ----------------------------------------------------------

    async def backfill_regimes(
        self,
        start_date: date,
        end_date: date | None = None,
    ) -> dict:
        """
        Backfill macro_regimes for [start_date, end_date].

        end_date defaults to today (UTC). The last run is written
        with end_date = None so it remains the "current" regime.

        Returns:
            {
                "status":         "ok" | "skipped_already_running"
                                  | "no_data",
                "rows_inserted":  int,
                "date_range":     (start_date, end_date),
                "regimes_found":  list[str],   # distinct, in order
            }

        Never raises on a lock-contention or no-data outcome; those
        are reported via the status field. Any DB or classifier
        error propagates after the transaction is rolled back.
        """

        if end_date is None:
            end_date = datetime.now(timezone.utc).date()

        if start_date > end_date:
            raise ValueError(
                f"start_date ({start_date}) must be <= "
                f"end_date ({end_date})"
            )

        # ------------------------------------------------------
        # ADVISORY LOCK
        # ------------------------------------------------------

        if not self._acquire_lock():
            logger.warning(
                "Regime backfill skipped: another backfill holds "
                "the advisory lock"
            )
            return {
                "status": "skipped_already_running",
                "rows_inserted": 0,
                "date_range": (start_date, end_date),
                "regimes_found": [],
            }

        try:
            return self._run_backfill(start_date, end_date)
        finally:
            self._release_lock()

    # ----------------------------------------------------------
    # INTERNAL — TOP-LEVEL RUN
    # ----------------------------------------------------------

    def _run_backfill(
        self,
        start_date: date,
        end_date: date,
    ) -> dict:
        # ------------------------------------------------------
        # 1. Load indicator history
        # ------------------------------------------------------

        indicators = self._load_indicators(start_date, end_date)

        if not indicators:
            logger.warning(
                "Regime backfill: no macro_indicators rows in "
                "[%s, %s] for %s — nothing to do",
                start_date,
                end_date,
                ", ".join(_CLASSIFIER_INDICATORS),
            )
            return {
                "status": "no_data",
                "rows_inserted": 0,
                "date_range": (start_date, end_date),
                "regimes_found": [],
            }

        # ------------------------------------------------------
        # 2. Walk forward, classify at each change point
        # ------------------------------------------------------

        timeline = self._build_timeline(indicators)

        if not timeline:
            logger.warning(
                "Regime backfill: indicator history produced an "
                "empty walk-forward timeline"
            )
            return {
                "status": "no_data",
                "rows_inserted": 0,
                "date_range": (start_date, end_date),
                "regimes_found": [],
            }

        runs = self._classify_runs(
            indicators=indicators,
            timeline=timeline,
            start_date=start_date,
            end_date=end_date,
        )

        if not runs:
            logger.warning(
                "Regime backfill: no regime runs produced"
            )
            return {
                "status": "no_data",
                "rows_inserted": 0,
                "date_range": (start_date, end_date),
                "regimes_found": [],
            }

        # ------------------------------------------------------
        # 3. Idempotency check — drop fully-covered runs
        # ------------------------------------------------------

        runs_to_insert = self._filter_covered_runs(
            runs, start_date, end_date
        )

        if not runs_to_insert:
            logger.info(
                "Regime backfill: all %d candidate run(s) already "
                "covered by existing macro_regimes rows — no-op",
                len(runs),
            )
            return {
                "status": "ok",
                "rows_inserted": 0,
                "date_range": (start_date, end_date),
                "regimes_found": self._distinct_regimes(runs),
            }

        # ------------------------------------------------------
        # 4. Atomic write: delete open row + insert runs
        # ------------------------------------------------------

        rows_inserted = self._write_runs(runs_to_insert)

        # ------------------------------------------------------
        # 5. Reconcile current_regime with the final run
        # ------------------------------------------------------

        self._reconcile_current_regime(runs)

        logger.info(
            "Regime backfill complete: inserted=%d, "
            "range=%s..%s",
            rows_inserted,
            start_date,
            end_date,
        )

        return {
            "status": "ok",
            "rows_inserted": rows_inserted,
            "date_range": (start_date, end_date),
            "regimes_found": self._distinct_regimes(runs),
        }

    # ----------------------------------------------------------
    # INTERNAL — LOADING
    # ----------------------------------------------------------

    def _load_indicators(
        self,
        start_date: date,
        end_date: date,
    ) -> list[MacroIndicator]:
        """
        Load all classifier-relevant macro_indicators rows with
        time <= end of end_date (UTC).

        Filtering to time <= end_date only — no lower bound — is
        deliberate: the classifier needs lookback history (up to
        ~1 year for CPI, ~3 months for FFR) to compute its
        comparisons, even for classifications near start_date.
        Truncating the lower end would corrupt the earliest runs.

        The start_date floor is applied when building the timeline,
        not here.
        """

        end_of_day = datetime.combine(
            end_date, time.max, tzinfo=timezone.utc
        )

        return (
            self.db.query(MacroIndicator)
            .filter(
                MacroIndicator.indicator_name.in_(
                    _CLASSIFIER_INDICATORS
                ),
                MacroIndicator.time <= end_of_day,
            )
            .order_by(MacroIndicator.time.asc())
            .all()
        )

    # ----------------------------------------------------------
    # INTERNAL — TIMELINE
    # ----------------------------------------------------------

    @staticmethod
    def _build_timeline(
        indicators: list[MacroIndicator],
    ) -> list[datetime]:
        """
        Sorted, de-duplicated list of timestamps at which the
        classifier's input can change.

        That is: every distinct MacroIndicator.time value across
        the loaded rows. The walk-forward loop steps through
        these points only.
        """

        return sorted({ind.time for ind in indicators})

    # ----------------------------------------------------------
    # INTERNAL — CLASSIFICATION
    # ----------------------------------------------------------

    def _classify_runs(
        self,
        indicators: list[MacroIndicator],
        timeline: list[datetime],
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """
        Walk forward over `timeline`, calling determine_regime at
        each point with the PIT-correct indicator subset. Group
        consecutive identical labels into runs.

        Returns a list of dicts:
            {
                "regime_type":   str,
                "start_date":    date,
                "end_date":      date | None,
                "duration_days": int | None,
            }

        The final run is always written with end_date = None
        (per the get_current_regime invariant).
        """

        start_dt = datetime.combine(
            start_date, time.min, tzinfo=timezone.utc
        )

        # We only classify at timeline points on/after start_date.
        # Anything before is used only as lookback history.
        relevant_points = [t for t in timeline if t >= start_dt]

        if not relevant_points:
            return []

        # Indicator rows sorted ascending, for the incremental
        # "time <= T" subset construction below.
        indicators_sorted = sorted(indicators, key=lambda i: i.time)

        runs: list[dict] = []
        cursor = 0  # how many indicators have time <= current T

        previous_label: str | None = None
        current_run_start: datetime | None = None

        for T in relevant_points:
            # Advance the cursor to include all indicators with
            # time <= T. The list passed to determine_regime is a
            # slice of indicators_sorted — no per-step filtering.
            while (
                cursor < len(indicators_sorted)
                and indicators_sorted[cursor].time <= T
            ):
                cursor += 1

            subset = indicators_sorted[:cursor]

            label = self.regime_service.determine_regime(subset)

            if label != previous_label:
                # Close the previous run at T - 1 second
                # (so the next run starts exactly at T).
                if previous_label is not None and current_run_start is not None:
                    runs.append(
                        self._make_run(
                            regime_type=previous_label,
                            run_start=current_run_start,
                            run_end_exclusive=T,
                        )
                    )

                previous_label = label
                current_run_start = T

        # Close the final run. Per Q3, it stays open (end_date=None).
        if previous_label is not None and current_run_start is not None:
            runs.append(
                {
                    "regime_type": previous_label,
                    "start_date": current_run_start.date(),
                    "end_date": None,
                    "duration_days": None,
                }
            )

        return runs

    @staticmethod
    def _make_run(
        regime_type: str,
        run_start: datetime,
        run_end_exclusive: datetime,
    ) -> dict:
        """
        Build a closed run dict from a [start, end_exclusive)
        interval. The end_date written is the last full day in
        the interval.
        """

        run_end = run_end_exclusive - timedelta(seconds=1)

        start_d = run_start.date()
        end_d = run_end.date()

        duration = (end_d - start_d).days

        return {
            "regime_type": regime_type,
            "start_date": start_d,
            "end_date": end_d,
            "duration_days": duration,
        }

    # ----------------------------------------------------------
    # INTERNAL — IDEMPOTENCY
    # ----------------------------------------------------------

    def _filter_covered_runs(
        self,
        runs: list[dict],
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """
        Drop runs whose [start_date, end_date] is fully covered by
        an existing macro_regimes row. Open runs are dropped if any
        existing open row already covers their start_date.

        Coverage test:
            exists a regime R such that
                R.start_date <= run.start_date
                AND (R.end_date IS NULL OR R.end_date >= run.end_date)

        For an open run (run.end_date is None), the second condition
        becomes "R.end_date IS NULL OR R.end_date >= run.start_date".
        """

        existing = self.repository.get_regimes_in_range(
            start_date, end_date
        )

        if not existing:
            return list(runs)

        kept: list[dict] = []

        for run in runs:
            if not self._is_covered(run, existing):
                kept.append(run)

        dropped = len(runs) - len(kept)
        if dropped:
            logger.info(
                "Regime backfill: dropped %d already-covered "
                "run(s) of %d",
                dropped,
                len(runs),
            )

        return kept

    @staticmethod
    def _is_covered(
        run: dict,
        existing: list,
    ) -> bool:
        run_start = run["start_date"]
        run_end = run.get("end_date")

        for regime in existing:
            r_start = regime.start_date
            r_end = regime.end_date

            if r_start > run_start:
                continue

            if run_end is None:
                # Open run: covered iff an open regime exists that
                # started on or before run_start.
                if r_end is None:
                    return True
                continue

            if r_end is None or r_end >= run_end:
                return True

        return False

    # ----------------------------------------------------------
    # INTERNAL — WRITE
    # ----------------------------------------------------------

    def _write_runs(
        self,
        runs: list[dict],
    ) -> int:
        """
        Atomically replace the open macro_regimes row (if any) and
        insert the new runs.

        A single commit covers the delete + insert. If either
        fails, both roll back.
        """

        try:
            self.repository.delete_open_regime()
            inserted = self.repository.create_regime_many(runs)
            self.db.commit()
            return inserted
        except Exception:
            self.db.rollback()
            raise

    # ----------------------------------------------------------
    # INTERNAL — CURRENT_REGIME RECONCILIATION
    # ----------------------------------------------------------

    def _reconcile_current_regime(
        self,
        runs: list[dict],
    ) -> None:
        """
        Align current_regime with the final run's label.

        Uses CurrentRegimeService so confidence + visual are
        computed the same way the daily job would compute them.

        Loaded lazily to avoid a circular import at module top
        (CurrentRegimeService imports RegimeService, which this
        module also imports).
        """

        if not runs:
            return

        final = runs[-1]

        from app.services.current_regime_service import (
            CurrentRegimeService,
        )

        current_service = CurrentRegimeService(self.db)

        # The classifier's inputs at the end of the range are the
        # full loaded indicator set. Recompute confidence from
        # those, matching what the live path does.
        end_dt = datetime.now(timezone.utc)
        indicators = (
            self.db.query(MacroIndicator)
            .filter(
                MacroIndicator.indicator_name.in_(
                    _CLASSIFIER_INDICATORS
                ),
                MacroIndicator.time <= end_dt,
            )
            .order_by(MacroIndicator.time.desc())
            .all()
        )

        try:
            current_service.update_current_regime(
                regime_type=final["regime_type"],
                indicators=indicators,
            )
        except Exception:
            # Reconciliation is best-effort: the macro_regimes
            # history is already committed, and the daily job will
            # reconcile current_regime on its next run anyway.
            logger.exception(
                "Regime backfill: current_regime reconciliation "
                "failed; will retry on next daily run"
            )

    # ----------------------------------------------------------
    # INTERNAL — HELPERS
    # ----------------------------------------------------------

    @staticmethod
    def _distinct_regimes(runs: list[dict]) -> list[str]:
        """Ordered distinct list of regime types in the run list."""

        seen: list[str] = []
        for run in runs:
            if run["regime_type"] not in seen:
                seen.append(run["regime_type"])
        return seen

    # ----------------------------------------------------------
    # INTERNAL — ADVISORY LOCK
    # ----------------------------------------------------------

    def _acquire_lock(self) -> bool:
        """
        Try to acquire the advisory lock. Non-blocking.

        The lock is session-scoped in Postgres: it releases
        automatically when the connection/session ends, so a
        crashed process cannot leave a stuck lock.
        """

        result = self.db.execute(
            text("SELECT pg_try_advisory_lock(:key)"),
            {"key": _ADVISORY_LOCK_KEY},
        ).scalar()

        return bool(result)

    def _release_lock(self) -> None:
        try:
            self.db.execute(
                text("SELECT pg_advisory_unlock(:key)"),
                {"key": _ADVISORY_LOCK_KEY},
            )
        except Exception:
            # Nothing useful to do here — the session will release
            # the lock on close regardless.
            logger.exception(
                "Regime backfill: failed to release advisory lock"
            )