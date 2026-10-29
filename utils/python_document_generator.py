import copy
import hashlib
import os
import re
import shutil
import tempfile
from pathlib import Path


_WORD_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_WORD_TAG = f"{{{_WORD_NAMESPACE}}}"
_HIGHLIGHT_TAG = f"{_WORD_TAG}highlight"
_TEXT_TAG = f"{_WORD_TAG}t"
_RUN_PROPERTIES_TAG = f"{_WORD_TAG}rPr"
_YELLOW = "yellow"


class PythonDocumentGenerator:
    """Заполняет DOCX-шаблоны Python-кодом и создаёт PDF через Word."""

    def __init__(self, template_path, replacements, line_items=None, line_table_index=None):
        self.template_path = Path(template_path)
        if not self.template_path.is_file():
            raise FileNotFoundError(f"Не найден шаблон документа: {self.template_path}")

        self.replacements = replacements
        self.line_items = line_items or []
        self.line_table_index = line_table_index
        self._temporary_directory = Path(
            tempfile.mkdtemp(prefix="srm-python-document-")
        )
        self._preview_path = self._temporary_directory / "preview.docx"
        self._closed = False
        self._word = None
        self._preview_document = None

    def show_preview(self):
        document = self._load_document()
        self._populate_document(document, highlight=True)
        document.save(self._preview_path)
        self._word_application().Visible = True
        self._preview_document = self._word_application().Documents.Open(
            str(self._preview_path),
            False,
            True,
            False
        )
        self._preview_document.Activate()

    def save(self, docx_path, pdf_path):
        docx_path = Path(docx_path)
        pdf_path = Path(pdf_path)
        if docx_path.exists() or pdf_path.exists():
            raise FileExistsError("Документ с таким именем уже существует.")

        try:
            document = self._load_document()
            self._populate_document(document, highlight=False)
            document.save(docx_path)
            self._close_preview()
            word = self._word_application()
            word.Visible = False
            pdf_document = word.Documents.Open(
                str(docx_path),
                False,
                True,
                False
            )
            try:
                pdf_document.ExportAsFixedFormat(str(pdf_path), 17)
            finally:
                pdf_document.Close(0)
        except Exception:
            docx_path.unlink(missing_ok=True)
            pdf_path.unlink(missing_ok=True)
            raise

        if not docx_path.is_file() or not pdf_path.is_file():
            docx_path.unlink(missing_ok=True)
            pdf_path.unlink(missing_ok=True)
            raise OSError("Не удалось создать DOCX- и PDF-файлы.")

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

    def _load_document(self):
        try:
            from docx import Document
        except ImportError as error:
            raise RuntimeError(
                "Для генерации DOCX установите зависимость python-docx."
            ) from error
        return Document(self._docx_template_path())

    def _docx_template_path(self):
        if self.template_path.suffix.casefold() == ".docx":
            return self.template_path
        if self.template_path.suffix.casefold() != ".doc":
            raise ValueError("Шаблон должен иметь формат DOC или DOCX.")

        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            raise RuntimeError("В Windows не задан путь LOCALAPPDATA.")

        source = self.template_path.resolve()
        signature = (
            f"{source}|{source.stat().st_size}|{source.stat().st_mtime_ns}"
        ).encode("utf-8")
        cache_key = hashlib.sha256(signature).hexdigest()
        cache_dir = Path(local_app_data) / "SRM FMM" / "template-cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        converted_path = cache_dir / f"{cache_key}.docx"
        if converted_path.is_file():
            return converted_path

        self._convert_legacy_template(converted_path)
        return converted_path

    def _convert_legacy_template(self, converted_path):
        if os.name != "nt":
            raise OSError("Конвертация шаблонов DOC поддерживается только в Windows.")
        try:
            import win32com.client
        except ImportError as error:
            raise RuntimeError(
                "Для первого чтения шаблона DOC требуется Microsoft Word и pywin32."
            ) from error

        word = self._word_application()
        document = None
        try:
            word.Visible = False
            word.DisplayAlerts = 0
            document = word.Documents.Open(
                str(self.template_path),
                False,
                True,
                False
            )
            document.SaveAs2(str(converted_path), 16)
        except Exception:
            converted_path.unlink(missing_ok=True)
            raise
        finally:
            if document is not None:
                document.Close(0)

        if not converted_path.is_file():
            raise OSError("Microsoft Word не создал кэш DOCX-шаблона.")

    def _word_application(self):
        if self._closed:
            raise RuntimeError("Генератор документов уже закрыт.")
        if self._word is None:
            if os.name != "nt":
                raise OSError("Создание PDF поддерживается только в Windows.")
            try:
                import win32com.client
            except ImportError as error:
                raise RuntimeError(
                    "Для предпросмотра и экспорта PDF требуются Microsoft Word и pywin32."
                ) from error
            self._word = win32com.client.DispatchEx("Word.Application")
            self._word.Visible = False
            self._word.DisplayAlerts = 0
        return self._word

    def _close_preview(self):
        if self._preview_document is not None:
            self._preview_document.Close(0)
            self._preview_document = None

    def _populate_document(self, document, highlight):
        for paragraph in _iter_paragraphs(document):
            for placeholder, value in sorted(
                self.replacements.items(),
                key=lambda item: len(item[0]),
                reverse=True
            ):
                _replace_paragraph_text(
                    paragraph,
                    placeholder,
                    str(value),
                    highlight
                )

        if self.line_table_index is not None:
            self._populate_line_table(document, highlight)

        unresolved_fields = {
            value
            for paragraph in _iter_paragraphs(document)
            for value in re.findall(r"\[[^\]]+\]", paragraph.text)
        }
        if unresolved_fields:
            raise ValueError(
                "В шаблоне остались незаполненные поля: "
                + ", ".join(sorted(unresolved_fields))
            )

    def _populate_line_table(self, document, highlight):
        table_index = self.line_table_index - 1
        if table_index < 0 or table_index >= len(document.tables):
            raise ValueError("В шаблоне не найдена таблица услуг.")

        table = document.tables[table_index]
        if len(table.rows) < 2:
            raise ValueError("В шаблоне не найдена строка для услуг.")

        for index, item in enumerate(self.line_items):
            if index == 0:
                row = table.rows[1]
            else:
                source_row = table.rows[1]._tr
                row_element = copy.deepcopy(source_row)
                if len(table.rows) > 2:
                    table.rows[-1]._tr.addprevious(row_element)
                else:
                    table._tbl.append(row_element)
                row = table.rows[index + 1]

            values = (
                str(index + 1),
                item["name"],
                item["term"],
                item["amount"]
            )
            if len(row.cells) != len(values):
                raise ValueError(
                    "Структура таблицы услуг в шаблоне не совпадает с ожидаемой."
                )
            for cell, value in zip(row.cells, values):
                _set_paragraph_text(cell.paragraphs[0], str(value), highlight)
                for paragraph in cell.paragraphs[1:]:
                    _set_paragraph_text(paragraph, "", False)

def _iter_paragraphs(document):
    seen = set()

    def collect(container):
        for paragraph in getattr(container, "paragraphs", ()):
            element = paragraph._p
            if element not in seen:
                seen.add(element)
                yield paragraph
        for table in getattr(container, "tables", ()):
            for row in table.rows:
                for cell in row.cells:
                    yield from collect(cell)

    yield from collect(document)
    for section in document.sections:
        for container in (
            section.header,
            section.footer,
            section.first_page_header,
            section.first_page_footer,
            section.even_page_header,
            section.even_page_footer
        ):
            yield from collect(container)


def _replace_paragraph_text(paragraph, placeholder, replacement, highlight):
    if not placeholder:
        return
    while True:
        runs = _paragraph_runs(paragraph)
        full_text = "".join(run.text for run in runs)
        start = full_text.find(placeholder)
        if start < 0:
            return
        _replace_run_span(paragraph, runs, start, start + len(placeholder), replacement, highlight)


def _paragraph_runs(paragraph):
    """Include runs nested in hyperlinks and other paragraph content."""
    from docx.text.run import Run

    return [
        Run(run_element, paragraph)
        for run_element in paragraph._p.iter(f"{_WORD_TAG}r")
    ]


def _replace_run_span(paragraph, runs, start, end, replacement, highlight):
    cursor = 0
    first_index = last_index = None
    first_offset = last_offset = 0
    for index, run in enumerate(runs):
        next_cursor = cursor + len(run.text)
        if first_index is None and cursor <= start < next_cursor:
            first_index = index
            first_offset = start - cursor
        if cursor < end <= next_cursor:
            last_index = index
            last_offset = end - cursor
            break
        cursor = next_cursor

    if first_index is None or last_index is None:
        return

    first_run = runs[first_index]
    last_run = runs[last_index]
    first_text = first_run.text
    if first_index == last_index:
        prefix = first_text[:first_offset]
        suffix = first_text[last_offset:]
    else:
        prefix = first_text[:first_offset]
        suffix = last_run.text[last_offset:]

    first_run.text = prefix
    for run in runs[first_index + 1:last_index]:
        run.text = ""
    if first_index != last_index:
        last_run.text = suffix
    replacement_run = _insert_run_after(first_run, replacement, highlight)
    if first_index == last_index and suffix:
        _insert_run_after(replacement_run, suffix, False)


def _set_paragraph_text(paragraph, text, highlight):
    runs = paragraph.runs
    if not runs:
        run = paragraph.add_run(text)
        _set_run_highlight(run, highlight)
        return
    runs[0].text = text
    _set_run_highlight(runs[0], highlight)
    for run in runs[1:]:
        run.text = ""


def _insert_run_after(run, text, highlight):
    from docx.oxml import OxmlElement
    from docx.text.run import Run

    new_run_element = copy.deepcopy(run._r)
    for child in list(new_run_element):
        if child.tag != _RUN_PROPERTIES_TAG:
            new_run_element.remove(child)

    text_element = OxmlElement("w:t")
    text_element.text = text
    if text[:1].isspace() or text[-1:].isspace():
        text_element.set(
            "{http://www.w3.org/XML/1998/namespace}space",
            "preserve"
        )
    new_run_element.append(text_element)
    run._r.addnext(new_run_element)
    new_run = Run(new_run_element, run._parent)
    _set_run_highlight(new_run, highlight)
    return new_run


def _set_run_highlight(run, highlight):
    properties = run._r.get_or_add_rPr()
    existing = properties.find(_HIGHLIGHT_TAG)
    if existing is not None:
        properties.remove(existing)
    if highlight:
        from docx.oxml import OxmlElement

        highlight_element = OxmlElement("w:highlight")
        highlight_element.set(f"{_WORD_TAG}val", _YELLOW)
        properties.append(highlight_element)
