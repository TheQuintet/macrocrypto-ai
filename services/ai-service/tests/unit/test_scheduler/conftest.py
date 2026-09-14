"""Shared pytest fixtures for scheduler tests.

Ensures the scheduler is disabled by default so no test spawns
background jobs. Tests that need to exercise the scheduler
explicitly construct a manager with enabled=True.
"""

import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def disable_scheduler(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force settings.scheduler_enabled=False for every test.

    Individual tests can still create a SchedulerManager with
    enabled=True explicitly to override this behavior.
    """
    monkeypatch.setattr(settings, "scheduler_enabled", False)