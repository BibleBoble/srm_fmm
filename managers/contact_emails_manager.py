"""
Менеджер для работы с email контактных лиц в БД
"""
from managers.database import Database


class ContactEmailsManager:
    """Класс для управления email адресами контактных лиц"""

    def __init__(self):
        self.db = Database()

    def add(self, contact_person_id, email, is_primary=False):
        """
        Добавить email для контактного лица.

        Args:
            contact_person_id: int - ID контактного лица
            email: str - email адрес
            is_primary: bool - основной email?

        Returns:
            int - ID добавленного email
        """
        # Если это основной email, снимаем флаг с остальных email этого контакта
        if is_primary:
            self.db.execute(
                "UPDATE contact_emails SET is_primary = 0 WHERE contact_person_id = ?",
                (contact_person_id,)
            )

        query = """
            INSERT INTO contact_emails (contact_person_id, email, is_primary) 
            VALUES (?, ?, ?)
        """
        return self.db.execute(query, (contact_person_id, email, int(is_primary)))

    def get_by_contact(self, contact_person_id):
        """
        Получить все email контактного лица.

        Args:
            contact_person_id: int - ID контактного лица

        Returns:
            list - список email
        """
        query = """
            SELECT * FROM contact_emails 
            WHERE contact_person_id = ? 
            ORDER BY is_primary DESC
        """
        rows = self.db.fetch_all(query, (contact_person_id,))
        return [dict(row) for row in rows]

    def get_by_client(self, client_id):
        """
        Получить все email всех контактных лиц клиента.

        Args:
            client_id: int - ID клиента

        Returns:
            list - список всех email клиента
        """
        query = """
            SELECT ce.*, cp.full_name as contact_name
            FROM contact_emails ce
            JOIN contact_persons cp ON ce.contact_person_id = cp.id
            WHERE cp.client_id = ?
            ORDER BY ce.is_primary DESC, cp.is_primary DESC
        """
        rows = self.db.fetch_all(query, (client_id,))
        return [dict(row) for row in rows]

    def get_primary_by_contact(self, contact_person_id):
        """
        Получить основной email контактного лица.

        Args:
            contact_person_id: int - ID контактного лица

        Returns:
            dict или None
        """
        query = """
            SELECT * FROM contact_emails 
            WHERE contact_person_id = ? AND is_primary = 1
        """
        row = self.db.fetch_one(query, (contact_person_id,))
        return dict(row) if row else None

    def get_primary_by_client(self, client_id):
        """
        Получить основной email для клиента (первый основной среди контактов).

        Args:
            client_id: int - ID клиента

        Returns:
            dict или None
        """
        query = """
            SELECT ce.* 
            FROM contact_emails ce
            JOIN contact_persons cp ON ce.contact_person_id = cp.id
            WHERE cp.client_id = ? AND ce.is_primary = 1
            LIMIT 1
        """
        row = self.db.fetch_one(query, (client_id,))
        return dict(row) if row else None

    def delete(self, email_id):
        """
        Удалить email.

        Args:
            email_id: int - ID записи email
        """
        query = "DELETE FROM contact_emails WHERE id = ?"
        self.db.execute(query, (email_id,))

    def set_primary(self, email_id):
        """
        Установить email как основной для контакта.

        Args:
            email_id: int - ID записи email
        """
        # Получаем contact_person_id
        email_record = self.db.fetch_one("SELECT contact_person_id FROM contact_emails WHERE id = ?", (email_id,))

        if email_record:
            # Снимаем флаг со всех email этого контакта
            self.db.execute(
                "UPDATE contact_emails SET is_primary = 0 WHERE contact_person_id = ?",
                (email_record['contact_person_id'],)
            )
            # Устанавливаем на выбранный
            self.db.execute(
                "UPDATE contact_emails SET is_primary = 1 WHERE id = ?",
                (email_id,)
            )

    def get_count_by_contact(self, contact_person_id):
        """
        Получить количество email у контактного лица.

        Args:
            contact_person_id: int - ID контактного лица

        Returns:
            int - количество email
        """
        query = "SELECT COUNT(*) as count FROM contact_emails WHERE contact_person_id = ?"
        result = self.db.fetch_one(query, (contact_person_id,))
        return result['count'] if result else 0

    def update(self, email_id, email, is_primary):
        """
        Обновить email.

        Args:
            email_id: int - ID записи email
            email: str - новый email
            is_primary: bool - основной?
        """
        # Получаем contact_person_id
        email_record = self.db.fetch_one("SELECT contact_person_id FROM contact_emails WHERE id = ?", (email_id,))

        if email_record and is_primary:
            # Снимаем флаг с других email этого контакта
            self.db.execute(
                "UPDATE contact_emails SET is_primary = 0 WHERE contact_person_id = ? AND id != ?",
                (email_record['contact_person_id'], email_id)
            )

        query = """
            UPDATE contact_emails 
            SET email = ?, is_primary = ?
            WHERE id = ?
        """
        self.db.execute(query, (email, int(is_primary), email_id))

    def delete_by_contact(self, contact_person_id):
        """
        Удалить все email контактного лица.

        Args:
            contact_person_id: int - ID контактного лица
        """
        query = "DELETE FROM contact_emails WHERE contact_person_id = ?"
        self.db.execute(query, (contact_person_id,))