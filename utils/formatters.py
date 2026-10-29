# -*- coding: utf-8 -*-
"""
Форматеры для представления данных в UI
"""
from datetime import datetime, date


class DateFormatter:
    """Форматер дат"""

    DEFAULT_FORMAT = "%d.%m.%Y"
    DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"

    @staticmethod
    def format_date(date_obj, format_str: str = DEFAULT_FORMAT) -> str:
        """Форматирует дату в нужный вид"""
        if not date_obj:
            return ""

        if isinstance(date_obj, str):
            # Если уже строка и в нужном формате — возвращаем
            if all(c in "0123456789.-/" for c in date_obj):
                return date_obj
            # Иначе пробуем распарсить
            from utils.parsers import DateParser
            parsed = DateParser.parse_date(date_obj)
            if parsed:
                return parsed.strftime(format_str)
            return date_obj

        elif isinstance(date_obj, (datetime, date)):
            return date_obj.strftime(format_str)

        return str(date_obj) if date_obj else ""


class PriorityFormatter:
    """Форматер приоритета"""

    ICONS = {
        'Высокий': '🔴',
        'Средний': '🟡',
        'Низкий': '🟢'
    }

    @staticmethod
    def format(priority: str, with_icon: bool = True) -> str:
        """Форматирует приоритет с иконкой"""
        if not priority:
            return ""

        icon = PriorityFormatter.ICONS.get(priority, "")
        if with_icon and icon:
            return f"{icon} {priority}"
        return priority


class StatusFormatter:
    """Форматер статуса"""

    ICONS = {
        'Активная': '⏳',
        'Выполнена': '✅',
        'Новая': '📝',
        'В работе': '🔄',
        'Отложена': '⏸',
        'Отменена': '❌'
    }

    @staticmethod
    def format(status: str, with_icon: bool = True) -> str:
        """Форматирует статус с иконкой"""
        if not status:
            return "Новая"

        icon = StatusFormatter.ICONS.get(status, "")
        if with_icon and icon:
            return f"{icon} {status}"
        return status

    @staticmethod
    def normalize(status: str) -> str:
        """Нормализует статус (Новая/В работе/Отложена → Активная)"""
        if status in ['Новая', 'В работе', 'Отложена']:
            return 'Активная'
        return status


