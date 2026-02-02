#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый скрипт восстановления и повторной миграции
"""
import shutil
from pathlib import Path


def restore_and_migrate():
    """Восстановить БД из бэкапа и запустить миграцию"""

    # Найти последний бэкап
    backups = sorted(Path('.').glob('database_backup_*.db'))

    if not backups:
        print("✗ Бэкап не найден!")
        print("  Создайте бэкап вручную: cp database.db database_backup.db")
        return False

    latest_backup = backups[-1]
    print(f"→ Найден последний бэкап: {latest_backup}")

    # Восстанавливаем
    print("→ Восстанавливаем БД из бэкапа...")
    shutil.copy(latest_backup, 'database.db')
    print("✓ БД восстановлена")

    # Запускаем миграцию
    print("\n→ Запускаем миграцию...")
    from migrate_database import Migration

    migration = Migration('database.db')
    success = migration.run()

    if success:
        print("\n✅ Миграция успешно завершена!")
        print(f"   Старый бэкап сохранен: {latest_backup}")
        return True
    else:
        print("\n✗ Миграция не удалась")
        return False


if __name__ == "__main__":
    restore_and_migrate()