"""
Helper utility functions.
"""

import re
from datetime import datetime
from typing import Optional


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Безопасное деление с защитой от деления на ноль.
    
    Args:
        numerator: Числитель
        denominator: Знаменатель
        default: Значение по умолчанию при делении на ноль
        
    Returns:
        Результат деления или default
    """
    if denominator == 0 or denominator is None:
        return default
    return numerator / denominator


def is_successful_status(status_code: int) -> bool:
    """
    Проверка, является ли HTTP статус успешным.
    
    Args:
        status_code: HTTP статус код
        
    Returns:
        True если статус успешный (200-299)
    """
    return 200 <= status_code < 300


def format_time(dt, format_str: str = '%H:%M:%S') -> str:
    """
    Безопасное форматирование времени.
    
    Args:
        dt: datetime объект или строка
        format_str: Формат времени
        
    Returns:
        Отформатированное время или 'N/A'
    """
    if isinstance(dt, datetime):
        return dt.strftime(format_str)
    elif isinstance(dt, str):
        try:
            dt_obj = datetime.fromisoformat(dt)
            return dt_obj.strftime(format_str)
        except (ValueError, AttributeError):
            return 'N/A'
    return 'N/A'


def sanitize_user_input(text: Optional[str], max_length: int = 200, 
                        allowed_pattern: Optional[str] = None) -> Optional[str]:
    """
    Санитизация пользовательского ввода.
    
    Args:
        text: Входной текст
        max_length: Максимальная длина
        allowed_pattern: Optional regex pattern for allowed characters
        
    Returns:
        Очищенный текст или None если невалидный
    """
    if not text or not isinstance(text, str):
        return None
    # Удаляем опасные символы
    text = text.strip()
    # Удаляем множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    # Ограничиваем длину
    if len(text) > max_length:
        return None
    # Pattern validation if provided
    if allowed_pattern:
        if not re.match(allowed_pattern, text):
            return None
    return text


def validate_config_input(text: str) -> bool:
    """
    Validate config command input format.
    
    Allows only alphanumeric characters, underscores, equals signs, dashes, and spaces.
    This prevents command injection and ensures safe parameter parsing.
    
    Args:
        text: Input text to validate
        
    Returns:
        True if input matches allowed pattern, False otherwise
    """
    if not text or not isinstance(text, str):
        return False
    # Pattern: alphanumeric, underscore, equals, dash, space
    pattern = re.compile(r'^[a-zA-Z0-9_=\s-]+$')
    return bool(pattern.match(text))


