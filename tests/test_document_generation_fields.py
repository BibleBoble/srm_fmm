import unittest
from decimal import Decimal

from views.client_card_view import ClientCardView


class DocumentGenerationFieldTests(unittest.TestCase):
    def test_initials_use_surname_for_both_full_name_orders(self):
        self.assertEqual(
            ClientCardView._document_initials("Василий Васильевич Пушкин"),
            "Пушкин В.В."
        )
        self.assertEqual(
            ClientCardView._document_initials("Пушкин Василий Васильевич"),
            "Пушкин В.В."
        )

    def test_declines_director_name_in_genitive(self):
        self.assertEqual(
            ClientCardView._document_name_genitive("Василий Васильевич Пушкин"),
            "Василия Васильевича Пушкина"
        )

    def test_specification_uses_contract_date_and_customer_case(self):
        view = ClientCardView.__new__(ClientCardView)
        view.client_id = 2016
        view.client_data = {
            "public_id": "2016-2026",
            "company": "ООО Тестовая компания"
        }
        values = {
            "document_date": "01.11.2026",
            "contract_date": "29.10.2026",
            "postal_address": "",
            "legal_address": "Москва",
            "phone": "",
            "signature_position": "Генеральный директор",
            "responsible_person": "Василий Васильевич Пушкин",
            "responsible_person_genitive": "Василия Васильевича Пушкина",
            "company": "ООО Тестовая компания",
            "inn_kpp": "123/456",
            "email": "",
            "signature_short_name": "Пушкин В.В."
        }

        replacements, _, _ = view._document_replacements(
            "specification",
            4,
            values,
            [{"name": "Оценка продукции", "term": "10", "amount": Decimal("100.00")}]
        )

        self.assertEqual(replacements["[29октября 2026г]"], "29октября 2026г")
        self.assertEqual(replacements["[Должность]"], "Генерального директора")
        self.assertEqual(replacements["[ответственное лицо]"], "Василия Васильевича Пушкина")
        self.assertEqual(
            replacements["[ответственное лицо в формате (Гущин С.А.)]"],
            "Пушкин В.В."
        )

    def test_contract_fills_current_template_compact_date_placeholder(self):
        view = ClientCardView.__new__(ClientCardView)
        view.client_id = 2016
        view.client_data = {"public_id": "2016-2026", "company": "ООО Тест"}
        values = {
            "document_date": "29.10.2026",
            "postal_address": "",
            "legal_address": "Москва",
            "phone": "",
            "signature_position": "Директор",
            "responsible_person": "Василий Васильевич Пушкин",
            "signature_short_name": "Пушкин В.В.",
            "company": "ООО Тест",
            "inn_kpp": "123/456",
            "email": "",
            "organization_name": "ООО Тест",
            "position_genitive": "Директора",
            "person_genitive": "Василия Васильевича Пушкина",
            "bank_details": ""
        }

        replacements, _, _ = view._document_replacements(
            "contract",
            "2016-2026",
            values,
            []
        )

        self.assertEqual(
            replacements["[дата в формате(01октября 2026года)]"],
            "29октября 2026года"
        )


if __name__ == "__main__":
    unittest.main()
