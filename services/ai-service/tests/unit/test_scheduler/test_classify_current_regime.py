"""Unit tests for the classify_current_regime helper.

`classify_current_regime` is a Phase 4 helper in
`app/scheduler/jobs.py` that:

    1. Fetches the trailing `window_hours` of BTC prices from the
       shared `btc_prices` table via `PredictionRepository`.
    2. Runs `classify_market_condition_safe` on the `close` column.
    3. Returns one of 'bull', 'bear', 'volatile', 'neutral', or
       None.

The helper never raises — any failure (repository error, empty
frame, too few prices, non-positive prices) results in a None
return so the caller can fall back to the global champion.

Note on `None` results from the classifier itself:
    `classify_market_condition_safe` only returns None when the
    price series has a non-positive first value (which makes the
    cumulative return undefined). A flat series — same price
    repeated — classifies as 'neutral', not None. The tests below
    reflect that.

These tests mock the repository so no live DB is required. The
classifier itself is exercised with real inputs — it's a pure
function and its own test file covers its thresholds.

Test organization:
    - TestClassifyCurrentRegimeHappyPath: normal results
    - TestClassifyCurrentRegimeDefensive: failure modes that
      yield None
    - TestClassifyCurrentRegimeInvariants: window_hours passing,
      column extraction
"""

from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from app.scheduler.jobs import classify_current_regime


# ============================================================
# HELPERS
# ============================================================
def _make_btc_frame(prices: list) -> pd.DataFrame:
    """Build a minimal btc_prices-style DataFrame with a close column.

    The real repository returns more columns, but the helper only
    reads `close`, so a single-column frame is sufficient.
    """
    return pd.DataFrame({"close": prices})


def _make_repo_with_frame(prices: list) -> MagicMock:
    """Build a mocked PredictionRepository returning the given prices."""
    repo = MagicMock()
    repo.fetch_recent_btc_data = AsyncMock(
        return_value=_make_btc_frame(prices)
    )
    return repo


# ============================================================
# HAPPY PATH
# ============================================================
class TestClassifyCurrentRegimeHappyPath:
    """Tests for the normal, successful path."""

    @pytest.mark.asyncio
    async def test_returns_label_from_classifier(self) -> None:
        """A strong upward move should classify as 'bull'."""
        # 25 prices trending up strongly — well above the 20% bull
        # threshold from settings.market_bull_threshold_pct
        prices = [100.0 + i * 1.5 for i in range(25)]
        repo = _make_repo_with_frame(prices)

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert result == "bull"

    @pytest.mark.asyncio
    async def test_returns_bear_on_strong_downtrend(self) -> None:
        """A strong downward move should classify as 'bear'."""
        # 25 prices trending down strongly from 200 → ~64
        prices = [200.0 - i * 5.6 for i in range(25)]
        repo = _make_repo_with_frame(prices)

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert result == "bear"

    @pytest.mark.asyncio
    async def test_returns_neutral_on_flat_prices(self) -> None:
        """Flat prices (small change, low volatility) → neutral."""
        prices = [100.0, 100.5, 100.2, 100.4, 100.1, 100.3]
        repo = _make_repo_with_frame(prices)

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert result == "neutral"

    @pytest.mark.asyncio
    async def test_returns_volatile_on_choppy_prices(self) -> None:
        """Large swings regardless of direction → volatile."""
        # Alternating ±10% moves produce high std
        prices = [100.0, 110.0, 99.0, 108.9, 98.01, 107.8, 97.0]
        repo = _make_repo_with_frame(prices)

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert result == "volatile"

    @pytest.mark.asyncio
    async def test_flat_two_price_series_is_neutral(self) -> None:
        """A flat series classifies as 'neutral', not None.

        This pins the classifier's actual behavior: zero variance
        alone does not produce a None result — the series only
        becomes unclassifiable when the first price is
        non-positive or there are fewer than 2 prices.
        """
        repo = _make_repo_with_frame([100.0, 100.0])

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert result == "neutral"


# ============================================================
# DEFENSIVE PATHS — every failure returns None
# ============================================================
class TestClassifyCurrentRegimeDefensive:
    """Tests for the failure modes that must return None."""

    @pytest.mark.asyncio
    async def test_empty_dataframe_returns_none(self) -> None:
        """An empty frame → None (defensive)."""
        repo = MagicMock()
        repo.fetch_recent_btc_data = AsyncMock(return_value=pd.DataFrame())

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_none_returned_by_repository_returns_none(self) -> None:
        """A None frame (defensive) → None."""
        repo = MagicMock()
        repo.fetch_recent_btc_data = AsyncMock(return_value=None)

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_single_price_returns_none(self) -> None:
        """One price is not enough — the classifier needs at least 2."""
        repo = _make_repo_with_frame([50000.0])

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_zero_prices_returns_none(self) -> None:
        """Empty close column → None."""
        repo = _make_repo_with_frame([])

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_repository_exception_returns_none(self) -> None:
        """A repository exception is swallowed and None is returned."""
        repo = MagicMock()
        repo.fetch_recent_btc_data = AsyncMock(
            side_effect=RuntimeError("DB connection lost")
        )

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_socket_error_returns_none(self) -> None:
        """Network errors (DNS, connection refused) are swallowed."""
        import socket

        repo = MagicMock()
        repo.fetch_recent_btc_data = AsyncMock(
            side_effect=socket.gaierror("Name or service not known")
        )

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_non_positive_prices_return_none(self) -> None:
        """Negative or zero first price → None.

        This is the only path where `classify_market_condition_safe`
        returns None from a non-trivial input: `cumulative_return_pct`
        cannot be computed when the first price is <= 0.
        """
        repo = _make_repo_with_frame([0.0, 100.0, 200.0])

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert result is None


# ============================================================
# INVARIANTS
# ============================================================
class TestClassifyCurrentRegimeInvariants:
    """Invariants about how the helper calls the repository."""

    @pytest.mark.asyncio
    async def test_passes_window_hours_to_fetch(self) -> None:
        """The `window_hours` argument is forwarded verbatim."""
        repo = _make_repo_with_frame([100.0, 110.0, 120.0])

        await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        kwargs = repo.fetch_recent_btc_data.call_args.kwargs
        assert kwargs["hours"] == 24

    @pytest.mark.asyncio
    async def test_passes_168_window_for_7d(self) -> None:
        """The 7d window (168h) is forwarded correctly."""
        repo = _make_repo_with_frame([100.0, 110.0, 120.0])

        await classify_current_regime(
            prediction_repo=repo, window_hours=168
        )

        kwargs = repo.fetch_recent_btc_data.call_args.kwargs
        assert kwargs["hours"] == 168

    @pytest.mark.asyncio
    async def test_uses_close_column(self) -> None:
        """The helper extracts the `close` column, not others."""
        # Include a decoy column that should be ignored
        df = pd.DataFrame(
            {
                "close": [100.0 + i * 2.0 for i in range(25)],
                "volume": [999.0] * 25,
            }
        )
        repo = MagicMock()
        repo.fetch_recent_btc_data = AsyncMock(return_value=df)

        result = await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        # If the helper used `volume`, the classifier would see a
        # constant series (zero variance) and return 'neutral'.
        # The `close` column trends up, so we expect 'bull'.
        assert result == "bull"

    @pytest.mark.asyncio
    async def test_does_not_mutate_the_frame(self) -> None:
        """The helper treats the returned frame as read-only."""
        df = pd.DataFrame({"close": [100.0 + i for i in range(10)]})
        original = df.copy()
        repo = MagicMock()
        repo.fetch_recent_btc_data = AsyncMock(return_value=df)

        await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        pd.testing.assert_frame_equal(df, original)

    @pytest.mark.asyncio
    async def test_calls_repository_exactly_once(self) -> None:
        """Only one fetch per invocation — no retries inside the helper."""
        repo = _make_repo_with_frame([100.0, 105.0, 110.0])

        await classify_current_regime(
            prediction_repo=repo, window_hours=24
        )

        assert repo.fetch_recent_btc_data.call_count == 1