# -*- coding: utf-8 -*-
"""
Скрипт добавления колонки notes в таблицу experts
"""
import sqlite3
from pathlib import Path
from datetime import datetime


def add_notes_column():
    """Добавляет колонку notes в таблицу experts"""
    db_path = "database.db"
    
    if not Path(db_path).exists():
        print(f"❌ База данных {db_path} не найдена")
        return False
    
    try:
        # Создаем резервную копию
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"database_backup_notes_{timestamp}.db"
        
        conn = sqlite3.connect(db_path)
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
        print(f"✓ Резервная копия создана: {backup_path}")
        
        # Проверяем, есть ли уже колонка notes
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(experts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'notes' in columns:
            print("✓ Колонка notes уже существует в таблице experts")
            conn.close()
            return True
        
        # Добавляем колонку
        cursor.execute("ALTER TABLE experts ADD COLUMN notes TEXT")
        conn.commit()
        
        print("✓ Колонка notes успешно добавлена в таблицу experts")
        
        # Проверяем результат
        cursor.execute("PRAGMA table_info(experts)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"✓ Текущие колонки experts: {', '.join(columns)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении колонки notes: {e}")
        return False


if __name__ == "__main__":
    print("🔄 Добавление колонки notes в таблицу experts...")
    if add_notes_column():
        print("✅ Миграция завершена успешно")
    else:
        print("❌ Миграция завершилась с ошибкой")
