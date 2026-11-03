"""
Модель задачи
"""
from datetime import datetime, date


class Task:
    """
    Класс, представляющий задачу
    """

    def __init__(self, id=None, title="", description="", due_date=None,
                 completed=False, client_id=None, created_at=None, priority=None,
                 is_financial=False, work_id=None):
        self.id = id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.completed = completed
        self.client_id = client_id
        self.created_at = created_at or datetime.now()
        self.priority = priority
        self.is_financial = bool(is_financial)
        self.work_id = work_id

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
            'is_financial': 1 if self.is_financial else 0,
            'work_id': self.work_id,
            'status': self.status
        }

    @staticmethod
    def from_dict(data):
        """Создать объект Task из sqlite3.Row"""
        if not data:
            return None

        # Преобразуем даты
        due_date = data.get('due_date')
        if isinstance(due_date, str):
            due_date = None
            for date_format in (
                '%Y-%m-%d',
                '%d.%m.%Y',
                '%Y-%m-%d %H:%M:%S',
                '%d.%m.%Y %H:%M:%S'
            ):
                try:
                    due_date = datetime.strptime(data.get('due_date'), date_format).date()
                    break
                except ValueError:
                    continue

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
            priority=data.get('priority'),
            is_financial=bool(data.get('is_financial', 0)),
            work_id=data.get('work_id')
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

    def validate_title(self, title: str) -> tuple:
        """
        Валидация названия задачи

        Returns:
            (is_valid: bool, error_message: str)
        """
        title = title.strip() if isinstance(title, str) else ""

        if not title:
            return False, "Название задачи обязательно"
        if len(title) < 3:
            return False, "Название должно содержать минимум 3 символа"
        if len(title) > 255:
            return False, "Название слишком длинное (макс 255 символов)"

        return True, ""

    def is_valid_for_save(self) -> bool:
        """Полная валидация перед сохранением"""
        is_ok, _ = self.validate_title(self.title)
        return is_ok
