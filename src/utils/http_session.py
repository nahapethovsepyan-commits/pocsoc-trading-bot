"""
HTTP session management for API requests.
"""

import logging
import aiohttp
from typing import Optional

# Глобальный HTTP session для переиспользования
http_session: Optional[aiohttp.ClientSession] = None


async def get_http_session() -> aiohttp.ClientSession:
    """
    Получить или создать глобальный HTTP session для переиспользования.
    
    Создает новую сессию только если она не существует или была закрыта.
    Это позволяет переиспользовать соединения и повысить производительность.
    
    Returns:
        Глобальная HTTP сессия для API запросов
        
    Example:
        >>> session = await get_http_session()
        >>> async with session.get(url) as response:
        ...     data = await response.json()
    """
    global http_session
    try:
        if http_session is None or http_session.closed:
            http_session = aiohttp.ClientSession()
            logging.info("✓ Created new HTTP session")
        return http_session
    except Exception as e:
        logging.error(f"Error creating HTTP session: {e}")
        # Создаем новую сессию при ошибке
        http_session = aiohttp.ClientSession()
        return http_session


async def close_http_session() -> None:
    """
    Закрыть HTTP session при завершении работы бота.
    
    Корректно закрывает все соединения и освобождает ресурсы.
    Должна вызываться при graceful shutdown.
    
    Note:
        Функция безопасна к повторному вызову - проверяет состояние сессии.
    """
    global http_session
    if http_session and not http_session.closed:
        try:
            await http_session.close()
            logging.info("✓ Closed HTTP session")
        except Exception as e:
            logging.error(f"Error closing HTTP session: {e}")
        finally:
            http_session = None


