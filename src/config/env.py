"""
Environment variable loading and validation.
"""

import os
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI
from httpx import AsyncClient
from typing import Optional, Tuple

# Load environment variables
load_dotenv()


def load_environment_variables() -> None:
    """
    Load environment variables from .env file.
    
    This function should be called at application startup.
    """
    load_dotenv()


def get_bot_token() -> str:
    """
    Get Telegram bot token from environment variables.
    
    Returns:
        str: Bot token
        
    Raises:
        ValueError: If BOT_TOKEN is not found in environment
    """
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN not found in .env file")
    return token


def get_api_keys() -> Tuple[Optional[str], Optional[str]]:
    """
    Get API keys for forex data sources.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: (TWELVE_DATA_KEY, ALPHA_VANTAGE_KEY)
    """
    twelvedata_key = os.getenv("TWELVE_DATA_API_KEY")
    alphavantage_key = os.getenv("ALPHA_VANTAGE_KEY")
    return twelvedata_key, alphavantage_key


def get_openai_client() -> Tuple[Optional[AsyncOpenAI], bool]:
    """
    Initialize OpenAI client if API key is available.
    
    Returns:
        Tuple[Optional[AsyncOpenAI], bool]: (client instance or None, use_gpt flag)
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    use_gpt = bool(openai_key)
    
    if not use_gpt:
        return None, False
    
    try:
        http_client = None
        proxy = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')
        if proxy:
            http_client = AsyncClient(proxies={"http://": proxy, "https://": proxy})
        client = AsyncOpenAI(api_key=openai_key, http_client=http_client)
        logging.info("✓ OpenAI API key found - GPT analysis enabled")
        return client, True
    except Exception as e:
        logging.warning(f"⚠️  Disabling GPT due to client init error: {e}")
        return None, False


