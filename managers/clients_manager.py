"""
Менеджер для работы с клиентами (компаниями) в БД
"""
from managers.database import Database


class ClientsManager:
    """Класс для управления клиентами"""

    def __init__(self):
        self.db = Database()

    def add(self, company, address="", notes=""):
        """
        Добавить нового клиента (компанию).

        Args:
            company: str - название компании
            address: str - адрес
            notes: str - примечания

        Returns:
            int - ID добавленного клиента
        """
        query = """
            INSERT INTO clients (company, address, notes) 
            VALUES (?, ?, ?)
        """
        return self.db.execute(query, (company, address, notes))

    def get_all(self):
        """Получить всех клиентов с основной контактной информацией"""
        query = """
            SELECT 
                c.*,
                cp.full_name as primary_contact,
                cp.position as primary_position,
                cp.phone as primary_phone,
                ce.email as primary_email
            FROM clients c
            LEFT JOIN contact_persons cp ON c.id = cp.client_id AND cp.is_primary = 1
            LEFT JOIN contact_emails ce ON cp.id = ce.contact_person_id AND ce.is_primary = 1
            ORDER BY c.company
        """
        rows = self.db.fetch_all(query)
        return [dict(row) for row in rows]

    def get_by_id(self, client_id):
        """Получить клиента по ID с основной контактной информацией"""
        query = """
            SELECT 
                c.*,
                cp.full_name as primary_contact,
                cp.position as primary_position,
                cp.phone as primary_phone,
                ce.email as primary_email
            FROM clients c
            LEFT JOIN contact_persons cp ON c.id = cp.client_id AND cp.is_primary = 1
            LEFT JOIN contact_emails ce ON cp.id = ce.contact_person_id AND ce.is_primary = 1
            WHERE c.id = ?
        """
        row = self.db.fetch_one(query, (client_id,))
        return dict(row) if row else None

    def search(self, query_text):
        """Поиск клиентов с основной контактной информацией"""
        search_term = f"%{query_text}%"
        query = """
            SELECT 
                c.*,
                cp.full_name as primary_contact,
                cp.position as primary_position,
                cp.phone as primary_phone,
                ce.email as primary_email
            FROM clients c
            LEFT JOIN contact_persons cp ON c.id = cp.client_id AND cp.is_primary = 1
            LEFT JOIN contact_emails ce ON cp.id = ce.contact_person_id AND ce.is_primary = 1
            WHERE c.company LIKE ? OR cp.full_name LIKE ? OR ce.email LIKE ?
            ORDER BY c.company
        """
        rows = self.db.fetch_all(query, (search_term, search_term, search_term))
        return [dict(row) for row in rows]

    def update(self, client_id, company, address, notes):
        """
        Обновить данные клиента.

        Args:
            client_id: int - ID клиента
            company: str - название компании
            address: str - адрес
            notes: str - примечания
        """
        query = """
            UPDATE clients 
            SET company = ?, address = ?, notes = ?
            WHERE id = ?
        """
        self.db.execute(query, (company, address, notes, client_id))

    def delete(self, client_id):
        """
        Удалить клиента.
        При удалении автоматически удалятся все связанные данные
        (контактные лица, email, история) благодаря CASCADE.

        Args:
            client_id: int - ID клиента
        """
        query = "DELETE FROM clients WHERE id = ?"
        self.db.execute(query, (client_id,))

    def get_count(self):
        """Количество клиентов"""
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM clients")
        return result['count'] if result else 0

    def get_primary_contact(self, client_id):
        """Получить основной контакт клиента (возвращает словарь)"""
        query = """
            SELECT * FROM contact_persons 
            WHERE client_id = ? AND is_primary = 1 
            LIMIT 1
        """
        row = self.db.fetch_one(query, (client_id,))

        if row:
            return dict(row)
        return None