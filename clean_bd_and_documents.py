# -*- coding: utf-8 -*-
"""Очистка базы данных и папки с документами клиентов.

Удаляет database.db (вместе с -wal/-shm) и все папки клиентов внутри
clients_files. Шаблоны документов (файлы «шаблон …») сохраняются.

Запуск:
    python clean_bd_and_documents.py          # спросит подтверждение
    python clean_bd_and_documents.py --yes    # без вопроса
"""
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILES = (
    "database.db",
    "database.db-wal",
    "database.db-shm",
)
DOCUMENTS_DIR = BASE_DIR / "clients_files"
TEMPLATE_PREFIX = "шаблон"


def _confirm():
    if "--yes" in sys.argv or "-y" in sys.argv:
        return True
    answer = input(
        "Удалить базу данных и все документы клиентов? Введите ДА: "
    ).strip().casefold()
    return answer in {"да", "yes", "y"}


def clean_database():
    removed = 0
    for name in DATABASE_FILES:
        path = BASE_DIR / name
        if not path.exists():
            continue
        try:
            path.unlink()
            removed += 1
            print(f"Удалён файл: {name}")
        except OSError as error:
            print(f"Не удалось удалить {name}: {error}")
    return removed


def clean_documents():
    if not DOCUMENTS_DIR.is_dir():
        print("Папка clients_files не найдена — пропускаю.")
        return 0

    removed = 0
    for entry in DOCUMENTS_DIR.iterdir():
        if entry.is_file() and entry.name.casefold().startswith(TEMPLATE_PREFIX):
            continue
        try:
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)
            else:
                entry.unlink()
            removed += 1
            print(f"Удалено: {entry.name}")
        except OSError as error:
            print(f"Не удалось удалить {entry.name}: {error}")
    return removed


def main():
    if not _confirm():
        print("Отменено.")
        return

    database_files = clean_database()
    documents = clean_documents()
    print(
        f"Готово. Удалено файлов БД: {database_files}, "
        f"объектов в clients_files: {documents}."
    )


if __name__ == "__main__":
    main()
