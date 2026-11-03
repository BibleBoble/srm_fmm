import tkinter as tk
import unittest

from managers.clients_manager import ClientsManager
from managers.database import Database
from managers.interactions_manager import InteractionsManager
from managers.tasks_manager import TasksManager
from managers.works_manager import WorksManager
from views.reports_view import ReportsView


class WorksReportsTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.db = Database()
        self.works_mgr = WorksManager()
        self.tasks_mgr = TasksManager()
        self.client_id = 21
        self.source = "__test_work_source__.docx"
        self.works_mgr._upsert(
            client_id=self.client_id,
            source_path=self.source,
            title="Тестовая работа",
            amount=1000.0,
            status="Выполнена",
            start_date="2026-10-01",
            completed_date="2026-10-10",
        )
        self.work = self.works_mgr.get_by_source(self.source)

    def tearDown(self):
        for expense in self.works_mgr.list_expenses(self.work["id"]):
            self.works_mgr.delete_expense(expense["id"])
        self.db.execute("DELETE FROM works WHERE id = ?", (self.work["id"],))
        self.root.destroy()

    def test_payment_and_expenses(self):
        self.works_mgr.set_payment(self.work["id"], 400, "2026-10-05")
        self.works_mgr.add_expense(
            self.work["id"], "2026-10-06", "Услуги", 150, "Контрагент", "тест"
        )

        updated = self.works_mgr.get(self.work["id"])
        self.assertEqual(updated["paid_amount"], 400)
        self.assertEqual(WorksManager.display_status(updated), "Частично оплачена")
        self.assertEqual(self.works_mgr.expenses_total(self.work["id"]), 150)
        self.assertEqual(len(self.works_mgr.list_expenses(self.work["id"])), 1)

    def _reports_view(self):
        return ReportsView(
            self.root, ClientsManager(), TasksManager(), InteractionsManager()
        )

    def test_income_report_contains_payment(self):
        self.works_mgr.set_payment(self.work["id"], 400, "2026-10-05")
        columns, rows, summary = self._reports_view()._report_income(
            "2026-10-01", "2026-10-31", self.client_id
        )

        self.assertEqual(columns[0], "Дата")
        self.assertTrue(any("400,00" in row[-1] for row in rows))
        self.assertIn("400,00", summary)

    def test_debt_report(self):
        self.works_mgr.set_payment(self.work["id"], 400, "2026-10-05")
        columns, rows, summary = self._reports_view()._report_debt(
            "2026-10-01", "2026-10-31", self.client_id
        )

        work_row = [
            row for row in rows if row[1] == "Тестовая работа"
        ]
        self.assertEqual(len(work_row), 1)
        self.assertEqual(work_row[0][4], "600,00")
        self.assertIn("Общая задолженность", summary)

    def test_financial_task_is_saved_with_work(self):
        task_id = self.tasks_mgr.add(
            "Фин. задача",
            client_id=self.client_id,
            is_financial=1,
            work_id=self.work["id"]
        )
        try:
            task = self.tasks_mgr.get_by_id(task_id)
            self.assertTrue(task.is_financial)
            self.assertEqual(task.work_id, self.work["id"])
        finally:
            self.tasks_mgr.delete(task_id)

    def test_expense_can_be_updated(self):
        self.works_mgr.add_expense(
            self.work["id"], "2026-10-01", "Другое", 100, "Кто-то", "черновик"
        )
        expense_id = max(
            item["id"]
            for item in self.works_mgr.list_expenses(self.work["id"])
        )

        self.works_mgr.update_expense(
            expense_id, "2026-10-02", "Налог", 60, "ФНС", "правка"
        )

        row = next(
            item for item in self.works_mgr.list_expenses(self.work["id"])
            if item["id"] == expense_id
        )
        self.assertEqual(row["date"], "2026-10-02")
        self.assertEqual(row["category"], "Налог")
        self.assertEqual(row["amount"], 60)
        self.assertEqual(row["counterparty"], "ФНС")
        self.assertEqual(row["comment"], "правка")

    def test_assign_expert_to_work(self):
        expert_id = self.db.execute(
            "INSERT INTO experts (name) VALUES (?)", ("Тестовый эксперт",)
        )
        try:
            self.works_mgr.set_expert(self.work["id"], expert_id)

            expert_works = self.works_mgr.list_works_for_expert(expert_id)
            self.assertEqual(
                [item["id"] for item in expert_works], [self.work["id"]]
            )

            all_works = self.works_mgr.list_works(self.client_id)
            row = next(
                item for item in all_works if item["id"] == self.work["id"]
            )
            self.assertEqual(row["expert_name"], "Тестовый эксперт")
        finally:
            self.works_mgr.set_expert(self.work["id"], None)
            self.db.execute(
                "DELETE FROM experts WHERE id = ?", (expert_id,)
            )

    def test_contract_company_key_ignores_dots_and_case(self):
        self.assertEqual(
            ReportsView._company_key("ИП Васильев А.А."),
            ReportsView._company_key("ип васильев а.а"),
        )

    def test_contract_status_is_translated(self):
        self.assertEqual(ReportsView._contract_status("active"), "Заключён")
        self.assertEqual(ReportsView._contract_status("closed"), "Закрыт")
        self.assertEqual(ReportsView._contract_status("Заключён"), "Заключён")

    def test_contracts_report_has_no_amount_column(self):
        columns, _rows, summary = self._reports_view()._report_contracts(
            "2026-01-01", "2026-12-31", None
        )

        self.assertEqual(columns, ["Номер", "Дата", "Клиент", "Статус"])
        self.assertIn("Договоров", summary)

    def test_kudir_running_total(self):
        self.works_mgr.set_payment(self.work["id"], 400, "2026-10-05")
        columns, rows, summary = self._reports_view()._report_kudir(
            "2026-10-01", "2026-10-31", self.client_id
        )

        work_row = [
            row for row in rows if "Тестовая работа" in row[1]
        ]
        self.assertEqual(len(work_row), 1)
        self.assertTrue(work_row[0][3].endswith("400,00"))


if __name__ == "__main__":
    unittest.main()
