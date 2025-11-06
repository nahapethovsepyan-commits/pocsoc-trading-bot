"""
Database repository for signal storage and retrieval.
"""

import os
import shutil
import logging
import aiosqlite
from datetime import datetime
from typing import Dict, List, Any, Optional
from ..models.state import STATS, stats_lock

DB_PATH = "signals.db"


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
        async with aiosqlite.connect(DB_PATH) as db:
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
            except Exception:
                # Колонка уже существует, это нормально
                pass
            
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
            
            await db.commit()
            logging.info("✓ Database initialized")
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
        async with aiosqlite.connect(DB_PATH) as db:
            indicators = signal_data.get("indicators", {})
            await db.execute("""
                INSERT INTO signals (timestamp, signal, price, score, confidence, reasoning, rsi, macd, entry, atr)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                signal_data.get("atr")
            ))
            await db.commit()
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
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM signals 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                
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
            async with aiosqlite.connect(DB_PATH) as db:
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


