"""
Telegram bot keyboard definitions.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard(lang='ru'):
    """
    Создает главную клавиатуру для Telegram бота.
    
    Args:
        lang: Язык интерфейса ('ru' или 'en')
        
    Returns:
        ReplyKeyboardMarkup с основными кнопками
    """
    buttons = {
        'ru': [
            [KeyboardButton(text="📊 СИГНАЛ"), KeyboardButton(text="📈 СТАТИСТИКА")],
            [KeyboardButton(text="⚙️ НАСТРОЙКИ"), KeyboardButton(text="📜 ИСТОРИЯ")]
        ],
        'en': [
            [KeyboardButton(text="📊 SIGNAL"), KeyboardButton(text="📈 STATISTICS")],
            [KeyboardButton(text="⚙️ SETTINGS"), KeyboardButton(text="📜 HISTORY")]
        ]
    }
    return ReplyKeyboardMarkup(keyboard=buttons[lang], resize_keyboard=True)


language_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
    [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")]
])

