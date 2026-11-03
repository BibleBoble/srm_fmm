import tempfile
import unittest
from pathlib import Path

from docx import Document

from utils.client_card_reader import read_client_card


class ClientCardReaderTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(prefix="srm-card-test-"))

    def _save(self, document, name="card.docx"):
        path = self.directory / name
        document.save(path)
        return path

    def test_requisites_table_card(self):
        document = Document()
        document.add_paragraph("КАРТОЧКА")
        document.add_paragraph(
            "Генеральный директор МАЛЫГИНА ИРИНА ВЛАДИМИРОВНА И.В. Малыгина"
        )
        rows = [
            ("Полное наименование юридического лица на русском языке",
             "Акционерное общество «Центр перспективных технологий»"),
            ("Сокращенное наименование юридического лица на русском языке", "АО «ЦПТ»"),
            ("Адрес", "115409, Москва, Каширское шоссе, дом 44, корпус 2"),
            ("Телефон", "(499) 323-37-10"),
            ("Идентификационный номер ИНН", "7724185856/772401001"),
            ("Основной государственный регистрационный номер ОГРН", "1027700343626"),
            ("Расчетный счет", "40702810724000018886"),
            ("Корреспондентский счет", "30101810500000000976"),
            ("Полное наименование учреждения банка",
             'АКБ "Абсолют Банк" (ПАО) БИК 044525976'),
        ]
        table = document.add_table(rows=len(rows), cols=2)
        for index, (label, value) in enumerate(rows):
            table.cell(index, 0).text = label
            table.cell(index, 1).text = value

        data = read_client_card(self._save(document))

        self.assertEqual(data["company"], "АО «ЦПТ»")
        self.assertEqual(
            data["full_legal_name"],
            "Акционерное общество «Центр перспективных технологий»"
        )
        self.assertEqual(data["inn_kpp"], "7724185856/772401001")
        self.assertEqual(data["ogrn"], "1027700343626")
        self.assertIn("р/с 40702810724000018886", data["bank_details"])
        self.assertIn("БИК 044525976", data["bank_details"])
        self.assertEqual(data["bank_details"].count("БИК"), 1)
        self.assertEqual(data["responsible_person"], "Малыгина Ирина Владимировна")
        self.assertEqual(data["partner_phone"], "(499) 323-37-10")

    def test_combined_card_with_contacts(self):
        document = Document()
        rows = [
            ("Организационно-правовая форма", "Общество с ограниченной ответственностью"),
            ("Фирменное наименование", "Общество с ограниченной ответственностью «Фаза»"),
            ("Сокращенное наименование", "ООО «Фаза»"),
            ("ИНН/КПП", "1840052461/184001001"),
            ("ОГРН", "1161832055054"),
            ("Банковские реквизиты",
             "Расчетный счет: 40702810202500130714 БИК: 044525104"),
            ("Генеральный директор",
             "Гущин Сергей Александрович, действует на основании Устава"),
            ("Контакты",
             "Отдел продаж 8(904) 248-43-52; E-mail: gushinser@mail.ru;"),
        ]
        table = document.add_table(rows=len(rows), cols=2)
        for index, (label, value) in enumerate(rows):
            table.cell(index, 0).text = label
            table.cell(index, 1).text = value

        data = read_client_card(self._save(document))

        self.assertEqual(data["company"], "ООО «Фаза»")
        self.assertEqual(data["inn_kpp"], "1840052461/184001001")
        self.assertIn("40702810202500130714", data["bank_details"])
        self.assertEqual(data["responsible_person"], "Гущин Сергей Александрович")
        self.assertEqual(data["partner_email"], "gushinser@mail.ru")
        self.assertEqual(data["partner_phone"], "8(904) 248-43-52")

    def test_short_card_with_separate_bank_rows(self):
        document = Document()
        rows = [
            ("Полное наименование",
             "Общество с ограниченной ответственностью «Электропоставка»"),
            ("Сокращенное наименование",
             "ООО «Электропоставка» Открыт 16/04/2008г."),
            ("Юридический адрес", ". Москва, ул. Соловьиная роща 12/4 - 9"),
            ("ИНН/КПП", "7733652708 / 773301001"),
            ("Расчетный счет", "40702810200001434759"),
            ("Банк получателя", "АО «Райффайзенбанк»"),
            ("БИК Банка", "044525700"),
            ("к/с", "30101810200000000700"),
            ("ОГРН", "1087746522698 от 16/04/2008г."),
            ("Ген. директор", "Ростомян Гайк Генрикович"),
        ]
        table = document.add_table(rows=len(rows), cols=2)
        for index, (label, value) in enumerate(rows):
            table.cell(index, 0).text = label
            table.cell(index, 1).text = value
        document.add_paragraph("Эл.почта: info@elektropost.ru Сайт: www.elektropost.ru")
        document.add_paragraph("тел.(495) 790-78-54")

        data = read_client_card(self._save(document))

        self.assertEqual(data["company"], "ООО «Электропоставка»")
        self.assertEqual(data["legal_address"], "Москва, ул. Соловьиная роща 12/4 - 9")
        self.assertEqual(data["inn_kpp"], "7733652708/773301001")
        self.assertEqual(data["ogrn"], "1087746522698")
        self.assertIn("БИК 044525700", data["bank_details"])
        self.assertIn("к/с 30101810200000000700", data["bank_details"])
        self.assertEqual(data["responsible_person"], "Ростомян Гайк Генрикович")
        self.assertEqual(data["partner_email"], "info@elektropost.ru")
        self.assertEqual(data["partner_phone"], "(495) 790-78-54")

    def test_blank_document_returns_empty_fields(self):
        document = Document()
        document.add_paragraph("КАРТОЧКА ПАРТНЁРА")

        data = read_client_card(self._save(document))

        self.assertEqual(data["company"], "")
        self.assertEqual(data["inn_kpp"], "")
        self.assertEqual(data["partner_email"], "")


if __name__ == "__main__":
    unittest.main()
