import pytest

from unittest.mock import AsyncMock, patch

from app.services.scheduler import wait_until_next_run


@pytest.mark.asyncio
async def test_wait_until_next_run():
    """
    Verify scheduler calculates next execution
    time and sleeps.
    """

    with patch(
        "app.services.scheduler.asyncio.sleep",
        new=AsyncMock(),
    ) as mock_sleep:

        await wait_until_next_run(
            hour=1,
            minute=0,
        )


    mock_sleep.assert_called_once()