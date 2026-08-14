"""
Service for calculating BTC performance during macroeconomic regimes.

The service calculates BTC performance for macroeconomic regimes
and stores the results in regime_performance.

BTC price data is read from the existing BTCPrice table.
"""

import csv
import io
import logging
import math
from datetime import datetime, timedelta, timezone

from app.models.btc_price import BTCPrice
from app.models.macro_regime import MacroRegime
from app.models.regime_performance import RegimePerformance

logger = logging.getLogger(__name__)


class RegimePerformanceService:
    """
    Calculates and stores BTC performance for macroeconomic regimes.
    """

    SUPPORTED_TIMEFRAMES = {
        "30d": 30,
        "90d": 90,
        "1y": 365,
        "5y": 1825,
    }

    def __init__(self, db):
        self.db = db

    # --------------------------------------------------
    # PRICE DATA
    # --------------------------------------------------

    def get_regime_prices(
        self,
        regime: MacroRegime,
        timeframe: str | None = None,
    ) -> list[BTCPrice]:
        """
        Retrieve BTC prices recorded during a regime.

        If timeframe is provided, only prices within that
        timeframe from the end of the regime are returned.
        """

        if (
            timeframe is not None
            and timeframe not in self.SUPPORTED_TIMEFRAMES
        ):
            raise ValueError(
                f"Unsupported timeframe: {timeframe}. "
                f"Supported timeframes: "
                f"{', '.join(self.SUPPORTED_TIMEFRAMES)}"
            )

        start_datetime = datetime.combine(
            regime.start_date,
            datetime.min.time(),
            tzinfo=timezone.utc,
        )

        if regime.end_date:
            end_datetime = datetime.combine(
                regime.end_date,
                datetime.max.time(),
                tzinfo=timezone.utc,
            )
        else:
            end_datetime = datetime.now(timezone.utc)

        if timeframe is not None:
            timeframe_days = self.SUPPORTED_TIMEFRAMES[timeframe]

            timeframe_start = (
                end_datetime
                - timedelta(days=timeframe_days)
            )

            if timeframe_start > start_datetime:
                start_datetime = timeframe_start

        query = (
            self.db.query(BTCPrice)
            .filter(
                BTCPrice.time >= start_datetime,
                BTCPrice.time <= end_datetime,
            )
            .order_by(BTCPrice.time.asc())
        )

        return query.all()

    # --------------------------------------------------
    # AVERAGE RETURN
    # --------------------------------------------------

    def calculate_return(
        self,
        prices: list[BTCPrice],
    ) -> float | None:
        """
        Calculate the arithmetic mean of period-to-period
        BTC percentage returns.
        """

        if len(prices) < 2:
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
                or current_price <= 0
            ):
                continue

            period_return = (
                (current_price - previous_price)
                / previous_price
            ) * 100

            returns.append(period_return)

        if not returns:
            return None

        return sum(returns) / len(returns)

    # --------------------------------------------------
    # DRAWDOWN
    # --------------------------------------------------

    def calculate_max_drawdown(
        self,
        prices: list[BTCPrice],
    ) -> float | None:
        """
        Calculate maximum BTC drawdown during the supplied period.

        The result is expressed as a negative percentage.
        """

        if len(prices) < 2:
            return None

        valid_prices = [
            record.price
            for record in prices
            if record.price is not None
            and record.price > 0
        ]

        if len(valid_prices) < 2:
            return None

        peak = valid_prices[0]
        max_drawdown = 0.0

        for price in valid_prices:
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
        Calculate sample standard deviation of BTC returns.
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
                or current_price is None
            ):
                continue

            period_return = (
                (current_price - previous_price)
                / previous_price
            ) * 100

            returns.append(period_return)

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
                or current_price is None
            ):
                continue

            period_return = (
                (current_price - previous_price)
                / previous_price
            ) * 100

            returns.append(period_return)

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
    # CALCULATE METRICS
    # --------------------------------------------------

    def calculate_metrics(
        self,
        prices: list[BTCPrice],
    ) -> dict:
        """
        Calculate all BTC performance metrics for a price period.
        """

        if len(prices) < 2:
            return {
                "avg_return": None,
                "max_drawdown": None,
                "volatility": None,
                "sharpe_ratio": None,
                "btc_price_start": None,
                "btc_price_end": None,
            }

        return {
            "avg_return": self.calculate_return(prices),
            "max_drawdown": self.calculate_max_drawdown(prices),
            "volatility": self.calculate_volatility(prices),
            "sharpe_ratio": self.calculate_sharpe_ratio(prices),
            "btc_price_start": prices[0].price,
            "btc_price_end": prices[-1].price,
        }

    # --------------------------------------------------
    # TIMEFRAME METRICS
    # --------------------------------------------------

    def calculate_regime_metrics(
        self,
        regime: MacroRegime,
        timeframe: str,
    ) -> dict:
        """
        Calculate BTC performance metrics for a specific timeframe.
        """

        if timeframe not in self.SUPPORTED_TIMEFRAMES:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}. "
                f"Supported timeframes: "
                f"{', '.join(self.SUPPORTED_TIMEFRAMES)}"
            )

        prices = self.get_regime_prices(
            regime,
            timeframe=timeframe,
        )

        metrics = self.calculate_metrics(prices)

        return {
            "regime_id": regime.id,
            "regime_type": regime.regime_type,
            "timeframe": timeframe,
            "price_records": len(prices),
            **metrics,
        }

    def calculate_all_timeframes(
        self,
        regime: MacroRegime,
    ) -> dict[str, dict]:
        """
        Calculate metrics for all supported timeframes.
        """

        return {
            timeframe: self.calculate_regime_metrics(
                regime,
                timeframe,
            )
            for timeframe in self.SUPPORTED_TIMEFRAMES
        }

    # --------------------------------------------------
    # PERFORMANCE PERSISTENCE
    # --------------------------------------------------

    def calculate_regime_performance(
        self,
        regime: MacroRegime,
    ) -> RegimePerformance | None:
        """
        Calculate and persist BTC performance for a regime.

        If a performance record already exists, it is updated
        with the latest available BTC price data.

        This works for both active and completed regimes.
        """

        prices = self.get_regime_prices(regime)

        if len(prices) < 2:
            logger.info(
                "Not enough BTC price data for regime %s",
                regime.id,
            )
            return None

        metrics = self.calculate_metrics(prices)

        existing = (
            self.db.query(RegimePerformance)
            .filter(
                RegimePerformance.regime_id == regime.id
            )
            .order_by(
                RegimePerformance.created_at.desc()
            )
            .first()
        )

        if existing:
            existing.avg_return = metrics["avg_return"]
            existing.max_drawdown = metrics["max_drawdown"]
            existing.volatility = metrics["volatility"]
            existing.sharpe_ratio = metrics["sharpe_ratio"]
            existing.btc_price_start = metrics["btc_price_start"]
            existing.btc_price_end = metrics["btc_price_end"]

            self.db.commit()
            self.db.refresh(existing)

            logger.info(
                "Updated BTC performance for regime %s",
                regime.id,
            )

            return existing

        performance = RegimePerformance(
            regime_id=regime.id,
            avg_return=metrics["avg_return"],
            max_drawdown=metrics["max_drawdown"],
            volatility=metrics["volatility"],
            sharpe_ratio=metrics["sharpe_ratio"],
            btc_price_start=metrics["btc_price_start"],
            btc_price_end=metrics["btc_price_end"],
            created_at=datetime.now(timezone.utc),
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
        Calculate and persist performance for completed regimes.
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
            performance = (
                self.calculate_regime_performance(
                    regime
                )
            )

            if performance:
                results.append(performance)

        logger.info(
            "Processed %s completed regime performance records",
            len(results),
        )

        return results

    # --------------------------------------------------
    # PROCESS CURRENT REGIME
    # --------------------------------------------------

    def process_current_regime(
        self,
        regime: MacroRegime,
    ):
        """
        Calculate and persist performance for the current regime.

        Active regimes are now persisted and updated on each
        scheduler execution.
        """

        if regime is None:
            logger.warning(
                "No regime supplied for performance calculation"
            )
            return None

        logger.info(
            "Calculating BTC performance for active regime %s",
            regime.id,
        )

        return self.calculate_regime_performance(
            regime
        )

    # --------------------------------------------------
    # PROCESS ACTIVE REGIME
    # --------------------------------------------------

    def process_active_regime(self):
        """
        Find the currently active regime and persist its
        latest BTC performance.

        Returns:
            RegimePerformance | None
        """

        regime = (
            self.db.query(MacroRegime)
            .filter(
                MacroRegime.end_date.is_(None)
            )
            .order_by(
                MacroRegime.start_date.desc()
            )
            .first()
        )

        if regime is None:
            logger.info(
                "No active macroeconomic regime found"
            )
            return None

        return self.process_current_regime(
            regime
        )

    # --------------------------------------------------
    # PROCESS ALL REGIMES
    # --------------------------------------------------

    def process_all_regimes(self):
        """
        Process both completed and active regimes.

        Completed regimes are persisted and the active regime
        is inserted or updated with the latest BTC performance.
        """

        results = []

        completed = self.process_completed_regimes()
        results.extend(completed)

        active = self.process_active_regime()

        if active:
            results.append(active)

        logger.info(
            "Processed total of %s regime performance records",
            len(results),
        )

        return results

    # --------------------------------------------------
    # ACTIVE REGIME PERFORMANCE
    # --------------------------------------------------

    def get_active_regime_performance(self):
        """
        Calculate BTC performance for the currently active regime.

        This method also persists the calculated performance.
        """

        regime = (
            self.db.query(MacroRegime)
            .filter(
                MacroRegime.end_date.is_(None)
            )
            .order_by(
                MacroRegime.start_date.desc()
            )
            .first()
        )

        if regime is None:
            logger.info(
                "No active regime found"
            )
            return None

        performance = (
            self.calculate_regime_performance(
                regime
            )
        )

        if performance is None:
            return None

        return {
            "regime_id": regime.id,
            "regime_type": regime.regime_type,
            "start_date": regime.start_date,
            "end_date": regime.end_date,
            "avg_return": performance.avg_return,
            "max_drawdown": performance.max_drawdown,
            "volatility": performance.volatility,
            "sharpe_ratio": performance.sharpe_ratio,
            "btc_price_start": performance.btc_price_start,
            "btc_price_end": performance.btc_price_end,
        }

    # --------------------------------------------------
    # CSV EXPORT
    # --------------------------------------------------

    def export_regime_performance_csv(
        self,
        regimes: list[MacroRegime] | None = None,
    ) -> str:
        """
        Export regime performance metrics as CSV.

        If regimes are not supplied, all regimes with stored
        performance records are exported.
        """

        if regimes is None:
            regimes = (
                self.db.query(MacroRegime)
                .join(
                    RegimePerformance,
                    RegimePerformance.regime_id
                    == MacroRegime.id,
                )
                .order_by(
                    MacroRegime.start_date.asc()
                )
                .all()
            )

        output = io.StringIO()

        fieldnames = [
            "regime_id",
            "regime_type",
            "start_date",
            "end_date",
            "avg_return",
            "max_drawdown",
            "volatility",
            "sharpe_ratio",
            "btc_price_start",
            "btc_price_end",
        ]

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for regime in regimes:
            performance = (
                self.db.query(RegimePerformance)
                .filter(
                    RegimePerformance.regime_id
                    == regime.id,
                )
                .order_by(
                    RegimePerformance.created_at.desc()
                )
                .first()
            )

            if performance is None:
                continue

            writer.writerow(
                {
                    "regime_id": regime.id,
                    "regime_type": regime.regime_type,
                    "start_date": regime.start_date,
                    "end_date": regime.end_date,
                    "avg_return": performance.avg_return,
                    "max_drawdown": performance.max_drawdown,
                    "volatility": performance.volatility,
                    "sharpe_ratio": performance.sharpe_ratio,
                    "btc_price_start": performance.btc_price_start,
                    "btc_price_end": performance.btc_price_end,
                }
            )

        return output.getvalue()