# -*- coding: utf-8 -*-
"""Раздел «Отчёты»: выбор отчёта, фильтры, таблица и экспорт в Excel."""
import re
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

from managers.contracts_manager import ContractsManager
from managers.works_manager import WorksManager
from utils.date_utils import parse_ddmmyyyy
from views.base_view import BaseView

MONTH_NAMES = (
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
)

REPORTS = (
    ("Финансы", (
        ("income", "Доходы за период"),
        ("expenses", "Расходы за период"),
        ("profit", "Прибыль по месяцам"),
        ("debt", "Дебиторская задолженность"),
    )),
    ("Продажи", (
        ("funnel", "Воронка работ"),
        ("revenue_clients", "Выручка по клиентам"),
    )),
    ("Клиенты", (
        ("activity", "Активность клиентов"),
        ("interactions", "Статистика взаимодействий"),
    )),
    ("Задачи", (
        ("tasks", "Выполнение задач"),
    )),
    ("Документы", (
        ("contracts", "Реестр договоров"),
        ("specifications", "Реестр спецификаций"),
    )),
    ("УСН", (
        ("kudir", "КУДиР (доходы)"),
        ("usn", "Итоги УСН (6%)"),
    )),
)


def _money(value):
    return f"{float(value or 0):,.2f}".replace(",", " ").replace(".", ",")


def _date(value):
    if not value:
        return "—"
    text = str(value)
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return f"{text[8:10]}.{text[5:7]}.{text[0:4]}"
    return text


def _month_title(month):
    try:
        year, month_number = month.split("-")
        return f"{MONTH_NAMES[int(month_number)]} {year}"
    except (ValueError, IndexError):
        return month


class ReportsView(BaseView):
    """Экран отчётов: список, фильтры, таблица и экспорт."""

    def __init__(
        self,
        parent_frame,
        clients_mgr=None,
        tasks_mgr=None,
        interactions_mgr=None
    ):
        super().__init__(parent_frame)
        self.clients_mgr = clients_mgr
        self.tasks_mgr = tasks_mgr
        self.interactions_mgr = interactions_mgr
        self.works_mgr = WorksManager()
        self.contracts_mgr = ContractsManager()

        self.selected_report = "income"
        self.current_columns = []
        self.current_rows = []
        self.current_title = "Доходы за период"
        self.report_table = None
        self.summary_label = None
        self.period_from = None
        self.period_to = None
        self.client_filter = None
        self._client_ids = []

    # --- отрисовка ---
    def show(self):
        self.clear()
        self.parent_frame.configure(bg="white")

        header = tk.Frame(self.parent_frame, bg="white")
        header.pack(fill=tk.X, padx=20, pady=(16, 4))
        tk.Label(
            header, text="📊 Отчёты", font=("Arial", 22, "bold"),
            bg="white", fg="#172b4d"
        ).pack(side=tk.LEFT)
        tk.Label(
            header,
            text="Данные по работам, оплатам и документам",
            font=("Arial", 10), bg="white", fg="#64748b"
        ).pack(side=tk.LEFT, padx=14, pady=(8, 0))

        self._build_filters()
        self._build_body()

        self._select_default_report()
        self._render_selected()

    def _build_filters(self):
        filters = tk.Frame(self.parent_frame, bg="white")
        filters.pack(fill=tk.X, padx=20, pady=(4, 10))

        today = date.today()
        tk.Label(filters, text="Период с", bg="white").grid(
            row=0, column=0, sticky="w"
        )
        self.period_from = tk.StringVar(
            value=date(today.year, 1, 1).strftime("%d.%m.%Y")
        )
        ttk.Entry(filters, textvariable=self.period_from, width=12).grid(
            row=0, column=1, padx=(6, 12)
        )

        tk.Label(filters, text="по", bg="white").grid(row=0, column=2, sticky="w")
        self.period_to = tk.StringVar(value=today.strftime("%d.%m.%Y"))
        ttk.Entry(filters, textvariable=self.period_to, width=12).grid(
            row=0, column=3, padx=(6, 12)
        )

        tk.Label(filters, text="Клиент", bg="white").grid(
            row=0, column=4, sticky="w"
        )
        clients = []
        if self.clients_mgr is not None:
            try:
                clients = list(self.clients_mgr.get_all())
            except Exception:  # noqa: BLE001 - фильтр не критичен
                clients = []
        self._client_ids = [None]
        names = ["Все клиенты"]
        for client in clients:
            self._client_ids.append(client["id"])
            names.append(client["company"])
        self.client_filter = ttk.Combobox(
            filters, values=names, state="readonly", width=28
        )
        self.client_filter.current(0)
        self.client_filter.grid(row=0, column=5, padx=(6, 12))

        ttk.Button(
            filters, text="Сформировать", command=self._render_selected
        ).grid(row=0, column=6, padx=(6, 6))

        ttk.Button(
            filters, text="Экспорт в Excel", command=self._export_excel
        ).grid(row=0, column=7)

    def _build_body(self):
        body = tk.Frame(self.parent_frame, bg="white")
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 16))

        left = tk.Frame(body, bg="white")
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        self.report_tree = ttk.Treeview(left, show="tree", selectmode="browse")
        self.report_tree.column("#0", width=250)
        self.report_tree.pack(fill=tk.BOTH, expand=True)

        self.group_ids = set()
        for group, reports in REPORTS:
            self.group_ids.add(group)
            parent = self.report_tree.insert("", "end", iid=group, text=group, open=True)
            for report_id, title in reports:
                self.report_tree.insert(parent, "end", iid=report_id, text=title)

        self.report_tree.bind("<<TreeviewSelect>>", self._on_report_select)

        right = tk.Frame(body, bg="white")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.table_container = tk.Frame(right, bg="white")
        self.table_container.pack(fill=tk.BOTH, expand=True)

        self.summary_label = tk.Label(
            right, text="", font=("Arial", 10, "bold"),
            bg="white", fg="#172b4d", anchor="w"
        )
        self.summary_label.pack(fill=tk.X, pady=(8, 0))

    def _select_default_report(self):
        self.report_tree.selection_set(self.selected_report)
        self.report_tree.see(self.selected_report)

    def _on_report_select(self, event=None):
        selection = self.report_tree.selection()
        if not selection:
            return
        report_id = selection[0]
        if report_id in self.group_ids:
            return
        self.selected_report = report_id
        self._render_selected()

    # --- формирование ---
    def _period(self):
        start = parse_ddmmyyyy(self.period_from.get())
        end = parse_ddmmyyyy(self.period_to.get())
        if start is None or end is None:
            raise ValueError("Проверьте период: даты в формате ДД.ММ.ГГГГ.")
        if start > end:
            raise ValueError("Дата начала периода позже даты окончания.")
        return start.isoformat(), end.isoformat()

    def _selected_client_id(self):
        index = self.client_filter.current() if self.client_filter else 0
        if 0 <= index < len(self._client_ids):
            return self._client_ids[index]
        return None

    def _render_selected(self):
        if not hasattr(self, "table_container"):
            return
        try:
            columns, rows, summary = self._build_report(self.selected_report)
        except Exception as error:  # noqa: BLE001 - показываем пользователю
            messagebox.showerror(
                "Отчёты", f"Не удалось построить отчёт:\n{error}",
                parent=self.parent_frame
            )
            return

        self.current_columns = columns
        self.current_rows = rows
        self.current_title = self._report_title(self.selected_report)

        for child in self.table_container.winfo_children():
            child.destroy()

        table_frame = tk.Frame(self.table_container, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True)

        column_keys = [f"c{index}" for index in range(len(columns))]
        self.report_table = ttk.Treeview(
            table_frame, columns=column_keys, show="headings"
        )
        for index, column in enumerate(columns):
            key = column_keys[index]
            self.report_table.heading(key, text=column)
            self.report_table.column(
                key, width=110 if index == 0 else 190, anchor="center"
            )
        for row in rows:
            self.report_table.insert("", "end", values=row)

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.report_table.yview
        )
        self.report_table.configure(yscrollcommand=scrollbar.set)
        self.report_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.summary_label.config(text=summary)

    @staticmethod
    def _report_title(report_id):
        for _group, reports in REPORTS:
            for key, title in reports:
                if key == report_id:
                    return title
        return "Отчёт"

    def _build_report(self, report_id):
        builder = getattr(self, f"_report_{report_id}")
        return builder(*self._period(), self._selected_client_id())

    # --- отчёты ---
    def _report_income(self, start, end, client_id):
        query = """
            SELECT w.paid_date, c.company, w.title, w.paid_amount
            FROM works w
            JOIN clients c ON c.id = w.client_id
            WHERE w.paid_date IS NOT NULL
              AND w.paid_date BETWEEN ? AND ?
              AND w.paid_amount > 0
        """
        params = [start, end]
        if client_id is not None:
            query += " AND w.client_id = ?"
            params.append(client_id)
        query += " ORDER BY w.paid_date"
        rows = self.works_mgr.db.fetch_all(query, tuple(params))
        data = [
            [_date(row["paid_date"]), row["company"], row["title"],
             _money(row["paid_amount"])]
            for row in rows
        ]
        total = sum(float(row["paid_amount"] or 0) for row in rows)
        return (
            ["Дата", "Клиент", "Работа", "Сумма, руб."],
            data,
            f"Всего доходов за период: {_money(total)}"
        )

    def _report_expenses(self, start, end, client_id):
        query = """
            SELECT e.date, e.category, e.counterparty, c.company,
                   w.title, e.amount
            FROM work_expenses e
            JOIN works w ON w.id = e.work_id
            JOIN clients c ON c.id = w.client_id
            WHERE e.date BETWEEN ? AND ?
        """
        params = [start, end]
        if client_id is not None:
            query += " AND w.client_id = ?"
            params.append(client_id)
        query += " ORDER BY e.date"
        rows = self.works_mgr.db.fetch_all(query, tuple(params))
        data = [
            [_date(row["date"]), row["category"] or "", row["counterparty"] or "",
             row["company"], row["title"], _money(row["amount"])]
            for row in rows
        ]
        total = sum(float(row["amount"] or 0) for row in rows)
        return (
            ["Дата", "Категория", "Контрагент", "Клиент", "Работа", "Сумма, руб."],
            data,
            f"Всего расходов за период: {_money(total)}"
        )

    def _report_profit(self, start, end, client_id):
        client_condition = " AND w.client_id = ?" if client_id is not None else ""
        params = (start, end) + ((client_id,) if client_id is not None else ())

        income_rows = self.works_mgr.db.fetch_all(
            "SELECT substr(w.paid_date, 1, 7) AS month, "
            "SUM(w.paid_amount) AS total FROM works w "
            "WHERE w.paid_date BETWEEN ? AND ?"
            + client_condition
            + " GROUP BY month",
            params
        )
        expense_rows = self.works_mgr.db.fetch_all(
            "SELECT substr(e.date, 1, 7) AS month, SUM(e.amount) AS total "
            "FROM work_expenses e JOIN works w ON w.id = e.work_id "
            "WHERE e.date BETWEEN ? AND ?"
            + client_condition
            + " GROUP BY month",
            params
        )
        income = {row["month"]: float(row["total"] or 0) for row in income_rows}
        expenses = {row["month"]: float(row["total"] or 0) for row in expense_rows}

        data = []
        total_income = 0.0
        total_expenses = 0.0
        for month in sorted(set(income) | set(expenses)):
            month_income = income.get(month, 0.0)
            month_expenses = expenses.get(month, 0.0)
            total_income += month_income
            total_expenses += month_expenses
            margin = (
                f"{(month_income - month_expenses) / month_income * 100:.0f}%"
                if month_income else "—"
            )
            data.append([
                _month_title(month), _money(month_income),
                _money(month_expenses), _money(month_income - month_expenses),
                margin
            ])

        return (
            ["Месяц", "Доходы", "Расходы", "Прибыль", "Маржа"],
            data,
            f"Доходы: {_money(total_income)} | Расходы: {_money(total_expenses)} "
            f"| Прибыль: {_money(total_income - total_expenses)}"
        )

    def _report_debt(self, start, end, client_id):
        query = """
            SELECT c.company, w.title, w.amount, w.paid_amount,
                   (w.amount - w.paid_amount) AS debt
            FROM works w
            JOIN clients c ON c.id = w.client_id
            WHERE w.amount > w.paid_amount
        """
        params = []
        if client_id is not None:
            query += " AND w.client_id = ?"
            params.append(client_id)
        query += " ORDER BY debt DESC"
        rows = self.works_mgr.db.fetch_all(query, tuple(params))

        data = [
            [
                row["company"], row["title"], _money(row["amount"]),
                _money(row["paid_amount"]), _money(row["debt"])
            ]
            for row in rows
        ]
        total = sum(float(row["debt"] or 0) for row in rows)
        return (
            ["Клиент", "Работа", "Сумма", "Оплачено", "Долг"],
            data,
            f"Общая задолженность: {_money(total)}"
        )

    def _report_funnel(self, start, end, client_id):
        query = """
            SELECT w.status, COUNT(*) AS cnt,
                   COALESCE(SUM(w.amount), 0) AS amount,
                   COALESCE(SUM(w.paid_amount), 0) AS paid
            FROM works w
        """
        params = []
        if client_id is not None:
            query += " WHERE w.client_id = ?"
            params.append(client_id)
        query += " GROUP BY w.status ORDER BY cnt DESC"
        rows = self.works_mgr.db.fetch_all(query, tuple(params))

        data = [
            [row["status"] or "—", str(row["cnt"]), _money(row["amount"]),
             _money(row["paid"])]
            for row in rows
        ]
        total = sum(int(row["cnt"]) for row in rows)
        return (
            ["Статус", "Работ", "Сумма", "Оплачено"],
            data,
            f"Всего работ: {total}"
        )

    def _report_revenue_clients(self, start, end, client_id):
        query = """
            SELECT c.company, COUNT(*) AS cnt, SUM(w.paid_amount) AS total
            FROM works w
            JOIN clients c ON c.id = w.client_id
            WHERE w.paid_date BETWEEN ? AND ? AND w.paid_amount > 0
        """
        params = [start, end]
        if client_id is not None:
            query += " AND w.client_id = ?"
            params.append(client_id)
        query += " GROUP BY c.id ORDER BY total DESC"
        rows = self.works_mgr.db.fetch_all(query, tuple(params))

        data = [
            [row["company"], str(row["cnt"]), _money(row["total"])]
            for row in rows
        ]
        total = sum(float(row["total"] or 0) for row in rows)
        return (
            ["Клиент", "Работ", "Выручка, руб."],
            data,
            f"Всего выручки: {_money(total)}"
        )

    def _report_activity(self, start, end, client_id):
        query = """
            SELECT c.id, c.company, MAX(i.date) AS last_contact,
                   (SELECT COUNT(*) FROM works w WHERE w.client_id = c.id)
                       AS works_count
            FROM clients c
            LEFT JOIN interaction_history i ON i.client_id = c.id
        """
        params = []
        if client_id is not None:
            query += " WHERE c.id = ?"
            params.append(client_id)
        query += " GROUP BY c.id ORDER BY c.company"
        rows = self.works_mgr.db.fetch_all(query, tuple(params))

        today = date.today()
        data = []
        for row in rows:
            last_contact = row["last_contact"]
            if last_contact:
                try:
                    days = (today - date.fromisoformat(str(last_contact)[:10])).days
                    days_text = str(days)
                except ValueError:
                    days_text = "—"
            else:
                days_text = "—"
            data.append([
                row["company"], _date(last_contact), days_text,
                str(row["works_count"])
            ])
        return (
            ["Клиент", "Последний контакт", "Дней без контакта", "Работ"],
            data,
            f"Клиентов в базе: {len(rows)}"
        )

    def _report_interactions(self, start, end, client_id):
        query = """
            SELECT type, COUNT(*) AS cnt
            FROM interaction_history
            WHERE date BETWEEN ? AND ?
        """
        params = [start, end]
        if client_id is not None:
            query += " AND client_id = ?"
            params.append(client_id)
        query += " GROUP BY type ORDER BY cnt DESC"
        rows = self.works_mgr.db.fetch_all(query, tuple(params))

        data = [[row["type"], str(row["cnt"])] for row in rows]
        total = sum(int(row["cnt"]) for row in rows)
        return (
            ["Тип взаимодействия", "Количество"],
            data,
            f"Всего взаимодействий: {total}"
        )

    def _report_tasks(self, start, end, client_id):
        query = """
            SELECT COALESCE(c.company, 'Без клиента') AS company,
                   COUNT(*) AS total,
                   SUM(CASE WHEN t.completed = 1 THEN 1 ELSE 0 END) AS done,
                   SUM(CASE WHEN t.completed = 0
                            AND t.due_date < date('now') THEN 1 ELSE 0 END) AS overdue
            FROM tasks t
            LEFT JOIN clients c ON c.id = t.client_id
        """
        params = []
        if client_id is not None:
            query += " WHERE t.client_id = ?"
            params.append(client_id)
        query += " GROUP BY t.client_id ORDER BY total DESC"
        rows = self.works_mgr.db.fetch_all(query, tuple(params))

        data = [
            [row["company"], str(row["total"]), str(row["done"] or 0),
             str(row["overdue"] or 0)]
            for row in rows
        ]
        total = sum(int(row["total"]) for row in rows)
        overdue = sum(int(row["overdue"] or 0) for row in rows)
        return (
            ["Клиент", "Всего", "Выполнено", "Просрочено"],
            data,
            f"Всего задач: {total} | Просрочено: {overdue}"
        )

    def _report_contracts(self, start, end, client_id):
        rows = []
        seen = set()

        for item in self._contract_file_rows():
            if client_id is not None and item["client_id"] != client_id:
                continue
            key = (self._company_key(item["company"]), item["date"])
            if key in seen:
                continue
            seen.add(key)
            rows.append([
                item["number"], _date(item["date"]),
                item["company"], item["status"]
            ])

        query = """
            SELECT ct.number, ct.date, c.company, ct.status
            FROM contracts ct
            LEFT JOIN clients c ON c.id = ct.client_id
        """
        params = []
        if client_id is not None:
            query += " WHERE ct.client_id = ?"
            params.append(client_id)
        for row in self.works_mgr.db.fetch_all(query, tuple(params)):
            company = str(row["company"] or "—")
            key = (self._company_key(company), str(row["date"])[:10])
            if key in seen:
                continue
            seen.add(key)
            rows.append([
                row["number"], _date(row["date"]), company,
                self._contract_status(row["status"])
            ])

        rows.sort(key=lambda item: tuple(reversed(item[1].split("."))))
        return (
            ["Номер", "Дата", "Клиент", "Статус"],
            rows,
            f"Договоров: {len(rows)}"
        )

    def _contract_file_rows(self):
        """Договоры, найденные в папках клиентов (DOCX/PDF)."""
        root = Path(__file__).resolve().parents[1] / "clients_files"
        if not root.is_dir():
            return []

        rows = []
        try:
            client_dirs = sorted(
                (path for path in root.iterdir() if path.is_dir()),
                key=lambda path: path.name.casefold()
            )
        except OSError:
            return []

        for client_dir in client_dirs:
            if client_dir.is_symlink():
                continue
            contracts_dir = client_dir / "договоры"
            if not contracts_dir.is_dir():
                continue

            token = client_dir.name.split(" ", 1)[0]
            fallback = self.works_mgr.db.fetch_one(
                "SELECT id, company FROM clients WHERE public_id = ?",
                (token,)
            )
            if fallback is None and token.isdigit():
                fallback = self.works_mgr.db.fetch_one(
                    "SELECT id, company FROM clients WHERE id = ?",
                    (int(token),)
                )
            fallback_id = fallback["id"] if fallback else None
            fallback_name = (
                fallback["company"] if fallback
                else client_dir.name.split(" ", 1)[-1]
            )

            try:
                entries = sorted(
                    contracts_dir.iterdir(),
                    key=lambda path: path.name.casefold()
                )
            except OSError:
                continue

            for path in entries:
                if not path.is_file() or path.is_symlink():
                    continue
                if path.name.startswith("~$"):
                    continue
                if path.suffix.casefold() not in {".docx", ".doc", ".pdf"}:
                    continue
                if not path.name.casefold().startswith("договор"):
                    continue
                match = re.search(
                    r"договор\s+(.+?)\s+от\s+(\d{2})\.(\d{2})\.(\d{4})\s*(.*)$",
                    path.stem,
                    re.IGNORECASE
                )
                if not match:
                    continue
                company = match.group(5).strip() or fallback_name
                client_id = self._client_id_by_company(company, fallback_id)
                canonical = self._company_by_id(client_id)
                if canonical:
                    company = canonical
                rows.append({
                    "number": match.group(1).strip(),
                    "date": (
                        f"{match.group(4)}-{match.group(3)}-{match.group(2)}"
                    ),
                    "client_id": client_id,
                    "company": company,
                    "status": "Заключён",
                })
        return rows

    @staticmethod
    def _company_key(value):
        return re.sub(r"\s+", " ", str(value)).strip(" .").casefold()

    def _company_by_id(self, client_id):
        if client_id is None:
            return None
        row = self.works_mgr.db.fetch_one(
            "SELECT company FROM clients WHERE id = ?", (client_id,)
        )
        return row["company"] if row else None

    def _client_id_by_company(self, company, fallback_id=None):
        normalized = re.sub(r"\s+", " ", str(company)).strip(" .").casefold()
        for row in self.works_mgr.db.fetch_all(
            "SELECT id, company FROM clients"
        ):
            candidate = re.sub(
                r"\s+", " ", str(row["company"])
            ).strip(" .").casefold()
            if candidate == normalized:
                return row["id"]
        return fallback_id

    @staticmethod
    def _contract_status(status):
        value = str(status or "").strip().casefold()
        if value in {"active", "заключен", "заключён", "действует"}:
            return "Заключён"
        if value in {"closed", "закрыт", "закрытый"}:
            return "Закрыт"
        return str(status or "—")

    def _report_specifications(self, start, end, client_id):
        query = """
            SELECT c.company, w.title, w.start_date, w.amount, w.status
            FROM works w
            JOIN clients c ON c.id = w.client_id
        """
        params = []
        if client_id is not None:
            query += " WHERE w.client_id = ?"
            params.append(client_id)
        query += " ORDER BY w.start_date DESC"
        rows = self.works_mgr.db.fetch_all(query, tuple(params))

        data = [
            [row["company"], row["title"], _date(row["start_date"]),
             _money(row["amount"]), row["status"] or ""]
            for row in rows
        ]
        total = sum(float(row["amount"] or 0) for row in rows)
        return (
            ["Клиент", "Работа", "Дата", "Сумма, руб.", "Статус"],
            data,
            f"Работ: {len(rows)} | Сумма: {_money(total)}"
        )

    def _report_kudir(self, start, end, client_id):
        query = """
            SELECT w.paid_date, c.company, w.title, w.paid_amount
            FROM works w
            JOIN clients c ON c.id = w.client_id
            WHERE w.paid_date BETWEEN ? AND ? AND w.paid_amount > 0
        """
        params = [start, end]
        if client_id is not None:
            query += " AND w.client_id = ?"
            params.append(client_id)
        query += " ORDER BY w.paid_date"
        rows = self.works_mgr.db.fetch_all(query, tuple(params))

        data = []
        running = 0.0
        for row in rows:
            amount = float(row["paid_amount"] or 0)
            running += amount
            data.append([
                _date(row["paid_date"]),
                f"{row['company']} — {row['title']}",
                _money(amount),
                _money(running)
            ])
        return (
            ["Дата", "Основание", "Доход, руб.", "Нарастающий итог"],
            data,
            f"Итого доходов: {_money(running)}"
        )

    def _report_usn(self, start, end, client_id):
        query = """
            SELECT w.paid_date, w.paid_amount
            FROM works w
            WHERE w.paid_date BETWEEN ? AND ? AND w.paid_amount > 0
        """
        params = [start, end]
        if client_id is not None:
            query += " AND w.client_id = ?"
            params.append(client_id)
        rows = self.works_mgr.db.fetch_all(query, tuple(params))

        quarters = {}
        for row in rows:
            try:
                year = str(row["paid_date"])[:4]
                month = int(str(row["paid_date"])[5:7])
            except (TypeError, ValueError):
                continue
            quarter = (month - 1) // 3 + 1
            key = f"{year}-Q{quarter}"
            quarters[key] = quarters.get(key, 0.0) + float(row["paid_amount"] or 0)

        data = [
            [key, _money(total), _money(total * 0.06)]
            for key, total in sorted(quarters.items())
        ]
        total_income = sum(quarters.values())
        return (
            ["Квартал", "Доходы", "Налог 6%"],
            data,
            f"Доходы: {_money(total_income)} | Налог УСН 6%: "
            f"{_money(total_income * 0.06)}"
        )

    # --- экспорт ---
    def _export_excel(self):
        if not self.current_rows:
            messagebox.showinfo(
                "Отчёты", "Сначала сформируйте отчёт.",
                parent=self.parent_frame
            )
            return

        path = filedialog.asksaveasfilename(
            parent=self.parent_frame,
            title="Экспорт отчёта в Excel",
            defaultextension=".xlsx",
            filetypes=(("Excel", "*.xlsx"),),
            initialfile=f"{self.current_title}.xlsx"
        )
        if not path:
            return

        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = self.current_title[:31]
            sheet.append(list(self.current_columns))
            for cell in sheet[1]:
                cell.font = Font(bold=True)
            for row in self.current_rows:
                sheet.append([self._excel_value(value) for value in row])
            sheet.freeze_panes = "A2"

            for column_cells in sheet.columns:
                length = max(
                    len(str(cell.value or "")) for cell in column_cells
                )
                sheet.column_dimensions[
                    column_cells[0].column_letter
                ].width = min(60, length + 2)

            workbook.save(path)
        except Exception as error:  # noqa: BLE001 - показываем пользователю
            messagebox.showerror(
                "Отчёты", f"Не удалось сохранить файл:\n{error}",
                parent=self.parent_frame
            )
            return

        messagebox.showinfo(
            "Отчёты", f"Отчёт сохранён:\n{path}", parent=self.parent_frame
        )

    @staticmethod
    def _excel_value(value):
        text = str(value)
        if not text or text == "—":
            return None
        normalized = text.replace(" ", "").replace("₽", "").replace("%", "")
        if "," in normalized and normalized.replace(",", ".").replace(".", "").isdigit():
            try:
                return float(normalized.replace(",", "."))
            except ValueError:
                return text
        return text
