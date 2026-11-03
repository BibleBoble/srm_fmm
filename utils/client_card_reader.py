# -*- coding: utf-8 -*-
"""Извлечение данных клиента из карточек партнёра (DOC/DOCX).

Карточки не стандартизированы, поэтому используются два подхода:
подписи в таблицах («ИНН», «Юридический адрес» и т. п.) и поиск
характерных значений (email, телефон, ИНН/КПП) по всему тексту.
"""
import re
import shutil
import tempfile
from pathlib import Path

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+7|8)\s*[(-]?\s*\d{3,4}\s*[)-]?\s*\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"
    r"|(?<!\d)\(\d{3,4}\)\s*\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"
)
_INN_KPP_RE = re.compile(r"(\d{10})\s*[/\\]?\s*(\d{9})")
_INN_RE = re.compile(r"\b\d{10}\b")
_KPP_RE = re.compile(r"\b\d{9}\b")
_OGRN_RE = re.compile(r"\b\d{13,15}\b")
_BIK_RE = re.compile(r"БИК[:\s]*(\d{9})", re.IGNORECASE)

_PERSON_LABELS = (
    ("генеральный", "директор"),
    ("ген.", "директор"),
    ("директор",),
    ("руководитель",),
)


def read_client_card(path):
    """Прочитать карточку и вернуть словарь с полями клиента."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Файл карточки не найден: {path}")

    document, temp_dir = _load_document(path)
    try:
        pairs, texts = _collect(document)
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return _extract(pairs, texts)


# --- чтение документа ---

def _load_document(path):
    suffix = path.suffix.casefold()
    if suffix == ".docx":
        from docx import Document
        return Document(path), None
    if suffix != ".doc":
        raise ValueError("Поддерживаются карточки в форматах DOC и DOCX.")

    try:
        import win32com.client
    except ImportError as error:
        raise RuntimeError(
            "Для чтения карточек DOC требуется Microsoft Word и pywin32."
        ) from error

    temp_dir = Path(tempfile.mkdtemp(prefix="srm-card-"))
    target = temp_dir / f"{path.stem}.docx"
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        document = word.Documents.Open(str(path.resolve()), False, True, False)
        try:
            document.SaveAs2(str(target), 16)
        finally:
            document.Close(0)
    finally:
        word.Quit()

    from docx import Document
    return Document(target), temp_dir


def _clean(text):
    return " ".join(str(text or "").replace("\xa0", " ").split())


def _split_label(text):
    if ":" not in text:
        return []
    label, value = text.split(":", 1)
    label = label.strip(" .")
    value = value.strip()
    if not label or not value:
        return []
    return [(label, value)]


def _collect(document):
    pairs = []
    texts = []
    for table in document.tables:
        for row in table.rows:
            cells = [_clean(cell.text) for cell in row.cells]
            deduped = []
            for value in cells:
                if not deduped or deduped[-1] != value:
                    deduped.append(value)
            if len(deduped) >= 2 and deduped[0]:
                value = " ".join(part for part in deduped[1:] if part).strip()
                if value:
                    pairs.append((deduped[0], value))
            for value in deduped:
                texts.append(value)
                pairs.extend(_split_label(value))

    for paragraph in document.paragraphs:
        text = _clean(paragraph.text)
        if not text:
            continue
        texts.append(text)
        pairs.extend(_split_label(text))

    return pairs, texts


# --- разбор полей ---

def _value(pairs, keywords, exclude=()):
    for label, value in pairs:
        low = label.casefold().replace("ё", "е")
        if all(word in low for word in keywords) and not any(
            word in low for word in exclude
        ):
            return value
    return ""


def _strip_company_noise(value):
    value = re.split(r"\s+Открыт\b|\s+открыт\b", value, maxsplit=1)[0]
    return value.strip(" .,;")


def _clean_address(value):
    return _clean(value).lstrip(" .,;:")


def _clean_person(value):
    value = _clean(value)
    value = re.split(r"[,;]|\s+действующ", value, maxsplit=1)[0].strip()
    words = value.split()
    if len(words) >= 3:
        value = " ".join(words[:3])
    if value.isupper():
        value = value.title()
    return value


def _first(patterns, texts):
    for text in texts:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match
    return None


def _extract(pairs, texts):
    full_name = _value(pairs, ("полное", "наименование"), exclude=("англ",))
    if not full_name:
        full_name = _value(pairs, ("фирменное", "наименование"))

    company = _value(pairs, ("сокращенное", "наименование"))
    if not company:
        company = _value(pairs, ("фирменное", "наименование"))
    if not company:
        company = full_name
    company = _strip_company_noise(company)

    legal_address = _value(pairs, ("юридический", "адрес"))
    if not legal_address:
        legal_address = _value(
            pairs,
            ("адрес",),
            exclude=("банк", "местонахождение", "почтов", "англ", "юридическ")
        )
    postal_address = _value(pairs, ("почтовый", "адрес"))
    legal_address = _clean_address(legal_address)
    postal_address = _clean_address(postal_address)

    inn_kpp = ""
    inn_raw = _value(pairs, ("инн",))
    match = _INN_KPP_RE.search(inn_raw)
    if match:
        inn_kpp = f"{match.group(1)}/{match.group(2)}"
    else:
        inn_match = _INN_RE.search(inn_raw)
        kpp_match = _KPP_RE.search(_value(pairs, ("кпп",)))
        if inn_match and kpp_match:
            inn_kpp = f"{inn_match.group(0)}/{kpp_match.group(0)}"
        elif inn_match:
            inn_kpp = inn_match.group(0)
    if not inn_kpp:
        found = _first([_INN_KPP_RE.pattern], texts)
        if found:
            inn_kpp = f"{found.group(1)}/{found.group(2)}"

    ogrn = ""
    ogrn_raw = _value(pairs, ("огрн",))
    match = _OGRN_RE.search(ogrn_raw)
    if match:
        ogrn = match.group(0)
    else:
        found = _first([_OGRN_RE.pattern], texts)
        if found:
            ogrn = found.group(0)

    bank_details = _build_bank_details(pairs)

    person = ""
    for keywords in _PERSON_LABELS:
        person = _value(pairs, keywords)
        if person:
            break
    if not person:
        found = _first(
            [
                r"(?:генеральный|ген\.?)\s*директор[:\s]+(.+)",
                r"директор[:\s]+(.+)",
            ],
            texts
        )
        if found:
            person = found.group(1)
    person = _clean_person(person)

    email = ""
    email_raw = (
        _value(pairs, ("e-mail",))
        or _value(pairs, ("эл.почта",))
        or _value(pairs, ("почта",))
    )
    match = _EMAIL_RE.search(email_raw)
    if not match:
        found = _first([_EMAIL_RE.pattern], texts)
        match = found
    if match:
        email = match.group(0)

    phone = ""
    phone_raw = _value(pairs, ("телефон",)) or _value(pairs, ("тел.",))
    match = _PHONE_RE.search(phone_raw)
    if not match:
        found = _first([_PHONE_RE.pattern], texts)
        match = found
    if match:
        phone = match.group(0)

    return {
        "company": company,
        "full_legal_name": full_name,
        "address": legal_address or postal_address,
        "legal_address": legal_address,
        "postal_address": postal_address,
        "inn_kpp": inn_kpp,
        "ogrn": ogrn,
        "bank_details": bank_details,
        "responsible_person": person,
        "partner_email": email,
        "partner_phone": phone,
    }


def _build_bank_details(pairs):
    combined = _value(pairs, ("банковские", "реквизиты"))
    if combined:
        return combined

    account = _value(pairs, ("расчетный", "счет")) or _value(pairs, ("р/с",))
    bank = _value(
        pairs,
        ("банк",),
        exclude=("бик", "местонахождение", "банковские")
    )
    bik = ""
    bik_raw = _value(pairs, ("бик",))
    match = _BIK_RE.search(bik_raw) or re.search(r"\b\d{9}\b", bik_raw)
    if match:
        bik = match.group(1) if match.lastindex else match.group(0)
    bank_bik = _BIK_RE.search(bank)
    if bank_bik and not bik:
        bik = bank_bik.group(1)
    if bank_bik:
        bank = _BIK_RE.sub("", bank).strip(" ,;")
    korr = (
        _value(pairs, ("корреспондентский", "счет"))
        or _value(pairs, ("к/с",))
    )

    parts = []
    if account:
        parts.append(f"р/с {account}")
    if bank:
        parts.append(f"Банк: {bank}")
    if bik:
        parts.append(f"БИК {bik}")
    if korr:
        parts.append(f"к/с {korr}")
    return "\n".join(parts)
