import tempfile
import unittest
from pathlib import Path

from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement

from utils.python_document_generator import PythonDocumentGenerator


class PythonDocumentGeneratorTests(unittest.TestCase):
    def test_replaces_across_runs_and_preserves_surrounding_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "template.docx"
            document = Document()
            paragraph = document.add_paragraph()
            paragraph.add_run("Дата: [дата ")
            paragraph.add_run("договора], договор № [номер].")
            document.save(path)

            generator = PythonDocumentGenerator(
                path,
                {
                    "[дата договора]": "29 октября 2026 года",
                    "[номер]": "4"
                }
            )
            result = generator._load_document()
            generator._populate_document(result, highlight=False)

        self.assertEqual(
            result.paragraphs[0].text,
            "Дата: 29 октября 2026 года, договор № 4."
        )
        generator.close()

    def test_replaces_placeholders_inside_hyperlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "template.docx"
            document = Document()
            paragraph = document.add_paragraph()
            hyperlink = OxmlElement("w:hyperlink")
            run = OxmlElement("w:r")
            text = OxmlElement("w:t")
            text.text = "[email]"
            run.append(text)
            hyperlink.append(run)
            paragraph._p.append(hyperlink)
            document.save(path)

            generator = PythonDocumentGenerator(path, {"[email]": "user@example.com"})
            result = generator._load_document()
            generator._populate_document(result, highlight=False)

        self.assertEqual(result.paragraphs[0].text, "user@example.com")
        generator.close()

    def test_adds_and_highlights_service_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "template.docx"
            document = Document()
            table = document.add_table(rows=3, cols=4)
            for index, value in enumerate(("№", "Наименование", "Срок", "Сумма")):
                table.rows[0].cells[index].text = value
            table.rows[1].cells[0].text = "1"
            table.rows[2].cells[0].text = "Итого"
            document.save(path)

            generator = PythonDocumentGenerator(
                path,
                {},
                line_items=[
                    {"name": "Услуга 1", "term": "10 дней", "amount": "100,00"},
                    {"name": "Услуга 2", "term": "5 дней", "amount": "200,00"}
                ],
                line_table_index=1
            )
            result = generator._load_document()
            generator._populate_document(result, highlight=True)
            values = [
                [cell.text for cell in row.cells]
                for row in result.tables[0].rows
            ]
            highlighted = result.tables[0].rows[1].cells[1].paragraphs[0].runs[0]

        self.assertEqual(len(values), 4)
        self.assertEqual(values[1], ["1", "Услуга 1", "10 дней", "100,00"])
        self.assertEqual(values[2], ["2", "Услуга 2", "5 дней", "200,00"])
        self.assertEqual(highlighted.font.highlight_color, WD_COLOR_INDEX.YELLOW)
        generator.close()

    def test_render_is_reused_when_saving(self):
        with tempfile.TemporaryDirectory() as directory:
            template = Path(directory) / "template.docx"
            document = Document()
            document.add_paragraph("[name]")
            document.save(template)

            generator = PythonDocumentGenerator(template, {"[name]": "ООО Тест"})
            data = generator.render()
            target = Path(directory) / "result.docx"
            generator.save_docx(target)

            self.assertEqual(target.read_bytes(), data)
            self.assertIs(generator.render(), data)
            self.assertIn("ООО Тест", Document(target).paragraphs[0].text)

    def test_unknown_placeholder_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            template = Path(directory) / "template.docx"
            document = Document()
            document.add_paragraph("[name] [unknown]")
            document.save(template)

            generator = PythonDocumentGenerator(template, {"[name]": "ООО Тест"})

            with self.assertRaises(ValueError) as raised:
                generator.render()
            self.assertIn("[unknown]", str(raised.exception))

    def test_save_docx_does_not_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            template = Path(directory) / "template.docx"
            document = Document()
            document.add_paragraph("[name]")
            document.save(template)
            target = Path(directory) / "result.docx"
            target.write_bytes(b"existing")

            generator = PythonDocumentGenerator(template, {"[name]": "ООО Тест"})

            with self.assertRaises(FileExistsError):
                generator.save_docx(target)
            self.assertEqual(target.read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()
