"""
Database repository for signal storage and retrieval.
"""

import os
import shutil
import logging
import asyncio
import aiosqlite
from datetime import datetime
from typing import Dict, List, Any, Optional
from ..models.state import (
    STATS,
    stats_lock,
    SUBSCRIBED_USERS,
    user_languages,
    user_expiration_preferences,
)

DB_PATH = "signals.db"


async def optimize_db_connection(db: aiosqlite.Connection) -> None:
    """
    Optimize SQLite connection settings for better performance.
    
    Sets pragmas for:
    - WAL mode: Better concurrency for reads
    - NORMAL synchronous: Good balance of safety and performance
    - Increased cache size: Better performance for frequent queries
    
    Args:
        db: Database connection to optimize
    """
    try:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.execute("PRAGMA cache_size=10000")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.commit()
    except Exception as e:
        logging.warning(f"Could not optimize database connection: {e}")


async def init_database() -> None:
    """
    Инициализация базы данных SQLite.
    
    Создает таблицы для хранения сигналов и статистики, если они не существуют.
    Также выполняет миграцию для добавления колонки ATR, если она отсутствует.
    
    Raises:
        Exception: Логирует ошибку при неудачной инициализации, но не прерывает работу.
        
    Note:
        Функция безопасна к повторному вызову - использует CREATE TABLE IF NOT EXISTS.
    """
    try:
        db = await aiosqlite.connect(DB_PATH)
        await optimize_db_connection(db)
        try:
            # Таблица сигналов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    price REAL NOT NULL,
                    score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT,
                    rsi REAL,
                    macd REAL,
                    entry REAL,
                    atr REAL
                )
            """)
            
            # Миграция: добавляем колонку atr если она не существует (для старых БД)
            try:
                await db.execute("ALTER TABLE signals ADD COLUMN atr REAL")
                await db.commit()
                logging.info("✓ Added ATR column to signals table")
            except aiosqlite.OperationalError as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    logging.debug("ATR column already exists (expected)")
                else:
                    logging.warning(f"Migration warning while adding ATR column: {e}")
            except Exception as e:
                logging.warning(f"Unexpected error during ATR migration: {e}")
            
            # Миграция: добавляем колонку symbol если она не существует (для старых БД)
            try:
                await db.execute("ALTER TABLE signals ADD COLUMN symbol TEXT DEFAULT 'EURUSD'")
                await db.commit()
                logging.info("✓ Added symbol column to signals table")
            except aiosqlite.OperationalError as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    logging.debug("Symbol column already exists (expected)")
                else:
                    logging.warning(f"Migration warning while adding symbol column: {e}")
            except Exception as e:
                logging.warning(f"Unexpected error during symbol migration: {e}")
            
            # Таблица статистики
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    call_count INTEGER DEFAULT 0,
                    put_count INTEGER DEFAULT 0,
                    ai_signals INTEGER DEFAULT 0,
                    total_signals INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0
                )
            """)

            # Таблица подписчиков
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    chat_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'ru',
                    expiration_seconds INTEGER,
                    subscribed_at TEXT NOT NULL
                )
            """)

            # Migration: ensure expiration_seconds column exists
            try:
                await db.execute("ALTER TABLE subscribers ADD COLUMN expiration_seconds INTEGER")
                await db.commit()
                logging.info("✓ Added expiration_seconds column to subscribers table")
            except aiosqlite.OperationalError as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    logging.debug("expiration_seconds column already exists (expected)")
                else:
                    logging.warning(f"Migration warning while adding expiration_seconds column: {e}")
            except Exception as e:
                logging.warning(f"Unexpected error during expiration_seconds migration: {e}")
            
            await db.commit()
            logging.info("✓ Database initialized")
        finally:
            await db.close()
        
        await load_subscribers_into_state()
    except Exception as e:
        logging.error(f"Database initialization error: {e}")


async def save_signal_to_db(signal_data: Dict[str, Any]) -> None:
    """
    Сохранить торговый сигнал в базу данных.
    
    Args:
        signal_data: Словарь с данными сигнала
        
    Raises:
        Exception: Логирует ошибку при неудачном сохранении, но не прерывает работу.
    """
    try:
        db = await aiosqlite.connect(DB_PATH)
        await optimize_db_connection(db)
        try:
            indicators = signal_data.get("indicators", {})
            await db.execute("""
                INSERT INTO signals (timestamp, signal, price, score, confidence, reasoning, rsi, macd, entry, atr, symbol)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_data["time"].isoformat() if isinstance(signal_data["time"], datetime) else str(signal_data["time"]),
                signal_data["signal"],
                signal_data["price"],
                signal_data["score"],
                signal_data["confidence"],
                signal_data.get("reasoning", ""),
                indicators.get("rsi"),
                indicators.get("macd"),
                signal_data.get("entry", signal_data["price"]),
                signal_data.get("atr"),
                signal_data.get("symbol", "EURUSD")
            ))
            await db.commit()
        finally:
            await db.close()
    except Exception as e:
        logging.error(f"Error saving signal to database: {e}")


async def load_recent_signals_from_db(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Загрузить последние сигналы из базы данных.
    
    Args:
        limit: Количество последних сигналов для загрузки
        
    Returns:
        Список словарей с данными сигналов, отсортированных по времени
    """
    try:
        db = await aiosqlite.connect(DB_PATH)
        await optimize_db_connection(db)
        try:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM signals 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            await cursor.close()
            
            signals = []
            for row in rows:
                try:
                    timestamp_str = row["timestamp"]
                    try:
                        signal_time = datetime.fromisoformat(timestamp_str)
                    except (ValueError, AttributeError):
                        try:
                            signal_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        except (ValueError, AttributeError):
                            logging.warning(f"Invalid timestamp format: {timestamp_str}, skipping signal")
                            continue
                    
                    signals.append({
                        "signal": row["signal"],
                        "price": float(row["price"]) if row["price"] is not None else 0.0,
                        "score": float(row["score"]) if row["score"] is not None else 50.0,
                        "confidence": float(row["confidence"]) if row["confidence"] is not None else 0.0,
                        "reasoning": row["reasoning"] or "",
                        "time": signal_time,
                        "entry": float(row["entry"]) if row["entry"] is not None else float(row["price"]) if row["price"] is not None else 0.0,
                        "atr": float(row["atr"]) if row.get("atr") is not None else None,
                        "symbol": row.get("symbol") or "EURUSD",  # Add symbol field
                        "indicators": {
                            "rsi": float(row["rsi"]) if row["rsi"] is not None else None,
                            "macd": float(row["macd"]) if row["macd"] is not None else None
                        }
                    })
                except Exception as e:
                    logging.error(f"Error parsing signal from database: {e}, skipping row")
                    continue
            
            signals.reverse()
            logging.info(f"✓ Loaded {len(signals)} signals from database")
            return signals
        finally:
            await db.close()
    except Exception as e:
        logging.error(f"Error loading signals from database: {e}")
        return []


async def save_stats_to_db() -> None:
    """
    Сохранить текущую статистику в базу данных.
    
    Raises:
        Exception: Логирует ошибку при неудачном сохранении.
    """
    try:
        async with stats_lock:
            db = await aiosqlite.connect(DB_PATH)
            await optimize_db_connection(db)
            try:
                await db.execute("""
                    INSERT INTO stats (timestamp, call_count, put_count, ai_signals, total_signals, wins, losses)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    STATS.get("BUY", 0),
                    STATS.get("SELL", 0),
                    STATS.get("AI_signals", 0),
                    STATS.get("total_signals", 0),
                    STATS.get("wins", 0),
                    STATS.get("losses", 0)
                ))
                await db.commit()
            finally:
                await db.close()
    except Exception as e:
        logging.error(f"Error saving stats to database: {e}")


async def backup_database() -> None:
    """
    Автоматическое резервное копирование базы данных.
    
    Создает резервную копию БД в папке backups/ с временной меткой.
    Автоматически удаляет старые бэкапы, оставляя только последние 7.
    
    Raises:
        Exception: Логирует ошибку при неудачном создании бэкапа.
    """
    try:
        if not os.path.exists(DB_PATH):
            logging.warning(f"Database {DB_PATH} not found, skipping backup")
            return
        
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"signals_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        shutil.copy2(DB_PATH, backup_path)
        
        backup_files = []
        for filename in os.listdir(backup_dir):
            if filename.startswith("signals_backup_") and filename.endswith('.db'):
                filepath = os.path.join(backup_dir, filename)
                backup_files.append((filepath, os.path.getmtime(filepath)))
        
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        deleted_count = 0
        for filepath, _ in backup_files[7:]:
            try:
                os.remove(filepath)
                deleted_count += 1
            except Exception:
                pass
        
        db_size = os.path.getsize(backup_path) / 1024
        logging.info(f"✅ Database backup created: {backup_filename} ({db_size:.2f} KB)")
        if deleted_count > 0:
            logging.info(f"🗑️  Removed {deleted_count} old backup(s)")
            
    except Exception as e:
        logging.error(f"Error creating database backup: {e}")


async def add_subscriber_to_db(
    chat_id: int,
    language: str = 'ru',
    expiration_seconds: Optional[int] = None
) -> None:
    """
    Persist subscriber into database.
    """
    try:
        db = await aiosqlite.connect(DB_PATH)
        await optimize_db_connection(db)
        try:
            await db.execute("""
                INSERT INTO subscribers (chat_id, language, expiration_seconds, subscribed_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    language=excluded.language,
                    expiration_seconds=excluded.expiration_seconds,
                    subscribed_at=excluded.subscribed_at
            """, (
                chat_id,
                language or 'ru',
                expiration_seconds,
                datetime.now().isoformat()
            ))
            await db.commit()
        finally:
            await db.close()
    except Exception as e:
        logging.error(f"Error saving subscriber {chat_id} to database: {e}")


async def remove_subscriber_from_db(chat_id: int) -> None:
    """
    Remove subscriber from database.
    """
    try:
        db = await aiosqlite.connect(DB_PATH)
        await optimize_db_connection(db)
        try:
            await db.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
            await db.commit()
        finally:
            await db.close()
        
        user_languages.pop(chat_id, None)
        user_expiration_preferences.pop(chat_id, None)
    except Exception as e:
        logging.error(f"Error removing subscriber {chat_id} from database: {e}")


async def load_subscribers_into_state() -> None:
    """
    Load subscribers from DB into in-memory state on startup.
    """
    try:
        db = await aiosqlite.connect(DB_PATH)
        await optimize_db_connection(db)
        try:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT chat_id, language, expiration_seconds
                FROM subscribers
            """)
            rows = await cursor.fetchall()
            await cursor.close()
        finally:
            await db.close()
        
        SUBSCRIBED_USERS.clear()
        SUBSCRIBED_USERS.update({row["chat_id"] for row in rows})
        user_languages.clear()
        user_expiration_preferences.clear()
        for row in rows:
            lang = row.get("language") or 'ru'
            user_languages[row["chat_id"]] = lang
            expiration = row.get("expiration_seconds")
            if expiration:
                user_expiration_preferences[row["chat_id"]] = expiration

        logging.info(f"✓ Loaded {len(SUBSCRIBED_USERS)} subscribers from database")
    except Exception as e:
        logging.error(f"Error loading subscribers from database: {e}")


