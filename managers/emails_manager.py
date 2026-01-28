"""
Менеджер для работы с email клиентов в БД
"""
from managers.database import Database


class EmailsManager:
    """Класс для управления email адресами клиентов"""

    def __init__(self):
        self.db = Database()

    def add(self, client_id, email, is_primary=False):
        """
        Добавить email.

        Args:
            client_id: int - ID клиента
            email: str - email адрес
            is_primary: bool - основной email?

        Returns:
            int - ID добавленного email
        """
        # Если это основной email, снимаем флаг с остальных
        if is_primary:
            self.db.execute(
                "UPDATE client_emails SET is_primary = 0 WHERE client_id = ?",
                (client_id,)
            )

        query = """
            INSERT INTO client_emails (client_id, email, is_primary) 
            VALUES (?, ?, ?)
        """
        return self.db.execute(query, (client_id, email, int(is_primary)))

    def get_by_client(self, client_id):
        """
        Получить все email клиента.

        Args:
            client_id: int - ID клиента

        Returns:
            list - список email
        """
        query = """
            SELECT * FROM client_emails 
            WHERE client_id = ? 
            ORDER BY is_primary DESC
        """
        return self.db.fetch_all(query, (client_id,))

    def get_primary(self, client_id):
        """
        Получить основной email клиента.

        Args:
            client_id: int - ID клиента

        Returns:
            sqlite3.Row или None
        """
        query = """
            SELECT * FROM client_emails 
            WHERE client_id = ? AND is_primary = 1
        """
        return self.db.fetch_one(query, (client_id,))

    def update(self, email_id, email, is_primary):
        """
        Обновить email.

        Args:
            email_id: int - ID записи email
            email: str - новый email
            is_primary: bool - основной?
        """
        # Получаем client_id
        email_record = self.db.fetch_one("SELECT client_id FROM client_emails WHERE id = ?", (email_id,))

        if email_record and is_primary:
            # Снимаем флаг с других email этого клиента
            self.db.execute(
                "UPDATE client_emails SET is_primary = 0 WHERE client_id = ? AND id != ?",
                (email_record['client_id'], email_id)
            )

        query = """
            UPDATE client_emails 
            SET email = ?, is_primary = ?
            WHERE id = ?
        """
        self.db.execute(query, (email, int(is_primary), email_id))

    def delete(self, email_id):
        """
        Удалить email.

        Args:
            email_id: int - ID записи email
        """
        query = "DELETE FROM client_emails WHERE id = ?"
        self.db.execute(query, (email_id,))

    def set_primary(self, email_id):
        """
        Установить email как основной.

        Args:
            email_id: int - ID записи email
        """
        # Получаем client_id
        email_record = self.db.fetch_one("SELECT client_id FROM client_emails WHERE id = ?", (email_id,))

        if email_record:
            # Снимаем флаг со всех
            self.db.execute(
                "UPDATE client_emails SET is_primary = 0 WHERE client_id = ?",
                (email_record['client_id'],)
            )
            # Устанавливаем на выбранный
            self.db.execute(
                "UPDATE client_emails SET is_primary = 1 WHERE id = ?",
                (email_id,)
            )

    def get_count(self, client_id):
        """
        Получить количество email у клиента.

        Args:
            client_id: int - ID клиента

        Returns:
            int - количество email
        """
        query = "SELECT COUNT(*) as count FROM client_emails WHERE client_id = ?"
        result = self.db.fetch_one(query, (client_id,))
        return result['count'] if result else 0

    def update(self, email_id, email, is_primary):
        """
        Обновить email.

        Args:
            email_id: int - ID записи email
            email: str - новый email
            is_primary: bool - основной?
        """
        # Получаем client_id
        email_record = self.db.fetch_one("SELECT client_id FROM client_emails WHERE id = ?", (email_id,))

        if email_record and is_primary:
            # Снимаем флаг с других email этого клиента
            self.db.execute(
                "UPDATE client_emails SET is_primary = 0 WHERE client_id = ? AND id != ?",
                (email_record['client_id'], email_id)
            )

        query = """
            UPDATE client_emails 
            SET email = ?, is_primary = ?
            WHERE id = ?
        """
        self.db.execute(query, (email, int(is_primary), email_id))