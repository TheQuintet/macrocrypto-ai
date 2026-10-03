"""Unit tests for app.ai.champion_selector.

Covers the pure ranking + gating logic:

    - DecisionStatus values — each reachable through a scenario
    - The three gates in isolation
    - Ranking rules (lower-is-better vs higher-is-better, secondary
      tiebreak, lexicographic final tiebreak)
    - Improvement math
    - Boundary cases (sample size == threshold, improvement ==
      min_lead_pct, streak == stability_days)
    - The INCUMBENT_MISSING / first-champion path
    - Construction-time validation
    - build_selector_from_settings wiring

No DB, no I/O. Every test is a plain synchronous function.
"""

from __future__ import annotations

from typing import Dict

import pytest

from app.ai.champion_selector import (
    ChampionSelector,
    DecisionStatus,
    ModelMetrics,
    PromotionDecision,
    build_selector_from_settings,
)


# ============================================================
# FIXTURES AND HELPERS
# ============================================================
def make_selector(
    metric_name: str = "mae",
    higher_is_better: bool = False,
    min_sample_size: int = 100,
    min_lead_pct: float = 0.05,
    stability_days: int = 3,
    require_secondary_window: bool = True,
) -> ChampionSelector:
    """Construct a ChampionSelector with test-friendly defaults."""
    return ChampionSelector(
        metric_name=metric_name,
        higher_is_better=higher_is_better,
        min_sample_size=min_sample_size,
        min_lead_pct=min_lead_pct,
        stability_days=stability_days,
        require_secondary_window=require_secondary_window,
    )


def make_metrics(
    name: str,
    primary: float = 100.0,
    primary_n: int = 200,
    secondary: float = 110.0,
    secondary_n: int = 500,
) -> ModelMetrics:
    """Construct a ModelMetrics with fully-populated values."""
    return ModelMetrics(
        model_name=name,
        primary_metric_value=primary,
        primary_sample_size=primary_n,
        secondary_metric_value=secondary,
        secondary_sample_size=secondary_n,
    )


def candidates_2(
    a_primary: float = 90.0,
    b_primary: float = 100.0,
) -> Dict[str, ModelMetrics]:
    """Two candidates, A better than B on primary by 10 units."""
    return {
        "model_a": make_metrics("model_a", primary=a_primary),
        "model_b": make_metrics("model_b", primary=b_primary),
    }


# ============================================================
# CONSTRUCTION VALIDATION
# ============================================================
class TestConstruction:
    """Constructor accepts valid config and rejects invalid."""

    def test_accepts_valid_config(self) -> None:
        selector = make_selector()
        assert selector.metric_name == "mae"
        assert selector.higher_is_better is False
        assert selector.min_sample_size == 100
        assert selector.min_lead_pct == 0.05
        assert selector.stability_days == 3

    @pytest.mark.parametrize(
        "metric",
        ["mae", "rmse", "mape", "directional_accuracy"],
    )
    def test_accepts_all_valid_metrics(self, metric: str) -> None:
        selector = ChampionSelector(
            metric_name=metric,
            higher_is_better=(metric == "directional_accuracy"),
            min_sample_size=100,
            min_lead_pct=0.05,
            stability_days=3,
        )
        assert selector.metric_name == metric

    def test_rejects_unknown_metric(self) -> None:
        with pytest.raises(ValueError, match="Unknown metric_name"):
            ChampionSelector(
                metric_name="not_a_metric",
                higher_is_better=False,
                min_sample_size=100,
                min_lead_pct=0.05,
                stability_days=3,
            )

    def test_rejects_non_positive_min_sample_size(self) -> None:
        with pytest.raises(ValueError, match="min_sample_size"):
            ChampionSelector(
                metric_name="mae",
                higher_is_better=False,
                min_sample_size=0,
                min_lead_pct=0.05,
                stability_days=3,
            )

    def test_rejects_negative_min_lead_pct(self) -> None:
        with pytest.raises(ValueError, match="min_lead_pct"):
            ChampionSelector(
                metric_name="mae",
                higher_is_better=False,
                min_sample_size=100,
                min_lead_pct=-0.01,
                stability_days=3,
            )

    def test_rejects_zero_stability_days(self) -> None:
        with pytest.raises(ValueError, match="stability_days"):
            ChampionSelector(
                metric_name="mae",
                higher_is_better=False,
                min_sample_size=100,
                min_lead_pct=0.05,
                stability_days=0,
            )


# ============================================================
# METRIC_INVALID
# ============================================================
class TestMetricInvalid:
    """METRIC_INVALID is defensive — construction rejects bad metrics."""

    def test_metric_invalid_returned_when_metric_mutated_post_construction(
        self,
    ) -> None:
        # Construction validates the metric, but .decide() re-checks
        # it defensively. Force the bad state and confirm the status.
        selector = make_selector()
        selector.metric_name = "not_a_metric"

        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates={},
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=0,
        )

        assert decision.status == DecisionStatus.METRIC_INVALID
        assert "not_a_metric" in decision.reason


# ============================================================
# NO_CANDIDATES
# ============================================================
class TestNoCandidates:
    """NO_CANDIDATES when no models are provided."""

    def test_empty_candidates_dict(self) -> None:
        selector = make_selector()
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates={},
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=0,
        )
        assert decision.status == DecisionStatus.NO_CANDIDATES
        assert decision.candidate_name is None
        assert decision.horizon == "24h"


# ============================================================
# INSUFFICIENT_SAMPLE
# ============================================================
class TestInsufficientSample:
    """INSUFFICIENT_SAMPLE when no candidate meets the sample gate."""

    def test_primary_sample_below_threshold(self) -> None:
        selector = make_selector(min_sample_size=100)
        candidates = {
            "model_a": make_metrics(
                "model_a", primary=90.0, primary_n=50
            ),
        }
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates,
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=0,
        )
        assert decision.status == DecisionStatus.INSUFFICIENT_SAMPLE

    def test_secondary_sample_below_threshold(self) -> None:
        selector = make_selector(min_sample_size=100)
        candidates = {
            "model_a": make_metrics(
                "model_a",
                primary_n=200,
                secondary_n=50,  # below
            ),
        }
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates,
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=0,
        )
        assert decision.status == DecisionStatus.INSUFFICIENT_SAMPLE

    def test_secondary_ignored_when_require_secondary_false(self) -> None:
        selector = make_selector(
            min_sample_size=100,
            require_secondary_window=False,
        )
        candidates = {
            "model_a": make_metrics(
                "model_a",
                primary=90.0,
                primary_n=200,
                secondary=None,
                secondary_n=0,
            ),
        }
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates,
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=0,
        )
        # Eligible; no incumbent → first champion
        assert decision.status == DecisionStatus.INCUMBENT_MISSING

    def test_metric_none_makes_ineligible(self) -> None:
        selector = make_selector(min_sample_size=100)
        candidates = {
            "model_a": ModelMetrics(
                model_name="model_a",
                primary_metric_value=None,
                primary_sample_size=200,
                secondary_metric_value=100.0,
                secondary_sample_size=200,
            ),
        }
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates,
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=0,
        )
        assert decision.status == DecisionStatus.INSUFFICIENT_SAMPLE

    def test_sample_size_exactly_at_threshold_is_eligible(self) -> None:
        selector = make_selector(min_sample_size=100)
        candidates = {
            "model_a": make_metrics(
                "model_a",
                primary=90.0,
                primary_n=100,  # exactly at threshold
                secondary_n=100,
            ),
        }
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates,
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=0,
        )
        assert decision.status == DecisionStatus.INCUMBENT_MISSING


# ============================================================
# INCUMBENT_MISSING (first champion)
# ============================================================
class TestIncumbentMissing:
    """First-ever run: promote the top candidate."""

    def test_promotes_top_candidate_with_no_streak(self) -> None:
        selector = make_selector()
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates_2(a_primary=90.0, b_primary=100.0),
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=0,
        )
        assert decision.status == DecisionStatus.INCUMBENT_MISSING
        assert decision.candidate_name == "model_a"
        assert decision.candidate_primary_metric == 90.0
        assert decision.incumbent_name is None
        assert decision.improvement_pct is None

    def test_promotes_with_partial_streak(self) -> None:
        # First-champion path doesn't enforce the full stability gate.
        selector = make_selector(stability_days=3)
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates_2(),
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=1,
        )
        assert decision.status == DecisionStatus.INCUMBENT_MISSING

    def test_not_stable_when_streak_belongs_to_other_model(self) -> None:
        selector = make_selector()
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates_2(),
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=5,
            candidate_stability_model="model_b",  # but model_a is top
        )
        assert decision.status == DecisionStatus.NOT_STABLE
        assert "model_b" in decision.reason


# ============================================================
# NO_IMPROVEMENT
# ============================================================
class TestNoImprovement:
    """Incumbent stays when candidate doesn't beat it enough."""

    def test_incumbent_is_top_candidate(self) -> None:
        # Incumbent "model_a" is also the top-ranked candidate.
        selector = make_selector()
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates_2(a_primary=90.0, b_primary=100.0),
            incumbent_name="model_a",
            incumbent_metric=90.0,
            candidate_stability_days=5,
        )
        assert decision.status == DecisionStatus.NO_IMPROVEMENT
        assert decision.candidate_name == "model_a"
        assert decision.improvement_pct == 0.0

    def test_candidate_below_min_lead(self) -> None:
        # Incumbent 100, candidate 98 → improvement = 2%, below 5%.
        selector = make_selector(min_lead_pct=0.05)
        candidates = {
            "model_a": make_metrics("model_a", primary=98.0),
            "model_b": make_metrics("model_b", primary=105.0),
        }
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates,
            incumbent_name="model_b",
            incumbent_metric=100.0,
            candidate_stability_days=10,
        )
        assert decision.status == DecisionStatus.NO_IMPROVEMENT
        assert decision.candidate_name == "model_a"
        assert decision.improvement_pct == pytest.approx(0.02)

    def test_candidate_worse_than_incumbent(self) -> None:
        # Candidate is worse — improvement is negative, below min_lead.
        selector = make_selector(min_lead_pct=0.05)
        candidates = {
            "model_a": make_metrics("model_a", primary=110.0),
        }
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates,
            incumbent_name="model_b",
            incumbent_metric=100.0,
            candidate_stability_days=10,
        )
        assert decision.status == DecisionStatus.NO_IMPROVEMENT
        assert decision.improvement_pct == pytest.approx(-0.10)


# ============================================================
# NOT_STABLE
# ============================================================
class TestNotStable:
    """Candidate beats incumbent but streak is too short."""

    def test_streak_below_requirement(self) -> None:
        selector = make_selector(
            min_lead_pct=0.05, stability_days=3
        )
        # model_a: 90 vs incumbent 100 → improvement 10% ≥ 5%.
        candidates = {
            "model_a": make_metrics("model_a", primary=90.0),
            "model_b": make_metrics("model_b", primary=95.0),
        }
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates,
            incumbent_name="model_b",
            incumbent_metric=100.0,
            candidate_stability_days=2,  # < 3
        )
        assert decision.status == DecisionStatus.NOT_STABLE
        assert decision.improvement_pct == pytest.approx(0.10)
        assert decision.stability_days == 2
        assert decision.stability_required == 3

    def test_streak_belongs_to_other_model(self) -> None:
        selector = make_selector(
            min_lead_pct=0.05, stability_days=3
        )
        candidates = {
            "model_a": make_metrics("model_a", primary=90.0),
            "model_b": make_metrics("model_b", primary=95.0),
        }
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates,
            incumbent_name="model_b",
            incumbent_metric=100.0,
            candidate_stability_days=5,
            candidate_stability_model="model_b",  # wrong model
        )
        assert decision.status == DecisionStatus.NOT_STABLE
        assert "model_b" in decision.reason

    def test_streak_exactly_at_requirement_promotes(self) -> None:
        selector = make_selector(
            min_lead_pct=0.05, stability_days=3
        )
        candidates = {
            "model_a": make_metrics("model_a", primary=90.0),
        }
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates,
            incumbent_name="model_b",
            incumbent_metric=100.0,
            candidate_stability_days=3,  # exactly at threshold
        )
        assert decision.status == DecisionStatus.PROMOTE


# ============================================================
# PROMOTE
# ============================================================
class TestPromote:
    """All gates pass: candidate displaces incumbent."""

    def test_promotes_with_all_gates_passing(self) -> None:
        selector = make_selector(
            min_lead_pct=0.05, stability_days=3
        )
        candidates = {
            "model_a": make_metrics(
                "model_a", primary=90.0, secondary=95.0
            ),
        }
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates,
            incumbent_name="model_b",
            incumbent_metric=100.0,
            candidate_stability_days=5,
        )
        assert decision.status == DecisionStatus.PROMOTE
        assert decision.candidate_name == "model_a"
        assert decision.candidate_primary_metric == 90.0
        assert decision.incumbent_name == "model_b"
        assert decision.incumbent_metric == 100.0
        assert decision.improvement_pct == pytest.approx(0.10)

    def test_improvement_exactly_at_min_lead_promotes(self) -> None:
        # Improvement = exactly 5%. Gate is `< min_lead_pct`, so
        # exactly-equal passes.
        selector = make_selector(
            min_lead_pct=0.05, stability_days=3
        )
        candidates = {
            "model_a": make_metrics("model_a", primary=95.0),
        }
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates,
            incumbent_name="model_b",
            incumbent_metric=100.0,
            candidate_stability_days=3,
        )
        assert decision.status == DecisionStatus.PROMOTE
        assert decision.improvement_pct == pytest.approx(0.05)

    def test_promotes_with_regime_context(self) -> None:
        selector = make_selector(
            min_lead_pct=0.05, stability_days=3
        )
        candidates = {
            "model_a": make_metrics("model_a", primary=90.0),
        }
        decision = selector.decide(
            horizon="7d",
            market_condition="bull",
            candidates=candidates,
            incumbent_name="model_b",
            incumbent_metric=100.0,
            candidate_stability_days=3,
        )
        assert decision.status == DecisionStatus.PROMOTE
        assert decision.horizon == "7d"
        assert decision.market_condition == "bull"


# ============================================================
# IMPROVEMENT MATH
# ============================================================
class TestImprovementMath:
    """_improvement_pct handles both metric directions."""

    def test_lower_is_better(self) -> None:
        selector = make_selector(higher_is_better=False)
        # candidate 90, incumbent 100 → +10%
        assert selector._improvement_pct(90.0, 100.0) == pytest.approx(0.10)
        # candidate 110, incumbent 100 → -10%
        assert selector._improvement_pct(110.0, 100.0) == pytest.approx(-0.10)
        # equal
        assert selector._improvement_pct(100.0, 100.0) == 0.0

    def test_higher_is_better(self) -> None:
        selector = make_selector(
            metric_name="directional_accuracy",
            higher_is_better=True,
        )
        # candidate 0.60, incumbent 0.50 → +20%
        assert selector._improvement_pct(0.60, 0.50) == pytest.approx(0.20)
        # candidate 0.40, incumbent 0.50 → -20%
        assert selector._improvement_pct(0.40, 0.50) == pytest.approx(-0.20)

    def test_returns_none_when_inputs_missing(self) -> None:
        selector = make_selector()
        assert selector._improvement_pct(None, 100.0) is None
        assert selector._improvement_pct(90.0, None) is None
        assert selector._improvement_pct(None, None) is None

    def test_zero_incumbent_falls_back_to_raw_difference(self) -> None:
        selector = make_selector(higher_is_better=False)
        # incumbent 0 is unusual but must not crash
        assert selector._improvement_pct(5.0, 0.0) == -5.0
        assert selector._improvement_pct(-5.0, 0.0) == 5.0

    def test_zero_incumbent_higher_is_better(self) -> None:
        selector = make_selector(
            metric_name="directional_accuracy",
            higher_is_better=True,
        )
        assert selector._improvement_pct(5.0, 0.0) == 5.0
        assert selector._improvement_pct(-5.0, 0.0) == -5.0


# ============================================================
# RANKING
# ============================================================
class TestRanking:
    """_rank_top_candidate picks the right model."""

    def test_lower_is_better_picks_minimum(self) -> None:
        selector = make_selector(higher_is_better=False)
        eligible = [
            make_metrics("model_a", primary=100.0),
            make_metrics("model_b", primary=90.0),
            make_metrics("model_c", primary=110.0),
        ]
        top = selector._rank_top_candidate(eligible)
        assert top.model_name == "model_b"

    def test_higher_is_better_picks_maximum(self) -> None:
        selector = make_selector(
            metric_name="directional_accuracy",
            higher_is_better=True,
        )
        eligible = [
            make_metrics("model_a", primary=0.55),
            make_metrics("model_b", primary=0.65),
            make_metrics("model_c", primary=0.50),
        ]
        top = selector._rank_top_candidate(eligible)
        assert top.model_name == "model_b"

    def test_secondary_breaks_primary_tie(self) -> None:
        selector = make_selector(higher_is_better=False)
        eligible = [
            make_metrics("model_a", primary=90.0, secondary=100.0),
            make_metrics("model_b", primary=90.0, secondary=95.0),
        ]
        top = selector._rank_top_candidate(eligible)
        assert top.model_name == "model_b"

    def test_lexicographic_breaks_secondary_tie(self) -> None:
        selector = make_selector(higher_is_better=False)
        eligible = [
            make_metrics("model_z", primary=90.0, secondary=95.0),
            make_metrics("model_a", primary=90.0, secondary=95.0),
        ]
        top = selector._rank_top_candidate(eligible)
        assert top.model_name == "model_a"

    def test_missing_primary_sorts_last(self) -> None:
        selector = make_selector(higher_is_better=False)
        eligible = [
            make_metrics("model_a", primary=100.0),
            ModelMetrics(
                model_name="model_b",
                primary_metric_value=None,
                primary_sample_size=0,
                secondary_metric_value=95.0,
                secondary_sample_size=500,
            ),
        ]
        top = selector._rank_top_candidate(eligible)
        assert top.model_name == "model_a"

    def test_missing_secondary_sorts_last_on_primary_tie(self) -> None:
        selector = make_selector(higher_is_better=False)
        eligible = [
            make_metrics("model_a", primary=90.0, secondary=100.0),
            ModelMetrics(
                model_name="model_b",
                primary_metric_value=90.0,
                primary_sample_size=200,
                secondary_metric_value=None,
                secondary_sample_size=0,
            ),
        ]
        top = selector._rank_top_candidate(eligible)
        assert top.model_name == "model_a"


# ============================================================
# DECISION SERIALIZATION
# ============================================================
class TestDecisionSerialization:
    """PromotionDecision.to_dict is JSON-safe."""

    def test_to_dict_includes_status_as_string(self) -> None:
        selector = make_selector()
        decision = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates=candidates_2(),
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=0,
        )
        d = decision.to_dict()
        assert d["status"] == "incumbent_missing"
        assert d["horizon"] == "24h"
        assert d["market_condition"] is None
        assert isinstance(d["candidate_name"], str)

    def test_repr_is_readable(self) -> None:
        selector = make_selector()
        decision = selector.decide(
            horizon="7d",
            market_condition="bear",
            candidates=candidates_2(),
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=0,
        )
        r = repr(decision)
        assert "7d" in r
        assert "bear" in r
        assert "incumbent_missing" in r


# ============================================================
# BUILD FROM SETTINGS
# ============================================================
class TestBuildFromSettings:
    """build_selector_from_settings maps settings fields correctly."""

    class FakeSettings:
        champion_selection_metric = "mae"
        champion_metric_is_higher_better = False
        champion_min_sample_size = 50
        champion_min_lead_pct = 0.10
        champion_stability_days = 2

    def test_builds_selector_with_matching_config(self) -> None:
        selector = build_selector_from_settings(self.FakeSettings())
        assert selector.metric_name == "mae"
        assert selector.higher_is_better is False
        assert selector.min_sample_size == 50
        assert selector.min_lead_pct == 0.10
        assert selector.stability_days == 2

    def test_rejects_unknown_metric(self) -> None:
        class BadSettings:
            champion_selection_metric = "nonsense"
            champion_metric_is_higher_better = False
            champion_min_sample_size = 50
            champion_min_lead_pct = 0.10
            champion_stability_days = 2

        with pytest.raises(ValueError, match="Unsupported"):
            build_selector_from_settings(BadSettings())

    def test_directional_accuracy_settings(self) -> None:
        class DASettings:
            champion_selection_metric = "directional_accuracy"
            champion_metric_is_higher_better = True
            champion_min_sample_size = 100
            champion_min_lead_pct = 0.05
            champion_stability_days = 3

        selector = build_selector_from_settings(DASettings())
        assert selector.metric_name == "directional_accuracy"
        assert selector.higher_is_better is True


# ============================================================
# INTEGRATION: FULL DECISION FLOW
# ============================================================
class TestFullFlow:
    """End-to-end decisions through .decide() across a few days."""

    def test_day_one_first_champion_then_day_four_promotion(self) -> None:
        """Simulate a multi-day flow.

        Day 1: no incumbent → model_a becomes champion.
        Day 4: model_b improves enough and is stable → promotes.
        """
        selector = make_selector(
            min_lead_pct=0.05, stability_days=3
        )

        # Day 1
        day1 = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates={
                "model_a": make_metrics("model_a", primary=100.0),
                "model_b": make_metrics("model_b", primary=110.0),
            },
            incumbent_name=None,
            incumbent_metric=None,
            candidate_stability_days=0,
        )
        assert day1.status == DecisionStatus.INCUMBENT_MISSING
        assert day1.candidate_name == "model_a"

        # Day 4: model_b now 90 (10% better than model_a's 100),
        # streak of 3 days.
        day4 = selector.decide(
            horizon="24h",
            market_condition=None,
            candidates={
                "model_a": make_metrics("model_a", primary=100.0),
                "model_b": make_metrics("model_b", primary=90.0),
            },
            incumbent_name="model_a",
            incumbent_metric=100.0,
            candidate_stability_days=3,
            candidate_stability_model="model_b",
        )
        assert day4.status == DecisionStatus.PROMOTE
        assert day4.candidate_name == "model_b"
        assert day4.incumbent_name == "model_a"
        assert day4.improvement_pct == pytest.approx(0.10)

    def test_incumbent_defends_for_multiple_days(self) -> None:
        """No promotion when the challenger never crosses min_lead."""
        selector = make_selector(
            min_lead_pct=0.05, stability_days=3
        )

        for candidate_value in (98.0, 97.0, 96.0):
            decision = selector.decide(
                horizon="24h",
                market_condition=None,
                candidates={
                    "challenger": make_metrics(
                        "challenger", primary=candidate_value
                    ),
                },
                incumbent_name="incumbent",
                incumbent_metric=100.0,
                candidate_stability_days=10,
            )
            # Improvement maxes out at 4% < 5% → never promotes.
            assert decision.status == DecisionStatus.NO_IMPROVEMENT