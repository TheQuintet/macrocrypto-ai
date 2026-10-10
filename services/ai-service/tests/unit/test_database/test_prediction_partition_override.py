"""Unit tests for the PREDICTION_FEATURE_PARTITION override.

fetch_training_frame_for_source() resolves FeatureContext.PREDICTION
to live_frontier by default. When settings.prediction_feature_partition
is set, that partition is used instead. An explicit `partition`
argument always wins, and other contexts are unaffected.
"""

from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from app.config import settings
from app.database.enums import FeatureContext, FeaturePartition
from app.database.repositories.prediction_repository import (
    PredictionRepository,
)


@pytest.fixture
def repo(monkeypatch: pytest.MonkeyPatch) -> PredictionRepository:
    monkeypatch.setattr(settings, "feature_source", "parquet")
    repository = PredictionRepository(MagicMock())
    repository.fetch_training_frame_from_files = AsyncMock(  # type: ignore[method-assign]
        return_value=pd.DataFrame()
    )
    return repository


def _resolved_partition(repository: PredictionRepository) -> FeaturePartition:
    call = repository.fetch_training_frame_from_files.call_args  # type: ignore[attr-defined]
    return call.kwargs["partition"]


class TestPredictionPartitionOverride:
    @pytest.mark.asyncio
    async def test_prediction_defaults_to_live_frontier(
        self, repo: PredictionRepository, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "prediction_feature_partition", "")

        await repo.fetch_training_frame_for_source(
            hours=24, context=FeatureContext.PREDICTION
        )

        assert _resolved_partition(repo) == FeaturePartition.LIVE_FRONTIER

    @pytest.mark.asyncio
    async def test_prediction_uses_override(
        self, repo: PredictionRepository, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "prediction_feature_partition", "test")

        await repo.fetch_training_frame_for_source(
            hours=24, context=FeatureContext.PREDICTION
        )

        assert _resolved_partition(repo) == FeaturePartition.TEST

    @pytest.mark.asyncio
    async def test_override_does_not_affect_training(
        self, repo: PredictionRepository, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "prediction_feature_partition", "test")

        await repo.fetch_training_frame_for_source(
            hours=24, context=FeatureContext.TRAINING
        )

        assert _resolved_partition(repo) == FeaturePartition.TRAIN

    @pytest.mark.asyncio
    async def test_explicit_partition_wins_over_override(
        self, repo: PredictionRepository, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "prediction_feature_partition", "test")

        await repo.fetch_training_frame_for_source(
            hours=24,
            context=FeatureContext.PREDICTION,
            partition=FeaturePartition.VAL,
        )

        assert _resolved_partition(repo) == FeaturePartition.VAL

    @pytest.mark.asyncio
    async def test_invalid_override_raises(
        self, repo: PredictionRepository, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "prediction_feature_partition", "bogus")

        with pytest.raises(ValueError):
            await repo.fetch_training_frame_for_source(
                hours=24, context=FeatureContext.PREDICTION
            )
