"""
Модель отчёта
"""
from datetime import datetime, date


class Report:
    """
    Класс, представляющий отчёт
    """

    def __init__(self, id=None, title="", report_type="general",
                 date_from=None, date_to=None, data=None, created_at=None):
        """
        Args:
            id: int - ID отчёта в БД
            title: str - название отчёта
            report_type: str - тип отчёта (general, clients, contracts, tasks)
            date_from: date - период с
            date_to: date - период по
            data: dict - данные отчёта в формате JSON
            created_at: datetime - дата создания
        """
        self.id = id
        self.title = title
        self.report_type = report_type
        self.date_from = date_from or date.today()
        self.date_to = date_to or date.today()
        self.data = data or {}
        self.created_at = created_at or datetime.now()

    def __repr__(self):
        """Строковое представление объекта"""
        return f"Report(id={self.id}, title='{self.title}', type='{self.report_type}')"

    def __str__(self):
        """Пользовательское строковое представление"""
        return f"Отчёт: {self.title} ({self.date_from} - {self.date_to})"

    def to_dict(self):
        """
        Преобразовать объект в словарь

        Returns:
            dict - словарь с данными отчёта
        """
        return {
            'id': self.id,
            'title': self.title,
            'report_type': self.report_type,
            'date_from': self.date_from.isoformat() if isinstance(self.date_from, date) else self.date_from,
            'date_to': self.date_to.isoformat() if isinstance(self.date_to, date) else self.date_to,
            'data': self.data,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    @staticmethod
    def from_dict(data):
        """
        Создать объект Report из словаря

        Args:
            data: dict - словарь с данными

        Returns:
            Report - объект отчёта
        """
        date_from = data.get('date_from')
        if isinstance(date_from, str):
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()

        date_to = data.get('date_to')
        if isinstance(date_to, str):
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

        return Report(
            id=data.get('id'),
            title=data.get('title', ''),
            report_type=data.get('report_type', 'general'),
            date_from=date_from,
            date_to=date_to,
            data=data.get('data', {}),
            created_at=data.get('created_at')
        )

    def is_valid(self):
        """
        Проверка корректности данных отчёта

        Returns:
            bool - True если данные корректны
        """
        if not self.title or len(self.title.strip()) == 0:
            return False
        if self.date_from > self.date_to:
            return False
        return True