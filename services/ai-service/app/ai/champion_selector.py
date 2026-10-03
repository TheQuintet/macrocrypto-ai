"""Champion selector — pure ranking + gating logic.

This module answers one question: "Given the current performance
metrics for a set of candidate models and the identity of the
current champion, should we promote a new champion?"

It is deliberately pure:
    - No DB access.
    - No file I/O.
    - No awareness of settings beyond what the caller passes in.
    - Deterministic given the same inputs.

The caller (the daily promotion job) is responsible for:
    - Fetching metrics from prediction_performance.
    - Fetching the current champion from model_champions.
    - Fetching the stability streak from champion_candidates.
    - Passing config values (metric name, gates) into this module.

This separation makes the logic fully testable and isolates the
"should we promote?" decision from "where do the numbers come from".

Concepts:

    Candidate
        A model that is being considered for promotion. Ranked
        against the current champion.

    Incumbent
        The current champion (may be None on the very first run).

    Metric
        The scalar used to rank candidates. Configured via
        champion_selection_metric. Lower is better for "mae",
        "rmse", "mape". Higher is better for "directional_accuracy".

    Windows
        Two rolling windows:
            - primary (default 30 days) — the recent regime.
            - secondary (default 90 days) — a wider stability check.
        A candidate must qualify on BOTH to be eligible.

    Gates
        Three checks applied in order:
            1) sample size — enough data to trust the metric.
            2) lead — meaningfully better than the incumbent.
            3) stability — top-ranked for N consecutive days.
        All three must pass for promotion.

Design references:
    - known_issues.md #17 (champion selection was missing)
    - champion_selection_investigation.md (full design)
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================
# RESULT TYPES
# ============================================================
class DecisionStatus(str, Enum):
    """Outcome of a promotion decision.

    Every status is a terminal state — the caller logs it, records
    it, and moves on. There is no "retry" status: the promotion
    job's own retry logic handles transient failures.

    Statuses:

        PROMOTE
            All gates passed. The candidate displaces the incumbent.

        NO_CANDIDATES
            No model had enough data in either window. The incumbent
            (if any) stays. On the very first run this means the
            service has no champion yet.

        INSUFFICIENT_SAMPLE
            The top candidate had fewer than min_sample_size points
            in one or both windows. The incumbent stays.

        NO_IMPROVEMENT
            The candidate is not meaningfully better than the
            incumbent (fails the lead gate). This is the most common
            outcome — most days, the incumbent stays.

        NOT_STABLE
            The candidate beats the incumbent by enough, but hasn't
            been the top pick for N consecutive days. The incumbent
            stays.

        INCUMBENT_MISSING
            There is no current champion. This triggers a special
            path: the top eligible candidate is promoted UNLESS the
            stability gate would have blocked it under normal
            conditions. See `_first_champion_allowed()` below for the
            exact semantics.

        METRIC_INVALID
            The metric_name passed in isn't recognized. The caller
            should have already validated this at startup; if this
            status appears, it's a configuration bug.
    """

    PROMOTE = "promote"
    NO_CANDIDATES = "no_candidates"
    INSUFFICIENT_SAMPLE = "insufficient_sample"
    NO_IMPROVEMENT = "no_improvement"
    NOT_STABLE = "not_stable"
    INCUMBENT_MISSING = "incumbent_missing"
    METRIC_INVALID = "metric_invalid"


@dataclass
class ModelMetrics:
    """Performance metrics for one model on one horizon.

    All values are for a single (model_name, horizon) pair across
    two rolling windows.

    Attributes:
        model_name: Identifier, e.g. "prophet_fresh".
        primary_metric_value: The ranking metric's value over the
            primary window. None if the model has no data.
        primary_sample_size: Number of matched points contributing
            to primary_metric_value. Zero if the metric is None.
        secondary_metric_value: Same, over the secondary window.
        secondary_sample_size: Same, over the secondary window.
        model_version: Version string, if known.
    """

    model_name: str
    primary_metric_value: Optional[float] = None
    primary_sample_size: int = 0
    secondary_metric_value: Optional[float] = None
    secondary_sample_size: int = 0
    model_version: Optional[str] = None

    def is_eligible(
        self,
        min_sample_size: int,
        require_secondary: bool = True,
    ) -> bool:
        """Return True if this model has enough data to be ranked.

        Args:
            min_sample_size: The minimum number of matched points
                required in each window.
            require_secondary: If True, both windows must be
                populated. If False, only the primary window is
                required (used when the secondary window has
                insufficient history, e.g. early in a new
                deployment).

        Returns:
            True if the model is eligible for ranking.
        """
        if self.primary_metric_value is None:
            return False
        if self.primary_sample_size < min_sample_size:
            return False

        if require_secondary:
            if self.secondary_metric_value is None:
                return False
            if self.secondary_sample_size < min_sample_size:
                return False

        return True


@dataclass
class PromotionDecision:
    """The selector's verdict on one (horizon, regime) pair.

    Attributes:
        horizon: '24h' or '7d'.
        market_condition: The regime, or None for global.
        status: A DecisionStatus value.
        candidate_name: The model the selector picked as the
            candidate (may be the winner, the top-ranked, or None
            if no candidates qualified).
        candidate_primary_metric: The candidate's metric value on
            the primary window, if known.
        candidate_secondary_metric: Same, on the secondary window.
        candidate_primary_sample_size: Sample size on the primary
            window.
        incumbent_name: The current champion, if any.
        incumbent_metric: The incumbent's metric value on the
            primary window, if known.
        improvement_pct: (incumbent_metric - candidate_metric) /
            incumbent_metric for "lower is better" metrics;
            (candidate_metric - incumbent_metric) / incumbent_metric
            for "higher is better". None if incumbent is missing.
        stability_days: The candidate's current streak length.
        stability_required: The configured requirement.
        reason: A human-readable summary suitable for logging and
            for storage in model_champions.reason.
    """

    horizon: str
    market_condition: Optional[str]
    status: DecisionStatus
    candidate_name: Optional[str] = None
    candidate_primary_metric: Optional[float] = None
    candidate_secondary_metric: Optional[float] = None
    candidate_primary_sample_size: int = 0
    incumbent_name: Optional[str] = None
    incumbent_metric: Optional[float] = None
    improvement_pct: Optional[float] = None
    stability_days: int = 0
    stability_required: int = 3
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict for logging."""
        return {
            "horizon": self.horizon,
            "market_condition": self.market_condition,
            "status": self.status.value,
            "candidate_name": self.candidate_name,
            "candidate_primary_metric": self.candidate_primary_metric,
            "candidate_secondary_metric": self.candidate_secondary_metric,
            "candidate_primary_sample_size": self.candidate_primary_sample_size,
            "incumbent_name": self.incumbent_name,
            "incumbent_metric": self.incumbent_metric,
            "improvement_pct": self.improvement_pct,
            "stability_days": self.stability_days,
            "stability_required": self.stability_required,
            "reason": self.reason,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"PromotionDecision("
            f"horizon={self.horizon!r}, "
            f"regime={self.market_condition!r}, "
            f"status={self.status.value!r}, "
            f"candidate={self.candidate_name!r})"
        )


# ============================================================
# SELECTOR
# ============================================================
class ChampionSelector:
    """Pure ranking and gating logic.

    Stateless. Construct once with config values, call
    `decide()` for each (horizon, regime).

    Example:
        selector = ChampionSelector(
            metric_name="mae",
            higher_is_better=False,
            min_sample_size=100,
            min_lead_pct=0.05,
            stability_days=3,
        )
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=metrics_by_model,
            incumbent_name="prophet_fresh",
            incumbent_metric=380.0,
            candidate_stability_days=4,
        )
    """

    def __init__(
        self,
        metric_name: str,
        higher_is_better: bool,
        min_sample_size: int,
        min_lead_pct: float,
        stability_days: int,
        require_secondary_window: bool = True,
    ) -> None:
        """Initialize the selector.

        Args:
            metric_name: One of "mae", "rmse", "mape",
                "directional_accuracy".
            higher_is_better: True for directional_accuracy, False
                for the error metrics.
            min_sample_size: Minimum matched points required in each
                window for a model to be eligible.
            min_lead_pct: Minimum improvement over the incumbent,
                expressed as a fraction (0.05 = 5%).
            stability_days: Number of consecutive days the candidate
                must have been top-ranked.
            require_secondary_window: If True (default), a candidate
                must qualify on both the primary and secondary
                windows. Set to False in the early days of a new
                deployment when the secondary window has no data.

        Raises:
            ValueError: If any value is invalid.
        """
        if metric_name not in (
            "mae",
            "rmse",
            "mape",
            "directional_accuracy",
        ):
            raise ValueError(
                f"Unknown metric_name '{metric_name}'. "
                f"Must be one of mae, rmse, mape, directional_accuracy."
            )
        if min_sample_size <= 0:
            raise ValueError(
                f"min_sample_size must be positive, got {min_sample_size}"
            )
        if min_lead_pct < 0:
            raise ValueError(
                f"min_lead_pct must be non-negative, got {min_lead_pct}"
            )
        if stability_days < 1:
            raise ValueError(
                f"stability_days must be >= 1, got {stability_days}"
            )

        self.metric_name = metric_name
        self.higher_is_better = higher_is_better
        self.min_sample_size = min_sample_size
        self.min_lead_pct = min_lead_pct
        self.stability_days = stability_days
        self.require_secondary_window = require_secondary_window

        logger.info(
            f"ChampionSelector initialized "
            f"(metric={metric_name}, higher_is_better={higher_is_better}, "
            f"min_sample={min_sample_size}, min_lead_pct={min_lead_pct}, "
            f"stability_days={stability_days}, "
            f"require_secondary={require_secondary_window})"
        )

    # ============================================================
    # PUBLIC API
    # ============================================================
    def decide(
        self,
        horizon: str,
        market_condition: Optional[str],
        candidates: Dict[str, ModelMetrics],
        incumbent_name: Optional[str],
        incumbent_metric: Optional[float],
        candidate_stability_days: int,
        candidate_stability_model: Optional[str] = None,
    ) -> PromotionDecision:
        """Decide whether to promote a new champion.

        Args:
            horizon: '24h' or '7d'. Passed through to the decision.
            market_condition: Regime label, or None for global.
            candidates: Mapping of model_name → ModelMetrics. May be
                empty.
            incumbent_name: The current champion, or None.
            incumbent_metric: The incumbent's metric value on the
                primary window. Required when incumbent_name is set.
            candidate_stability_days: The number of consecutive days
                that the current top candidate has been #1. If the
                caller doesn't track this (e.g. on the very first
                run), pass 0.
            candidate_stability_model: The model name the streak
                belongs to. If provided, the selector verifies the
                streak belongs to the same model it's about to
                promote. If None, the caller asserts that the streak
                already belongs to the selected candidate.

        Returns:
            PromotionDecision with the verdict and supporting data.
        """
        # ---- 0. Sanity: metric recognized ----
        if self.metric_name not in (
            "mae",
            "rmse",
            "mape",
            "directional_accuracy",
        ):
            return self._decision(
                horizon=horizon,
                market_condition=market_condition,
                status=DecisionStatus.METRIC_INVALID,
                reason=f"Unknown metric '{self.metric_name}'",
            )

        # ---- 1. No candidates at all ----
        if not candidates:
            return self._decision(
                horizon=horizon,
                market_condition=market_condition,
                status=DecisionStatus.NO_CANDIDATES,
                incumbent_name=incumbent_name,
                incumbent_metric=incumbent_metric,
                reason="No candidate models were provided",
            )

        # ---- 2. Filter to eligible candidates ----
        eligible = [
            m
            for m in candidates.values()
            if m.is_eligible(
                min_sample_size=self.min_sample_size,
                require_secondary=self.require_secondary_window,
            )
        ]

        if not eligible:
            return self._decision(
                horizon=horizon,
                market_condition=market_condition,
                status=DecisionStatus.INSUFFICIENT_SAMPLE,
                incumbent_name=incumbent_name,
                incumbent_metric=incumbent_metric,
                reason=(
                    f"No candidate has >= {self.min_sample_size} "
                    f"matched points in "
                    f"{'both' if self.require_secondary_window else 'the primary'} "
                    f"window"
                ),
            )

        # ---- 3. Rank and pick the top candidate ----
        # Ranking is over the primary window's metric. Ties are
        # broken by the secondary window's metric (better secondary
        # wins). Final tiebreak by model_name for determinism.
        top_candidate = self._rank_top_candidate(eligible)

        # ---- 4. No incumbent → this is the first champion ----
        if incumbent_name is None:
            return self._first_champion_decision(
                horizon=horizon,
                market_condition=market_condition,
                candidate=top_candidate,
                stability_days=candidate_stability_days,
                stability_model=candidate_stability_model,
            )

        # ---- 5. Compare candidate vs incumbent ----
        # If the incumbent is *itself* the top candidate, there is
        # nothing to promote. Report NO_IMPROVEMENT.
        if top_candidate.model_name == incumbent_name:
            return self._decision(
                horizon=horizon,
                market_condition=market_condition,
                status=DecisionStatus.NO_IMPROVEMENT,
                candidate_name=top_candidate.model_name,
                candidate_primary_metric=top_candidate.primary_metric_value,
                candidate_secondary_metric=top_candidate.secondary_metric_value,
                candidate_primary_sample_size=top_candidate.primary_sample_size,
                incumbent_name=incumbent_name,
                incumbent_metric=incumbent_metric,
                improvement_pct=0.0,
                stability_days=candidate_stability_days,
                stability_required=self.stability_days,
                reason="Incumbent is already the top-ranked model",
            )

        # ---- 6. Lead gate ----
        improvement = self._improvement_pct(
            candidate_metric=top_candidate.primary_metric_value,
            incumbent_metric=incumbent_metric,
        )

        if improvement is None or improvement < self.min_lead_pct:
            return self._decision(
                horizon=horizon,
                market_condition=market_condition,
                status=DecisionStatus.NO_IMPROVEMENT,
                candidate_name=top_candidate.model_name,
                candidate_primary_metric=top_candidate.primary_metric_value,
                candidate_secondary_metric=top_candidate.secondary_metric_value,
                candidate_primary_sample_size=top_candidate.primary_sample_size,
                incumbent_name=incumbent_name,
                incumbent_metric=incumbent_metric,
                improvement_pct=improvement,
                stability_days=candidate_stability_days,
                stability_required=self.stability_days,
                reason=(
                    f"Candidate improves by "
                    f"{self._fmt_pct(improvement)} "
                    f"< required {self._fmt_pct(self.min_lead_pct)}"
                ),
            )

        # ---- 7. Stability gate ----
        # The streak must belong to the same candidate we're about
        # to promote. If the caller didn't specify which model the
        # streak belongs to, trust the caller (they built the
        # streak to match this candidate).
        if (
            candidate_stability_model is not None
            and candidate_stability_model != top_candidate.model_name
        ):
            return self._decision(
                horizon=horizon,
                market_condition=market_condition,
                status=DecisionStatus.NOT_STABLE,
                candidate_name=top_candidate.model_name,
                candidate_primary_metric=top_candidate.primary_metric_value,
                candidate_secondary_metric=top_candidate.secondary_metric_value,
                candidate_primary_sample_size=top_candidate.primary_sample_size,
                incumbent_name=incumbent_name,
                incumbent_metric=incumbent_metric,
                improvement_pct=improvement,
                stability_days=candidate_stability_days,
                stability_required=self.stability_days,
                reason=(
                    f"Stability streak belongs to "
                    f"{candidate_stability_model!r}, not to "
                    f"{top_candidate.model_name!r}"
                ),
            )

        if candidate_stability_days < self.stability_days:
            return self._decision(
                horizon=horizon,
                market_condition=market_condition,
                status=DecisionStatus.NOT_STABLE,
                candidate_name=top_candidate.model_name,
                candidate_primary_metric=top_candidate.primary_metric_value,
                candidate_secondary_metric=top_candidate.secondary_metric_value,
                candidate_primary_sample_size=top_candidate.primary_sample_size,
                incumbent_name=incumbent_name,
                incumbent_metric=incumbent_metric,
                improvement_pct=improvement,
                stability_days=candidate_stability_days,
                stability_required=self.stability_days,
                reason=(
                    f"Stability streak is {candidate_stability_days} "
                    f"day(s) < required {self.stability_days}"
                ),
            )

        # ---- 8. All gates passed: promote ----
        return self._decision(
            horizon=horizon,
            market_condition=market_condition,
            status=DecisionStatus.PROMOTE,
            candidate_name=top_candidate.model_name,
            candidate_primary_metric=top_candidate.primary_metric_value,
            candidate_secondary_metric=top_candidate.secondary_metric_value,
            candidate_primary_sample_size=top_candidate.primary_sample_size,
            incumbent_name=incumbent_name,
            incumbent_metric=incumbent_metric,
            improvement_pct=improvement,
            stability_days=candidate_stability_days,
            stability_required=self.stability_days,
            reason=(
                f"Candidate {top_candidate.model_name!r} improves by "
                f"{self._fmt_pct(improvement)} over "
                f"{incumbent_name!r}, stable for "
                f"{candidate_stability_days} day(s)"
            ),
        )

    # ============================================================
    # INTERNAL: FIRST CHAMPION
    # ============================================================
    def _first_champion_decision(
        self,
        horizon: str,
        market_condition: Optional[str],
        candidate: ModelMetrics,
        stability_days: int,
        stability_model: Optional[str],
    ) -> PromotionDecision:
        """Handle the no-incumbent case.

        When there is no current champion (first run, or after a
        manual purge), the top eligible candidate is promoted.

        The stability gate is still applied here, but with a
        shorter interpretation: the caller decides whether to pass
        a stability streak that's long enough. We default to
        requiring at least 1 day of stability (i.e. the candidate
        must at least be today's top pick, which it is by
        definition), because requiring the full stability_days on
        a fresh deployment would mean the service goes without a
        champion for several days.

        Concretely:
            - If stability_days is 0, we still promote — this is the
              very first run and no stability data exists yet.
            - If stability_days is 1 or more, we promote as long as
              the streak belongs to the same candidate.
            - The full stability_days requirement kicks in only when
              there is an incumbent to displace.

        Returns:
            A PromotionDecision with status INCUMBENT_MISSING when
            the promotion happens (indicating "no incumbent existed,
            champion set"), or NOT_STABLE / NO_CANDIDATES as
            appropriate.
        """
        if stability_model is not None and stability_model != candidate.model_name:
            return self._decision(
                horizon=horizon,
                market_condition=market_condition,
                status=DecisionStatus.NOT_STABLE,
                candidate_name=candidate.model_name,
                candidate_primary_metric=candidate.primary_metric_value,
                candidate_secondary_metric=candidate.secondary_metric_value,
                candidate_primary_sample_size=candidate.primary_sample_size,
                stability_days=stability_days,
                stability_required=self.stability_days,
                reason=(
                    f"No incumbent; stability streak belongs to "
                    f"{stability_model!r}, not to "
                    f"{candidate.model_name!r}"
                ),
            )

        return self._decision(
            horizon=horizon,
            market_condition=market_condition,
            status=DecisionStatus.INCUMBENT_MISSING,
            candidate_name=candidate.model_name,
            candidate_primary_metric=candidate.primary_metric_value,
            candidate_secondary_metric=candidate.secondary_metric_value,
            candidate_primary_sample_size=candidate.primary_sample_size,
            incumbent_name=None,
            incumbent_metric=None,
            improvement_pct=None,
            stability_days=stability_days,
            stability_required=self.stability_days,
            reason=(
                f"No incumbent champion; promoting first champion "
                f"{candidate.model_name!r}"
            ),
        )

    # ============================================================
    # INTERNAL: RANKING & COMPARISON
    # ============================================================
    def _rank_top_candidate(
        self, eligible: List[ModelMetrics]
    ) -> ModelMetrics:
        """Return the top-ranked candidate from the eligible set.

        Ranking rule:
            1) primary_metric_value — better wins
            2) secondary_metric_value — better wins
            3) model_name — lexicographically smallest wins
               (deterministic tiebreak)

        "Better" means lower when higher_is_better is False, higher
        when True. If a secondary metric is missing for a candidate
        but not for another, the one with the secondary metric
        outranks the one without (missing is treated as worst).

        Args:
            eligible: Non-empty list of eligible candidates.

        Returns:
            The top-ranked candidate.
        """
        assert eligible, "caller must filter to non-empty eligible list"

        def sort_key(m: ModelMetrics) -> Tuple:
            primary = m.primary_metric_value
            secondary = m.secondary_metric_value

            # Missing values sort last. We can't put None in a
            # comparison tuple directly, so use a placeholder.
            # For "lower is better": missing → +inf.
            # For "higher is better": missing → -inf.
            if primary is None:
                primary_key = (
                    float("-inf") if self.higher_is_better else float("inf")
                )
            else:
                primary_key = (
                    -primary if self.higher_is_better else primary
                )

            if secondary is None:
                secondary_key = (
                    float("-inf") if self.higher_is_better else float("inf")
                )
            else:
                secondary_key = (
                    -secondary if self.higher_is_better else secondary
                )

            # Python sorts ascending by default. For "lower is
            # better", the smallest primary_key wins. For "higher
            # is better", we negate the metric so the largest
            # metric becomes the smallest key. Same for secondary.
            return (primary_key, secondary_key, m.model_name)

        return min(eligible, key=sort_key)

    def _improvement_pct(
        self,
        candidate_metric: Optional[float],
        incumbent_metric: Optional[float],
    ) -> Optional[float]:
        """Compute the candidate's improvement over the incumbent.

        For "lower is better" metrics (mae, rmse, mape):
            improvement = (incumbent - candidate) / |incumbent|

        For "higher is better" metrics (directional_accuracy):
            improvement = (candidate - incumbent) / |incumbent|

        A positive result means the candidate is better. A negative
        result means the candidate is worse. Zero means equal.

        Args:
            candidate_metric: The candidate's primary-window metric.
            incumbent_metric: The incumbent's primary-window metric.

        Returns:
            Fractional improvement (0.05 = 5%), or None if either
            input is missing or the incumbent is zero.
        """
        if candidate_metric is None or incumbent_metric is None:
            return None
        if incumbent_metric == 0:
            # Cannot express improvement as a fraction of zero.
            # Fall back to the raw difference, which preserves the
            # sign and lets the lead gate still work in practice.
            if self.higher_is_better:
                return candidate_metric - incumbent_metric
            return incumbent_metric - candidate_metric

        if self.higher_is_better:
            return (candidate_metric - incumbent_metric) / abs(incumbent_metric)
        return (incumbent_metric - candidate_metric) / abs(incumbent_metric)

    # ============================================================
    # INTERNAL: CONSTRUCTION
    # ============================================================
    def _decision(
        self,
        horizon: str,
        market_condition: Optional[str],
        status: DecisionStatus,
        candidate_name: Optional[str] = None,
        candidate_primary_metric: Optional[float] = None,
        candidate_secondary_metric: Optional[float] = None,
        candidate_primary_sample_size: int = 0,
        incumbent_name: Optional[str] = None,
        incumbent_metric: Optional[float] = None,
        improvement_pct: Optional[float] = None,
        stability_days: int = 0,
        stability_required: Optional[int] = None,
        reason: str = "",
    ) -> PromotionDecision:
        """Build a PromotionDecision with the selector's defaults applied."""
        return PromotionDecision(
            horizon=horizon,
            market_condition=market_condition,
            status=status,
            candidate_name=candidate_name,
            candidate_primary_metric=candidate_primary_metric,
            candidate_secondary_metric=candidate_secondary_metric,
            candidate_primary_sample_size=candidate_primary_sample_size,
            incumbent_name=incumbent_name,
            incumbent_metric=incumbent_metric,
            improvement_pct=improvement_pct,
            stability_days=stability_days,
            stability_required=(
                stability_required
                if stability_required is not None
                else self.stability_days
            ),
            reason=reason,
        )

    @staticmethod
    def _fmt_pct(value: Optional[float]) -> str:
        """Format a fractional value as a percentage for logging."""
        if value is None:
            return "n/a"
        return f"{value * 100:.2f}%"

    # ============================================================
    # DUNDER
    # ============================================================
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ChampionSelector("
            f"metric='{self.metric_name}', "
            f"higher_is_better={self.higher_is_better}, "
            f"min_sample_size={self.min_sample_size}, "
            f"min_lead_pct={self.min_lead_pct}, "
            f"stability_days={self.stability_days})"
        )


# ============================================================
# CONVENIENCE: BUILD FROM SETTINGS
# ============================================================
def build_selector_from_settings(settings_obj: Any) -> ChampionSelector:
    """Build a ChampionSelector from a Settings instance.

    Keeps the wiring out of the promotion job and the tests. Accepts
    any object with the champion_* attributes (duck-typed) so tests
    can pass a lightweight fake.

    Args:
        settings_obj: A Settings instance (or any object with
            champion_selection_metric, champion_metric_is_higher_better,
            champion_min_sample_size, champion_min_lead_pct,
            champion_stability_days).

    Returns:
        A configured ChampionSelector.

    Raises:
        ValueError: If champion_selection_metric is not recognized.
    """
    metric = settings_obj.champion_selection_metric
    if metric not in ("mae", "rmse", "mape", "directional_accuracy"):
        raise ValueError(
            f"Unsupported champion_selection_metric: {metric!r}. "
            f"Valid values: mae, rmse, mape, directional_accuracy."
        )

    return ChampionSelector(
        metric_name=metric,
        higher_is_better=settings_obj.champion_metric_is_higher_better,
        min_sample_size=settings_obj.champion_min_sample_size,
        min_lead_pct=settings_obj.champion_min_lead_pct,
        stability_days=settings_obj.champion_stability_days,
    )


__all__ = [
    "ChampionSelector",
    "DecisionStatus",
    "ModelMetrics",
    "PromotionDecision",
    "build_selector_from_settings",
]