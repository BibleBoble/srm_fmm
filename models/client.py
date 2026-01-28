"""
Модель клиента (компании)
"""
from datetime import datetime


class Client:
    """
    Класс, представляющий клиента (компанию)
    """

    def __init__(self, id=None, company="", address="", notes="", created_at=None):
        """
        Args:
            id: int - ID клиента в БД
            company: str - название компании
            address: str - адрес
            notes: str - примечания
            created_at: datetime - дата создания
        """
        self.id = id
        self.company = company
        self.address = address
        self.notes = notes
        self.created_at = created_at or datetime.now()

    def __repr__(self):
        return f"Client(id={self.id}, company='{self.company}')"

    def __str__(self):
        return self.company

    def to_dict(self):
        """Преобразовать объект в словарь"""
        return {
            'id': self.id,
            'company': self.company,
            'address': self.address,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    @staticmethod
    def from_dict(data):
        """Создать объект Client из словаря"""
        return Client(
            id=data.get('id'),
            company=data.get('company', ''),
            address=data.get('address', ''),
            notes=data.get('notes', ''),
            created_at=data.get('created_at')
        )

    def is_valid(self):
        """Проверка корректности данных"""
        if not self.company or len(self.company.strip()) < 2:
            return False
        return True