"""
Integration tests for the similar historical periods API.

Endpoint under test:

GET /api/v1/regimes/history/similar-periods
"""

from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# ============================================================
# MOCK DATA
# ============================================================

def mock_service():
    """
    Create a mocked SimilarPeriodService response.
    """

    service = MagicMock()

    service.find_similar_periods.return_value = {
        "current_conditions": {
            "cpi": 3.0,
            "federal_funds_rate": 4.0,
            "m2_money_supply": 21000.0,
            "dxy": 100.0,
            "ten_year_treasury": 4.2,
            "gdp": 2.5,
            "unemployment": 4.0,
        },
        "method": "normalized_euclidean_distance",
        "period_count": 3,
        "similar_periods": [
            {
                "period_start": "2020-01-01",
                "period_end": "2020-01-31",
                "distance": 0.25,
                "similarity_score": 0.8,
                "reason": (
                    "Similar macro conditions primarily driven by: "
                    "cpi, gdp, unemployment"
                ),
                "matching_indicators": [
                    {
                        "indicator": "cpi",
                        "normalized_difference": 0.05,
                    },
                    {
                        "indicator": "gdp",
                        "normalized_difference": 0.08,
                    },
                    {
                        "indicator": "unemployment",
                        "normalized_difference": 0.12,
                    },
                ],
                "macro_conditions": {
                    "cpi": 3.1,
                    "federal_funds_rate": 4.1,
                    "m2_money_supply": 20900.0,
                    "dxy": 100.5,
                    "ten_year_treasury": 4.1,
                    "gdp": 2.4,
                    "unemployment": 4.1,
                },
                "btc_performance": {
                    "price_start": 7000.0,
                    "price_end": 7500.0,
                    "return_percent": 7.142857,
                    "observations": 100,
                },
            },
            {
                "period_start": "2019-01-01",
                "period_end": "2019-01-31",
                "distance": 0.50,
                "similarity_score": 0.666667,
                "reason": (
                    "Similar macro conditions primarily driven by: "
                    "cpi, federal_funds_rate, gdp"
                ),
                "matching_indicators": [
                    {
                        "indicator": "cpi",
                        "normalized_difference": 0.10,
                    },
                    {
                        "indicator": "federal_funds_rate",
                        "normalized_difference": 0.15,
                    },
                    {
                        "indicator": "gdp",
                        "normalized_difference": 0.20,
                    },
                ],
                "macro_conditions": {
                    "cpi": 3.2,
                    "federal_funds_rate": 3.9,
                    "m2_money_supply": 20800.0,
                    "dxy": 101.0,
                    "ten_year_treasury": 4.3,
                    "gdp": 2.3,
                    "unemployment": 4.2,
                },
                "btc_performance": None,
            },
            {
                "period_start": "2018-01-01",
                "period_end": "2018-01-31",
                "distance": 0.75,
                "similarity_score": 0.571429,
                "reason": (
                    "Similar macro conditions primarily driven by: "
                    "unemployment, cpi, dxy"
                ),
                "matching_indicators": [
                    {
                        "indicator": "unemployment",
                        "normalized_difference": 0.18,
                    },
                    {
                        "indicator": "cpi",
                        "normalized_difference": 0.22,
                    },
                    {
                        "indicator": "dxy",
                        "normalized_difference": 0.30,
                    },
                ],
                "macro_conditions": {
                    "cpi": 3.3,
                    "federal_funds_rate": 3.8,
                    "m2_money_supply": 20700.0,
                    "dxy": 101.5,
                    "ten_year_treasury": 4.4,
                    "gdp": 2.2,
                    "unemployment": 4.3,
                },
                "btc_performance": None,
            },
        ],
    }

    return service


# ============================================================
# SUCCESS
# ============================================================

@patch(
    "app.api.similar_periods.SimilarPeriodService"
)
def test_get_similar_periods_success(
    mock_service_class,
):
    """
    API should return similar historical periods successfully.
    """

    mock_service_class.return_value = mock_service()

    response = client.get(
        "/api/v1/regimes/history/similar-periods"
    )

    assert response.status_code == 200

    data = response.json()

    assert "current_conditions" in data
    assert "method" in data
    assert "period_count" in data
    assert "similar_periods" in data

    assert data["method"] == (
        "normalized_euclidean_distance"
    )

    assert data["period_count"] == 3
    assert len(data["similar_periods"]) == 3


# ============================================================
# LIMIT = 3
# ============================================================

@patch(
    "app.api.similar_periods.SimilarPeriodService"
)
def test_get_similar_periods_limit_3(
    mock_service_class,
):
    """
    API should pass limit=3 to the service.
    """

    service = mock_service()
    mock_service_class.return_value = service

    response = client.get(
        "/api/v1/regimes/history/similar-periods?limit=3"
    )

    assert response.status_code == 200

    service.find_similar_periods.assert_called_once_with(
        limit=3
    )


# ============================================================
# LIMIT = 5
# ============================================================

@patch(
    "app.api.similar_periods.SimilarPeriodService"
)
def test_get_similar_periods_limit_5(
    mock_service_class,
):
    """
    API should support the maximum allowed limit.
    """

    service = mock_service()
    mock_service_class.return_value = service

    response = client.get(
        "/api/v1/regimes/history/similar-periods?limit=5"
    )

    assert response.status_code == 200

    service.find_similar_periods.assert_called_once_with(
        limit=5
    )


# ============================================================
# LIMIT BELOW MINIMUM
# ============================================================

def test_get_similar_periods_limit_below_minimum():
    """
    Limit below 3 should be rejected by FastAPI validation.
    """

    response = client.get(
        "/api/v1/regimes/history/similar-periods?limit=2"
    )

    assert response.status_code == 422


# ============================================================
# LIMIT ABOVE MAXIMUM
# ============================================================

def test_get_similar_periods_limit_above_maximum():
    """
    Limit above 5 should be rejected by FastAPI validation.
    """

    response = client.get(
        "/api/v1/regimes/history/similar-periods?limit=6"
    )

    assert response.status_code == 422


# ============================================================
# NO RESULTS
# ============================================================

@patch(
    "app.api.similar_periods.SimilarPeriodService"
)
def test_get_similar_periods_no_results(
    mock_service_class,
):
    """
    API should safely return an empty result set.
    """

    service = MagicMock()

    service.find_similar_periods.return_value = {
        "current_conditions": {
            "cpi": 3.0,
        },
        "method": "normalized_euclidean_distance",
        "period_count": 0,
        "similar_periods": [],
        "message": (
            "Insufficient historical macroeconomic "
            "snapshots for similarity matching."
        ),
    }

    mock_service_class.return_value = service

    response = client.get(
        "/api/v1/regimes/history/similar-periods"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["similar_periods"] == []
    assert data["period_count"] == 0
    assert data["message"] is not None


# ============================================================
# MISSING CURRENT CONDITIONS
# ============================================================

@patch(
    "app.api.similar_periods.SimilarPeriodService"
)
def test_get_similar_periods_missing_current_conditions(
    mock_service_class,
):
    """
    API should safely handle missing current macro data.
    """

    service = MagicMock()

    service.find_similar_periods.return_value = {
        "current_conditions": {},
        "method": "normalized_euclidean_distance",
        "period_count": 0,
        "similar_periods": [],
        "message": (
            "Current macroeconomic conditions are unavailable."
        ),
    }

    mock_service_class.return_value = service

    response = client.get(
        "/api/v1/regimes/history/similar-periods"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["current_conditions"] == {}
    assert data["similar_periods"] == []
    assert data["period_count"] == 0


# ============================================================
# RESPONSE STRUCTURE
# ============================================================

@patch(
    "app.api.similar_periods.SimilarPeriodService"
)
def test_similar_period_response_structure(
    mock_service_class,
):
    """
    Each similar period should expose the required fields.
    """

    mock_service_class.return_value = mock_service()

    response = client.get(
        "/api/v1/regimes/history/similar-periods?limit=3"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["similar_periods"]) == 3

    period = data["similar_periods"][0]

    assert "period_start" in period
    assert "period_end" in period
    assert "distance" in period
    assert "similarity_score" in period
    assert "reason" in period
    assert "matching_indicators" in period
    assert "macro_conditions" in period
    assert "btc_performance" in period


# ============================================================
# SORTING
# ============================================================

@patch(
    "app.api.similar_periods.SimilarPeriodService"
)
def test_similar_periods_sorted_by_distance(
    mock_service_class,
):
    """
    API should return periods ordered from most similar
    to least similar.
    """

    mock_service_class.return_value = mock_service()

    response = client.get(
        "/api/v1/regimes/history/similar-periods?limit=3"
    )

    assert response.status_code == 200

    periods = response.json()["similar_periods"]

    distances = [
        period["distance"]
        for period in periods
    ]

    assert distances == sorted(distances)


# ============================================================
# SIMILARITY SCORE
# ============================================================

@patch(
    "app.api.similar_periods.SimilarPeriodService"
)
def test_similarity_score_present(
    mock_service_class,
):
    """
    Each result should contain a similarity score between
    zero and one.
    """

    mock_service_class.return_value = mock_service()

    response = client.get(
        "/api/v1/regimes/history/similar-periods?limit=3"
    )

    assert response.status_code == 200

    periods = response.json()["similar_periods"]

    assert len(periods) > 0

    for period in periods:
        assert "similarity_score" in period

        score = period["similarity_score"]

        assert isinstance(score, (int, float))
        assert 0.0 <= score <= 1.0


# ============================================================
# BTC PERFORMANCE OPTIONAL
# ============================================================

@patch(
    "app.api.similar_periods.SimilarPeriodService"
)
def test_btc_performance_is_optional(
    mock_service_class,
):
    """
    BTC performance may be None when historical BTC data
    is unavailable.
    """

    mock_service_class.return_value = mock_service()

    response = client.get(
        "/api/v1/regimes/history/similar-periods?limit=3"
    )

    assert response.status_code == 200

    periods = response.json()["similar_periods"]

    assert periods[0]["btc_performance"] is not None
    assert periods[1]["btc_performance"] is None


# ============================================================
# SIMILARITY REASON
# ============================================================

@patch(
    "app.api.similar_periods.SimilarPeriodService"
)
def test_similarity_reason_is_exposed(
    mock_service_class,
):
    """
    API should expose the similarity reasoning.
    """

    mock_service_class.return_value = mock_service()

    response = client.get(
        "/api/v1/regimes/history/similar-periods?limit=3"
    )

    assert response.status_code == 200

    periods = response.json()["similar_periods"]

    assert len(periods) > 0

    for period in periods:
        assert "reason" in period
        assert isinstance(period["reason"], str)
        assert len(period["reason"]) > 0

        assert "matching_indicators" in period
        assert isinstance(
            period["matching_indicators"],
            list,
        )

        assert len(
            period["matching_indicators"]
        ) <= 3


# ============================================================
# SERVICE ERROR HANDLING
# ============================================================

@patch(
    "app.api.similar_periods.SimilarPeriodService"
)
def test_similar_periods_service_value_error(
    mock_service_class,
):
    """
    ValueError from the service should be returned as HTTP 422.
    """

    service = MagicMock()

    service.find_similar_periods.side_effect = ValueError(
        "limit must be between 3 and 5"
    )

    mock_service_class.return_value = service

    response = client.get(
        "/api/v1/regimes/history/similar-periods?limit=3"
    )

    assert response.status_code == 422

    data = response.json()

    assert data["detail"] == (
        "limit must be between 3 and 5"
    )


# ============================================================
# SERVICE INTERNAL ERROR
# ============================================================

@patch(
    "app.api.similar_periods.SimilarPeriodService"
)
def test_similar_periods_service_internal_error(
    mock_service_class,
):
    """
    Unexpected service errors should return HTTP 500.
    """

    service = MagicMock()

    service.find_similar_periods.side_effect = RuntimeError(
        "Unexpected database failure"
    )

    mock_service_class.return_value = service

    response = client.get(
        "/api/v1/regimes/history/similar-periods?limit=3"
    )

    assert response.status_code == 500

    data = response.json()

    assert data["detail"] == (
        "Failed to calculate similar "
        "historical periods"
    )