# -*- coding: utf-8 -*-
"""Набор простых валидаторов для UI форм"""
from typing import Tuple, Optional
from utils.date_utils import parse_ddmmyyyy
from utils.helpers import show_message
import tkinter as tk


def validate_non_empty(value: str, field_name: str) -> Tuple[bool, Optional[str]]:
    """Проверяет, что строка не пустая (после strip). Возвращает (ok, error_msg)."""
    if value is None or len(value.strip()) == 0:
        return False, f"Поле '{field_name}' не может быть пустым"
    return True, None


def validate_date_format(date_str: str) -> Tuple[bool, Optional[str]]:
    """Проверяет формат даты DD.MM.YYYY. Возвращает (ok, error_msg)."""
    if not date_str:
        return True, None
    parsed = parse_ddmmyyyy(date_str)
    if parsed is None:
        return False, "Неверный формат даты. Используйте ДД.ММ.ГГГГ"
    return True, None


def show_validation_error(parent: tk.Widget, message: str) -> None:
    """Показать сообщение об ошибке пользователю через show_message"""
    show_message(parent, "Ошибка", message, "error")

