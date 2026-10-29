# -*- coding: utf-8 -*-
"""
Миграционный скрипт: добавляет недостающие колонки в существующую БД
1) notes в таблицу experts
2) status в таблицу tasks

Скрипт делает резервную копию базы перед изменениями и безопасно проверяет наличие колонок.
"""
import sqlite3
from pathlib import Path
from datetime import datetime


def add_missing_columns(db_path: str = "database.db") -> bool:
    if not Path(db_path).exists():
        print(f"❌ База данных {db_path} не найдена")
        return False

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"database_backup_add_columns_{timestamp}.db"

        conn = sqlite3.connect(db_path)
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
        print(f"✓ Резервная копия создана: {backup_path}")

        cursor = conn.cursor()

        # experts.notes
        cursor.execute("PRAGMA table_info(experts)")
        experts_cols = [col[1] for col in cursor.fetchall()]
        if 'notes' not in experts_cols:
            print("🔄 Добавление колонки 'notes' в таблицу experts...")
            cursor.execute("ALTER TABLE experts ADD COLUMN notes TEXT")
            print("✓ Колонка 'notes' добавлена")
        else:
            print("✓ Колонка 'notes' уже существует")

        # tasks.status
        cursor.execute("PRAGMA table_info(tasks)")
        tasks_cols = [col[1] for col in cursor.fetchall()]
        if 'status' not in tasks_cols:
            print("🔄 Добавление колонки 'status' в таблицу tasks...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT 'Новая'")
            print("✓ Колонка 'status' добавлена")
        else:
            print("✓ Колонка 'status' уже существует")

        conn.commit()
        conn.close()
        print("\n✅ Миграция завершена успешно")
        return True

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False


if __name__ == '__main__':
    add_missing_columns()

