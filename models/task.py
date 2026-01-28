"""
Модель задачи
"""
from datetime import datetime, date


class Task:
    """
    Класс, представляющий задачу
    """

    def __init__(self, id=None, title="", description="", due_date=None,
                 completed=False, client_id=None, created_at=None):
        """
        Args:
            id: int - ID задачи в БД
            title: str - название задачи
            description: str - описание
            due_date: date - срок выполнения
            completed: bool - выполнена ли задача
            client_id: int - ID связанного клиента (опционально)
            created_at: datetime - дата создания
        """
        self.id = id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.completed = completed
        self.client_id = client_id
        self.created_at = created_at or datetime.now()

    def __repr__(self):
        """Строковое представление объекта"""
        status = "✓" if self.completed else "✗"
        return f"Task(id={self.id}, title='{self.title}', completed={status})"

    def __str__(self):
        """Пользовательское строковое представление"""
        status = "Выполнена" if self.completed else "Не выполнена"
        return f"{self.title} [{status}]"

    def to_dict(self):
        """
        Преобразовать объект в словарь

        Returns:
            dict - словарь с данными задачи
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if isinstance(self.due_date, date) else self.due_date,
            'completed': self.completed,
            'client_id': self.client_id,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    @staticmethod
    def from_dict(data):
        """
        Создать объект Task из словаря

        Args:
            data: dict - словарь с данными

        Returns:
            Task - объект задачи
        """
        due_date = data.get('due_date')
        if isinstance(due_date, str):
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()

        return Task(
            id=data.get('id'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            due_date=due_date,
            completed=bool(data.get('completed', False)),
            client_id=data.get('client_id'),
            created_at=data.get('created_at')
        )

    def is_valid(self):
        """
        Проверка корректности данных задачи

        Returns:
            bool - True если данные корректны
        """
        if not self.title or len(self.title.strip()) == 0:
            return False
        return True

    def mark_completed(self):
        """Отметить задачу как выполненную"""
        self.completed = True

    def mark_uncompleted(self):
        """Отметить задачу как невыполненную"""
        self.completed = False

    def is_overdue(self):
        """
        Проверка просрочена ли задача

        Returns:
            bool - True если задача просрочена
        """
        if not self.due_date or self.completed:
            return False
        return self.due_date < date.today()