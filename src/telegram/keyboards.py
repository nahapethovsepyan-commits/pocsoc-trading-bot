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
            [KeyboardButton(text="⚙️ НАСТРОЙКИ"), KeyboardButton(text="📜 ИСТОРИЯ")],
            [KeyboardButton(text="📈 Активы")]
        ],
        'en': [
            [KeyboardButton(text="📊 SIGNAL"), KeyboardButton(text="📈 STATISTICS")],
            [KeyboardButton(text="⚙️ SETTINGS"), KeyboardButton(text="📜 HISTORY")],
            [KeyboardButton(text="📈 Symbols")]
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


def get_expiration_keyboard(lang: str = 'ru', symbol: str = None) -> InlineKeyboardMarkup:
    """
    Generate inline keyboard for expiration selection.
    
    Args:
        lang: Language code ('ru' or 'en')
        symbol: Trading symbol (EURUSD, XAUUSD) - if None, uses default
        
    Returns:
        InlineKeyboardMarkup with expiration selection buttons
    """
    # Получаем настройки для символа или используем дефолтные
    if symbol:
        from ..utils.symbols import normalize_symbol
        try:
            normalized_symbol = normalize_symbol(symbol)
            symbol_config = CONFIG.get("symbol_configs", {}).get(normalized_symbol, {})
            layout = symbol_config.get("expiration_button_layout")
            if layout:
                rows = []
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
        except ValueError:
            pass  # Fallback to default if symbol invalid
    
    # Default layout (fallback)
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


def get_symbol_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """
    Generate inline keyboard for symbol selection.
    
    Args:
        lang: Language code ('ru' or 'en')
        
    Returns:
        InlineKeyboardMarkup with symbol selection buttons
    """
    symbols = CONFIG.get("symbols", ["EURUSD", "XAUUSD"])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=symbol, callback_data=f"symbol_{symbol}")
            for symbol in symbols
        ]
    ])
    return keyboard

