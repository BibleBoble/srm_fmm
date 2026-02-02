"""
Модель задачи
"""
from datetime import datetime, date


class Task:
    """
    Класс, представляющий задачу
    """

    def __init__(self, id=None, title="", description="", due_date=None,
                 completed=False, client_id=None, created_at=None, priority=None):
        self.id = id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.completed = completed
        self.client_id = client_id
        self.created_at = created_at or datetime.now()
        self.priority = priority  # ← ДОБАВЬТЕ ЭТО

    def __repr__(self):
        """Строковое представление объекта для отладки"""
        status = "✓" if self.completed else "✗"
        return f"Task(id={self.id}, title='{self.title}', completed={status}, priority='{self.priority}')"

    def __str__(self):
        """Пользовательское строковое представление"""
        status = "Выполнена" if self.completed else "Не выполнена"
        return f"{self.title} [{status}] ({self.priority})"

    @property
    def status(self):
        """Свойство для получения статуса в текстовом виде"""
        return "Выполнена" if self.completed else "Новая"

    def to_dict(self):
        """Преобразовать объект в словарь для сохранения или передачи"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if isinstance(self.due_date, (date, datetime)) else self.due_date,
            'completed': self.completed,
            'client_id': self.client_id,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'priority': self.priority,
            'status': self.status  # ← ДОБАВЬТЕ status в словарь
        }

    @staticmethod
    def from_dict(data):
        """Создать объект Task из sqlite3.Row"""
        if not data:
            return None

        # Преобразуем даты
        due_date = data.get('due_date')
        if isinstance(due_date, str):
            try:
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except:
                try:
                    due_date = datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S').date()
                except:
                    due_date = None

        created_at = data.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            except:
                created_at = datetime.now()

        return Task(
            id=data.get('id'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            due_date=due_date,
            completed=bool(data.get('completed', 0)),
            client_id=data.get('client_id'),
            created_at=created_at,
            priority=data.get('priority')  # ← ИСПРАВЬТЕ: было None
        )

    def is_valid(self):
        """Проверка корректности данных задачи"""
        if not self.title or len(self.title.strip()) == 0:
            return False
        return True

    def is_overdue(self):
        """Проверка просрочки: не выполнена и дата меньше сегодня"""
        if not self.due_date or self.completed:
            return False
        return self.due_date < date.today()