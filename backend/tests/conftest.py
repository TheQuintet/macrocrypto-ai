import sys
from pathlib import Path
import time
import pytest
import requests

# Add backend root directory to Python path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

# Add this fixture to prevent rate limit interference
@pytest.fixture(autouse=True)
def wait_for_rate_limit_reset():
    """
    Wait for rate limit to reset before each test.
    This prevents tests from interfering with each other.
    """
    # Small delay between tests to let rate limit window settle
    time.sleep(2)
    yield