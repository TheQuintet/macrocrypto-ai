"""Unit tests for regime-aware champion serving (Phase 4).

Two related things are tested here:

    1. `_load_champion_model` with a non-None `market_condition`
       argument. When a regime champion exists and loads, it's
       returned. When it doesn't exist or fails to load, the
       helper falls through to the global champion chain.

    2. The two prediction jobs (`hourly_prediction_job`,
       `daily_7d_prediction_job`) when
       `settings.champion_serve_regime_aware` is on. Each job
       classifies the current regime via
       `classify_current_regime` and passes it to
       `_load_champion_model`. When the flag is off, no
       classification happens.

All DB access is mocked — no live DB is required.

Test organization:
    - TestLoadChampionModelRegime: the regime branch of
      _load_champion_model, in isolation
    - TestHourlyPredictionJobRegimeAware: hourly_prediction_job
      with the flag on and off
    - TestDaily7dPredictionJobRegimeAware: daily_7d_prediction_job
      with the flag on and off
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scheduler.jobs import (
    _load_champion_model,
    daily_7d_prediction_job,
    hourly_prediction_job,
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


def _champion_row(
    model_name: str = "prophet_fresh",
    previous: str = None,
) -> dict:
    """Build a champion row dict as ChampionRepository.get_champion would return."""
    return {
        "id": 1,
        "horizon": "24h",
        "market_condition": None,
        "model_name": model_name,
        "model_version": "1.0.0",
        "promoted_at": None,
        "metric_name": "mae",
        "metric_value": 100.0,
        "sample_size": 200,
        "lookback_days": 30,
        "previous_champion": previous,
        "reason": "seed",
        "created_at": None,
    }


def _make_model(name: str = "model") -> MagicMock:
    """Build a mocked trained model."""
    m = MagicMock()
    m.load = MagicMock()
    m.is_model_trained = MagicMock(return_value=True)
    m.name = name
    return m


def _make_generation_result(succeeded: bool = True) -> MagicMock:
    """Build a GenerationResult-like object for prediction-job tests."""
    r = MagicMock()
    r.succeeded = succeeded
    r.horizon = "24h"
    r.model_name = "prophet"
    r.prediction_time = MagicMock()
    r.prediction_time.isoformat.return_value = "2026-01-01T00:00:00+00:00"
    r.rows_generated = 24
    r.rows_saved = 24
    r.elapsed_seconds = 0.5
    r.error = None if succeeded else "generation failed"
    return r


# ============================================================
# _load_champion_model — REGIME BRANCH
# ============================================================
class TestLoadChampionModelRegime:
    """Tests for the regime-aware branch of _load_champion_model."""

    @pytest.mark.asyncio
    async def test_regime_champion_loaded_when_present(self) -> None:
        """A regime champion that exists and loads is returned."""
        regime_row = _champion_row(model_name="xgboost_fresh")
        regime_model = _make_model("xgboost_fresh")

        repo = MagicMock()
        repo.get_champion = AsyncMock(return_value=regime_row)

        def fake_load_generic(name):
            if name == "xgboost_fresh":
                return regime_model
            raise FileNotFoundError(f"no artifact for {name}")

        with patch(
            "app.scheduler.jobs._load_variant_model_generic",
            side_effect=fake_load_generic,
        ):
            result = await _load_champion_model(
                champion_repo=repo,
                horizon="24h",
                market_condition="bull",
            )

        assert result is regime_model
        # Repo called with the regime label, not None
        kwargs = repo.get_champion.call_args.kwargs
        assert kwargs["market_condition"] == "bull"

    @pytest.mark.asyncio
    async def test_falls_through_to_global_when_no_regime_row(
        self,
    ) -> None:
        """No regime champion row → global champion is loaded."""
        global_row = _champion_row(model_name="prophet_fresh")
        global_model = _make_model("prophet_fresh")

        repo = MagicMock()
        # First call (regime) returns None; second (global) returns the row
        repo.get_champion = AsyncMock(
            side_effect=[None, global_row]
        )

        with patch(
            "app.scheduler.jobs._load_variant_model_generic",
            return_value=global_model,
        ) as mock_load:
            result = await _load_champion_model(
                champion_repo=repo,
                horizon="24h",
                market_condition="bull",
            )

        assert result is global_model
        assert mock_load.call_args.args[0] == "prophet_fresh"
        # Two calls: first with regime, second with None
        assert repo.get_champion.call_count == 2
        assert (
            repo.get_champion.call_args_list[0].kwargs["market_condition"]
            == "bull"
        )
        assert (
            repo.get_champion.call_args_list[1].kwargs["market_condition"]
            is None
        )

    @pytest.mark.asyncio
    async def test_regime_artifact_missing_falls_through_to_global(
        self,
    ) -> None:
        """Regime champion exists but its artifact is missing → global."""
        regime_row = _champion_row(model_name="xgboost_fresh")
        global_row = _champion_row(model_name="prophet_fresh")
        global_model = _make_model("prophet_fresh")

        repo = MagicMock()
        repo.get_champion = AsyncMock(
            side_effect=[regime_row, global_row]
        )

        def fake_load_generic(name):
            if name == "xgboost_fresh":
                raise FileNotFoundError("no artifact")
            return global_model

        with patch(
            "app.scheduler.jobs._load_variant_model_generic",
            side_effect=fake_load_generic,
        ):
            result = await _load_champion_model(
                champion_repo=repo,
                horizon="24h",
                market_condition="bull",
            )

        assert result is global_model

    @pytest.mark.asyncio
    async def test_regime_previous_champion_tried_before_global(
        self,
    ) -> None:
        """Regime champion artifact missing → regime predecessor tried."""
        regime_row = _champion_row(
            model_name="xgboost_fresh",
            previous="prophet_warm",
        )
        regime_previous_model = _make_model("prophet_warm")

        repo = MagicMock()
        repo.get_champion = AsyncMock(return_value=regime_row)

        def fake_load_generic(name):
            if name == "xgboost_fresh":
                raise FileNotFoundError("missing xgboost")
            if name == "prophet_warm":
                return regime_previous_model
            raise FileNotFoundError(f"no artifact for {name}")

        with patch(
            "app.scheduler.jobs._load_variant_model_generic",
            side_effect=fake_load_generic,
        ):
            result = await _load_champion_model(
                champion_repo=repo,
                horizon="24h",
                market_condition="bull",
            )

        assert result is regime_previous_model

    @pytest.mark.asyncio
    async def test_market_condition_none_skips_regime_branch(self) -> None:
        """With market_condition=None, no regime lookup happens."""
        global_row = _champion_row(model_name="prophet_fresh")
        global_model = _make_model("prophet_fresh")

        repo = MagicMock()
        repo.get_champion = AsyncMock(return_value=global_row)

        with patch(
            "app.scheduler.jobs._load_variant_model_generic",
            return_value=global_model,
        ):
            result = await _load_champion_model(
                champion_repo=repo,
                horizon="24h",
                market_condition=None,
            )

        assert result is global_model
        # Only one call: the global lookup
        assert repo.get_champion.call_count == 1
        assert repo.get_champion.call_args.kwargs["market_condition"] is None

    @pytest.mark.asyncio
    async def test_no_regime_and_no_global_falls_back_to_prophet_fresh(
        self,
    ) -> None:
        """Both regime and global lookups return None → prophet_fresh."""
        prophet_model = _make_model("prophet_fresh")

        repo = MagicMock()
        repo.get_champion = AsyncMock(return_value=None)

        with patch(
            "app.scheduler.jobs._load_variant_model_generic",
            return_value=prophet_model,
        ) as mock_load:
            result = await _load_champion_model(
                champion_repo=repo,
                horizon="24h",
                market_condition="bull",
            )

        assert result is prophet_model
        assert mock_load.call_args.args[0] == "prophet_fresh"


# ============================================================
# hourly_prediction_job — REGIME-AWARE BEHAVIOR
# ============================================================
class TestHourlyPredictionJobRegimeAware:
    """Tests for hourly_prediction_job with regime-aware serving."""

    @pytest.mark.asyncio
    async def test_flag_off_skips_classification(self) -> None:
        """With the flag off, the classifier is never called."""
        model = _make_model("prophet_fresh")
        gen = _make_generation_result()

        mock_classifier = AsyncMock()
        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(return_value=gen)

        with patch(
            "app.scheduler.jobs.settings.champion_serve_regime_aware",
            False,
        ), patch(
            "app.scheduler.jobs.classify_current_regime",
            mock_classifier,
        ), patch(
            "app.scheduler.jobs._load_champion_model",
            new_callable=AsyncMock,
            return_value=model,
        ) as mock_load, patch(
            "app.scheduler.jobs.PredictionGenerator",
            return_value=mock_generator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            await hourly_prediction_job()

        # Classifier never called
        mock_classifier.assert_not_called()
        # Champion loaded with market_condition=None
        assert mock_load.call_args.kwargs["market_condition"] is None

    @pytest.mark.asyncio
    async def test_flag_on_passes_regime_to_load(self) -> None:
        """With the flag on, the classified regime is passed down."""
        model = _make_model("xgboost_fresh")
        gen = _make_generation_result()

        mock_classifier = AsyncMock(return_value="bull")
        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(return_value=gen)

        with patch(
            "app.scheduler.jobs.settings.champion_serve_regime_aware",
            True,
        ), patch(
            "app.scheduler.jobs.classify_current_regime",
            mock_classifier,
        ), patch(
            "app.scheduler.jobs._load_champion_model",
            new_callable=AsyncMock,
            return_value=model,
        ) as mock_load, patch(
            "app.scheduler.jobs.PredictionGenerator",
            return_value=mock_generator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            await hourly_prediction_job()

        # Classifier called with the 24h window
        clf_kwargs = mock_classifier.call_args.kwargs
        assert clf_kwargs["window_hours"] == 24
        # Champion loaded with the classified regime
        assert mock_load.call_args.kwargs["market_condition"] == "bull"

    @pytest.mark.asyncio
    async def test_flag_on_classifier_returns_none_passes_none(
        self,
    ) -> None:
        """Classifier returning None → market_condition=None passed down."""
        model = _make_model("prophet_fresh")
        gen = _make_generation_result()

        mock_classifier = AsyncMock(return_value=None)
        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(return_value=gen)

        with patch(
            "app.scheduler.jobs.settings.champion_serve_regime_aware",
            True,
        ), patch(
            "app.scheduler.jobs.classify_current_regime",
            mock_classifier,
        ), patch(
            "app.scheduler.jobs._load_champion_model",
            new_callable=AsyncMock,
            return_value=model,
        ) as mock_load, patch(
            "app.scheduler.jobs.PredictionGenerator",
            return_value=mock_generator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            await hourly_prediction_job()

        # Classifier called with the 24h window
        assert mock_classifier.call_args.kwargs["window_hours"] == 24
        # Champion loaded with None (fallback to global)
        assert mock_load.call_args.kwargs["market_condition"] is None


# ============================================================
# daily_7d_prediction_job — REGIME-AWARE BEHAVIOR
# ============================================================
class TestDaily7dPredictionJobRegimeAware:
    """Tests for daily_7d_prediction_job with regime-aware serving."""

    @pytest.mark.asyncio
    async def test_flag_off_skips_classification(self) -> None:
        """With the flag off, the classifier is never called."""
        model = _make_model("prophet_fresh")
        gen = _make_generation_result()
        gen.horizon = "7d"

        mock_classifier = AsyncMock()
        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(return_value=gen)

        with patch(
            "app.scheduler.jobs.settings.champion_serve_regime_aware",
            False,
        ), patch(
            "app.scheduler.jobs.classify_current_regime",
            mock_classifier,
        ), patch(
            "app.scheduler.jobs._load_champion_model",
            new_callable=AsyncMock,
            return_value=model,
        ) as mock_load, patch(
            "app.scheduler.jobs.PredictionGenerator",
            return_value=mock_generator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            await daily_7d_prediction_job()

        mock_classifier.assert_not_called()
        assert mock_load.call_args.kwargs["market_condition"] is None

    @pytest.mark.asyncio
    async def test_flag_on_uses_168h_window(self) -> None:
        """The 7d job classifies with a 168h window."""
        model = _make_model("xgboost_fresh")
        gen = _make_generation_result()
        gen.horizon = "7d"

        mock_classifier = AsyncMock(return_value="bear")
        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(return_value=gen)

        with patch(
            "app.scheduler.jobs.settings.champion_serve_regime_aware",
            True,
        ), patch(
            "app.scheduler.jobs.classify_current_regime",
            mock_classifier,
        ), patch(
            "app.scheduler.jobs._load_champion_model",
            new_callable=AsyncMock,
            return_value=model,
        ) as mock_load, patch(
            "app.scheduler.jobs.PredictionGenerator",
            return_value=mock_generator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            await daily_7d_prediction_job()

        assert mock_classifier.call_args.kwargs["window_hours"] == 168
        assert mock_load.call_args.kwargs["market_condition"] == "bear"

    @pytest.mark.asyncio
    async def test_flag_on_regime_is_forwarded_verbatim(self) -> None:
        """The classified regime is passed through without modification."""
        model = _make_model("xgboost_fresh")
        gen = _make_generation_result()
        gen.horizon = "7d"

        for regime in ("bull", "bear", "volatile", "neutral"):
            mock_classifier = AsyncMock(return_value=regime)
            mock_generator = MagicMock()
            mock_generator.generate = AsyncMock(return_value=gen)

            with patch(
                "app.scheduler.jobs.settings.champion_serve_regime_aware",
                True,
            ), patch(
                "app.scheduler.jobs.classify_current_regime",
                mock_classifier,
            ), patch(
                "app.scheduler.jobs._load_champion_model",
                new_callable=AsyncMock,
                return_value=model,
            ) as mock_load, patch(
                "app.scheduler.jobs.PredictionGenerator",
                return_value=mock_generator,
            ), patch(
                "app.scheduler.jobs.session_scope",
                return_value=_session_scope_mock(),
            ):
                await daily_7d_prediction_job()

            assert mock_load.call_args.kwargs["market_condition"] == regime