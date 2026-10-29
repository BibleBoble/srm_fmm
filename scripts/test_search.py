# -*- coding: utf-8 -*-
"""Простой тестовый раннер для проверки поиска задач/клиентов.
Запускайте из корня проекта:
    python .\scripts\test_search.py
"""
import sys
import traceback
import re
from pathlib import Path

# Добавляем корень репозитория в sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def run():
    try:
        from managers.tasks_manager import TasksManager
        from managers.clients_manager import ClientsManager
        import sqlite3

        print(f"Repo root: {ROOT}")
        db_path = ROOT / 'database.db'
        print('Using DB:', db_path)

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        # Sample client
        cur.execute("SELECT company FROM clients WHERE company IS NOT NULL AND company<>'' LIMIT 1")
        row = cur.fetchone()
        company = row[0] if row else None

        # Sample task
        cur.execute("SELECT title, description FROM tasks WHERE (title IS NOT NULL AND title<>'') OR (description IS NOT NULL AND description<>'') LIMIT 1")
        row = cur.fetchone()
        title = row[0] if row else None
        description = row[1] if row else None

        print('\nSample values from DB:')
        print(' company:', company)
        print(' title:', title)
        print(' description (first 120 chars):', (description[:120] + '...') if description else None)

        tasks_mgr = TasksManager()
        clients_mgr = ClientsManager()

        if company:
            print('\nClientsManager.search tests (case-insensitive):')
            for val in (company, company.upper(), company.lower()):
                res = clients_mgr.search(val)
                print(f" search('{val}') -> {len(res)} results")

        if title:
            print('\nTasksManager.search tests (title/description/client, case-insensitive):')
            for val in (title, title.upper(), title.lower()):
                res = tasks_mgr.search(val)
                print(f" search('{val}') -> {len(res)} results")

        # Test searching by a token from description if available
        if description:
            # Используем regex для извлечения слов длиной >=4 (удобно и безопасно для любых символов)
            tokens = re.findall(r"\\w{4,}", description)
            token = None
            for w in tokens:
                if title and w.lower() not in title.lower():
                    token = w
                    break
            if token:
                print(f"\nSearching by token from description: '{token}'")
                res = tasks_mgr.search(token)
                print(' results:', len(res))
                for t in res[:10]:
                    print('  ->', getattr(t, 'id', None), '-', getattr(t, 'title', None), '| client=', getattr(t, 'client_name', None))

        # Test searching by part of client name via tasks search
        if company:
            part = company.split()[0]
            print(f"\nSearching tasks by client part: '{part}'")
            res = tasks_mgr.search(part)
            print(' results:', len(res))
            for t in res[:10]:
                print('  ->', getattr(t, 'id', None), '-', getattr(t, 'title', None), '| client=', getattr(t, 'client_name', None))

        conn.close()
    except Exception:
        traceback.print_exc()
        sys.exit(2)

if __name__ == '__main__':
    run()
