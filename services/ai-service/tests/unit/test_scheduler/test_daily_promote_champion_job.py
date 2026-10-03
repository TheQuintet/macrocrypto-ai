"""Unit tests for the champion promotion job.

Scope: daily_promote_champion_job and its private helpers only:

    - _build_champion_selector
    - _champion_key
    - _promote_one_key
    - _to_model_metrics
    - _pick_top_candidate_name
    - _metric_value_for
    - _model_version_for
    - daily_promote_champion_job (top-level orchestration)

Everything else in jobs.py has its own test coverage
(test_jobs.py). This file exercises only the champion-promotion
path.

All DB access is mocked. The tests assert orchestration:
    - Which repository methods get called, with what args
    - Which rows get upserted / recorded
    - The status that bubbles up into the results dict
    - Failure isolation between (horizon, regime) pairs
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.champion_selector import (
    ChampionSelector,
    DecisionStatus,
    ModelMetrics,
)
from app.scheduler.jobs import (
    ALL_VARIANTS,
    CHAMPION_HORIZONS,
    JOB_DAILY_PROMOTE_CHAMPION,
    _build_champion_selector,
    _champion_key,
    _metric_value_for,
    _model_version_for,
    _pick_top_candidate_name,
    _promote_one_key,
    _to_model_metrics,
    daily_promote_champion_job,
)


# ============================================================
# HELPERS
# ============================================================
def _session_scope_mock() -> MagicMock:
    """Build an async context manager mock for session_scope()."""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=MagicMock())
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _make_selector(
    metric_name: str = "mae",
    higher_is_better: bool = False,
    min_sample_size: int = 100,
    min_lead_pct: float = 0.05,
    stability_days: int = 3,
) -> ChampionSelector:
    """Build a real ChampionSelector for tests that need its API."""
    return ChampionSelector(
        metric_name=metric_name,
        higher_is_better=higher_is_better,
        min_sample_size=min_sample_size,
        min_lead_pct=min_lead_pct,
        stability_days=stability_days,
    )


def _make_metric_row(
    model_name: str,
    primary: float = 100.0,
    primary_n: int = 200,
    secondary: float = 110.0,
    secondary_n: int = 500,
) -> Dict[str, Any]:
    """Build a ranking row as fetch_metrics_for_ranking would return."""
    return {
        "model_name": model_name,
        "primary_metric_value": primary,
        "primary_sample_size": primary_n,
        "secondary_metric_value": secondary,
        "secondary_sample_size": secondary_n,
    }


def _make_champion_dict(
    model_name: str = "prophet_fresh",
    metric_value: float = 100.0,
    previous_champion: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a champion row as get_champion would return."""
    return {
        "id": 1,
        "horizon": "24h",
        "market_condition": None,
        "model_name": model_name,
        "model_version": "1.0.0",
        "promoted_at": datetime.now(timezone.utc),
        "metric_name": "mae",
        "metric_value": metric_value,
        "sample_size": 200,
        "lookback_days": 30,
        "previous_champion": previous_champion,
        "reason": "seed",
        "created_at": datetime.now(timezone.utc),
    }


class _FakeSettings:
    """Duck-typed Settings replacement for build_selector_from_settings."""

    def __init__(
        self,
        metric: str = "mae",
        higher_is_better: bool = False,
        min_sample_size: int = 100,
        min_lead_pct: float = 0.05,
        stability_days: int = 3,
        enable_regime_selection: bool = False,
        primary_days: int = 30,
        secondary_days: int = 90,
    ) -> None:
        self.champion_selection_metric = metric
        self.champion_metric_is_higher_better = higher_is_better
        self.champion_min_sample_size = min_sample_size
        self.champion_min_lead_pct = min_lead_pct
        self.champion_stability_days = stability_days
        self.champion_enable_regime_selection = enable_regime_selection
        self.champion_primary_lookback_days = primary_days
        self.champion_secondary_lookback_days = secondary_days


def _patch_settings(fake: _FakeSettings):
    """Patch app.scheduler.jobs.settings with the given fake."""
    return patch("app.scheduler.jobs.settings", fake)


# ============================================================
# _build_champion_selector
# ============================================================
class TestBuildChampionSelector:
    """Tests for _build_champion_selector()."""

    def test_builds_selector_from_valid_settings(self) -> None:
        fake = _FakeSettings(
            metric="mae",
            min_sample_size=50,
            min_lead_pct=0.10,
            stability_days=2,
        )
        selector = _build_champion_selector(fake)
        assert selector.metric_name == "mae"
        assert selector.min_sample_size == 50
        assert selector.min_lead_pct == 0.10
        assert selector.stability_days == 2

    def test_propagates_value_error_from_bad_metric(self) -> None:
        fake = _FakeSettings(metric="not_a_metric")
        with pytest.raises(ValueError):
            _build_champion_selector(fake)

    def test_directional_accuracy_settings(self) -> None:
        fake = _FakeSettings(
            metric="directional_accuracy",
            higher_is_better=True,
        )
        selector = _build_champion_selector(fake)
        assert selector.metric_name == "directional_accuracy"
        assert selector.higher_is_better is True


# ============================================================
# _champion_key
# ============================================================
class TestChampionKey:
    """Tests for _champion_key()."""

    def test_global_key(self) -> None:
        assert _champion_key("24h", None) == "24h_global"

    def test_regime_key(self) -> None:
        assert _champion_key("24h", "bull") == "24h_bull"

    def test_all_horizons_and_regimes(self) -> None:
        assert _champion_key("7d", None) == "7d_global"
        assert _champion_key("7d", "bear") == "7d_bear"
        assert _champion_key("7d", "volatile") == "7d_volatile"
        assert _champion_key("7d", "neutral") == "7d_neutral"


# ============================================================
# _to_model_metrics
# ============================================================
class TestToModelMetrics:
    """Tests for _to_model_metrics()."""

    def test_converts_rows_to_dict(self) -> None:
        rows = [
            _make_metric_row("model_a", primary=90.0),
            _make_metric_row("model_b", primary=100.0),
        ]
        out = _to_model_metrics(rows)
        assert set(out.keys()) == {"model_a", "model_b"}
        assert isinstance(out["model_a"], ModelMetrics)
        assert out["model_a"].primary_metric_value == 90.0

    def test_empty_rows_returns_empty_dict(self) -> None:
        assert _to_model_metrics([]) == {}

    def test_none_sample_size_coalesces_to_zero(self) -> None:
        rows = [
            {
                "model_name": "model_a",
                "primary_metric_value": 90.0,
                "primary_sample_size": None,
                "secondary_metric_value": 95.0,
                "secondary_sample_size": None,
            }
        ]
        out = _to_model_metrics(rows)
        assert out["model_a"].primary_sample_size == 0
        assert out["model_a"].secondary_sample_size == 0

    def test_missing_keys_default_to_none(self) -> None:
        rows = [{"model_name": "model_a"}]
        out = _to_model_metrics(rows)
        assert out["model_a"].primary_metric_value is None
        assert out["model_a"].secondary_metric_value is None


# ============================================================
# _pick_top_candidate_name
# ============================================================
class TestPickTopCandidateName:
    """Tests for _pick_top_candidate_name()."""

    def test_picks_best_lower_is_better(self) -> None:
        selector = _make_selector(higher_is_better=False)
        candidates = {
            "a": ModelMetrics("a", primary_metric_value=90.0, primary_sample_size=200,
                              secondary_metric_value=95.0, secondary_sample_size=500),
            "b": ModelMetrics("b", primary_metric_value=100.0, primary_sample_size=200,
                              secondary_metric_value=95.0, secondary_sample_size=500),
        }
        assert _pick_top_candidate_name(selector, candidates) == "a"

    def test_picks_best_higher_is_better(self) -> None:
        selector = _make_selector(
            metric_name="directional_accuracy", higher_is_better=True
        )
        candidates = {
            "a": ModelMetrics("a", primary_metric_value=0.55, primary_sample_size=200,
                              secondary_metric_value=0.60, secondary_sample_size=500),
            "b": ModelMetrics("b", primary_metric_value=0.65, primary_sample_size=200,
                              secondary_metric_value=0.60, secondary_sample_size=500),
        }
        assert _pick_top_candidate_name(selector, candidates) == "b"

    def test_returns_none_when_none_eligible(self) -> None:
        selector = _make_selector(min_sample_size=100)
        candidates = {
            "a": ModelMetrics("a", primary_metric_value=90.0, primary_sample_size=50,
                              secondary_metric_value=95.0, secondary_sample_size=50),
        }
        assert _pick_top_candidate_name(selector, candidates) is None

    def test_returns_none_on_empty_input(self) -> None:
        selector = _make_selector()
        assert _pick_top_candidate_name(selector, {}) is None

    def test_filters_out_candidates_below_sample_gate(self) -> None:
        selector = _make_selector(min_sample_size=100)
        candidates = {
            "small": ModelMetrics("small", primary_metric_value=10.0, primary_sample_size=50,
                                  secondary_metric_value=20.0, secondary_sample_size=50),
            "big": ModelMetrics("big", primary_metric_value=100.0, primary_sample_size=200,
                                secondary_metric_value=110.0, secondary_sample_size=500),
        }
        # "small" has better metric but fails sample gate → "big" wins
        assert _pick_top_candidate_name(selector, candidates) == "big"


# ============================================================
# _metric_value_for
# ============================================================
class TestMetricValueFor:
    """Tests for _metric_value_for()."""

    def test_returns_float_for_present_value(self) -> None:
        rows = [_make_metric_row("a", primary=90.5)]
        assert _metric_value_for(rows, "a", "primary_metric_value") == 90.5

    def test_returns_none_when_model_not_found(self) -> None:
        rows = [_make_metric_row("a", primary=90.0)]
        assert _metric_value_for(rows, "missing", "primary_metric_value") is None

    def test_returns_none_when_key_absent(self) -> None:
        rows = [{"model_name": "a"}]
        assert _metric_value_for(rows, "a", "primary_metric_value") is None

    def test_returns_none_when_value_is_none(self) -> None:
        rows = [{"model_name": "a", "primary_metric_value": None}]
        assert _metric_value_for(rows, "a", "primary_metric_value") is None

    def test_returns_none_on_empty_rows(self) -> None:
        assert _metric_value_for([], "a", "primary_metric_value") is None

    def test_coerces_int_to_float(self) -> None:
        rows = [{"model_name": "a", "primary_sample_size": 200}]
        result = _metric_value_for(rows, "a", "primary_sample_size")
        assert result == 200.0
        assert isinstance(result, float)


# ============================================================
# _model_version_for
# ============================================================
class TestModelVersionFor:
    """Tests for _model_version_for()."""

    def test_returns_hardcoded_1_0_0(self) -> None:
        assert _model_version_for([], "anything") == "1.0.0"

    def test_ignores_rows(self) -> None:
        rows = [_make_metric_row("a")]
        assert _model_version_for(rows, "a") == "1.0.0"


# ============================================================
# _promote_one_key
# ============================================================
class TestPromoteOneKey:
    """Tests for _promote_one_key().

    Each test patches the two repositories and the selector. The
    repository methods return canned data; the assertion is on
    which repository methods got called and what status came back.
    """

    @pytest.mark.asyncio
    async def test_first_champion_promoted_and_recorded(self) -> None:
        """No incumbent, eligible candidate → first_champion."""
        selector = _make_selector()
        metric_rows = [
            _make_metric_row("model_a", primary=90.0),
            _make_metric_row("model_b", primary=100.0),
        ]

        mock_perf_repo = MagicMock()
        mock_perf_repo.fetch_metrics_for_ranking = AsyncMock(
            return_value=metric_rows
        )
        mock_champion_repo = MagicMock()
        mock_champion_repo.get_champion = AsyncMock(return_value=None)
        mock_champion_repo.get_stability_streak = AsyncMock(return_value=0)
        mock_champion_repo.upsert_champion = AsyncMock(return_value=1)
        mock_champion_repo.record_candidate = AsyncMock(return_value=True)

        fake = _FakeSettings()

        with _patch_settings(fake), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ), patch(
            "app.scheduler.jobs.PerformanceRepository",
            return_value=mock_perf_repo,
        ), patch(
            "app.scheduler.jobs.ChampionRepository",
            return_value=mock_champion_repo,
        ):
            result = await _promote_one_key(
                selector=selector, horizon="24h", market_condition=None
            )

        assert result["status"] == "first_champion"
        assert result["candidate_name"] == "model_a"
        mock_champion_repo.upsert_champion.assert_awaited_once()
        mock_champion_repo.record_candidate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_promoted_when_all_gates_pass(self) -> None:
        """Incumbent exists but candidate beats it enough and is stable."""
        selector = _make_selector(min_lead_pct=0.05, stability_days=3)
        metric_rows = [
            _make_metric_row("model_a", primary=90.0),  # 10% better
            _make_metric_row("model_b", primary=100.0),
        ]
        incumbent = _make_champion_dict(model_name="model_b", metric_value=100.0)

        mock_perf_repo = MagicMock()
        mock_perf_repo.fetch_metrics_for_ranking = AsyncMock(
            return_value=metric_rows
        )
        mock_champion_repo = MagicMock()
        mock_champion_repo.get_champion = AsyncMock(return_value=incumbent)
        mock_champion_repo.get_stability_streak = AsyncMock(return_value=5)
        mock_champion_repo.upsert_champion = AsyncMock(return_value=1)
        mock_champion_repo.record_candidate = AsyncMock(return_value=True)

        fake = _FakeSettings()

        with _patch_settings(fake), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ), patch(
            "app.scheduler.jobs.PerformanceRepository",
            return_value=mock_perf_repo,
        ), patch(
            "app.scheduler.jobs.ChampionRepository",
            return_value=mock_champion_repo,
        ):
            result = await _promote_one_key(
                selector=selector, horizon="24h", market_condition=None
            )

        assert result["status"] == "promoted"
        assert result["candidate_name"] == "model_a"
        assert result["previous_champion"] == "model_b"
        mock_champion_repo.upsert_champion.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unchanged_when_no_improvement(self) -> None:
        """Candidate below min lead → unchanged, no upsert."""
        selector = _make_selector(min_lead_pct=0.05, stability_days=3)
        metric_rows = [
            _make_metric_row("model_a", primary=98.0),  # 2% better
        ]
        incumbent = _make_champion_dict(model_name="model_b", metric_value=100.0)

        mock_perf_repo = MagicMock()
        mock_perf_repo.fetch_metrics_for_ranking = AsyncMock(
            return_value=metric_rows
        )
        mock_champion_repo = MagicMock()
        mock_champion_repo.get_champion = AsyncMock(return_value=incumbent)
        mock_champion_repo.get_stability_streak = AsyncMock(return_value=5)
        mock_champion_repo.upsert_champion = AsyncMock()
        mock_champion_repo.record_candidate = AsyncMock(return_value=True)

        fake = _FakeSettings()

        with _patch_settings(fake), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ), patch(
            "app.scheduler.jobs.PerformanceRepository",
            return_value=mock_perf_repo,
        ), patch(
            "app.scheduler.jobs.ChampionRepository",
            return_value=mock_champion_repo,
        ):
            result = await _promote_one_key(
                selector=selector, horizon="24h", market_condition=None
            )

        assert result["status"] == "unchanged"
        mock_champion_repo.upsert_champion.assert_not_called()
        mock_champion_repo.record_candidate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unchanged_when_not_stable(self) -> None:
        """Candidate beats incumbent but streak is short."""
        selector = _make_selector(min_lead_pct=0.05, stability_days=3)
        metric_rows = [
            _make_metric_row("model_a", primary=90.0),  # 10% better
        ]
        incumbent = _make_champion_dict(model_name="model_b", metric_value=100.0)

        mock_perf_repo = MagicMock()
        mock_perf_repo.fetch_metrics_for_ranking = AsyncMock(
            return_value=metric_rows
        )
        mock_champion_repo = MagicMock()
        mock_champion_repo.get_champion = AsyncMock(return_value=incumbent)
        mock_champion_repo.get_stability_streak = AsyncMock(return_value=2)
        mock_champion_repo.upsert_champion = AsyncMock()
        mock_champion_repo.record_candidate = AsyncMock(return_value=True)

        fake = _FakeSettings()

        with _patch_settings(fake), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ), patch(
            "app.scheduler.jobs.PerformanceRepository",
            return_value=mock_perf_repo,
        ), patch(
            "app.scheduler.jobs.ChampionRepository",
            return_value=mock_champion_repo,
        ):
            result = await _promote_one_key(
                selector=selector, horizon="24h", market_condition=None
            )

        assert result["status"] == "unchanged"
        mock_champion_repo.upsert_champion.assert_not_called()

    @pytest.mark.asyncio
    async def test_skipped_when_no_candidates(self) -> None:
        """Empty metric rows → skipped, nothing written."""
        selector = _make_selector()

        mock_perf_repo = MagicMock()
        mock_perf_repo.fetch_metrics_for_ranking = AsyncMock(return_value=[])
        mock_champion_repo = MagicMock()
        mock_champion_repo.get_champion = AsyncMock(return_value=None)
        mock_champion_repo.get_stability_streak = AsyncMock()
        mock_champion_repo.upsert_champion = AsyncMock()
        mock_champion_repo.record_candidate = AsyncMock()

        fake = _FakeSettings()

        with _patch_settings(fake), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ), patch(
            "app.scheduler.jobs.PerformanceRepository",
            return_value=mock_perf_repo,
        ), patch(
            "app.scheduler.jobs.ChampionRepository",
            return_value=mock_champion_repo,
        ):
            result = await _promote_one_key(
                selector=selector, horizon="24h", market_condition=None
            )

        assert result["status"] == "skipped"
        mock_champion_repo.upsert_champion.assert_not_called()
        mock_champion_repo.record_candidate.assert_not_called()

    @pytest.mark.asyncio
    async def test_skipped_when_insufficient_sample(self) -> None:
        """All candidates fail sample-size gate → skipped."""
        selector = _make_selector(min_sample_size=100)
        metric_rows = [
            _make_metric_row("model_a", primary=90.0, primary_n=50),
        ]

        mock_perf_repo = MagicMock()
        mock_perf_repo.fetch_metrics_for_ranking = AsyncMock(
            return_value=metric_rows
        )
        mock_champion_repo = MagicMock()
        mock_champion_repo.get_champion = AsyncMock(return_value=None)
        mock_champion_repo.get_stability_streak = AsyncMock()
        mock_champion_repo.upsert_champion = AsyncMock()
        mock_champion_repo.record_candidate = AsyncMock()

        fake = _FakeSettings()

        with _patch_settings(fake), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ), patch(
            "app.scheduler.jobs.PerformanceRepository",
            return_value=mock_perf_repo,
        ), patch(
            "app.scheduler.jobs.ChampionRepository",
            return_value=mock_champion_repo,
        ):
            result = await _promote_one_key(
                selector=selector, horizon="24h", market_condition=None
            )

        assert result["status"] == "skipped"
        mock_champion_repo.upsert_champion.assert_not_called()
        mock_champion_repo.record_candidate.assert_not_called()

    @pytest.mark.asyncio
    async def test_passes_market_condition_to_repos(self) -> None:
        """The regime label is forwarded to both repositories."""
        selector = _make_selector()

        mock_perf_repo = MagicMock()
        mock_perf_repo.fetch_metrics_for_ranking = AsyncMock(return_value=[])
        mock_champion_repo = MagicMock()
        mock_champion_repo.get_champion = AsyncMock(return_value=None)
        mock_champion_repo.get_stability_streak = AsyncMock(return_value=0)
        mock_champion_repo.upsert_champion = AsyncMock()
        mock_champion_repo.record_candidate = AsyncMock()

        fake = _FakeSettings()

        with _patch_settings(fake), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ), patch(
            "app.scheduler.jobs.PerformanceRepository",
            return_value=mock_perf_repo,
        ), patch(
            "app.scheduler.jobs.ChampionRepository",
            return_value=mock_champion_repo,
        ):
            await _promote_one_key(
                selector=selector, horizon="24h", market_condition="bull"
            )

        assert (
            mock_perf_repo.fetch_metrics_for_ranking.call_args.kwargs[
                "market_condition"
            ]
            == "bull"
        )
        assert (
            mock_champion_repo.get_champion.call_args.kwargs[
                "market_condition"
            ]
            == "bull"
        )

    @pytest.mark.asyncio
    async def test_uses_settings_lookback_days(self) -> None:
        """primary_days and secondary_days come from settings."""
        selector = _make_selector()

        mock_perf_repo = MagicMock()
        mock_perf_repo.fetch_metrics_for_ranking = AsyncMock(return_value=[])
        mock_champion_repo = MagicMock()
        mock_champion_repo.get_champion = AsyncMock(return_value=None)
        mock_champion_repo.get_stability_streak = AsyncMock(return_value=0)
        mock_champion_repo.upsert_champion = AsyncMock()
        mock_champion_repo.record_candidate = AsyncMock()

        fake = _FakeSettings(primary_days=45, secondary_days=180)

        with _patch_settings(fake), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ), patch(
            "app.scheduler.jobs.PerformanceRepository",
            return_value=mock_perf_repo,
        ), patch(
            "app.scheduler.jobs.ChampionRepository",
            return_value=mock_champion_repo,
        ):
            await _promote_one_key(
                selector=selector, horizon="24h", market_condition=None
            )

        kwargs = mock_perf_repo.fetch_metrics_for_ranking.call_args.kwargs
        assert kwargs["primary_days"] == 45
        assert kwargs["secondary_days"] == 180

    @pytest.mark.asyncio
    async def test_streak_lookup_uses_top_candidate_name(self) -> None:
        """get_stability_streak is called with the top candidate's name."""
        selector = _make_selector(min_sample_size=100)
        metric_rows = [
            _make_metric_row("model_a", primary=90.0),
            _make_metric_row("model_b", primary=100.0),
        ]

        mock_perf_repo = MagicMock()
        mock_perf_repo.fetch_metrics_for_ranking = AsyncMock(
            return_value=metric_rows
        )
        mock_champion_repo = MagicMock()
        mock_champion_repo.get_champion = AsyncMock(return_value=None)
        mock_champion_repo.get_stability_streak = AsyncMock(return_value=0)
        mock_champion_repo.upsert_champion = AsyncMock(return_value=1)
        mock_champion_repo.record_candidate = AsyncMock(return_value=True)

        fake = _FakeSettings()

        with _patch_settings(fake), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ), patch(
            "app.scheduler.jobs.PerformanceRepository",
            return_value=mock_perf_repo,
        ), patch(
            "app.scheduler.jobs.ChampionRepository",
            return_value=mock_champion_repo,
        ):
            await _promote_one_key(
                selector=selector, horizon="24h", market_condition=None
            )

        kwargs = mock_champion_repo.get_stability_streak.call_args.kwargs
        assert kwargs["model_name"] == "model_a"
        assert kwargs["metric_name"] == "mae"

    @pytest.mark.asyncio
    async def test_returns_expected_keys(self) -> None:
        """The result dict contains the documented keys."""
        selector = _make_selector()
        metric_rows = [_make_metric_row("model_a", primary=90.0)]

        mock_perf_repo = MagicMock()
        mock_perf_repo.fetch_metrics_for_ranking = AsyncMock(
            return_value=metric_rows
        )
        mock_champion_repo = MagicMock()
        mock_champion_repo.get_champion = AsyncMock(return_value=None)
        mock_champion_repo.get_stability_streak = AsyncMock(return_value=0)
        mock_champion_repo.upsert_champion = AsyncMock(return_value=1)
        mock_champion_repo.record_candidate = AsyncMock(return_value=True)

        fake = _FakeSettings()

        with _patch_settings(fake), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ), patch(
            "app.scheduler.jobs.PerformanceRepository",
            return_value=mock_perf_repo,
        ), patch(
            "app.scheduler.jobs.ChampionRepository",
            return_value=mock_champion_repo,
        ):
            result = await _promote_one_key(
                selector=selector, horizon="24h", market_condition=None
            )

        expected = {
            "status",
            "decision_status",
            "candidate_name",
            "candidate_metric",
            "candidate_sample_size",
            "previous_champion",
            "improvement_pct",
            "stability_days",
            "reason",
        }
        assert set(result.keys()) == expected


# ============================================================
# daily_promote_champion_job — top-level orchestration
# ============================================================
class TestDailyPromoteChampionJob:
    """Tests for daily_promote_champion_job().

    Patches _promote_one_key so the top-level job's iteration,
    aggregation, and failure isolation can be tested without
    wiring up any repositories.
    """

    @pytest.mark.asyncio
    async def test_regime_disabled_iterates_only_none(self) -> None:
        """With the flag off, the job runs 2 pairs (one per horizon)."""
        fake = _FakeSettings(enable_regime_selection=False)

        mock_promote = AsyncMock(
            return_value={"status": "unchanged", "reason": "seed"}
        )

        with _patch_settings(fake), patch(
            "app.scheduler.jobs._promote_one_key", mock_promote
        ):
            result = await daily_promote_champion_job()

        assert result["pairs_attempted"] == 2
        assert result["regimes_processed"] == 1
        # Both calls used market_condition=None
        for call in mock_promote.call_args_list:
            assert call.kwargs["market_condition"] is None

    @pytest.mark.asyncio
    async def test_regime_enabled_iterates_all_regimes(self) -> None:
        """With the flag on, the job runs 10 pairs (5 regimes × 2 horizons)."""
        fake = _FakeSettings(enable_regime_selection=True)

        mock_promote = AsyncMock(
            return_value={"status": "unchanged", "reason": "seed"}
        )

        with _patch_settings(fake), patch(
            "app.scheduler.jobs._promote_one_key", mock_promote
        ):
            result = await daily_promote_champion_job()

        assert result["pairs_attempted"] == 10
        assert result["regimes_processed"] == 5

    @pytest.mark.asyncio
    async def test_aggregates_status_counts(self) -> None:
        """The job counts each status across all pairs."""
        fake = _FakeSettings(enable_regime_selection=False)

        # First pair promoted, second unchanged
        statuses = iter(["promoted", "unchanged"])

        async def fake_promote(*args, **kwargs):
            return {"status": next(statuses), "reason": "seed"}

        with _patch_settings(fake), patch(
            "app.scheduler.jobs._promote_one_key",
            side_effect=fake_promote,
        ):
            result = await daily_promote_champion_job()

        assert result["pairs_promoted"] == 1
        assert result["pairs_unchanged"] == 1
        assert result["pairs_first_champion"] == 0
        assert result["pairs_skipped"] == 0
        assert result["pairs_failed"] == 0

    @pytest.mark.asyncio
    async def test_aggregates_first_champion(self) -> None:
        fake = _FakeSettings()

        mock_promote = AsyncMock(
            return_value={"status": "first_champion", "reason": "seed"}
        )

        with _patch_settings(fake), patch(
            "app.scheduler.jobs._promote_one_key", mock_promote
        ):
            result = await daily_promote_champion_job()

        assert result["pairs_first_champion"] == 2

    @pytest.mark.asyncio
    async def test_aggregates_skipped(self) -> None:
        fake = _FakeSettings()

        mock_promote = AsyncMock(
            return_value={"status": "skipped", "reason": "seed"}
        )

        with _patch_settings(fake), patch(
            "app.scheduler.jobs._promote_one_key", mock_promote
        ):
            result = await daily_promote_champion_job()

        assert result["pairs_skipped"] == 2

    @pytest.mark.asyncio
    async def test_isolates_pair_failures(self) -> None:
        """One pair raising does not abort the others."""
        fake = _FakeSettings()

        call_count = {"n": 0}

        async def flaky(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("boom")
            return {"status": "unchanged", "reason": "seed"}

        with _patch_settings(fake), patch(
            "app.scheduler.jobs._promote_one_key", side_effect=flaky
        ):
            result = await daily_promote_champion_job()

        assert result["pairs_failed"] == 1
        assert result["pairs_unchanged"] == 1
        # No exception raised — the failed pair is captured
        assert result["pairs_attempted"] == 2

    @pytest.mark.asyncio
    async def test_raises_when_all_pairs_fail(self) -> None:
        fake = _FakeSettings()

        mock_promote = AsyncMock(side_effect=RuntimeError("boom"))

        with _patch_settings(fake), patch(
            "app.scheduler.jobs._promote_one_key", mock_promote
        ):
            with pytest.raises(RuntimeError, match="All .* pairs failed"):
                await daily_promote_champion_job()

    @pytest.mark.asyncio
    async def test_raises_on_selector_config_error(self) -> None:
        """A bad metric fails the whole job immediately."""
        fake = _FakeSettings(metric="not_a_metric")

        with _patch_settings(fake):
            with pytest.raises(RuntimeError, match="configuration error"):
                await daily_promote_champion_job()

    @pytest.mark.asyncio
    async def test_results_keyed_by_champion_key(self) -> None:
        """Each pair's outcome is stored under its <horizon>_<regime> key."""
        fake = _FakeSettings()

        mock_promote = AsyncMock(
            return_value={"status": "unchanged", "reason": "seed"}
        )

        with _patch_settings(fake), patch(
            "app.scheduler.jobs._promote_one_key", mock_promote
        ):
            result = await daily_promote_champion_job()

        assert set(result["results"].keys()) == {"24h_global", "7d_global"}

    @pytest.mark.asyncio
    async def test_summary_has_expected_keys(self) -> None:
        fake = _FakeSettings()

        mock_promote = AsyncMock(
            return_value={"status": "unchanged", "reason": "seed"}
        )

        with _patch_settings(fake), patch(
            "app.scheduler.jobs._promote_one_key", mock_promote
        ):
            result = await daily_promote_champion_job()

        expected = {
            "horizons_processed",
            "regimes_processed",
            "pairs_attempted",
            "pairs_promoted",
            "pairs_first_champion",
            "pairs_unchanged",
            "pairs_skipped",
            "pairs_failed",
            "results",
            "elapsed_seconds",
        }
        assert set(result.keys()) == expected

    @pytest.mark.asyncio
    async def test_iterates_over_champion_horizons(self) -> None:
        """The job runs for every horizon in CHAMPION_HORIZONS."""
        fake = _FakeSettings()

        mock_promote = AsyncMock(
            return_value={"status": "unchanged", "reason": "seed"}
        )

        with _patch_settings(fake), patch(
            "app.scheduler.jobs._promote_one_key", mock_promote
        ):
            await daily_promote_champion_job()

        horizons = {c.kwargs["horizon"] for c in mock_promote.call_args_list}
        assert horizons == set(CHAMPION_HORIZONS)


# ============================================================
# CONSTANTS
# ============================================================
class TestChampionJobConstants:
    """Sanity checks on the champion-related constants."""

    def test_job_name(self) -> None:
        assert JOB_DAILY_PROMOTE_CHAMPION == "daily_promote_champion"

    def test_two_horizons(self) -> None:
        assert CHAMPION_HORIZONS == ("24h", "7d")

    def test_all_variants_has_six_entries(self) -> None:
        assert len(ALL_VARIANTS) == 6
        assert "prophet_fresh" in ALL_VARIANTS