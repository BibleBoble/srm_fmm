# -*- coding: utf-8 -*-
"""Резервная копия базы данных и папки с документами в папку reservwork.

Копирует:
    database.db      -> reservwork/database.db   (через SQLite backup API)
    clients_files/   -> reservwork/clients_files/

Запуск:
    python backup_db_and_documents.py
"""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "reservwork"
DATABASE = BASE_DIR / "database.db"
DOCUMENTS = BASE_DIR / "clients_files"


def backup_database():
    """Скопировать БД через sqlite backup — копия согласована с WAL."""
    if not DATABASE.is_file():
        print("database.db не найден — БД не копирую.")
        return False

    target_path = BACKUP_DIR / "database.db"
    if target_path.exists():
        target_path.unlink()

    source = sqlite3.connect(DATABASE)
    try:
        target = sqlite3.connect(target_path)
        try:
            with target:
                source.backup(target)
        finally:
            target.close()
    finally:
        source.close()
    print(f"БД скопирована: {target_path}")
    return True


def backup_documents():
    """Скопировать папку с документами клиентов."""
    if not DOCUMENTS.is_dir():
        print("clients_files не найдена — документы не копирую.")
        return False

    target = BACKUP_DIR / "clients_files"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(DOCUMENTS, target)
    files = sum(1 for path in target.rglob("*") if path.is_file())
    print(f"Документы скопированы: {target} (файлов: {files})")
    return True


def main():
    BACKUP_DIR.mkdir(exist_ok=True)
    print(f"Папка резервных копий: {BACKUP_DIR}")

    database_done = backup_database()
    documents_done = backup_documents()

    info = BACKUP_DIR / "backup_info.txt"
    info.write_text(
        "\n".join(
            (
                f"Резервная копия от {datetime.now():%d.%m.%Y %H:%M:%S}",
                f"База данных: {'скопирована' if database_done else 'нет'}",
                f"Документы: {'скопированы' if documents_done else 'нет'}",
            )
        ),
        encoding="utf-8",
    )
    print("Готово.")


if __name__ == "__main__":
    main()
