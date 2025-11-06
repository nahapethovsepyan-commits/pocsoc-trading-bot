"""
Alpha Vantage API client.
"""

import pandas as pd
import logging
import aiohttp
from ..utils.helpers import is_successful_status
from ..config import get_api_keys


async def fetch_from_alphavantage(pair: str, session: aiohttp.ClientSession):
    """
    Fetch data from Alpha Vantage API.
    
    Args:
        pair: Currency pair (e.g., "EUR/USD")
        session: HTTP session
        
    Returns:
        Tuple of (DataFrame, source_name)
        
    Raises:
        ValueError: If API call fails or response is invalid
    """
    _, ALPHA_VANTAGE_KEY = get_api_keys()
    if not ALPHA_VANTAGE_KEY:
        raise ValueError("Alpha Vantage API key not configured")
    
    base, quote = pair.split("/")
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "FX_INTRADAY",
        "from_symbol": base,
        "to_symbol": quote,
        "interval": "1min",
        "apikey": ALPHA_VANTAGE_KEY
    }
    
    async with session.get(url, params=params, timeout=10) as resp:
        if not is_successful_status(resp.status):
            raise ValueError(f"Alpha Vantage returned status {resp.status}")
        data = await resp.json()
        
        if isinstance(data, dict):
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
            if "Note" in data:
                raise ValueError(f"Alpha Vantage rate limit: {data['Note']}")
        
        if "Time Series FX (1min)" not in data:
            raise ValueError("Invalid Alpha Vantage response format")
        
        raw = data["Time Series FX (1min)"]
        if not raw:
            raise ValueError("Alpha Vantage returned empty time series")
        
        df = pd.DataFrame([
            {
                "time": k,
                "open": float(v["1. open"]),
                "high": float(v["2. high"]),
                "low": float(v["3. low"]),
                "close": float(v["4. close"]),
            }
            for k, v in raw.items()
        ])
        df = df.sort_values("time")
        return df, "Alpha Vantage"


