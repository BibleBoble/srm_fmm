# managers/contracts_manager.py
"""
Менеджер для работы с договорами в БД
"""
from managers.database import Database


class ContractsManager:
    """Класс для управления договорами"""

    def __init__(self):
        self.db = Database()

    def add(self, client_id, number, date, amount):
        """Добавить договор"""
        query = """
            INSERT INTO contracts (client_id, number, date, amount) 
            VALUES (?, ?, ?, ?)
        """
        return self.db.execute(query, (client_id, number, date, amount))

    def get_all(self):
        """Получить все договора"""
        query = """
            SELECT c.*, cl.company as client_name  # ← ИЗМЕНИТЬ 'name' на 'company'
            FROM contracts c
            LEFT JOIN clients cl ON c.client_id = cl.id
            ORDER BY c.date DESC
        """
        return self.db.fetch_all(query)

    def get_by_client(self, client_id):
        """Получить договора клиента"""
        query = "SELECT * FROM contracts WHERE client_id = ? ORDER BY date DESC"
        return self.db.fetch_all(query, (client_id,))

    def delete(self, contract_id):
        """Удалить договор"""
        query = "DELETE FROM contracts WHERE id = ?"
        self.db.execute(query, (contract_id,))