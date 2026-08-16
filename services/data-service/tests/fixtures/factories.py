# Path: services/data-service/tests/fixtures/factories.py
# tests/fixtures/factories.py (minimal)
# Factory functions for creating test data

from datetime import datetime, timezone
from app.models.price_snapshot import PriceSnapshot


def create_price_snapshot(
    current_price: float = 45000.0,
    **kwargs
) -> PriceSnapshot:
    """Create a PriceSnapshot with optional overrides."""
    return PriceSnapshot(
        current_price=current_price,
        change_24h=kwargs.get("change_24h", 1000.0),
        change_24h_percent=kwargs.get("change_24h_percent", 2.27),
        high_24h=kwargs.get("high_24h", 46000.0),
        low_24h=kwargs.get("low_24h", 44000.0),
        volume_24h=kwargs.get("volume_24h", 1000.0),
        change_7d=kwargs.get("change_7d", 2000.0),
        change_7d_percent=kwargs.get("change_7d_percent", 4.65),
        updated_at=kwargs.get("updated_at", datetime.now(timezone.utc))
    )