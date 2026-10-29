import unittest
from unittest.mock import Mock

from managers.clients_manager import ClientsManager


class ClientSearchTests(unittest.TestCase):
    def test_search_matches_each_term_across_client_fields(self):
        manager = ClientsManager.__new__(ClientsManager)
        manager.db = Mock()
        manager.db.fetch_all.return_value = []

        manager.search("оценка б")

        query = manager.db.fetch_all.call_args.args[0]
        params = manager.db.fetch_all.call_args.args[1]
        self.assertIn(" AND ", query)
        self.assertEqual(
            params,
            [
                "оценка", "оценка", "оценка", "оценка", "%оценка%",
                "б", "б", "б", "б", "%б%"
            ]
        )


if __name__ == "__main__":
    unittest.main()
