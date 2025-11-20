"""
Telegram bot handler decorators.
"""

import asyncio
import logging
from functools import wraps
from ..models.state import SUBSCRIBED_USERS, user_languages
from ..config import CONFIG
from .localization import TEXTS


def require_subscription(func):
    """Decorator to check user subscription before handler execution.
    
    Works with both message handlers and callback query handlers.
    """
    @wraps(func)
    async def wrapper(event):
        # Handle both Message and CallbackQuery objects
        if hasattr(event, 'message') and event.message:
            # CallbackQuery object
            chat_id = event.message.chat.id
            message_obj = event.message
        else:
            # Message object
            chat_id = event.chat.id
            message_obj = event
        
        if chat_id not in SUBSCRIBED_USERS:
            lang = user_languages.get(chat_id, 'ru')
            t = TEXTS.get(lang, TEXTS['ru'])
            # Ensure answer is awaitable (for tests with AsyncMock)
            answer_func = getattr(message_obj, 'answer', None)
            if answer_func is not None:
                try:
                    # Try to await (works for AsyncMock and real async functions)
                    if asyncio.iscoroutinefunction(answer_func):
                        await answer_func(t.get('not_subscribed', '⚠️ Please send /start first to subscribe to signals'))
                    else:
                        # For AsyncMock in tests
                        result = answer_func(t.get('not_subscribed', '⚠️ Please send /start first to subscribe to signals'))
                        if asyncio.iscoroutine(result):
                            await result
                except (TypeError, AttributeError):
                    # Fallback for non-async mocks
                    pass
            return
        return await func(event)
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


def get_user_locale(event):
    """Get user's language and localized texts.
    
    Args:
        event: Telegram message or callback object
        
    Returns:
        tuple: (language_code, texts_dict)
    """
    # Handle both Message and CallbackQuery objects
    if hasattr(event, 'message') and event.message:
        # CallbackQuery object
        chat_id = event.message.chat.id
    else:
        # Message object
        chat_id = event.chat.id
    
    lang = user_languages.get(chat_id, 'ru')
    return lang, TEXTS.get(lang, TEXTS['ru'])

