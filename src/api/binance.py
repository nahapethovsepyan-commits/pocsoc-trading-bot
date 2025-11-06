"""
Binance API client.
"""

import pandas as pd
import logging
import aiohttp
from ..utils.helpers import is_successful_status
from ..config import CONFIG


async def fetch_from_binance(pair: str, session: aiohttp.ClientSession):
    """
    Fetch data from Binance API (EURUSD via USDT proxy).
    
    Args:
        pair: Currency pair (e.g., "EUR/USD")
        session: HTTP session
        
    Returns:
        Tuple of (DataFrame, source_name)
        
    Raises:
        ValueError: If API call fails or response is invalid
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": "EURUSDT", "interval": "1m", "limit": CONFIG["lookback_window"]}
    
    async with session.get(url, params=params, timeout=10) as resp:
        if not is_successful_status(resp.status):
            raise ValueError(f"Binance returned status {resp.status}")
        data = await resp.json()
        
        if not isinstance(data, list):
            raise ValueError("Invalid Binance response format")
        
        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ])
        df["time"] = pd.to_datetime(df["time"], unit='ms')
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df, "Binance"


