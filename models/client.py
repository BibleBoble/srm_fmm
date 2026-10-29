"""
Модель клиента (компании)
"""
from datetime import datetime


class Client:
    """
    Класс, представляющий клиента (компанию)
    """

    def __init__(
        self,
        id=None,
        company="",
        address="",
        notes="",
        created_at=None,
        public_id=None,
        full_legal_name="",
        legal_address="",
        postal_address="",
        ogrn="",
        inn_kpp="",
        bank_details="",
        responsible_person="",
        partner_email="",
        partner_phone=""
    ):
        """
        Args:
            id: int - ID клиента в БД
            company: str - название компании
            address: str - адрес
            notes: str - примечания
            created_at: datetime - дата создания
            public_id: str - публичный код клиента; None для старых записей
        """
        self.id = id
        self.company = company
        self.address = address
        self.notes = notes
        self.created_at = created_at or datetime.now()
        self.public_id = public_id
        self.full_legal_name = full_legal_name
        self.legal_address = legal_address
        self.postal_address = postal_address
        self.ogrn = ogrn
        self.inn_kpp = inn_kpp
        self.bank_details = bank_details
        self.responsible_person = responsible_person
        self.partner_email = partner_email
        self.partner_phone = partner_phone

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
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'public_id': self.public_id,
            'full_legal_name': self.full_legal_name,
            'legal_address': self.legal_address,
            'postal_address': self.postal_address,
            'ogrn': self.ogrn,
            'inn_kpp': self.inn_kpp,
            'bank_details': self.bank_details,
            'responsible_person': self.responsible_person,
            'partner_email': self.partner_email,
            'partner_phone': self.partner_phone
        }

    @staticmethod
    def from_dict(data):
        """Создать объект Client из словаря"""
        return Client(
            id=data.get('id'),
            company=data.get('company', ''),
            address=data.get('address', ''),
            notes=data.get('notes', ''),
            created_at=data.get('created_at'),
            public_id=data.get('public_id'),
            full_legal_name=data.get('full_legal_name', ''),
            legal_address=data.get('legal_address', ''),
            postal_address=data.get('postal_address', ''),
            ogrn=data.get('ogrn', ''),
            inn_kpp=data.get('inn_kpp', ''),
            bank_details=data.get('bank_details', ''),
            responsible_person=data.get('responsible_person', ''),
            partner_email=data.get('partner_email', ''),
            partner_phone=data.get('partner_phone', '')
        )

    def is_valid(self):
        """Проверка корректности данных"""
        if not self.company or len(self.company.strip()) < 2:
            return False
        return True

    def validate_company_name(self, name: str) -> tuple:
        """
        Валидация названия компании

        Returns:
            (is_valid: bool, error_message: str)
        """
        name = name.strip() if isinstance(name, str) else ""

        if not name:
            return False, "Название компании обязательно"
        if len(name) < 2:
            return False, "Название должно содержать минимум 2 символа"
        if len(name) > 255:
            return False, "Название слишком длинное (макс 255 символов)"

        return True, ""

    def is_valid_for_save(self) -> bool:
        """Полная валидация перед сохранением"""
        is_ok, _ = self.validate_company_name(self.company)
        return is_ok
