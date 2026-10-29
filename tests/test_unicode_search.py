import sqlite3
import unittest

from managers.database import _casefold_sql_value, _fuzzy_contains


class UnicodeSearchTests(unittest.TestCase):
    def test_sqlite_search_matches_cyrillic_without_case_sensitivity(self):
        connection = sqlite3.connect(":memory:")
        connection.create_function(
            "CASEFOLD",
            1,
            _casefold_sql_value,
            deterministic=True
        )
        try:
            match = connection.execute(
                "SELECT CASEFOLD(?) LIKE ?",
                ("ООО Ромашка", "%ромашка%")
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertEqual(match, 1)

    def test_search_accepts_one_extra_character_typo(self):
        self.assertEqual(
            _fuzzy_contains("тестовая компания", "тьест"),
            1
        )


if __name__ == "__main__":
    unittest.main()
