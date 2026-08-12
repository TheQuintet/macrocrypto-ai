"""
Service for calculating BTC performance during macroeconomic regimes.

The service calculates historical BTC performance for completed
macroeconomic regimes and stores the results in regime_performance.
"""

import logging
import math
from datetime import datetime, timezone

from app.models.btc_price import BTCPrice
from app.models.macro_regime import MacroRegime
from app.models.regime_performance import RegimePerformance

logger = logging.getLogger(__name__)


class RegimePerformanceService:
    """
    Calculates and stores BTC performance for macroeconomic regimes.
    """

    def __init__(self, db):
        self.db = db

    # --------------------------------------------------
    # PRICE DATA
    # --------------------------------------------------

    def get_regime_prices(
        self,
        regime: MacroRegime,
    ) -> list[BTCPrice]:
        """
        Retrieve BTC prices recorded during a regime.
        """

        start_datetime = datetime.combine(
            regime.start_date,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

        end_datetime = None

        if regime.end_date:
            end_datetime = datetime.combine(
                regime.end_date,
                datetime.max.time(),
                tzinfo=timezone.utc,
            )

        query = (
            self.db.query(BTCPrice)
            .filter(
                BTCPrice.time >= start_datetime
            )
        )

        if end_datetime:
            query = query.filter(
                BTCPrice.time <= end_datetime
            )

        return (
            query
            .order_by(BTCPrice.time.asc())
            .all()
        )

    # --------------------------------------------------
    # RETURN
    # --------------------------------------------------

    def calculate_return(
        self,
        prices: list[BTCPrice],
    ) -> float | None:
        """
        Calculate percentage return over the regime.
        """

        if len(prices) < 2:
            return None

        start_price = prices[0].price
        end_price = prices[-1].price

        if start_price is None or end_price is None:
            return None

        if start_price <= 0:
            return None

        return (
            (end_price - start_price)
            / start_price
        ) * 100

    # --------------------------------------------------
    # DRAWDOWN
    # --------------------------------------------------

    def calculate_max_drawdown(
        self,
        prices: list[BTCPrice],
    ) -> float | None:
        """
        Calculate maximum BTC drawdown during the regime.

        The result is expressed as a negative percentage.
        """

        if len(prices) < 2:
            return None

        peak = prices[0].price
        max_drawdown = 0.0

        for record in prices:
            price = record.price

            if price is None:
                continue

            if price > peak:
                peak = price

            if peak <= 0:
                continue

            drawdown = (
                (price - peak)
                / peak
            ) * 100

            if drawdown < max_drawdown:
                max_drawdown = drawdown

        return max_drawdown

    # --------------------------------------------------
    # VOLATILITY
    # --------------------------------------------------

    def calculate_volatility(
        self,
        prices: list[BTCPrice],
    ) -> float | None:
        """
        Calculate standard deviation of period-to-period
        BTC returns.

        Returns percentage volatility.
        """

        if len(prices) < 3:
            return None

        returns = []

        for previous, current in zip(
            prices,
            prices[1:],
        ):
            previous_price = previous.price
            current_price = current.price

            if (
                previous_price is None
                or current_price is None
                or previous_price <= 0
            ):
                continue

            daily_return = (
                (current_price - previous_price)
                / previous_price
            ) * 100

            returns.append(daily_return)

        if len(returns) < 2:
            return None

        mean_return = sum(returns) / len(returns)

        variance = sum(
            (value - mean_return) ** 2
            for value in returns
        ) / (len(returns) - 1)

        return math.sqrt(variance)

    # --------------------------------------------------
    # SHARPE RATIO
    # --------------------------------------------------

    def calculate_sharpe_ratio(
        self,
        prices: list[BTCPrice],
    ) -> float | None:
        """
        Calculate a simplified Sharpe ratio.

        A zero risk-free rate is used for the initial
        implementation.
        """

        if len(prices) < 3:
            return None

        returns = []

        for previous, current in zip(
            prices,
            prices[1:],
        ):
            previous_price = previous.price
            current_price = current.price

            if (
                previous_price is None
                or current_price is None
                or previous_price <= 0
            ):
                continue

            returns.append(
                (
                    (current_price - previous_price)
                    / previous_price
                ) * 100
            )

        if len(returns) < 2:
            return None

        mean_return = sum(returns) / len(returns)

        variance = sum(
            (value - mean_return) ** 2
            for value in returns
        ) / (len(returns) - 1)

        volatility = math.sqrt(variance)

        if volatility == 0:
            return None

        return mean_return / volatility

    # --------------------------------------------------
    # PERFORMANCE PERSISTENCE
    # --------------------------------------------------

    # def calculate_regime_performance(
    #     self,
    #     regime: MacroRegime,
    # ) -> RegimePerformance | None:
    #     """
    #     Calculate and store BTC performance for a regime.
    #     """

    #     prices = self.get_regime_prices(regime)

    #     if len(prices) < 2:
    #         logger.info(
    #             "Not enough BTC price data for regime %s",
    #             regime.id,
    #         )
    #         return None

    #     btc_price_start = prices[0].price
    #     btc_price_end = prices[-1].price

    #     performance = RegimePerformance(
    #         regime_id=regime.id,
    #         avg_return=self.calculate_return(prices),
    #         max_drawdown=self.calculate_max_drawdown(prices),
    #         volatility=self.calculate_volatility(prices),
    #         sharpe_ratio=self.calculate_sharpe_ratio(prices),
    #         btc_price_start=btc_price_start,
    #         btc_price_end=btc_price_end,
    #     )

    #     self.db.add(performance)
    #     self.db.commit()
    #     self.db.refresh(performance)

    #     logger.info(
    #         "Stored BTC performance for regime %s",
    #         regime.id,
    #     )

    #     return performance

    def calculate_regime_performance(
        self,
        regime: MacroRegime,
    ) -> RegimePerformance | None:
        """
        Calculate and store BTC performance for a regime.

        If performance has already been calculated for the regime,
        return the existing record instead of creating a duplicate.
        """

        existing = (
            self.db.query(RegimePerformance)
            .filter(
                RegimePerformance.regime_id == regime.id
            )
            .first()
        )

        if existing:
            logger.info(
                "Performance already exists for regime %s",
                regime.id,
            )
            return existing

        prices = self.get_regime_prices(regime)

        if len(prices) < 2:
            logger.info(
                "Not enough BTC price data for regime %s",
                regime.id,
            )
            return None

        btc_price_start = prices[0].price
        btc_price_end = prices[-1].price

        performance = RegimePerformance(
            regime_id=regime.id,
            avg_return=self.calculate_return(prices),
            max_drawdown=self.calculate_max_drawdown(prices),
            volatility=self.calculate_volatility(prices),
            sharpe_ratio=self.calculate_sharpe_ratio(prices),
            btc_price_start=btc_price_start,
            btc_price_end=btc_price_end,
        )

        self.db.add(performance)
        self.db.commit()
        self.db.refresh(performance)

        logger.info(
            "Stored BTC performance for regime %s",
            regime.id,
        )

        return performance

    # --------------------------------------------------
    # PROCESS COMPLETED REGIMES
    # --------------------------------------------------

    def process_completed_regimes(self):
        """
        Calculate performance for completed regimes.

        The currently active regime is intentionally excluded.
        """

        regimes = (
            self.db.query(MacroRegime)
            .filter(
                MacroRegime.end_date.isnot(None)
            )
            .order_by(
                MacroRegime.start_date.asc()
            )
            .all()
        )

        results = []

        for regime in regimes:

            existing = (
                self.db.query(RegimePerformance)
                .filter(
                    RegimePerformance.regime_id
                    == regime.id
                )
                .first()
            )

            if existing:
                continue

            performance = (
                self.calculate_regime_performance(
                    regime
                )
            )

            if performance:
                results.append(performance)

        return results

    # --------------------------------------------------
    # PROCESS CURRENT REGIME
    # --------------------------------------------------

    def process_current_regime(
        self,
        regime: MacroRegime,
    ):
        """
        Calculate performance for a regime when it becomes
        completed.

        This method is intended to be called immediately
        after a regime transition.
        """

        if regime.end_date is None:
            logger.info(
                "Regime %s is still active; "
                "performance calculation deferred",
                regime.id,
            )
            return None

        return self.calculate_regime_performance(
            regime
        )