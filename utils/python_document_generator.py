"""Заполнение DOCX-шаблонов без Microsoft Word.

Старые шаблоны DOC один раз конвертируются в DOCX (рядом с исходником или
в кэш), после чего формирование документа не требует запуска Word.

Документ рендерится один раз: результат хранится в памяти и записывается
на диск при сохранении. PDF готовится отдельно и не блокирует интерфейс.
"""
import copy
import hashlib
import io
import os
import re
from pathlib import Path

from docx import Document

_WORD_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_WORD_TAG = f"{{{_WORD_NAMESPACE}}}"
_HIGHLIGHT_TAG = f"{_WORD_TAG}highlight"
_TEXT_TAG = f"{_WORD_TAG}t"
_RUN_PROPERTIES_TAG = f"{_WORD_TAG}rPr"
_YELLOW = "yellow"
_PLACEHOLDER_PATTERN = re.compile(r"\[[^\]]+\]")

# Кэш содержимого шаблонов: путь -> (размер, mtime, байты).
_TEMPLATE_BYTES = {}


class PythonDocumentGenerator:
    """Заполняет DOCX-шаблон и сохраняет готовый документ."""

    def __init__(self, template_path, replacements, line_items=None, line_table_index=None):
        self.template_path = Path(template_path)
        if not self.template_path.is_file():
            raise FileNotFoundError(f"Не найден шаблон документа: {self.template_path}")

        self.replacements = {
            str(key): str(value) for key, value in replacements.items()
        }
        self.line_items = line_items or []
        self.line_table_index = line_table_index
        self._rendered = {}

    # --- публичный интерфейс ---

    def render(self, highlight=False):
        """Заполнить шаблон один раз и вернуть байты DOCX.

        highlight=True подсвечивает автоматически вставленные значения
        жёлтым — это используется для предпросмотра.
        """
        key = bool(highlight)
        if key not in self._rendered:
            document = self._load_document()
            self._populate_document(document, highlight=key)
            buffer = io.BytesIO()
            document.save(buffer)
            self._rendered[key] = buffer.getvalue()
        return self._rendered[key]

    def save_docx(self, target_path):
        """Записать готовый документ на диск, не перечитывая шаблон."""
        target_path = Path(target_path)
        data = self.render()
        with target_path.open("xb") as output:
            output.write(data)

    def close(self):
        """Совместимость: генератор не держит внешних ресурсов."""
        return

    # --- загрузка шаблона ---

    def _load_document(self):
        data = _template_bytes(self._docx_template_path())
        return Document(io.BytesIO(data))

    def _docx_template_path(self):
        suffix = self.template_path.suffix.casefold()
        if suffix == ".docx":
            return self.template_path
        if suffix != ".doc":
            raise ValueError("Шаблон должен иметь формат DOC или DOCX.")

        # Рядом с исходным DOC обычно лежит заранее сохранённый DOCX —
        # это избавляет от запуска Word при каждом формировании.
        sibling = self.template_path.with_suffix(".docx")
        if sibling.is_file():
            return sibling

        return self._convert_legacy_template()

    def _convert_legacy_template(self):
        """Одноразовая конвертация DOC в DOCX, если рядом нет готового DOCX."""
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            raise RuntimeError("В Windows не задан путь LOCALAPPDATA.")

        source = self.template_path.resolve()
        stat = source.stat()
        signature = f"{source}|{stat.st_size}|{stat.st_mtime_ns}".encode("utf-8")
        cache_key = hashlib.sha256(signature).hexdigest()
        cache_dir = Path(local_app_data) / "SRM FMM" / "template-cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        converted_path = cache_dir / f"{cache_key}.docx"
        if converted_path.is_file():
            return converted_path

        self._convert_with_word(converted_path)
        return converted_path

    def _convert_with_word(self, converted_path):
        if os.name != "nt":
            raise OSError("Конвертация шаблонов DOC поддерживается только в Windows.")
        try:
            import win32com.client
        except ImportError as error:
            raise RuntimeError(
                "Для первого чтения шаблона DOC требуется Microsoft Word и pywin32. "
                "Сохраните шаблон в формате DOCX рядом с исходным файлом."
            ) from error

        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = None
        try:
            document = word.Documents.Open(str(self.template_path), False, True, False)
            document.SaveAs2(str(converted_path), 16)
        except Exception:
            converted_path.unlink(missing_ok=True)
            raise
        finally:
            if document is not None:
                document.Close(0)
            word.Quit()

        if not converted_path.is_file():
            raise OSError("Microsoft Word не создал кэш DOCX-шаблона.")

    # --- заполнение ---

    def _populate_document(self, document, highlight):
        pattern = self._replacement_pattern()

        if pattern is not None:
            for paragraph in _iter_paragraphs(document):
                runs = _paragraph_runs(paragraph)
                full_text = "".join(run.text for run in runs)
                matches = list(pattern.finditer(full_text))
                if not matches:
                    continue

                # Идём справа налево: замена не сдвигает позиции левых вхождений.
                for match in reversed(matches):
                    _replace_run_span(
                        paragraph,
                        _paragraph_runs(paragraph),
                        match.start(),
                        match.end(),
                        self.replacements[match.group(0)],
                        highlight,
                    )

        if self.line_table_index is not None:
            self._populate_line_table(document, highlight)

        # Проверяем остатки только после заполнения таблицы услуг: шаблонная
        # строка таблицы содержит служебные плейсхолдеры, которые затираются.
        unresolved = {
            placeholder
            for paragraph in _iter_paragraphs(document)
            for placeholder in _PLACEHOLDER_PATTERN.findall(paragraph.text)
        }
        if unresolved:
            raise ValueError(
                "В шаблоне остались незаполненные поля: "
                + ", ".join(sorted(unresolved))
            )

    def _replacement_pattern(self):
        """Один regex из всех известных плейсхолдеров, длинные — первыми."""
        keys = sorted(self.replacements, key=len, reverse=True)
        if not keys:
            return None
        return re.compile("|".join(re.escape(key) for key in keys))

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


def _template_bytes(path):
    """Прочитать шаблон один раз и держать его байты в памяти."""
    path = Path(path)
    stat = path.stat()
    key = str(path.resolve())
    cached = _TEMPLATE_BYTES.get(key)
    if cached is not None:
        size, mtime_ns, data = cached
        if size == stat.st_size and mtime_ns == stat.st_mtime_ns:
            return data

    data = path.read_bytes()
    _TEMPLATE_BYTES[key] = (stat.st_size, stat.st_mtime_ns, data)
    return data


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
