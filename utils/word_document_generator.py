import os
import re
import shutil
import tempfile
from pathlib import Path


class WordDocumentGenerator:
    """Создаёт жёлтый предпросмотр и финальные DOCX/PDF из шаблонов Word."""

    def __init__(self, template_path, replacements, line_items=None, line_table_index=None):
        if os.name != "nt":
            raise OSError("Создание документов по шаблонам поддерживается только в Windows.")

        self.template_path = Path(template_path)
        if not self.template_path.is_file():
            raise FileNotFoundError(f"Не найден шаблон документа: {self.template_path}")

        try:
            import win32com.client
        except ImportError as error:
            raise RuntimeError(
                "Для работы с шаблонами требуется Microsoft Word и зависимость pywin32."
            ) from error

        self.replacements = replacements
        self.line_items = line_items or []
        self.line_table_index = line_table_index
        self._word = None
        self._preview_document = None
        self._closed = False
        self._temporary_directory = Path(tempfile.mkdtemp(prefix="srm-document-preview-"))
        self._preview_path = self._temporary_directory / "preview.docx"

        try:
            self._word = win32com.client.DispatchEx("Word.Application")
            self._word.Visible = False
            self._word.DisplayAlerts = 0
            self._word.AutomationSecurity = 3
        except Exception:
            self.close()
            raise

    def show_preview(self):
        document = self._open_template()
        try:
            self._populate_document(document, highlight=True)
            document.SaveAs2(str(self._preview_path), 16)
        except Exception:
            document.Close(0)
            raise
        document.Close(0)

        self._preview_document = self._word.Documents.Open(
            str(self._preview_path),
            False,
            True,
            False
        )
        self._word.Visible = True
        self._preview_document.Activate()

    def save(self, docx_path, pdf_path):
        docx_path = Path(docx_path)
        pdf_path = Path(pdf_path)
        if docx_path.exists() or pdf_path.exists():
            raise FileExistsError("Документ с таким именем уже существует.")

        self._close_preview()
        document = self._open_template()
        try:
            self._populate_document(document, highlight=False)
            document.SaveAs2(str(docx_path), 16)
            document.ExportAsFixedFormat(str(pdf_path), 17)
        except Exception:
            try:
                document.Close(0)
            finally:
                docx_path.unlink(missing_ok=True)
                pdf_path.unlink(missing_ok=True)
            raise
        document.Close(0)
        if not docx_path.is_file() or not pdf_path.is_file():
            docx_path.unlink(missing_ok=True)
            pdf_path.unlink(missing_ok=True)
            raise OSError("Word не создал DOCX- и PDF-файлы.")

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self._close_preview()
        finally:
            try:
                if self._word is not None:
                    self._word.Quit()
            finally:
                shutil.rmtree(self._temporary_directory, ignore_errors=False)

    def _open_template(self):
        if self._closed or self._word is None:
            raise RuntimeError("Окно предпросмотра документа уже закрыто.")
        return self._word.Documents.Open(
            str(self.template_path),
            False,
            True,
            False
        )

    def _close_preview(self):
        if self._preview_document is not None:
            self._preview_document.Close(0)
            self._preview_document = None

    def _populate_document(self, document, highlight):
        for placeholder, value in sorted(
            self.replacements.items(),
            key=lambda item: len(item[0]),
            reverse=True
        ):
            for story_range in self._story_ranges(document):
                self._replace_text(
                    story_range,
                    placeholder,
                    str(value),
                    highlight
                )

        if self.line_table_index is not None:
            self._populate_line_table(document, highlight)

        unresolved_fields = set()
        for story_range in self._story_ranges(document):
            unresolved_fields.update(
                re.findall(r"\[[^\]]+\]", str(story_range.Text))
            )
        unresolved = sorted(unresolved_fields)
        if unresolved:
            raise ValueError(
                "В шаблоне остались незаполненные поля: " + ", ".join(unresolved)
            )

    @staticmethod
    def _story_ranges(document):
        for first_range in document.StoryRanges:
            story_range = first_range
            while story_range is not None:
                yield story_range
                story_range = story_range.NextStoryRange

    @staticmethod
    def _replace_text(story_range, placeholder, replacement, highlight):
        story_start = story_range.Start
        search_end = story_range.End
        while search_end > story_start:
            search_range = story_range.Duplicate
            search_range.SetRange(story_start, search_end)
            finder = search_range.Find
            finder.ClearFormatting()
            finder.Text = placeholder
            finder.Forward = False
            finder.Wrap = 0
            finder.MatchCase = True
            finder.MatchWildcards = False

            if not finder.Execute():
                return

            replacement_range = search_range.Duplicate
            start = replacement_range.Start
            replacement_range.Text = replacement
            replacement_length = len(replacement.encode("utf-16-le")) // 2
            if highlight and replacement_length:
                replacement_range.HighlightColorIndex = 7
            search_end = start

    def _populate_line_table(self, document, highlight):
        table = document.Tables.Item(self.line_table_index)
        if table.Rows.Count < 2:
            raise ValueError("В шаблоне не найдена строка для услуг.")

        for index, item in enumerate(self.line_items):
            if index == 0:
                row = table.Rows.Item(2)
            elif table.Rows.Count > 2:
                # Insert each extra service before the template's final total row.
                row = table.Rows.Add(table.Rows.Item(table.Rows.Count))
            else:
                row = table.Rows.Add()
            values = (
                str(index + 1),
                item["name"],
                item["term"],
                item["amount"],
            )
            if row.Cells.Count != len(values):
                raise ValueError("Структура таблицы услуг в шаблоне не совпадает с ожидаемой.")
            for cell_index, value in enumerate(values, start=1):
                cell = row.Cells.Item(cell_index)
                cell.Range.Text = str(value)
                if highlight:
                    content_end = cell.Range.End - 1
                    if content_end > cell.Range.Start:
                        document.Range(cell.Range.Start, content_end).HighlightColorIndex = 7
