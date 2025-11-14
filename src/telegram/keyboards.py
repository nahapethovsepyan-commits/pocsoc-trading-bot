"""
Telegram bot keyboard definitions.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from ..config import CONFIG
from .localization import TEXTS


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


def _format_exp_label(seconds: int, lang: str) -> str:
    if seconds < 60:
        template = TEXTS[lang]['expiration_button_seconds']
        return template.format(value=seconds)
    minutes = seconds // 60
    template = TEXTS[lang]['expiration_button_minutes']
    return template.format(value=minutes)


def get_expiration_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    rows = []
    layout = CONFIG.get("expiration_button_layout", [[5, 10, 30], [60, 120, 180]])
    for row in layout:
        inline_row = []
        for seconds in row:
            label = _format_exp_label(seconds, lang)
            inline_row.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"exp_select:{seconds}"
                )
            )
        rows.append(inline_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

