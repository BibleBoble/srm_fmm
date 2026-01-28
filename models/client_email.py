"""
Модель email клиента
"""
from datetime import datetime


class ClientEmail:
    """
    Класс, представляющий email клиента
    """

    def __init__(self, id=None, client_id=None, email="", is_primary=False, created_at=None):
        """
        Args:
            id: int - ID записи
            client_id: int - ID клиента
            email: str - email адрес
            is_primary: bool - основной email?
            created_at: datetime - дата создания
        """
        self.id = id
        self.client_id = client_id
        self.email = email
        self.is_primary = is_primary
        self.created_at = created_at or datetime.now()

    def __repr__(self):
        return f"ClientEmail(id={self.id}, email='{self.email}')"

    def __str__(self):
        return self.email

    def to_dict(self):
        """Преобразовать объект в словарь"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'email': self.email,
            'is_primary': self.is_primary,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    @staticmethod
    def from_dict(data):
        """Создать объект ClientEmail из словаря"""
        return ClientEmail(
            id=data.get('id'),
            client_id=data.get('client_id'),
            email=data.get('email', ''),
            is_primary=bool(data.get('is_primary', 0)),
            created_at=data.get('created_at')
        )

    def is_valid(self):
        """Проверка корректности email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, self.email))