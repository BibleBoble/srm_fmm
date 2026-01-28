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
        """
        Получить всех клиентов с основным контактным лицом.

        Returns:
            list - список клиентов с информацией о главном контакте
        """
        query = """
            SELECT 
                c.id,
                c.company,
                c.address,
                c.notes,
                c.created_at,
                cp.full_name as primary_contact,
                cp.position as primary_position,
                cp.phone as primary_phone
            FROM clients c
            LEFT JOIN contact_persons cp ON c.id = cp.client_id AND cp.is_primary = 1
            ORDER BY c.company
        """
        return self.db.fetch_all(query)

    def get_by_id(self, client_id):
        """
        Получить клиента по ID.

        Args:
            client_id: int - ID клиента

        Returns:
            sqlite3.Row или None
        """
        query = "SELECT * FROM clients WHERE id = ?"
        return self.db.fetch_one(query, (client_id,))

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

    def search(self, search_text):
        """
        Поиск клиентов по названию компании, адресу или контактному лицу (без учёта регистра).

        Args:
            search_text: str - текст для поиска

        Returns:
            list - найденные клиенты
        """
        # Приводим поисковый запрос к нижнему регистру в Python
        search_lower = search_text.lower()

        query = """
            SELECT 
                c.id,
                c.company,
                c.address,
                c.notes,
                c.created_at,
                cp.full_name as primary_contact,
                cp.position as primary_position,
                cp.phone as primary_phone
            FROM clients c
            LEFT JOIN contact_persons cp ON c.id = cp.client_id AND cp.is_primary = 1
            ORDER BY c.company
        """

        # Получаем всех клиентов
        all_clients = self.db.fetch_all(query)

        # Фильтруем в Python (с учётом русских букв)
        if not search_lower:
            return all_clients

        filtered = []
        for client in all_clients:
            # Приводим все поля к нижнему регистру и проверяем вхождение
            company = (client['company'] or '').lower()
            address = (client['address'] or '').lower()
            contact = (client['primary_contact'] or '').lower()

            if (search_lower in company or
                    search_lower in address or
                    search_lower in contact):
                filtered.append(client)

        return filtered

    def get_count(self):
        """
        Получить количество клиентов.

        Returns:
            int - количество клиентов
        """
        query = "SELECT COUNT(*) as count FROM clients"
        result = self.db.fetch_one(query)
        return result['count'] if result else 0