"""
Symbol normalization utilities for different API providers.
"""

# Symbol mapping: internal symbol -> API-specific formats
SYMBOL_MAP = {
    "EURUSD": {
        "internal": "EURUSD",
        "pair": "EUR/USD",  # For Twelve Data, Alpha Vantage
        "twelvedata": "EUR/USD",
        "alphavantage": {"from": "EUR", "to": "USD"},
        "binance": "EURUSDT",
        "default_price": 1.0800,
    },
    "XAUUSD": {
        "internal": "XAUUSD",
        "pair": "XAU/USD",
        "twelvedata": "XAU/USD",
        "alphavantage": {"from": "XAU", "to": "USD"},
        "binance": "XAUUSDT",
        "default_price": 2700.0,
    },
}


def normalize_symbol(symbol: str) -> str:
    """
    Normalize symbol to internal format (uppercase, no separators).
    
    Args:
        symbol: Symbol in any format (EURUSD, EUR/USD, eurusd, etc.)
        
    Returns:
        Normalized symbol (EURUSD, XAUUSD, etc.)
        
    Raises:
        ValueError: If symbol is not supported
    """
    normalized = symbol.upper().replace("/", "").replace("-", "")
    if normalized in SYMBOL_MAP:
        return normalized
    # Fallback: try to construct if it looks like a pair
    if len(normalized) == 6:
        return normalized
    raise ValueError(f"Unsupported symbol: {symbol}")


def symbol_to_pair(symbol: str) -> str:
    """
    Convert symbol to pair format (EURUSD -> EUR/USD).
    
    Args:
        symbol: Normalized symbol (EURUSD, XAUUSD)
        
    Returns:
        Pair format (EUR/USD, XAU/USD)
        
    Raises:
        ValueError: If symbol is not supported
    """
    normalized = normalize_symbol(symbol)
    return SYMBOL_MAP[normalized]["pair"]


def get_symbol_config(symbol: str, key: str):
    """
    Get symbol-specific configuration.
    
    Args:
        symbol: Normalized symbol
        key: Configuration key (pair, twelvedata, alphavantage, binance, default_price)
        
    Returns:
        Configuration value
        
    Raises:
        ValueError: If symbol is not supported
        KeyError: If key is not found in symbol config
    """
    normalized = normalize_symbol(symbol)
    if key not in SYMBOL_MAP[normalized]:
        raise KeyError(f"Key '{key}' not found in symbol config for {normalized}")
    return SYMBOL_MAP[normalized].get(key)


def get_supported_symbols() -> list:
    """Get list of supported symbols."""
    return list(SYMBOL_MAP.keys())
