#!/usr/bin/env python3
"""
Скрипт резервного копирования базы данных signals.db

Использование:
    python backup_db.py              # Создать бэкап с текущей датой
    python backup_db.py --auto       # Автоматический режим (удаляет старые бэкапы)
    python backup_db.py --keep 7     # Хранить последние 7 бэкапов
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Константы
DB_PATH = "signals.db"
BACKUP_DIR = "backups"
BACKUP_PREFIX = "signals_backup_"

def create_backup():
    """Создать резервную копию базы данных"""
    # Проверяем существование БД
    if not os.path.exists(DB_PATH):
        print(f"❌ База данных {DB_PATH} не найдена!")
        return False
    
    # Создаем директорию для бэкапов
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Имя файла бэкапа с датой и временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{BACKUP_PREFIX}{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        # Копируем файл БД
        shutil.copy2(DB_PATH, backup_path)
        
        # Получаем размер файлов
        db_size = os.path.getsize(DB_PATH) / 1024  # KB
        backup_size = os.path.getsize(backup_path) / 1024  # KB
        
        print(f"✅ Бэкап создан успешно!")
        print(f"   📁 Файл: {backup_path}")
        print(f"   📊 Размер: {backup_size:.2f} KB")
        print(f"   📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return backup_path
        
    except Exception as e:
        print(f"❌ Ошибка при создании бэкапа: {e}")
        return False

def cleanup_old_backups(keep_count=7):
    """Удалить старые бэкапы, оставив только последние N"""
    if not os.path.exists(BACKUP_DIR):
        return
    
    # Получаем все файлы бэкапов
    backup_files = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.startswith(BACKUP_PREFIX) and filename.endswith('.db'):
            filepath = os.path.join(BACKUP_DIR, filename)
            backup_files.append((filepath, os.path.getmtime(filepath)))
    
    # Сортируем по дате изменения (новые сначала)
    backup_files.sort(key=lambda x: x[1], reverse=True)
    
    # Удаляем старые бэкапы
    if len(backup_files) > keep_count:
        deleted_count = 0
        for filepath, _ in backup_files[keep_count:]:
            try:
                os.remove(filepath)
                deleted_count += 1
            except Exception as e:
                print(f"⚠️  Не удалось удалить {filepath}: {e}")
        
        if deleted_count > 0:
            print(f"🗑️  Удалено старых бэкапов: {deleted_count}")
    
    print(f"📦 Всего бэкапов: {len(backup_files)} (хранится: {min(len(backup_files), keep_count)})")

def list_backups():
    """Показать список всех бэкапов"""
    if not os.path.exists(BACKUP_DIR):
        print("📁 Директория бэкапов не найдена")
        return
    
    backup_files = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.startswith(BACKUP_PREFIX) and filename.endswith('.db'):
            filepath = os.path.join(BACKUP_DIR, filename)
            size = os.path.getsize(filepath) / 1024  # KB
            mtime = os.path.getmtime(filepath)
            backup_files.append((filepath, filename, size, mtime))
    
    if not backup_files:
        print("📁 Бэкапы не найдены")
        return
    
    # Сортируем по дате (новые сначала)
    backup_files.sort(key=lambda x: x[3], reverse=True)
    
    print(f"\n📦 Список бэкапов ({len(backup_files)} файлов):")
    print("-" * 70)
    for filepath, filename, size, mtime in backup_files:
        date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  📄 {filename}")
        print(f"     Размер: {size:.2f} KB | Дата: {date_str}")
    print("-" * 70)

def restore_backup(backup_filename):
    """Восстановить базу данных из бэкапа"""
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    if not os.path.exists(backup_path):
        print(f"❌ Бэкап {backup_filename} не найден!")
        return False
    
    # Создаем бэкап текущей БД перед восстановлением
    if os.path.exists(DB_PATH):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = f"{BACKUP_DIR}/{BACKUP_PREFIX}before_restore_{timestamp}.db"
        shutil.copy2(DB_PATH, current_backup)
        print(f"💾 Создан бэкап текущей БД: {current_backup}")
    
    try:
        # Восстанавливаем из бэкапа
        shutil.copy2(backup_path, DB_PATH)
        print(f"✅ База данных восстановлена из {backup_filename}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при восстановлении: {e}")
        return False

def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Резервное копирование базы данных signals.db')
    parser.add_argument('--auto', action='store_true', help='Автоматический режим (удалить старые бэкапы)')
    parser.add_argument('--keep', type=int, default=7, help='Количество бэкапов для хранения (по умолчанию: 7)')
    parser.add_argument('--list', action='store_true', help='Показать список бэкапов')
    parser.add_argument('--restore', type=str, help='Восстановить из указанного бэкапа')
    
    args = parser.parse_args()
    
    # Показать список бэкапов
    if args.list:
        list_backups()
        return
    
    # Восстановить из бэкапа
    if args.restore:
        restore_backup(args.restore)
        return
    
    # Создать бэкап
    backup_path = create_backup()
    
    if backup_path and args.auto:
        cleanup_old_backups(args.keep)

if __name__ == "__main__":
    main()

