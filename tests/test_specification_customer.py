import tempfile
import unittest
from pathlib import Path

from docx import Document

from utils.specification_reader import read_specification_customer


class SpecificationCustomerTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(prefix="srm-spec-customer-"))

    def _save(self, text):
        document = Document()
        document.add_paragraph(text)
        path = self.directory / "spec.docx"
        document.save(path)
        return path

    def test_parses_position_and_person(self):
        path = self._save(
            "Заказчик: Общество с ограниченной ответственностью «Ромашка», "
            "в лице Генерального директора Пушкина Василия Васильевича, "
            "действующего на основании Устава"
        )

        data = read_specification_customer(path)

        self.assertEqual(
            data["company"], "Общество с ограниченной ответственностью «Ромашка»"
        )
        self.assertEqual(data["position_genitive"], "Генерального директора")
        self.assertEqual(
            data["person_genitive"], "Пушкина Василия Васильевича"
        )

    def test_parses_individual_entrepreneur(self):
        path = self._save(
            "Заказчик: ИП Бобалева, в лице Индивидуального предпринимателя "
            "Бобалевой Александры Олеговны"
        )

        data = read_specification_customer(path)

        self.assertEqual(data["position_genitive"], "Индивидуального предпринимателя")
        self.assertEqual(
            data["person_genitive"], "Бобалевой Александры Олеговны"
        )

    def test_missing_customer_line_returns_empty(self):
        path = self._save("Спецификация без строки заказчика")

        self.assertEqual(read_specification_customer(path), {})


if __name__ == "__main__":
    unittest.main()
