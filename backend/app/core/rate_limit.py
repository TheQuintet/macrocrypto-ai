from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiting configuration for the BTC price endpoint.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[]
)