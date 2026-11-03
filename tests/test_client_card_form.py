import tkinter as tk
import unittest

from views.clients_view import ClientsView


class ClientCardFormTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_card_data_is_applied_to_form_fields(self):
        company = tk.Entry(self.root)
        address = tk.Entry(self.root)
        partner_fields = {
            "full_legal_name": tk.Entry(self.root),
            "inn_kpp": tk.Entry(self.root),
            "bank_details": tk.Text(self.root),
        }
        data = {
            "company": "ООО Тест",
            "address": "г. Москва",
            "full_legal_name": "Общество с ограниченной ответственностью «Тест»",
            "inn_kpp": "1234567890/123456789",
            "bank_details": "р/с 40702810000000000001",
        }

        filled = ClientsView._apply_client_card(
            data, company, address, partner_fields
        )

        self.assertEqual(filled, 5)
        self.assertEqual(company.get(), "ООО Тест")
        self.assertEqual(address.get(), "г. Москва")
        self.assertEqual(
            partner_fields["full_legal_name"].get(),
            "Общество с ограниченной ответственностью «Тест»"
        )
        self.assertEqual(partner_fields["inn_kpp"].get(), "1234567890/123456789")
        self.assertEqual(
            partner_fields["bank_details"].get("1.0", "end-1c"),
            "р/с 40702810000000000001"
        )

    def test_empty_values_do_not_overwrite_form(self):
        company = tk.Entry(self.root)
        company.insert(0, "Старое имя")
        address = tk.Entry(self.root)
        partner_fields = {"full_legal_name": tk.Entry(self.root)}

        filled = ClientsView._apply_client_card(
            {"company": "", "address": "", "full_legal_name": ""},
            company,
            address,
            partner_fields
        )

        self.assertEqual(filled, 0)
        self.assertEqual(company.get(), "Старое имя")


if __name__ == "__main__":
    unittest.main()
