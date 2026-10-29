import tempfile
import unittest
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from utils.partner_card_reader import read_partner_card


class PartnerCardReaderTests(unittest.TestCase):
    def test_reads_labeled_partner_fields_from_docx(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body>
            <w:tbl>
              <w:tr>
                <w:tc><w:p><w:r><w:t>Полное наименование организации</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>ООО «Ромашка»</w:t></w:r></w:p></w:tc>
              </w:tr>
              <w:tr>
                <w:tc><w:p><w:r><w:t>Юридический адрес</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>Москва, ул. Тестовая, 1</w:t></w:r></w:p></w:tc>
              </w:tr>
              <w:tr>
                <w:tc><w:p><w:r><w:t>ИНН/КПП</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>1234567890/123456789</w:t></w:r></w:p></w:tc>
              </w:tr>
              <w:tr>
                <w:tc><w:p><w:r><w:t>ФИО директора</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>Василий Васильевич Пушкин</w:t></w:r></w:p></w:tc>
              </w:tr>
            </w:tbl>
          </w:body>
        </w:document>"""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partner.docx"
            with ZipFile(path, "w", compression=ZIP_DEFLATED) as document:
                document.writestr("word/document.xml", xml)

            fields = read_partner_card(path)

        self.assertEqual(fields["company"], "ООО «Ромашка»")
        self.assertEqual(fields["full_legal_name"], "ООО «Ромашка»")
        self.assertEqual(fields["legal_address"], "Москва, ул. Тестовая, 1")
        self.assertEqual(fields["postal_address"], "Москва, ул. Тестовая, 1")
        self.assertEqual(fields["inn_kpp"], "1234567890/123456789")
        self.assertEqual(fields["responsible_person"], "Василий Васильевич Пушкин")

    def test_rejects_non_word_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partner.txt"
            path.write_text("test", encoding="utf-8")

            with self.assertRaises(ValueError):
                read_partner_card(path)


if __name__ == "__main__":
    unittest.main()
