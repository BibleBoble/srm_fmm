import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree


_WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_AMOUNT_PATTERN = re.compile(
    r"(?<!\d)(?:\d{1,3}(?:[ \u00a0\u202f]\d{3})+|\d+)(?:[,.]\d{1,2})?(?!\d)"
)


@dataclass(frozen=True)
class SpecificationSummary:
    services: tuple[str, ...]
    total: Decimal


# Кэш разобранных спецификаций: путь + размер + mtime -> (позиции, итог).
_CACHE = {}
_CACHE_LIMIT = 256


def read_specification_items(path):
    """Прочитать таблицу услуг: наименование, срок и сумму по каждой строке."""
    path = Path(path)
    try:
        stat = path.stat()
    except OSError as error:
        raise ValueError(f"Не удалось прочитать файл спецификации: {path.name}") from error

    key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    items, total = _read_items(path)
    if len(_CACHE) >= _CACHE_LIMIT:
        _CACHE.clear()
    _CACHE[key] = (items, total)
    return items, total


def read_specification_summary(path: Path) -> SpecificationSummary:
    """Прочитать наименования услуг и итоговую сумму из таблицы DOCX."""
    items, total = read_specification_items(path)
    return SpecificationSummary(tuple(item["name"] for item in items), total)


def read_specification_customer(path):
    """Данные заказчика из строки «Заказчик: ... в лице ...»."""
    text = _document_text(path)
    match = re.search(
        r"Заказчик:\s*(.+?),\s*в лице\s+(.+?)(?:,\s*действующ|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )
    if not match:
        return {}

    company = " ".join(match.group(1).split())
    person_part = " ".join(match.group(2).split())
    result = {
        "company": company,
        "position_genitive": "",
        "person_genitive": person_part,
    }
    position = re.match(
        r"(.+?(?:директора|предпринимателя|президента))\s+(.+)$",
        person_part,
        re.IGNORECASE
    )
    if position:
        result["position_genitive"] = position.group(1).strip()
        result["person_genitive"] = position.group(2).strip()
    return result


def _document_text(path):
    path = Path(path)
    try:
        with ZipFile(path) as document:
            xml_content = document.read("word/document.xml")
    except (OSError, KeyError, BadZipFile) as error:
        raise ValueError(f"Не удалось прочитать файл спецификации: {path.name}") from error

    try:
        document_root = ElementTree.fromstring(xml_content)
    except ElementTree.ParseError as error:
        raise ValueError(f"Повреждён файл спецификации: {path.name}") from error

    return " ".join(
        (text_node.text or "")
        for text_node in document_root.iter(f"{_WORD_NAMESPACE}t")
    )


def _read_items(path: Path):
    try:
        with ZipFile(path) as document:
            xml_content = document.read("word/document.xml")
    except (OSError, KeyError, BadZipFile) as error:
        raise ValueError(f"Не удалось прочитать файл спецификации: {path.name}") from error

    try:
        document_root = ElementTree.fromstring(xml_content)
    except ElementTree.ParseError as error:
        raise ValueError(f"Повреждён файл спецификации: {path.name}") from error

    for table in document_root.iter(f"{_WORD_NAMESPACE}tbl"):
        items = []
        total_rows = []

        for row in table.findall(f"{_WORD_NAMESPACE}tr"):
            cells = [
                _cell_text(cell)
                for cell in row.findall(f"{_WORD_NAMESPACE}tc")
            ]
            if not cells:
                continue

            if any("итого" in cell.casefold() for cell in cells):
                total_rows.append(cells)

            if (
                len(cells) >= 4
                and re.fullmatch(r"\d+[.)]?", cells[0].strip())
                and cells[1].strip()
            ):
                items.append({
                    "name": cells[1].strip(),
                    "term": cells[2].strip(),
                    "amount": _parse_amount(cells[-1]) or Decimal("0.00"),
                })

        if items:
            total = _read_total(total_rows)
            if total is None:
                total = sum(
                    (item["amount"] for item in items),
                    Decimal("0.00")
                )
            return items, total

    raise ValueError(f"В спецификации {path.name} не найдена таблица услуг.")


def _cell_text(cell) -> str:
    return "".join(
        text_node.text or ""
        for text_node in cell.iter(f"{_WORD_NAMESPACE}t")
    ).strip()


def _parse_amount(value: str) -> Decimal | None:
    matches = _AMOUNT_PATTERN.findall(
        value.replace("\xa0", " ").replace("\u202f", " ")
    )
    if not matches:
        return None
    normalized = matches[-1].replace(" ", "").replace(",", ".")
    try:
        return Decimal(normalized)
    except InvalidOperation as error:
        raise ValueError(f"Некорректная сумма в спецификации: {value}") from error


def _read_total(rows: list[list[str]]) -> Decimal | None:
    for row in reversed(rows):
        for cell in reversed(row):
            amount = _parse_amount(cell)
            if amount is not None:
                return amount
    return None
