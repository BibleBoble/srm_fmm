"""
Модель эксперта
"""
from datetime import datetime


class Expert:
    """
    Класс, представляющий эксперта
    """

    def __init__(self, id=None, name="", specialization="", phone="",
                 email="", created_at=None):
        """
        Args:
            id: int - ID эксперта в БД
            name: str - имя эксперта
            specialization: str - специализация
            phone: str - телефон
            email: str - email
            created_at: datetime - дата создания записи
        """
        self.id = id
        self.name = name
        self.specialization = specialization
        self.phone = phone
        self.email = email
        self.created_at = created_at or datetime.now()

    def __repr__(self):
        """Строковое представление объекта"""
        return f"Expert(id={self.id}, name='{self.name}', specialization='{self.specialization}')"

    def __str__(self):
        """Пользовательское строковое представление"""
        return f"{self.name} - {self.specialization}"

    def to_dict(self):
        """
        Преобразовать объект в словарь

        Returns:
            dict - словарь с данными эксперта
        """
        return {
            'id': self.id,
            'name': self.name,
            'specialization': self.specialization,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    @staticmethod
    def from_dict(data):
        """
        Создать объект Expert из словаря

        Args:
            data: dict - словарь с данными

        Returns:
            Expert - объект эксперта
        """
        return Expert(
            id=data.get('id'),
            name=data.get('name', ''),
            specialization=data.get('specialization', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            created_at=data.get('created_at')
        )

    def is_valid(self):
        """
        Проверка корректности данных эксперта

        Returns:
            bool - True если данные корректны
        """
        if not self.name or len(self.name.strip()) < 2:
            return False
        return True