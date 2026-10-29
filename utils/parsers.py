# -*- coding: utf-8 -*-
"""
Парсеры для преобразования данных
"""
from datetime import datetime, date
from typing import Any, Optional, List, Union


class DateParser:
    """Парсер дат из разных форматов"""

    COMMON_FORMATS = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y"
    ]

    @staticmethod
    def parse_date(
        date_str: Union[str, date, datetime],
        formats: List[str] = None
    ) -> Optional[date]:
        """
        Распарсить дату из строки в date объект

        Args:
            date_str: строка, date или datetime
            formats: список форматов для попытки парсинга

        Returns:
            date объект или None
        """
        if not date_str:
            return None

        if isinstance(date_str, date):
            return date_str

        if isinstance(date_str, datetime):
            return date_str.date()

        if not isinstance(date_str, str):
            return None

        formats = formats or DateParser.COMMON_FORMATS

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.date()
            except (ValueError, AttributeError):
                continue

        return None


def safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """
    Безопасно получить поле из dict или object

    Args:
        obj: dict или объект с атрибутами
        key: ключ/имя атрибута
        default: значение по умолчанию

    Returns:
        значение поля или default
    """
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(key, default)

    try:
        return getattr(obj, key, default)
    except AttributeError:
        return default


def normalize_boolean(value: Any) -> bool:
    """Преобразовать значение в булев тип"""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on', 'да')
    return bool(value)


def normalize_string(value: Any, strip: bool = True) -> str:
    """Преобразовать значение в строку"""
    if value is None:
        return ""
    s = str(value)
    return s.strip() if strip else s

