"""
Macro event analysis service.
"""

import logging
from datetime import date, datetime
import csv
import io

from sqlalchemy.orm import Session

from app.database.regime_event_repository import (
    RegimeEventRepository,
)
from app.database.regime_repository import (
    RegimeRepository,
)

logger = logging.getLogger(__name__)


SUPPORTED_EVENTS = {
    "fed_meeting",
    "cpi_release",
    "gdp_release",
    "employment_report",
}


class RegimeEventService:
    """
    Calculates BTC reactions to macroeconomic events.
    """

    def __init__(self, db: Session):
        self.db = db
        self.events = RegimeEventRepository(db)
        self.regimes = RegimeRepository(db)

    # ============================================================
    # VALIDATION
    # ============================================================

    @staticmethod
    def validate_event_type(
        event_type: str,
    ) -> None:
        """
        Validate supported macroeconomic event types.
        """

        if event_type not in SUPPORTED_EVENTS:
            raise ValueError(
                f"Unsupported event type: {event_type}"
            )

    # ============================================================
    # BTC REACTION
    # ============================================================

    @staticmethod
    def calculate_reaction(
        btc_price_before: float,
        btc_price_after: float,
    ) -> float:
        """
        Calculate BTC percentage return around an event.
        """

        if btc_price_before <= 0:
            raise ValueError(
                "BTC price before event must be greater than zero"
            )

        return (
            (
                btc_price_after
                - btc_price_before
            )
            / btc_price_before
        ) * 100

    # ============================================================
    # CREATE EVENT ANALYSIS
    # ============================================================

    def analyze_event(
        self,
        regime_id: int,
        event_type: str,
        event_date: date,
        btc_price_before: float,
        btc_price_after: float,
    ):
        """
        Calculate and persist BTC reaction to a macroeconomic event.
        """

        self.validate_event_type(event_type)

        btc_return = self.calculate_reaction(
            btc_price_before,
            btc_price_after,
        )

        return self.events.create_event_analysis(
            regime_id=regime_id,
            event_type=event_type,
            event_date=event_date,
            btc_price_before=btc_price_before,
            btc_price_after=btc_price_after,
            btc_return=btc_return,
        )

    # ============================================================
    # GET EVENT ANALYSIS
    # ============================================================

    def get_event_analysis(
        self,
        regime_id: int | None = None,
    ):
        """
        Retrieve persisted macro event analysis.

        If regime_id is provided, return events belonging
        to that regime.

        Otherwise return all event analysis records.
        """

        if regime_id is not None:
            return self.events.get_by_regime(
                regime_id
            )

        return self.events.get_all()

    def export_event_analysis_csv(
        self,
        event_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> str:
        """
        Export macro event analysis as CSV.

        Optional filters:
        - event_type
        - start_date
        - end_date
        """

        events = self.get_event_analysis(
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
        )

        output = io.StringIO()

        fieldnames = [
            "id",
            "regime_id",
            "event_type",
            "event_date",
            "btc_price_before",
            "btc_price_after",
            "btc_return",
            "created_at",
        ]

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for event in events:
            writer.writerow(
                {
                    "id": event.id,
                    "regime_id": event.regime_id,
                    "event_type": event.event_type,
                    "event_date": event.event_date,
                    "btc_price_before": event.btc_price_before,
                    "btc_price_after": event.btc_price_after,
                    "btc_return": event.btc_return,
                    "created_at": event.created_at,
                }
            )

        return output.getvalue()

    def process_current_regime_event(self, regime):
        """
        Create/update a QA macro event analysis for the active regime.
        """

        if regime is None:
            return None

        from app.models.btc_price import BTCPrice

        prices = (
            self.db.query(BTCPrice)
            .order_by(BTCPrice.time.desc())
            .limit(2)
            .all()
        )

        if len(prices) < 2:
            logger.info(
                "Not enough BTC price data for event analysis"
            )
            return None

        latest = prices[0]
        previous = prices[1]
        macro_regime = self.regimes.get_current_regime()

        if macro_regime is None:
            logger.warning(
                "No active macro regime found for event analysis"
            )
            return None

        return self.analyze_event(
            regime_id= macro_regime.id, 
            event_type="fed_meeting",
            event_date=latest.time.date(),
            btc_price_before=previous.price,
            btc_price_after=latest.price,
        )