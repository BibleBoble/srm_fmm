import unittest
from unittest.mock import Mock

from managers.tasks_manager import TasksManager


class TaskSearchTests(unittest.TestCase):
    def test_search_matches_comment_description_and_client_name(self):
        manager = TasksManager.__new__(TasksManager)
        manager.db = Mock()
        manager.db.fetch_all.return_value = []

        manager.search("product spec")

        query = manager.db.fetch_all.call_args.args[0]
        params = manager.db.fetch_all.call_args.args[1]
        self.assertIn("t.title", query)
        self.assertIn("t.description", query)
        self.assertIn("c.company", query)
        self.assertEqual(
            params,
            ["product", "product", "product", "spec", "spec", "spec"]
        )


if __name__ == "__main__":
    unittest.main()
