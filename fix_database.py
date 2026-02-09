# -*- coding: utf-8 -*-
"""
Скрипт исправления базы данных - добавление недостающих колонок
"""
import sqlite3
from pathlib import Path
from datetime import datetime


def fix_database():
    """Исправляет структуру базы данных"""
    db_path = "database.db"
    
    if not Path(db_path).exists():
        print(f"❌ База данных {db_path} не найдена")
        return False
    
    try:
        # Создаем резервную копию
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"database_backup_fix_{timestamp}.db"
        
        conn = sqlite3.connect(db_path)
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
        print(f"✓ Резервная копия создана: {backup_path}")
        
        cursor = conn.cursor()
        
        # 1. Добавляем колонку notes в таблицу experts
        cursor.execute("PRAGMA table_info(experts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'notes' not in columns:
            print("🔄 Добавление колонки notes в таблицу experts...")
            cursor.execute("ALTER TABLE experts ADD COLUMN notes TEXT")
            print("✓ Колонка notes добавлена")
        else:
            print("✓ Колонка notes уже существует")
        
        # 2. Добавляем колонку status в таблицу tasks
        cursor.execute("PRAGMA table_info(tasks)")
        task_columns = [column[1] for column in cursor.fetchall()]
        
        if 'status' not in task_columns:
            print("🔄 Добавление колонки status в таблицу tasks...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT 'Новая'")
            print("✓ Колонка status добавлена")
        else:
            print("✓ Колонка status уже существует")
        
        # 3. Проверяем структуру таблиц
        print("\n📋 Текущая структура таблиц:")
        
        cursor.execute("PRAGMA table_info(experts)")
        experts_cols = [f"{col[1]}({col[2]})" for col in cursor.fetchall()]
        print(f"experts: {', '.join(experts_cols)}")
        
        cursor.execute("PRAGMA table_info(tasks)")
        tasks_cols = [f"{col[1]}({col[2]})" for col in cursor.fetchall()]
        print(f"tasks: {', '.join(tasks_cols)}")
        
        cursor.execute("PRAGMA table_info(expert_contacts)")
        contacts_cols = [f"{col[1]}({col[2]})" for col in cursor.fetchall()]
        print(f"expert_contacts: {', '.join(contacts_cols)}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ База данных успешно обновлена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении базы данных: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Исправление структуры базы данных...")
    if fix_database():
        print("✅ Исправление завершено успешно")
    else:
        print("❌ Исправление завершилось с ошибкой")
