import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from utils.specification_reader import read_specification_summary


class SpecificationReaderTests(unittest.TestCase):
    def test_reads_service_names_and_total_from_docx_table(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body>
            <w:tbl>
              <w:tr>
                <w:tc><w:p><w:r><w:t>№</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>Наименование</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>Срок</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>Сумма</w:t></w:r></w:p></w:tc>
              </w:tr>
              <w:tr>
                <w:tc><w:p><w:r><w:t>1</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>Оценка продукции</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>10 дней</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>1 250,00</w:t></w:r></w:p></w:tc>
              </w:tr>
              <w:tr>
                <w:tc><w:p><w:r><w:t>2</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>Выдача сертификата</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>5 дней</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>250,00</w:t></w:r></w:p></w:tc>
              </w:tr>
              <w:tr>
                <w:tc><w:p><w:r><w:t>Итого:</w:t></w:r></w:p></w:tc>
                <w:tc><w:p><w:r><w:t>1 500,00</w:t></w:r></w:p></w:tc>
              </w:tr>
            </w:tbl>
          </w:body>
        </w:document>"""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "specification.docx"
            with ZipFile(path, "w", compression=ZIP_DEFLATED) as document:
                document.writestr("word/document.xml", xml)

            summary = read_specification_summary(path)

        self.assertEqual(
            summary.services,
            ("Оценка продукции", "Выдача сертификата")
        )
        self.assertEqual(summary.total, Decimal("1500.00"))


if __name__ == "__main__":
    unittest.main()
