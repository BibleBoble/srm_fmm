"""
Модель записи в истории взаимодействий
"""
from datetime import datetime, date


class Interaction:
    """
    Класс, представляющий запись в истории взаимодействий с клиентом
    """

    # Типы взаимодействий
    TYPE_CALL = "Звонок"
    TYPE_KP_SENT = "Отправлено КП"
    TYPE_WORK_STARTED = "Запуск работы"
    TYPE_WORK_COMPLETED = "Работа выполнена"

    TYPES = [TYPE_CALL, TYPE_KP_SENT, TYPE_WORK_STARTED, TYPE_WORK_COMPLETED]

    def __init__(self, id=None, client_id=None, date_interaction=None,
                 type_interaction="", description="", created_at=None):
        """
        Args:
            id: int - ID записи
            client_id: int - ID клиента
            date_interaction: date - дата взаимодействия
            type_interaction: str - тип (Звонок, Отправлено КП и т.д.)
            description: str - описание
            created_at: datetime - дата создания записи
        """
        self.id = id
        self.client_id = client_id
        self.date_interaction = date_interaction or date.today()
        self.type_interaction = type_interaction
        self.description = description
        self.created_at = created_at or datetime.now()

    def __repr__(self):
        return f"Interaction(id={self.id}, type='{self.type_interaction}', date={self.date_interaction})"

    def __str__(self):
        return f"{self.date_interaction} - {self.type_interaction}"

    def to_dict(self):
        """Преобразовать объект в словарь"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'date': self.date_interaction.isoformat() if isinstance(self.date_interaction,
                                                                    date) else self.date_interaction,
            'type': self.type_interaction,
            'description': self.description,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    @staticmethod
    def from_dict(data):
        """Создать объект Interaction из словаря"""
        date_interaction = data.get('date')
        if isinstance(date_interaction, str):
            date_interaction = datetime.strptime(date_interaction, '%Y-%m-%d').date()

        return Interaction(
            id=data.get('id'),
            client_id=data.get('client_id'),
            date_interaction=date_interaction,
            type_interaction=data.get('type', ''),
            description=data.get('description', ''),
            created_at=data.get('created_at')
        )

    def is_valid(self):
        """Проверка корректности данных"""
        if self.type_interaction not in self.TYPES:
            return False
        return True