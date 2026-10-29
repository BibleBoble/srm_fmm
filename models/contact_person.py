"""
Модель контактного лица
"""
from datetime import datetime


class ContactPerson:
    """
    Класс, представляющий контактное лицо клиента
    """

    def __init__(self, id=None, client_id=None, full_name="", position="",
                 phone="", is_primary=False, created_at=None):
        """
        Args:
            id: int - ID контактного лица
            client_id: int - ID клиента
            full_name: str - ФИО
            position: str - должность
            phone: str - телефон
            is_primary: bool - основное контактное лицо?
            created_at: datetime - дата создания
        """
        self.id = id
        self.client_id = client_id
        self.full_name = full_name
        self.position = position
        self.phone = phone
        self.is_primary = is_primary
        self.created_at = created_at or datetime.now()

    def __repr__(self):
        return f"ContactPerson(id={self.id}, name='{self.full_name}', position='{self.position}')"

    def __str__(self):
        return f"{self.full_name} ({self.position})" if self.position else self.full_name

    def to_dict(self):
        """Преобразовать объект в словарь"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'full_name': self.full_name,
            'position': self.position,
            'phone': self.phone,
            'is_primary': self.is_primary,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    @staticmethod
    def from_dict(data):
        """Создать объект ContactPerson из словаря"""
        return ContactPerson(
            id=data.get('id'),
            client_id=data.get('client_id'),
            full_name=data.get('full_name', ''),
            position=data.get('position', ''),
            phone=data.get('phone', ''),
            is_primary=bool(data.get('is_primary', 0)),
            created_at=data.get('created_at')
        )

    def is_valid(self):
        """Проверка корректности данных"""
        if not self.full_name or len(self.full_name.strip()) < 2:
            return False
        return True

    def validate_full_name(self, name: str) -> tuple:
        """
        Валидация ФИО контактного лица

        Returns:
            (is_valid: bool, error_message: str)
        """
        name = name.strip() if isinstance(name, str) else ""

        if not name:
            return False, "ФИО контактного лица обязательно"
        if len(name) < 2:
            return False, "ФИО должно содержать минимум 2 символа"
        if len(name) > 200:
            return False, "ФИО слишком длинное (макс 200 символов)"

        return True, ""

    def is_valid_for_save(self) -> bool:
        """Полная валидация перед сохранением"""
        is_ok, _ = self.validate_full_name(self.full_name)
        return is_ok

