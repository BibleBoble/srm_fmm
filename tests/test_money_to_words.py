import unittest
from decimal import Decimal

from utils.money_to_words import amount_to_russian_words


class AmountToRussianWordsTests(unittest.TestCase):
    def test_formats_ruble_forms_and_kopecks(self):
        cases = {
            "0": "Ноль рублей 00 копеек",
            "1": "Один рубль 00 копеек",
            "2": "Два рубля 00 копеек",
            "5": "Пять рублей 00 копеек",
            "11": "Одиннадцать рублей 00 копеек",
            "21": "Двадцать один рубль 00 копеек",
            "101.05": "Сто один рубль 05 копеек",
            "1000": "Одна тысяча рублей 00 копеек",
        }

        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(
                    amount_to_russian_words(Decimal(value)),
                    expected
                )


if __name__ == "__main__":
    unittest.main()
