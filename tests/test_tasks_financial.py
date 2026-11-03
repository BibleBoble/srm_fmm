import tkinter as tk
import unittest

from managers.clients_manager import ClientsManager
from managers.tasks_manager import TasksManager
from views.tasks_view import TasksView


class FinancialTasksFilterTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.tasks = TasksManager()
        self.view = TasksView(self.root, self.tasks, ClientsManager())
        self.view.show()
        self.task_id = self.tasks.add(
            "Финансовая тестовая задача", client_id=21, is_financial=1
        )

    def tearDown(self):
        self.tasks.delete(self.task_id)
        self.root.destroy()

    def test_financial_tasks_hidden_by_default(self):
        self.assertFalse(self.view.show_financial_var.get())

        items, _total = self.view._get_data(1, "", None, "ASC")

        self.assertFalse(
            any(getattr(task, "is_financial", False) for task in items)
        )

    def test_financial_tasks_shown_when_enabled(self):
        self.view.show_financial_var.set(True)

        items, _total = self.view._get_data(1, "", None, "ASC")

        self.assertTrue(
            any(getattr(task, "is_financial", False) for task in items)
        )


if __name__ == "__main__":
    unittest.main()
