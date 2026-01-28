"""
Менеджер для работы с контактными лицами в БД
"""
from managers.database import Database


class ContactPersonsManager:
    """Класс для управления контактными лицами клиентов"""

    def __init__(self):
        self.db = Database()

    def add(self, client_id, full_name, position="", phone="", is_primary=False):
        """
        Добавить контактное лицо.

        Args:
            client_id: int - ID клиента
            full_name: str - ФИО
            position: str - должность
            phone: str - телефон
            is_primary: bool - основное контактное лицо?

        Returns:
            int - ID добавленного контактного лица
        """
        # Если это основное контактное лицо, снимаем флаг с остальных
        if is_primary:
            self.db.execute(
                "UPDATE contact_persons SET is_primary = 0 WHERE client_id = ?",
                (client_id,)
            )

        query = """
            INSERT INTO contact_persons (client_id, full_name, position, phone, is_primary) 
            VALUES (?, ?, ?, ?, ?)
        """
        return self.db.execute(query, (client_id, full_name, position, phone, int(is_primary)))

    def get_by_client(self, client_id):
        """
        Получить все контактные лица клиента.

        Args:
            client_id: int - ID клиента

        Returns:
            list - список контактных лиц
        """
        query = """
            SELECT * FROM contact_persons 
            WHERE client_id = ? 
            ORDER BY is_primary DESC, full_name
        """
        return self.db.fetch_all(query, (client_id,))

    def get_primary(self, client_id):
        """
        Получить основное контактное лицо клиента.

        Args:
            client_id: int - ID клиента

        Returns:
            sqlite3.Row или None
        """
        query = """
            SELECT * FROM contact_persons 
            WHERE client_id = ? AND is_primary = 1
        """
        return self.db.fetch_one(query, (client_id,))

    def update(self, contact_id, full_name, position, phone, is_primary):
        """
        Обновить данные контактного лица.

        Args:
            contact_id: int - ID контактного лица
            full_name: str - ФИО
            position: str - должность
            phone: str - телефон
            is_primary: bool - основное?
        """
        # Получаем client_id для этого контакта
        contact = self.db.fetch_one("SELECT client_id FROM contact_persons WHERE id = ?", (contact_id,))

        if contact and is_primary:
            # Снимаем флаг primary с других контактов этого клиента
            self.db.execute(
                "UPDATE contact_persons SET is_primary = 0 WHERE client_id = ? AND id != ?",
                (contact['client_id'], contact_id)
            )

        query = """
            UPDATE contact_persons 
            SET full_name = ?, position = ?, phone = ?, is_primary = ?
            WHERE id = ?
        """
        self.db.execute(query, (full_name, position, phone, int(is_primary), contact_id))

    def delete(self, contact_id):
        """
        Удалить контактное лицо.

        Args:
            contact_id: int - ID контактного лица
        """
        query = "DELETE FROM contact_persons WHERE id = ?"
        self.db.execute(query, (contact_id,))

    def set_primary(self, contact_id):
        """
        Установить контактное лицо как основное.

        Args:
            contact_id: int - ID контактного лица
        """
        # Получаем client_id
        contact = self.db.fetch_one("SELECT client_id FROM contact_persons WHERE id = ?", (contact_id,))

        if contact:
            # Снимаем флаг со всех
            self.db.execute(
                "UPDATE contact_persons SET is_primary = 0 WHERE client_id = ?",
                (contact['client_id'],)
            )
            # Устанавливаем флаг на выбранный
            self.db.execute(
                "UPDATE contact_persons SET is_primary = 1 WHERE id = ?",
                (contact_id,)
            )

    def get_count(self, client_id):
        """
        Получить количество контактных лиц у клиента.

        Args:
            client_id: int - ID клиента

        Returns:
            int - количество контактных лиц
        """
        query = "SELECT COUNT(*) as count FROM contact_persons WHERE client_id = ?"
        result = self.db.fetch_one(query, (client_id,))
        return result['count'] if result else 0