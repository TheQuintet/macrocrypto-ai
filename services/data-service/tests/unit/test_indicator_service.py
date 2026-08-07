import pytest
from unittest.mock import MagicMock

from app.services.indicator_service import IndicatorService



def create_service():
    """
    Create an IndicatorService instance using
    a mocked database session for unit testing.
    """

    return IndicatorService(
        MagicMock()
    )



def test_percentage_change_calculation():
    """
    Verify that percentage change is calculated
    correctly when current and previous values exist.
    """

    service = create_service()

    result = service.calculate_change_percent(
        110,
        100
    )

    assert result == 10



def test_percentage_change_missing_previous():
    """
    Verify that percentage change returns None
    when no previous value exists.
    """

    service = create_service()

    result = service.calculate_change_percent(
        100,
        None
    )

    assert result is None



def test_percentage_change_previous_zero():
    """
    Verify that division by zero is handled safely
    when the previous value is zero.
    """

    service = create_service()

    result = service.calculate_change_percent(
        100,
        0
    )

    assert result is None



def test_parse_fred_observations():
    """
    Verify that FRED observations are correctly
    converted into database-ready records including
    previous values and percentage changes.
    """

    service = create_service()

    response = {
        "observations": [
            {
                "date": "2026-01-01",
                "value": "100"
            },
            {
                "date": "2025-12-01",
                "value": "90"
            }
        ]
    }

    result = service.parse_observations(
        "cpi",
        response
    )

    assert len(result) == 2

    assert result[0]["indicator_name"] == "cpi"

    assert result[0]["value"] == 100

    assert result[0]["previous_value"] == 90



def test_parse_invalid_fred_value():
    """
    Verify that invalid FRED values represented
    by '.' are ignored during parsing.
    """

    service = create_service()

    response = {
        "observations": [
            {
                "date": "2026-01-01",
                "value": "."
            }
        ]
    }

    result = service.parse_observations(
        "cpi",
        response
    )

    assert result == []