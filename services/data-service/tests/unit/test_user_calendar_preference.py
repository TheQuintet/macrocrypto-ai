import pytest
from pydantic import ValidationError

from app.schemas.economic_event import (
    UserCalendarPreferenceCreate,
)


def test_valid_timezone():
    preference = UserCalendarPreferenceCreate(
        user_id=1,
        timezone="Africa/Addis_Ababa",
    )

    assert preference.timezone == "Africa/Addis_Ababa"


def test_default_timezone_is_utc():
    preference = UserCalendarPreferenceCreate(
        user_id=1,
    )

    assert preference.timezone == "UTC"


def test_invalid_timezone():
    with pytest.raises(ValidationError):
        UserCalendarPreferenceCreate(
            user_id=1,
            timezone="Not/ARealTimezone",
        )


def test_user_id_must_be_positive():
    with pytest.raises(ValidationError):
        UserCalendarPreferenceCreate(
            user_id=0,
            timezone="UTC",
        )