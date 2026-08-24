from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.models.economic_event import EconomicEvent
from app.database.session import SessionLocal


client = TestClient(app)


def create_test_events():
    """
    Insert sample economic events for API testing.
    """

    db = SessionLocal()

    try:
        events = [
            EconomicEvent(
                event_name="Consumer Price Index",
                event_type="cpi",
                event_date=datetime(
                    2026,
                    9,
                    10,
                    tzinfo=timezone.utc,
                ),
                impact_level="high",
                description=(
                    "CPI measures inflation "
                    "and impacts Bitcoin markets."
                ),
            ),
            EconomicEvent(
                event_name="Employment Report",
                event_type="employment",
                event_date=datetime(
                    2026,
                    9,
                    5,
                    tzinfo=timezone.utc,
                ),
                impact_level="medium",
                description=(
                    "Employment data affects "
                    "Federal Reserve expectations."
                ),
            ),
            EconomicEvent(
                event_name="Federal Reserve Decision",
                event_type="fed",
                event_date=datetime(
                    2026,
                    9,
                    16,
                    tzinfo=timezone.utc,
                ),
                impact_level="high",
                description=(
                    "Fed decisions influence "
                    "rates and Bitcoin liquidity."
                ),
            ),
            EconomicEvent(
                event_name="GDP Release",
                event_type="gdp",
                event_date=datetime(
                    2026,
                    9,
                    25,
                    tzinfo=timezone.utc,
                ),
                impact_level="high",
                description=(
                    "GDP measures economic growth."
                ),
            ),
        ]

        db.add_all(events)
        db.commit()

    finally:
        db.close()


def cleanup_events():
    """
    Remove test events.
    """

    db = SessionLocal()

    try:
        db.query(EconomicEvent).delete()
        db.commit()

    finally:
        db.close()


def setup_function():
    cleanup_events()
    create_test_events()


def teardown_function():
    cleanup_events()


def test_get_all_economic_calendar_events():
    response = client.get(
        "/api/v1/economic-calendar"
    )

    assert response.status_code == 200

    data = response.json()

    assert "events" in data
    assert data["count"] == 4

    names = [
        event["event_name"]
        for event in data["events"]
    ]

    assert "Consumer Price Index" in names
    assert "Federal Reserve Decision" in names


def test_filter_by_event_type_cpi():

    response = client.get(
        "/api/v1/economic-calendar",
        params={
            "event_type": "cpi"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 1

    event = data["events"][0]

    assert event["event_type"] == "cpi"


def test_filter_by_impact_level():

    response = client.get(
        "/api/v1/economic-calendar",
        params={
            "impact_level": "high"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 3

    for event in data["events"]:
        assert event["impact_level"] == "high"


def test_filter_by_event_type_and_impact():

    response = client.get(
        "/api/v1/economic-calendar",
        params={
            "event_type": "fed",
            "impact_level": "high",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 1

    event = data["events"][0]

    assert event["event_type"] == "fed"
    assert event["impact_level"] == "high"


def test_timezone_conversion_addis_ababa():

    response = client.get(
        "/api/v1/economic-calendar",
        params={
            "timezone": "Africa/Addis_Ababa"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 4

    event = data["events"][0]

    assert "event_date" in event

    # UTC midnight becomes 03:00 Addis time
    assert event["event_date"].endswith(
        "+03:00"
    )


def test_timezone_conversion_new_york():

    response = client.get(
        "/api/v1/economic-calendar",
        params={
            "timezone": "America/New_York"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 4

    event = data["events"][0]

    assert "event_date" in event

    assert (
        event["event_date"].endswith("-04:00")
        or event["event_date"].endswith("-05:00")
    )


def test_invalid_timezone_returns_error():

    response = client.get(
        "/api/v1/economic-calendar",
        params={
            "timezone": "Invalid/Timezone"
        },
    )

    assert response.status_code in [
        400,
        422,
    ]