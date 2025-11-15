"""
API clients for forex data sources.
"""

from .twelvedata import fetch_from_twelvedata
from .alphavantage import fetch_from_alphavantage
from .fetcher import fetch_forex_data, fetch_forex_data_parallel

__all__ = [
    'fetch_from_twelvedata',
    'fetch_from_alphavantage',
    'fetch_forex_data',
    'fetch_forex_data_parallel',
]


