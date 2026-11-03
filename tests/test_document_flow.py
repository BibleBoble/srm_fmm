import shutil
import tempfile
import tkinter as tk
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from tkinter import ttk
from unittest.mock import Mock, patch

from docx import Document

from managers.clients_manager import ClientsManager
from managers.tasks_manager import TasksManager
from models.task import Task
from utils.python_document_generator import PythonDocumentGenerator
from views.client_card_view import ClientCardView


class DocumentFlowTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.manager = ClientsManager()
        self.client = dict(self.manager.get_by_id(21))
        self.card = ClientCardView(
            self.root, self.client["id"], self.manager, None, None, None
        )
        self.card.client_data = self.client
        self.card.card_window = self.root
        self.card.documents_status = tk.Label(self.root)
        self.card.document_service = Mock()
        self.card._refresh_documents = Mock()
        self.card._refresh_completed_works = Mock()
        self.card.contracts_mgr = Mock()
        self.directory = Path(tempfile.mkdtemp(prefix="srm-flow-test-"))
        self.items = [
            {"name": "Услуга", "term": "2", "amount": Decimal("1000.00")}
        ]

    def tearDown(self):
        shutil.rmtree(self.directory, ignore_errors=True)
        self.root.destroy()

    def _values(self):
        values = {
            field["key"]: field.get("value", "")
            for field in self.card._document_form_fields("contract")
        }
        values.update({
            "document_date": "01.10.2026",
            "company": "ООО Тест",
            "responsible_person": "Пушкин Василий Васильевич",
            "inn_kpp": "7610015191/761001001",
            "legal_address": "г. Москва",
            "signature_position": "Директор",
            "signature_short_name": "Пушкин В.В.",
            "bank_details": "р/с 40702810",
        })
        return values

    def test_invalid_date_reopens_form_instead_of_closing(self):
        bad_values = self._values()
        bad_values["document_date"] = "32.13.2026"
        dialog_results = [
            {"values": bad_values, "line_items": self.items},
            {"values": self._values(), "line_items": self.items},
        ]

        with (
            patch(
                "views.client_card_view.show_document_input_dialog",
                side_effect=dialog_results
            ) as dialog,
            patch.object(self.card, "_confirm_document", return_value=True),
            patch("views.client_card_view.messagebox.showerror") as showerror,
            patch("views.client_card_view.os.startfile", create=True),
        ):
            self.card._create_template_document(
                "contract", self.directory, "1"
            )

        self.assertEqual(dialog.call_count, 2)
        showerror.assert_called_once()
        self.assertIn("Проверка данных", showerror.call_args.args[0])
        created = list(self.directory.glob("*.docx"))
        self.assertEqual(len(created), 1)

    def test_preview_is_highlighted_and_does_not_create_document(self):
        generator = Mock()
        generator.render.return_value = b"docx-bytes"

        with patch("views.client_card_view.os.startfile", create=True) as startfile:
            self.card._show_highlighted_preview([("Договор", generator)])

        generator.render.assert_called_once_with(highlight=True)
        startfile.assert_called_once()

    def test_act_is_built_from_specification(self):
        spec_dir = self.directory / "спецификации" / "спецификация 1"
        spec_dir.mkdir(parents=True)

        values = {
            field["key"]: field.get("value", "")
            for field in self.card._document_form_fields("specification")
        }
        values.update({
            "document_date": "01.10.2026",
            "contract_date": "15.09.2026",
            "company": "ООО Тест",
            "responsible_person": "Пушкин Василий Васильевич",
            "inn_kpp": "7610015191/761001001",
            "legal_address": "г. Москва",
            "signature_position": "Директор",
            "signature_short_name": "Пушкин В.В.",
        })
        line_items = [
            {"name": "Услуга из спецификации", "term": "5", "amount": Decimal("1000.00")}
        ]
        replacements, formatted, _ = self.card._document_replacements(
            "specification", 1, values, line_items
        )
        spec_generator = PythonDocumentGenerator(
            Path("clients_files/шаблон спецификации.docx"),
            replacements,
            line_items=formatted,
            line_table_index=1,
        )
        spec_path = spec_dir / "спецификация 1 к договору 2015-2026 ООО Тест.docx"
        spec_path.write_bytes(spec_generator.render())
        spec_generator.close()

        self.card.document_service = Mock()
        with (
            patch.object(self.card, "_choose_specification_folder", return_value=spec_dir),
            patch.object(self.card, "_ask_document_date", return_value=date(2026, 10, 1)),
            patch.object(self.card, "_confirm_document", return_value=True),
            patch.object(self.card, "_refresh_documents"),
            patch.object(self.card, "_refresh_completed_works"),
            patch("views.client_card_view.os.startfile", create=True),
        ):
            self.card._create_act()

        acts = list(spec_dir.glob("акт *.docx"))
        self.assertEqual(len(acts), 1)
        table_text = "\n".join(
            cell.text
            for table in Document(acts[0]).tables
            for row in table.rows
            for cell in row.cells
        )
        self.assertIn("Услуга из спецификации", table_text)

    def test_word_lock_files_are_removed(self):
        lock_file = self.directory / "~$договор.docx"
        lock_file.write_bytes(b"lock")
        self.card.documents_tree = ttk.Treeview(self.root)

        with patch.object(
            self.card, "_find_client_documents_dir", return_value=self.directory
        ):
            # В setUp метод заменён моком — вызываем реальную реализацию.
            ClientCardView._refresh_documents(self.card)

        self.assertFalse(lock_file.exists())

    def test_signature_position_is_saved_and_reused(self):
        try:
            self.card._save_signature_position("Генеральный директор")
            reloaded = dict(self.manager.get_by_id(self.client["id"]))
            self.assertEqual(
                reloaded.get("signature_position"), "Генеральный директор"
            )

            fields = {
                field["key"]: field.get("value")
                for field in self.card._document_form_fields("contract")
            }
            self.assertEqual(
                fields["signature_position"], "Генеральный директор"
            )
        finally:
            self.manager.db.execute(
                "UPDATE clients SET signature_position = NULL WHERE id = ?",
                (self.client["id"],),
            )
            self.card.client_data.pop("signature_position", None)

    def test_act_creates_financial_task(self):
        tasks_mgr = TasksManager()
        card = ClientCardView(
            self.root, self.client["id"], self.manager, None, None, tasks_mgr
        )
        card.client_data = self.client
        card.card_window = self.root

        card._create_financial_task(1, Path("акт.docx"), None)
        tasks = [
            task for task in tasks_mgr.get_all() if getattr(task, "is_financial", False)
        ]
        try:
            self.assertTrue(tasks)
            self.assertIn("акт 2015-2026-1", tasks[-1].title)
        finally:
            for task in tasks:
                tasks_mgr.delete(task.id)

    def test_financial_task_dialog_has_expenses_button(self):
        from views.tasks.forms import TaskFormDialog

        task = Task(
            id=1,
            title="Фин. задача",
            is_financial=True,
            work_id=1,
            client_id=self.client["id"]
        )
        dialog = TaskFormDialog(
            self.root, self.manager, lambda data: None, task=task
        )

        def collect_texts(widget):
            texts = []
            for child in widget.winfo_children():
                try:
                    texts.append(str(child.cget("text")))
                except Exception:
                    pass
                texts.extend(collect_texts(child))
            return texts

        try:
            self.assertTrue(
                any("Расходы" in text for text in collect_texts(dialog.dialog))
            )
        finally:
            dialog.dialog.destroy()

    def test_package_form_has_no_initials_field_and_today_date(self):
        fields = self.card._package_form_fields()
        keys = [field["key"] for field in fields]

        self.assertNotIn("signature_short_name", keys)
        contract_date = next(
            field["value"] for field in fields
            if field["key"] == "contract_date"
        )
        self.assertEqual(
            contract_date, date.today().strftime("%d.%m.%Y")
        )

    def test_iso_date_is_displayed_as_day_month_year(self):
        from views.client_card_view import _format_iso_date

        self.assertEqual(_format_iso_date("2026-12-10"), "10.12.2026")
        self.assertEqual(_format_iso_date(None), "—")

    def test_act_replacements_accept_specification_person(self):
        values = self._values()
        values["responsible_person"] = "Пушкин Василий"

        replacements, _items, _date = self.card._document_replacements(
            "act",
            1,
            values,
            self.items,
            person_genitive_override="Пушкина Василия Васильевича",
            position_genitive_override="Генерального директора"
        )

        self.assertEqual(
            replacements["[ответственное лицо]"], "Пушкина Василия Васильевича"
        )
        self.assertEqual(replacements["[Должность]"], "Генерального директора")

    def test_incomplete_full_name_is_rejected(self):
        values = self._values()
        values["responsible_person"] = "Пушкин Василий"

        with self.assertRaises(ValueError) as raised:
            self.card._document_replacements("contract", 1, values, self.items)

        self.assertIn("отчество", str(raised.exception))

    def test_incomplete_full_name_reopens_form(self):
        bad_values = self._values()
        bad_values["responsible_person"] = "Пушкин Василий"
        dialog_results = [
            {"values": bad_values, "line_items": self.items},
            {"values": self._values(), "line_items": self.items},
        ]

        with (
            patch(
                "views.client_card_view.show_document_input_dialog",
                side_effect=dialog_results
            ) as dialog,
            patch.object(self.card, "_confirm_document", return_value=True),
            patch("views.client_card_view.messagebox.showerror") as showerror,
            patch("views.client_card_view.os.startfile", create=True),
        ):
            self.card._create_template_document("contract", self.directory, "1")

        self.assertEqual(dialog.call_count, 2)
        showerror.assert_called_once()
        self.assertIn("отчество", showerror.call_args.args[1])

    def test_contract_date_is_saved_after_contract_creation(self):
        with (
            patch(
                "views.client_card_view.show_document_input_dialog",
                return_value={"values": self._values(), "line_items": self.items},
            ),
            patch.object(self.card, "_confirm_document", return_value=True),
            patch("views.client_card_view.os.startfile", create=True),
        ):
            self.card._create_template_document("contract", self.directory, "1")

        self.card.contracts_mgr.save_contract.assert_called_once()
        saved_date = self.card.contracts_mgr.save_contract.call_args.args[1]
        self.assertEqual(saved_date.strftime("%d.%m.%Y"), "01.10.2026")

    def test_confirmation_dialog_accepts_formatted_amounts(self):
        formatted = [
            {"name": "Услуга", "term": "1 день", "amount": "1000,00"}
        ]

        with patch.object(self.root, "wait_window", return_value=None):
            confirmed = self.card._confirm_document(
                "Договор",
                self._values(),
                formatted,
                date(2026, 10, 1),
                1
            )

        self.assertFalse(confirmed)
        for child in self.root.winfo_children():
            if isinstance(child, tk.Toplevel):
                child.destroy()

    def test_company_names_expand_legal_form_and_quote_name(self):
        full, short = self.card._company_names("ООО Ромашка")
        self.assertEqual(
            full, "Общество с ограниченной ответственностью «Ромашка»"
        )
        self.assertEqual(short, "ООО «Ромашка»")

        full_ip, short_ip = self.card._company_names("ИП Иванов Иван Иванович")
        self.assertEqual(
            full_ip, "Индивидуальный предприниматель Иванов Иван Иванович"
        )
        self.assertEqual(short_ip, "ИП Иванов Иван Иванович")

    def test_contract_uses_full_name_and_requisites_use_short_name(self):
        values = self._values()
        values["company"] = "ООО Ромашка"

        replacements, _, _ = self.card._document_replacements(
            "contract", 1, values, self.items
        )

        self.assertEqual(
            replacements["[название компании]"],
            "Общество с ограниченной ответственностью «Ромашка»"
        )
        self.assertEqual(
            replacements["[название компании кратко]"],
            "ООО «Ромашка»"
        )
        self.assertEqual(
            replacements["[название компании в формате( ООО «Техно-Центр»)]"],
            "ООО «Ромашка»"
        )


if __name__ == "__main__":
    unittest.main()
