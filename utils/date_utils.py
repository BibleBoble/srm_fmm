# -*- coding: utf-8 -*-
"""Утилиты для парсинга и форматирования дат в проекте"""
from datetime import datetime, date
from typing import Optional


def parse_ddmmyyyy(date_str: str) -> Optional[date]:
    """Парсит строку в формате DD.MM.YYYY в объект date.
    Возвращает None при пустой строке или неверном формате.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        return None


def format_ddmmyyyy(d: Optional[date]) -> str:
    """Форматирует date в строку DD.MM.YYYY или возвращает пустую строку, если None."""
    if not d:
        return ""
    if isinstance(d, datetime):
        d = d.date()
    return d.strftime("%d.%m.%Y")

