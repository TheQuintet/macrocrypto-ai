from datetime import timezone
import pytest

# Replace 'app.services.price_service' with the actual path 
# where your PriceSnapshot and class are defined.
from app.services.price_service import PriceSnapshot, PriceService

def test_price_snapshot_timezone_is_utc():
    """
    QA Test: Verifies that the PriceSnapshot initialization creates a 
    timezone-aware datetime object specifically set to UTC (Python 3.13 standard).
    """
    # 1. Arrange: Initialize the class that sets up self.snapshot
    service_instance = PriceService()
    
    # 2. Act: Extract the initialized snapshot and its timestamp
    snapshot = service_instance.snapshot
    timestamp = snapshot.updated_at
    
    # 3. Assert: Verify the timestamp is timezone-aware and matches UTC [1]
    assert timestamp.tzinfo is not None, (
        "CRITICAL QA FAIL: 'updated_at' is a naive datetime object. "
        "It lacks timezone information and will cause database syncing bugs!"
    )
    
    assert timestamp.tzinfo == timezone.utc, (
        f"QA FAIL: Expected timezone to be UTC, but got {timestamp.tzinfo} instead."
    )

