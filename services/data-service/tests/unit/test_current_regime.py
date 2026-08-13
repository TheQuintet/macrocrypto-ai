"""
Unit tests for current regime repository functionality.

Tests:
- Confidence persistence
- Confidence boundary values
- Confidence validation
- Visual indicator persistence
- Expiration persistence
- Latest current regime retrieval
- Missing current regime handling
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.database.regime_repository import RegimeRepository
from app.models.current_regime import CurrentRegime


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def mock_db():
    """Provide a mocked SQLAlchemy session."""
    return MagicMock()


@pytest.fixture
def repository(mock_db):
    """Provide a RegimeRepository using the mocked database."""
    return RegimeRepository(mock_db)


# ============================================================
# SET CURRENT REGIME
# ============================================================

def test_set_current_regime_persists_confidence(
    repository,
    mock_db,
):
    """
    Current regime should be stored together with its
    confidence percentage and visual indicator.
    """

    mock_db.refresh.side_effect = lambda obj: None

    result = repository.set_current_regime(
        regime_type="high_inflation",
        confidence=85.0,
        visual_indicator="bear",
    )

    assert isinstance(result, CurrentRegime)
    assert result.regime_type == "high_inflation"
    assert result.confidence == 85.0
    assert result.visual_indicator == "bear"

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(result)


def test_set_current_regime_accepts_zero_confidence(
    repository,
    mock_db,
):
    """
    Confidence of 0% is a valid boundary value.
    """

    mock_db.refresh.side_effect = lambda obj: None

    result = repository.set_current_regime(
        regime_type="growth",
        confidence=0.0,
        visual_indicator="bull",
    )

    assert result.confidence == 0.0
    assert result.visual_indicator == "bull"


def test_set_current_regime_accepts_full_confidence(
    repository,
    mock_db,
):
    """
    Confidence of 100% is a valid boundary value.
    """

    mock_db.refresh.side_effect = lambda obj: None

    result = repository.set_current_regime(
        regime_type="recession",
        confidence=100.0,
        visual_indicator="recession",
    )

    assert result.confidence == 100.0
    assert result.visual_indicator == "recession"


def test_set_current_regime_stores_expiration(
    repository,
    mock_db,
):
    """
    Optional expiration timestamp should be persisted.
    """

    mock_db.refresh.side_effect = lambda obj: None

    expires_at = datetime(
        2026,
        8,
        14,
        0,
        0,
        tzinfo=timezone.utc,
    )

    result = repository.set_current_regime(
        regime_type="rising_rates",
        confidence=72.5,
        visual_indicator="bear",
        expires_at=expires_at,
    )

    assert result.confidence == 72.5
    assert result.visual_indicator == "bear"
    assert result.expires_at == expires_at


# ============================================================
# VISUAL INDICATOR
# ============================================================

def test_set_current_regime_persists_visual_indicator(
    repository,
    mock_db,
):
    """
    Current regime should persist the visual indicator.
    """

    mock_db.refresh.side_effect = lambda obj: None

    result = repository.set_current_regime(
        regime_type="growth",
        confidence=90.0,
        visual_indicator="bull",
    )

    assert result.visual_indicator == "bull"


# ============================================================
# GET CURRENT REGIME SNAPSHOT
# ============================================================

def test_get_current_regime_snapshot_returns_latest(
    repository,
    mock_db,
):
    """
    Repository should return the most recently identified
    current regime.
    """

    expected = CurrentRegime(
        id=2,
        regime_type="growth",
        confidence=90.0,
        visual_indicator="bull",
    )

    query = mock_db.query.return_value
    ordered = query.order_by.return_value
    ordered.first.return_value = expected

    result = repository.get_current_regime_snapshot()

    assert result is expected
    assert result.regime_type == "growth"
    assert result.confidence == 90.0
    assert result.visual_indicator == "bull"

    mock_db.query.assert_called_once_with(CurrentRegime)


def test_get_current_regime_snapshot_returns_none_when_missing(
    repository,
    mock_db,
):
    """
    Repository should return None when no current regime
    has been stored.
    """

    query = mock_db.query.return_value
    ordered = query.order_by.return_value
    ordered.first.return_value = None

    result = repository.get_current_regime_snapshot()

    assert result is None


# ============================================================
# CONFIDENCE VALIDATION
# ============================================================

@pytest.mark.parametrize(
    "confidence",
    [
        -1.0,
        100.1,
        150.0,
    ],
)
def test_set_current_regime_rejects_invalid_confidence(
    repository,
    confidence,
):
    """
    Confidence must be between 0% and 100%.
    """

    with pytest.raises(ValueError):
        repository.set_current_regime(
            regime_type="growth",
            confidence=confidence,
            visual_indicator="bull",
        )