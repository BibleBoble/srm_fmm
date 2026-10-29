"""
Менеджер для работы с клиентами (компаниями) в БД
"""
from managers.database import Database


class ClientsManager:
    """Класс для управления клиентами"""

    def __init__(self):
        self.db = Database()

    def add(self, company, address="", notes="", partner_data=None):
        """
        Добавить нового клиента (компанию).

        Args:
            company: str - название компании
            address: str - адрес
            notes: str - примечания

        Returns:
            int - ID добавленного клиента
        """
        from datetime import date

        partner_data = partner_data or {}
        query = """
            INSERT INTO clients (
                company, address, notes, public_id, full_legal_name, legal_address,
                postal_address, ogrn, inn_kpp, bank_details, responsible_person,
                partner_email, partner_phone
            )
            VALUES (
                ?, ?, ?,
                (
                    SELECT printf(
                        '%d-%d',
                        COALESCE(
                            MAX(CAST(substr(public_id, 1, instr(public_id, '-') - 1) AS INTEGER)),
                            2014
                        ) + 1,
                        ?
                    )
                    FROM clients
                    WHERE public_id IS NOT NULL AND instr(public_id, '-') > 0
                ),
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """
        return self.db.execute(
            query,
            (
                company,
                address,
                notes,
                date.today().year,
                partner_data.get("full_legal_name", ""),
                partner_data.get("legal_address", ""),
                partner_data.get("postal_address", ""),
                partner_data.get("ogrn", ""),
                partner_data.get("inn_kpp", ""),
                partner_data.get("bank_details", ""),
                partner_data.get("responsible_person", ""),
                partner_data.get("partner_email", ""),
                partner_data.get("partner_phone", "")
            )
        )

    @staticmethod
    def get_display_id(client):
        """Return the public client code, falling back to the legacy database ID."""
        if not client:
            return ""
        return client.get("public_id") or client.get("id", "")

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
        # Нечувствительный к регистру поиск по названию компании, имени контактного лица и email
        search_term = f"%{query_text.lower()}%"
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
            WHERE LOWER(c.company) LIKE ?
               OR LOWER(cp.full_name) LIKE ?
               OR LOWER(ce.email) LIKE ?
               OR LOWER(COALESCE(c.public_id, '')) LIKE ?
               OR CAST(c.id AS TEXT) LIKE ?
            ORDER BY c.company
        """
        rows = self.db.fetch_all(
            query,
            (search_term, search_term, search_term, search_term, search_term)
        )
        return [dict(row) for row in rows]

    def update(self, client_id, company, address, notes, partner_data=None):
        """
        Обновить данные клиента.

        Args:
            client_id: int - ID клиента
            company: str - название компании
            address: str - адрес
            notes: str - примечания
        """
        if partner_data is None:
            query = """
                UPDATE clients
                SET company = ?, address = ?, notes = ?
                WHERE id = ?
            """
            self.db.execute(query, (company, address, notes, client_id))
            return

        query = """
            UPDATE clients
            SET company = ?, address = ?, notes = ?, full_legal_name = ?,
                legal_address = ?, postal_address = ?, ogrn = ?, inn_kpp = ?,
                bank_details = ?, responsible_person = ?, partner_email = ?,
                partner_phone = ?
            WHERE id = ?
        """
        self.db.execute(
            query,
            (
                company,
                address,
                notes,
                partner_data.get("full_legal_name", ""),
                partner_data.get("legal_address", ""),
                partner_data.get("postal_address", ""),
                partner_data.get("ogrn", ""),
                partner_data.get("inn_kpp", ""),
                partner_data.get("bank_details", ""),
                partner_data.get("responsible_person", ""),
                partner_data.get("partner_email", ""),
                partner_data.get("partner_phone", ""),
                client_id
            )
        )

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

    def get_id_by_company_name(self, company_name):
        """Вернуть id клиента по точному названию компании или None, если не найден"""
        try:
            if not company_name:
                return None
            # Нечувствительный к регистру точный поиск
            query = "SELECT id FROM clients WHERE LOWER(company) = ? LIMIT 1"
            row = self.db.fetch_one(query, (company_name.lower(),))
            if not row:
                return None
            # row может быть sqlite3.Row
            if hasattr(row, 'keys'):
                return row['id']
            return dict(row).get('id')
        except Exception as e:
            print(f"Ошибка поиска клиента по имени: {e}")
            return None

    def get_sorted_by_company(self, reverse: bool = False):
        """Получить клиентов отсортированные по названию компании"""
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
        if reverse:
            query = query.replace("ORDER BY c.company", "ORDER BY c.company DESC")
        rows = self.db.fetch_all(query)
        return [dict(row) for row in rows]

    def get_sorted_by_contact(self, reverse: bool = False):
        """Получить клиентов отсортированные по контакту"""
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
            ORDER BY cp.full_name
        """
        if reverse:
            query = query.replace("ORDER BY cp.full_name", "ORDER BY cp.full_name DESC")
        rows = self.db.fetch_all(query)
        return [dict(row) for row in rows]
