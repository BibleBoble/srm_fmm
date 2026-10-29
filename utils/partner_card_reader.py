import os
import re
from pathlib import Path
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree


_WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_FIELD_ALIASES = {
    "company": (
        "наименование организации",
        "наименование компании",
        "полное наименование",
        "название компании",
        "организация",
        "компания"
    ),
    "full_legal_name": (
        "полное наименование организации",
        "полное юридическое наименование",
        "полное наименование"
    ),
    "legal_address": ("юридический адрес", "адрес юридический"),
    "postal_address": ("почтовый адрес", "адрес для корреспонденции"),
    "ogrn": ("огрн", "основной государственный регистрационный номер"),
    "inn_kpp": ("инн/кпп", "инн / кпп", "инн кпп", "инн"),
    "bank_details": ("банковские реквизиты", "реквизиты банка"),
    "responsible_person": (
        "фио руководителя",
        "фио директора",
        "ответственное лицо",
        "руководитель",
        "подписант"
    ),
    "responsible_position": (
        "должность руководителя",
        "должность подписанта",
        "должность",
        "генеральный директор",
        "директор"
    ),
    "partner_email": ("электронная почта", "e-mail", "email", "почта"),
    "partner_phone": ("контактный телефон", "телефон", "тел.")
}
_BANK_LINE_ALIASES = (
    "банк",
    "наименование банка",
    "бик",
    "к/с",
    "корреспондентский счет",
    "р/с",
    "расчетный счет",
    "расчётный счет",
    "кор счет"
)


def read_partner_card(path: Path) -> dict[str, str]:
    """Считать реквизиты партнёра из документа Word формата DOCX или DOC."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Файл карточки партнёра не найден: {path}")

    suffix = path.suffix.casefold()
    if suffix == ".docx":
        content = _read_docx_text(path)
    elif suffix == ".doc":
        content = _read_doc_text(path)
    else:
        raise ValueError("Поддерживаются только файлы Word форматов DOC и DOCX.")

    fields = _parse_partner_fields(content)
    if not fields:
        raise ValueError(
            "В документе не удалось распознать реквизиты. "
            "Ожидается карточка с подписями полей и значениями."
        )
    return fields


def _read_docx_text(path: Path) -> str:
    try:
        with ZipFile(path) as document:
            xml_content = document.read("word/document.xml")
    except (OSError, KeyError, BadZipFile) as error:
        raise ValueError(f"Не удалось прочитать файл DOCX: {path.name}") from error

    try:
        document_root = ElementTree.fromstring(xml_content)
    except ElementTree.ParseError as error:
        raise ValueError(f"Повреждён файл DOCX: {path.name}") from error

    lines = []
    for row in document_root.iter(f"{_WORD_NAMESPACE}tr"):
        cells = [
            _element_text(cell)
            for cell in row.findall(f"{_WORD_NAMESPACE}tc")
        ]
        if any(cells):
            lines.append("\t".join(cells))

    for paragraph in document_root.iter(f"{_WORD_NAMESPACE}p"):
        text = _element_text(paragraph)
        if text:
            lines.append(text)
    return "\n".join(lines)


def _read_doc_text(path: Path) -> str:
    if os.name != "nt":
        raise OSError("Чтение файлов DOC поддерживается только в Windows.")

    try:
        import win32com.client
    except ImportError as error:
        raise RuntimeError(
            "Для чтения файлов DOC требуется Microsoft Word и зависимость pywin32."
        ) from error

    word = win32com.client.DispatchEx("Word.Application")
    document = None
    try:
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(
            str(path),
            False,
            True,
            False,
            "",
            "",
            True
        )
        return str(document.Content.Text)
    except Exception as error:
        raise ValueError(f"Не удалось прочитать файл DOC: {path.name}") from error
    finally:
        try:
            if document is not None:
                document.Close(0)
        finally:
            word.Quit()


def _element_text(element) -> str:
    return "".join(
        text_node.text or ""
        for text_node in element.iter(f"{_WORD_NAMESPACE}t")
    ).strip()


def _parse_partner_fields(content: str) -> dict[str, str]:
    fields = {}
    bank_lines = []
    aliases = sorted(
        (
            (field, alias)
            for field, names in _FIELD_ALIASES.items()
            for alias in names
        ),
        key=lambda item: len(item[1]),
        reverse=True
    )

    for raw_line in content.splitlines():
        raw_line = raw_line.strip(" \t\r\n\x07")
        label, value = _split_label_value(raw_line)
        line = re.sub(r"\s+", " ", raw_line)
        if not line:
            continue

        label = re.sub(r"\s+", " ", label).strip()
        value = re.sub(r"\s+", " ", value).strip()
        normalized_label = _normalize(label)
        matched_field = next(
            (
                field for field, alias in aliases
                if normalized_label == _normalize(alias)
            ),
            None
        )
        if matched_field and value:
            if matched_field == "inn_kpp" and "inn_kpp" in fields:
                fields["inn_kpp"] = f"{fields['inn_kpp']}/{value}"
            else:
                fields[matched_field] = value
            if normalized_label == _normalize("полное наименование"):
                fields.setdefault("full_legal_name", value)
            continue

        bank_line = _bank_detail_line(line)
        if bank_line:
            bank_lines.append(bank_line)

    if bank_lines and not fields.get("bank_details"):
        fields["bank_details"] = "\n".join(dict.fromkeys(bank_lines))
    if fields.get("full_legal_name") and not fields.get("company"):
        fields["company"] = fields["full_legal_name"]
    if fields.get("legal_address") and not fields.get("postal_address"):
        fields["postal_address"] = fields["legal_address"]
    return fields


def _split_label_value(line: str) -> tuple[str, str]:
    for separator in ("\t", ":"):
        if separator in line:
            label, value = line.split(separator, 1)
            return label.strip(), value.strip()
    return line, ""


def _normalize(value: str) -> str:
    return re.sub(r"[^0-9a-zа-я]+", "", value.casefold().replace("ё", "е"))


def _bank_detail_line(line: str) -> str:
    for alias in _BANK_LINE_ALIASES:
        match = re.match(
            rf"^\s*{re.escape(alias)}\s*[:\-]?\s*(.+?)\s*$",
            line,
            re.IGNORECASE
        )
        if match:
            return line
    return ""
