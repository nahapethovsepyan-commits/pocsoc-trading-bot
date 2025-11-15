"""
Main forex data fetcher with caching and retry logic.
"""

import asyncio
import logging
import aiohttp
import pandas as pd
from datetime import datetime
from typing import Optional, Tuple
from ..utils.http_session import get_http_session
from ..utils.helpers import is_successful_status
from ..utils.symbols import normalize_symbol, symbol_to_pair
from ..config import CONFIG, get_api_keys
from ..models.state import API_CACHE, CACHE_MAX_SIZE, cache_lock, METRICS, metrics_lock
from .twelvedata import fetch_from_twelvedata
from .alphavantage import fetch_from_alphavantage


async def fetch_forex_data_parallel(pair: str = "EUR/USD") -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Fetch forex data from multiple APIs in PARALLEL (race condition).
    
    Tries all available APIs simultaneously and returns the first successful response.
    This significantly reduces latency compared to sequential fallback.
    
    Args:
        pair: Currency pair (e.g., "EUR/USD")
        
    Returns:
        Tuple of (DataFrame, source_name) or (None, None) if all APIs fail
    """
    session = await get_http_session()
    tasks = []
    TWELVE_DATA_KEY, ALPHA_VANTAGE_KEY = get_api_keys()
    
    # Create tasks for all available APIs
    if TWELVE_DATA_KEY:
        tasks.append(("Twelve Data", fetch_from_twelvedata(pair, session)))
    if ALPHA_VANTAGE_KEY:
        tasks.append(("Alpha Vantage", fetch_from_alphavantage(pair, session)))
    
    if not tasks:
        logging.error("No API keys configured. Please set TWELVE_DATA_API_KEY or ALPHA_VANTAGE_KEY in .env")
        return None, None
    
    # Race all APIs - return first successful response
    for coro in asyncio.as_completed([task[1] for task in tasks]):
        try:
            result = await coro
            logging.info(f"✓ Parallel API fetch succeeded: {result[1]}")
            return result
        except Exception as e:
            logging.debug(f"API attempt failed: {e}")
            continue
    
    # All APIs failed
    return None, None


async def fetch_forex_data(symbol: str = "EURUSD", max_retries: int = 3) -> Optional[pd.DataFrame]:
    """
    Получение котировок с поддержкой символов (EURUSD, XAUUSD) из доступных источников с retry логикой и кешированием.
    
    Args:
        symbol: Торговый символ (EURUSD, XAUUSD). По умолчанию "EURUSD".
        max_retries: Максимальное количество попыток при ошибке.
        
    Returns:
        DataFrame с колонками ['time', 'open', 'high', 'low', 'close', 'volume']
        или None если все источники недоступны.
    """
    # Normalize symbol
    try:
        normalized_symbol = normalize_symbol(symbol)
        pair = symbol_to_pair(normalized_symbol)
    except ValueError as e:
        logging.error(f"Invalid symbol: {symbol} - {e}")
        return None
    
    # Import here to avoid circular dependency
    from ..indicators import get_adaptive_cache_duration
    
    start_time = datetime.now()
    TWELVE_DATA_KEY, ALPHA_VANTAGE_KEY = get_api_keys()
    
    # Check cache with adaptive duration (use normalized symbol in cache key)
    cache_key = f"forex_data:{normalized_symbol}"
    async with cache_lock:
        lookup_key = cache_key
        if lookup_key not in API_CACHE:
            legacy_keys = [
                f"{pair}_twelvedata",
                f"{pair}_alphavantage",
            ]
            for legacy_key in legacy_keys:
                if legacy_key in API_CACHE:
                    lookup_key = legacy_key
                    break

        if lookup_key in API_CACHE:
            cached_entry = API_CACHE[lookup_key]
            cached_time = datetime.now()
            cached_data = None
            cached_atr = None
            cached_price = None

            if isinstance(cached_entry, tuple):
                cached_time = cached_entry[0]
                cached_data = cached_entry[1]
                cached_atr = cached_entry[2] if len(cached_entry) > 2 else None
                cached_price = cached_entry[3] if len(cached_entry) > 3 else None
            elif isinstance(cached_entry, dict):
                cached_time = cached_entry.get("timestamp", datetime.now())
                cached_data = cached_entry.get("data")
                cached_atr = cached_entry.get("atr")
                cached_price = cached_entry.get("price") or cached_entry.get("close")
            
            age = (datetime.now() - cached_time).total_seconds()
            
            # Determine adaptive cache duration based on last ATR
            if cached_atr and cached_price:
                adaptive_duration = get_adaptive_cache_duration(cached_atr, cached_price)
            else:
                adaptive_duration = CONFIG["cache_duration_seconds"]
            
            if cached_data is not None and age < adaptive_duration:
                logging.debug(f"Using cached data for {normalized_symbol} (age: {age:.1f}s, max: {adaptive_duration}s)")
                async with metrics_lock:
                    METRICS["api_cache_hits"] += 1
                return cached_data.copy()
    
    async with metrics_lock:
        METRICS["api_cache_misses"] += 1
    
    for attempt in range(max_retries):
        try:
            # PARALLEL API FALLBACK
            if CONFIG["api_source"] == "auto":
                df, api_source = await fetch_forex_data_parallel(pair)
                if df is None:
                    raise ValueError("All parallel API attempts failed")
                logging.info(f"Parallel API winner: {api_source}")
            
            # SEQUENTIAL MODE
            else:
                base, quote = pair.split("/")
                url, params = None, None
                df = None
                api_source = CONFIG["api_source"]
                session = await get_http_session()

                # Twelve Data
                if CONFIG["api_source"] == "twelvedata" and TWELVE_DATA_KEY:
                    url = "https://api.twelvedata.com/time_series"
                    params = {
                        "symbol": f"{base}/{quote}",
                        "interval": "1min",
                        "outputsize": CONFIG["lookback_window"],
                        "apikey": TWELVE_DATA_KEY
                    }

                # Alpha Vantage
                elif CONFIG["api_source"] == "alphavantage" and ALPHA_VANTAGE_KEY:
                    url = "https://www.alphavantage.co/query"
                    params = {
                        "function": "FX_INTRADAY",
                        "from_symbol": base,
                        "to_symbol": quote,
                        "interval": "1min",
                        "apikey": ALPHA_VANTAGE_KEY
                    }
                else:
                    raise ValueError(f"No valid API source configured. Please set TWELVE_DATA_API_KEY or ALPHA_VANTAGE_KEY in .env")

                async with session.get(url, params=params, timeout=10) as resp:
                    if not is_successful_status(resp.status):
                        error_text = await resp.text()
                        raise ValueError(f"API returned status {resp.status}: {error_text}")
                    data = await resp.json()

                    # Parse response based on API source
                    if isinstance(data, dict):
                        if "values" in data:  # Twelve Data
                            df = pd.DataFrame(data["values"])
                            df = df.rename(columns={"datetime": "time"})
                            for col in ['open', 'high', 'low', 'close']:
                                df[col] = pd.to_numeric(df[col], errors='coerce')
                            df = df[::-1]
                        elif "Time Series FX (1min)" in data:  # Alpha Vantage
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
                        elif "Error Message" in data:
                            raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
                        elif "Note" in data:
                            raise ValueError(f"Alpha Vantage API note: {data['Note']}")
                    else:
                        raise ValueError(f"Unsupported API response format: {type(data)}")

            # Clean data
            if df is None or df.empty:
                raise ValueError("Empty dataframe")
            
            df = df.dropna()
            
            if len(df) < 10:
                raise ValueError("Not enough valid data points after cleaning")

            # Successfully got data
            result_df = df.tail(CONFIG["lookback_window"])
            
            # Calculate ATR for adaptive caching
            try:
                import ta
                temp_price = float(result_df["close"].iloc[-1])
                temp_atr = float(ta.volatility.AverageTrueRange(
                    result_df["high"], result_df["low"], result_df["close"]
                ).average_true_range().iloc[-1])
                if pd.isna(temp_atr) or temp_atr <= 0:
                    temp_atr = temp_price * 0.001
            except Exception:
                temp_price = float(result_df["close"].iloc[-1])
                temp_atr = temp_price * 0.001
            
            # Save to cache
            async with cache_lock:
                cache_max = CONFIG.get("cache_max_size", CACHE_MAX_SIZE)
                if len(API_CACHE) >= cache_max:
                    API_CACHE.popitem(last=False)
                
                API_CACHE[cache_key] = (datetime.now(), result_df.copy(deep=False), temp_atr, temp_price)
                API_CACHE.move_to_end(cache_key)
            
            # Update metrics
            response_time = (datetime.now() - start_time).total_seconds()
            async with metrics_lock:
                METRICS["api_calls"] += 1
                METRICS["total_response_time"] += response_time
                METRICS["response_count"] += 1
                if METRICS["response_count"] > 0:
                    METRICS["avg_response_time"] = METRICS["total_response_time"] / METRICS["response_count"]
                else:
                    METRICS["avg_response_time"] = 0.0
            
            return result_df
        
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
            if attempt < max_retries - 1:
                wait_time = CONFIG["exponential_backoff_base"] ** attempt
                logging.warning(f"fetch_forex_data() attempt {attempt + 1}/{max_retries} failed: {e}, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                async with metrics_lock:
                    METRICS["api_errors"] += 1
                logging.error(f"fetch_forex_data() failed after {max_retries} attempts: {e}")
        except Exception as e:
            async with metrics_lock:
                METRICS["api_errors"] += 1
            logging.error(f"Unexpected error in fetch_forex_data(): {e}")
            break
    
    return None

