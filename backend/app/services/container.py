"""
Service container.

Creates shared service instances used
throughout the application.

Services that maintain application state
should be instantiated here and reused.
"""


from app.services.price_service import PriceService


# Shared PriceService instance.
#
# Maintains:
# - Current BTC price
# - 24h market statistics
# - 7-day price calculations
#
# All components should access this same
# instance to keep market state consistent.
price_service = PriceService()