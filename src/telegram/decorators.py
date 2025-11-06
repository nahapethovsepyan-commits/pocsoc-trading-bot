"""
Telegram bot handler decorators.
"""

import logging
from functools import wraps
from ..models.state import SUBSCRIBED_USERS, user_languages
from ..config import CONFIG
from .localization import TEXTS


def require_subscription(func):
    """Decorator to check user subscription before handler execution."""
    @wraps(func)
    async def wrapper(message):
        chat_id = message.chat.id
        if chat_id not in SUBSCRIBED_USERS:
            lang = user_languages.get(chat_id, 'ru')
            t = TEXTS.get(lang, TEXTS['ru'])
            await message.answer(t.get('not_subscribed', '⚠️ Please send /start first to subscribe to signals'))
            return
        return await func(message)
    return wrapper


def with_error_handling(func):
    """Decorator to handle exceptions in handlers with localized error messages."""
    @wraps(func)
    async def wrapper(message):
        try:
            return await func(message)
        except Exception as e:
            lang = user_languages.get(message.chat.id, 'ru')
            t = TEXTS.get(lang, TEXTS['ru'])
            max_length = CONFIG.get("error_message_max_length", 100)
            await message.answer(t['error'].format(error=str(e)[:max_length]))
            logging.error(f"Error in {func.__name__}: {e}", exc_info=True)
    return wrapper


def get_user_locale(message):
    """Get user's language and localized texts.
    
    Args:
        message: Telegram message object
        
    Returns:
        tuple: (language_code, texts_dict)
    """
    chat_id = message.chat.id
    lang = user_languages.get(chat_id, 'ru')
    return lang, TEXTS.get(lang, TEXTS['ru'])

