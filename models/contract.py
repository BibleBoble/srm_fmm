"""
Модель договора
"""
from datetime import datetime, date


class Contract:
    """
    Класс, представляющий договор
    """

    def __init__(self, id=None, client_id=None, number="", contract_date=None,
                 amount=0.0, status="active", created_at=None):
        """
        Args:
            id: int - ID договора в БД
            client_id: int - ID клиента
            number: str - номер договора
            contract_date: date - дата договора
            amount: float - сумма договора
            status: str - статус (active, completed, cancelled)
            created_at: datetime - дата создания записи
        """
        self.id = id
        self.client_id = client_id
        self.number = number
        self.contract_date = contract_date or date.today()
        self.amount = amount
        self.status = status
        self.created_at = created_at or datetime.now()

    def __repr__(self):
        """Строковое представление объекта"""
        return f"Contract(id={self.id}, number='{self.number}', amount={self.amount})"

    def __str__(self):
        """Пользовательское строковое представление"""
        return f"Договор №{self.number} от {self.contract_date} на сумму {self.amount} руб."

    def to_dict(self):
        """
        Преобразовать объект в словарь

        Returns:
            dict - словарь с данными договора
        """
        return {
            'id': self.id,
            'client_id': self.client_id,
            'number': self.number,
            'contract_date': self.contract_date.isoformat() if isinstance(self.contract_date,
                                                                          date) else self.contract_date,
            'amount': self.amount,
            'status': self.status,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    @staticmethod
    def from_dict(data):
        """
        Создать объект Contract из словаря

        Args:
            data: dict - словарь с данными

        Returns:
            Contract - объект договора
        """
        contract_date = data.get('contract_date')
        if isinstance(contract_date, str):
            contract_date = datetime.strptime(contract_date, '%Y-%m-%d').date()

        return Contract(
            id=data.get('id'),
            client_id=data.get('client_id'),
            number=data.get('number', ''),
            contract_date=contract_date,
            amount=data.get('amount', 0.0),
            status=data.get('status', 'active'),
            created_at=data.get('created_at')
        )

    def is_valid(self):
        """
        Проверка корректности данных договора

        Returns:
            bool - True если данные корректны
        """
        if not self.number or len(self.number.strip()) == 0:
            return False
        if self.amount < 0:
            return False
        if not self.client_id:
            return False
        return True

    def is_active(self):
        """Проверка активности договора"""
        return self.status == 'active'