# -*- coding: utf-8 -*-
"""Работы (сделки) клиента: учёт оплат и расходов для отчётов."""
import re
from datetime import date, datetime
from pathlib import Path

from managers.database import Database
from utils.specification_reader import read_specification_items

FOLDER_PATTERN = re.compile(r"спецификация\s+(\d+)", re.IGNORECASE)
ACT_DATE_PATTERN = re.compile(r"от\s+(\d{2})\.(\d{2})\.(\d{4})", re.IGNORECASE)


class WorksManager:
    def __init__(self, clients_root=None):
        self.db = Database()
        self.clients_root = (
            Path(clients_root)
            if clients_root is not None
            else Path(__file__).resolve().parents[1] / "clients_files"
        )

    # --- синхронизация с папками документов ---
    def sync_from_documents(self):
        """Создать/обновить работы по папкам спецификаций."""
        if not self.clients_root.is_dir():
            return 0

        synced = 0
        for client_dir in self.clients_root.iterdir():
            if not client_dir.is_dir() or client_dir.is_symlink():
                continue
            public_id = client_dir.name.split(" ", 1)[0]
            client = self.db.fetch_one(
                "SELECT id FROM clients WHERE public_id = ?", (public_id,)
            )
            if not client:
                continue

            specifications_dir = client_dir / "спецификации"
            if not specifications_dir.is_dir():
                continue

            for folder in specifications_dir.iterdir():
                match = FOLDER_PATTERN.fullmatch(folder.name)
                if not folder.is_dir() or folder.is_symlink() or not match:
                    continue
                number = int(match.group(1))
                try:
                    specification_file = self._find_document(folder, "спецификация")
                    act_file = self._find_document(folder, "акт")
                except OSError:
                    continue
                if specification_file is None:
                    continue

                try:
                    items, total = read_specification_items(specification_file)
                except ValueError:
                    continue

                status = "Выполнена" if act_file is not None else "Запущена"
                completed_date = None
                if act_file is not None:
                    match_date = ACT_DATE_PATTERN.search(act_file.name)
                    if match_date:
                        completed_date = (
                            f"{match_date.group(3)}-{match_date.group(2)}"
                            f"-{match_date.group(1)}"
                        )

                try:
                    start_date = datetime.fromtimestamp(
                        specification_file.stat().st_mtime
                    ).date().isoformat()
                except OSError:
                    start_date = None

                title = "; ".join(item["name"] for item in items).strip()
                if not title:
                    title = f"Спецификация {number}"
                if len(title) > 120:
                    title = title[:117] + "…"

                self._upsert(
                    client_id=client["id"],
                    source_path=str(specification_file.resolve()),
                    title=title,
                    amount=float(total),
                    status=status,
                    start_date=start_date,
                    completed_date=completed_date,
                )
                synced += 1
        return synced

    @staticmethod
    def _find_document(folder, prefix):
        for path in sorted(
            folder.iterdir(), key=lambda item: item.name.casefold()
        ):
            if not path.is_file() or path.is_symlink():
                continue
            if path.name.startswith("~$"):
                continue
            if path.suffix.casefold() not in {".docx", ".pdf"}:
                continue
            if path.name.casefold().startswith(prefix):
                return path
        return None

    def _upsert(
        self, client_id, source_path, title, amount, status,
        start_date, completed_date
    ):
        row = self.db.fetch_one(
            "SELECT id FROM works WHERE source_path = ?", (source_path,)
        )
        if row:
            self.db.execute(
                """
                UPDATE works
                SET client_id = ?, title = ?, amount = ?, status = ?,
                    start_date = ?, completed_date = ?
                WHERE id = ?
                """,
                (client_id, title, amount, status, start_date, completed_date, row["id"])
            )
        else:
            self.db.execute(
                """
                INSERT INTO works
                    (client_id, source_path, title, amount, status,
                     start_date, completed_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (client_id, source_path, title, amount, status,
                 start_date, completed_date)
            )

    # --- чтение ---
    def list_works(self, client_id=None):
        query = """
            SELECT works.*, clients.company AS client_name,
                   clients.public_id AS client_public_id,
                   experts.name AS expert_name
            FROM works
            JOIN clients ON clients.id = works.client_id
            LEFT JOIN experts ON experts.id = works.expert_id
        """
        params = ()
        if client_id is not None:
            query += " WHERE works.client_id = ?"
            params = (client_id,)
        query += " ORDER BY works.start_date DESC, works.id DESC"
        return [dict(row) for row in self.db.fetch_all(query, params)]

    def list_works_for_expert(self, expert_id):
        """Работы, закреплённые за экспертом."""
        return [
            dict(row)
            for row in self.db.fetch_all(
                """
                SELECT works.*, clients.company AS client_name,
                       clients.public_id AS client_public_id
                FROM works
                JOIN clients ON clients.id = works.client_id
                WHERE works.expert_id = ?
                ORDER BY works.start_date DESC, works.id DESC
                """,
                (expert_id,)
            )
        ]

    def set_expert(self, work_id, expert_id):
        """Закрепить работу за экспертом."""
        self.db.execute(
            "UPDATE works SET expert_id = ? WHERE id = ?",
            (expert_id, work_id)
        )

    def get(self, work_id):
        row = self.db.fetch_one("SELECT * FROM works WHERE id = ?", (work_id,))
        return dict(row) if row else None

    def get_by_source(self, source_path):
        row = self.db.fetch_one(
            "SELECT * FROM works WHERE source_path = ?", (str(source_path),)
        )
        return dict(row) if row else None

    # --- оплата и расходы ---
    def set_payment(self, work_id, amount, paid_date):
        self.db.execute(
            "UPDATE works SET paid_amount = ?, paid_date = ? WHERE id = ?",
            (float(amount), paid_date, work_id)
        )

    def add_expense(
        self, work_id, expense_date, category, amount,
        counterparty="", comment=""
    ):
        self.db.execute(
            """
            INSERT INTO work_expenses
                (work_id, date, category, amount, counterparty, comment)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (work_id, expense_date, category, float(amount),
             counterparty, comment)
        )

    def list_expenses(self, work_id):
        return [
            dict(row)
            for row in self.db.fetch_all(
                "SELECT * FROM work_expenses WHERE work_id = ? ORDER BY date",
                (work_id,)
            )
        ]

    def delete_expense(self, expense_id):
        self.db.execute("DELETE FROM work_expenses WHERE id = ?", (expense_id,))

    def update_expense(
        self, expense_id, expense_date, category, amount,
        counterparty="", comment=""
    ):
        self.db.execute(
            """
            UPDATE work_expenses
            SET date = ?, category = ?, amount = ?, counterparty = ?,
                comment = ?
            WHERE id = ?
            """,
            (expense_date, category, float(amount), counterparty,
             comment, expense_id)
        )

    def expenses_total(self, work_id):
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(amount), 0) AS total "
            "FROM work_expenses WHERE work_id = ?",
            (work_id,)
        )
        return float(row["total"]) if row else 0.0

    # --- статус для отображения ---
    @staticmethod
    def display_status(work):
        amount = float(work.get("amount") or 0)
        paid = float(work.get("paid_amount") or 0)
        if amount > 0 and paid >= amount:
            return "Оплачена"
        if paid > 0:
            return "Частично оплачена"
        return work.get("status") or "Запущена"
