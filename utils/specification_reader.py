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


def read_specification_summary(path: Path) -> SpecificationSummary:
    """Прочитать наименования услуг и итоговую сумму из таблицы DOCX."""
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
        service_names = []
        service_total = Decimal("0.00")
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
                service_names.append(cells[1].strip())
                service_total += _parse_amount(cells[-1]) or Decimal("0.00")

        if service_names:
            total = _read_total(total_rows) or service_total
            return SpecificationSummary(tuple(service_names), total)

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
