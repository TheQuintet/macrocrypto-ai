"""
Integration tests for the current macroeconomic regime API.

Tests:
- Current regime response
- Confidence percentage
- Visual indicator
- Latest regime selection
- Expiration timestamp
- 404 behavior when no regime exists
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.database.regime_repository import RegimeRepository


# ============================================================
# CURRENT REGIME - CONFIDENCE AND VISUAL INDICATOR
# ============================================================


def test_get_current_regime_returns_confidence_and_visual_indicator(
    client: TestClient,
    db,
):
    """
    Current regime API should return confidence and
    visual indicator fields.
    """

    repository = RegimeRepository(db)

    repository.set_current_regime(
        regime_type="growth",
        confidence=85.0,
        visual_indicator="bull",
    )

    response = client.get(
        "/api/v1/regimes/current"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["regime_type"] == "growth"
    assert data["confidence"] == 85.0
    assert data["visual_indicator"] == "bull"


# ============================================================
# CURRENT REGIME - LATEST REGIME
# ============================================================


def test_get_current_regime_returns_latest_regime(
    client: TestClient,
    db,
):
    """
    API should return the most recently identified
    current regime.
    """

    repository = RegimeRepository(db)

    repository.set_current_regime(
        regime_type="growth",
        confidence=80.0,
        visual_indicator="bull",
    )

    repository.set_current_regime(
        regime_type="high_inflation",
        confidence=90.0,
        visual_indicator="bear",
    )

    response = client.get(
        "/api/v1/regimes/current"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["regime_type"] == "high_inflation"
    assert data["confidence"] == 90.0
    assert data["visual_indicator"] == "bear"


# ============================================================
# CURRENT REGIME - VISUAL INDICATOR
# ============================================================


def test_get_current_regime_returns_bull_indicator(
    client: TestClient,
    db,
):
    """
    A growth regime should return the configured
    bull visual indicator.
    """

    repository = RegimeRepository(db)

    repository.set_current_regime(
        regime_type="growth",
        confidence=0.0,
        visual_indicator="bull",
    )

    response = client.get(
        "/api/v1/regimes/current"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["regime_type"] == "growth"
    assert data["confidence"] == 0.0
    assert data["visual_indicator"] == "bull"


# ============================================================
# CURRENT REGIME - EXPIRATION
# ============================================================


def test_get_current_regime_returns_expiration(
    client: TestClient,
    db,
):
    """
    API should return the expiration timestamp when
    one is configured.
    """

    repository = RegimeRepository(db)

    expires_at = datetime(
        2026,
        8,
        14,
        0,
        0,
        tzinfo=timezone.utc,
    )

    repository.set_current_regime(
        regime_type="rising_rates",
        confidence=72.5,
        visual_indicator="bear",
        expires_at=expires_at,
    )

    response = client.get(
        "/api/v1/regimes/current"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["regime_type"] == "rising_rates"
    assert data["confidence"] == 72.5
    assert data["visual_indicator"] == "bear"
    assert data["expires_at"] is not None


# ============================================================
# CURRENT REGIME - 404
# ============================================================


def test_get_current_regime_returns_404_when_no_regime(
    client: TestClient,
    db,
):
    """
    API should return 404 when no current regime exists.

    This test removes existing current-regime records
    before making the request.
    """

    from app.models.current_regime import CurrentRegime

    db.query(CurrentRegime).delete()
    db.commit()

    response = client.get(
        "/api/v1/regimes/current"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == (
        "No current macroeconomic regime found"
        or "No active macroeconomic regime found"
    )