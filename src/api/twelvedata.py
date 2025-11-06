"""
Twelve Data API client.
"""

import pandas as pd
import logging
import aiohttp
from ..utils.helpers import is_successful_status
from ..config import CONFIG, get_api_keys


async def fetch_from_twelvedata(pair: str, session: aiohttp.ClientSession):
    """
    Fetch data from Twelve Data API.
    
    Args:
        pair: Currency pair (e.g., "EUR/USD")
        session: HTTP session
        
    Returns:
        Tuple of (DataFrame, source_name)
        
    Raises:
        ValueError: If API call fails or response is invalid
    """
    TWELVE_DATA_KEY, _ = get_api_keys()
    if not TWELVE_DATA_KEY:
        raise ValueError("Twelve Data API key not configured")
    
    base, quote = pair.split("/")
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": f"{base}/{quote}",
        "interval": "1min",
        "outputsize": CONFIG["lookback_window"],
        "apikey": TWELVE_DATA_KEY
    }
    
    async with session.get(url, params=params, timeout=10) as resp:
        if not is_successful_status(resp.status):
            raise ValueError(f"Twelve Data returned status {resp.status}")
        data = await resp.json()
        
        if isinstance(data, dict):
            if "code" in data and data.get("code") != 200:
                raise ValueError(f"Twelve Data error: {data.get('message', 'Unknown')}")
        
        if "values" not in data:
            raise ValueError("Invalid Twelve Data response format")
        
        df = pd.DataFrame(data["values"])
        df = df.rename(columns={"datetime": "time"})
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df[::-1]  # Reverse to chronological order
        return df, "Twelve Data"


