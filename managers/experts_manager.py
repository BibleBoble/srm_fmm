# managers/experts_manager.py

from managers.database import Database


class ExpertsManager:
    def __init__(self):
        self.db = Database()

    # Эксперты (основная запись)
    def add_expert(self, name: str) -> int:
        query = "INSERT INTO experts (name) VALUES (?)"
        return self.db.execute(query, (name.strip(),))

    def get_expert_by_id(self, expert_id: int) -> dict | None:
        expert = self.db.fetch_one("SELECT * FROM experts WHERE id = ?", (expert_id,))
        if not expert:
            return None

        expert_dict = dict(expert)
        expert_dict['contacts'] = self.get_contacts(expert_id)
        expert_dict['specializations'] = self.get_specializations(expert_id)
        return expert_dict

    def update_expert(self, expert_id: int, name: str):
        query = "UPDATE experts SET name = ? WHERE id = ?"
        self.db.execute(query, (name.strip(), expert_id))

    def delete_expert(self, expert_id: int):
        self.db.execute("DELETE FROM experts WHERE id = ?", (expert_id,))

    # Контактные лица (до 4)
    def add_contact(self, expert_id: int, full_name: str, position: str = "", phone: str = "", email: str = "", is_primary: bool = False) -> int | None:
        if self.get_contact_count(expert_id) >= 4:
            return None  # Лимит достигнут

        if is_primary:
            self.db.execute("UPDATE expert_contacts SET is_primary = 0 WHERE expert_id = ?", (expert_id,))

        query = """
            INSERT INTO expert_contacts (expert_id, full_name, position, phone, email, is_primary)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.db.execute(query, (expert_id, full_name.strip(), position.strip(), phone.strip(), email.strip(), int(is_primary)))

    def get_contacts(self, expert_id: int) -> list[dict]:
        query = """
            SELECT * FROM expert_contacts
            WHERE expert_id = ?
            ORDER BY is_primary DESC, full_name ASC
        """
        rows = self.db.fetch_all(query, (expert_id,))
        return [dict(row) for row in rows]

    def get_contact_count(self, expert_id: int) -> int:
        row = self.db.fetch_one("SELECT COUNT(*) as cnt FROM expert_contacts WHERE expert_id = ?", (expert_id,))
        return row["cnt"] if row else 0

    def update_contact(self, contact_id: int, full_name: str, position: str = "", phone: str = "", email: str = "", is_primary: bool = False):
        contact = self.db.fetch_one("SELECT expert_id FROM expert_contacts WHERE id = ?", (contact_id,))
        if not contact:
            return

        if is_primary:
            self.db.execute("UPDATE expert_contacts SET is_primary = 0 WHERE expert_id = ? AND id != ?", (contact['expert_id'], contact_id))

        query = """
            UPDATE expert_contacts
            SET full_name = ?, position = ?, phone = ?, email = ?, is_primary = ?
            WHERE id = ?
        """
        self.db.execute(query, (full_name.strip(), position.strip(), phone.strip(), email.strip(), int(is_primary), contact_id))

    def delete_contact(self, contact_id: int):
        self.db.execute("DELETE FROM expert_contacts WHERE id = ?", (contact_id,))

    # Специализации (неограниченно)
    def add_specialization(self, expert_id: int, specialization: str) -> int | None:
        spec = specialization.strip()
        if not spec or self.db.fetch_one(
            "SELECT 1 FROM expert_specializations WHERE expert_id = ? AND LOWER(specialization) = LOWER(?)",
            (expert_id, spec)
        ):
            return None  # Пусто или дубликат

        query = "INSERT INTO expert_specializations (expert_id, specialization) VALUES (?, ?)"
        return self.db.execute(query, (expert_id, spec))

    def get_specializations(self, expert_id: int) -> list[str]:
        rows = self.db.fetch_all(
            "SELECT specialization FROM expert_specializations WHERE expert_id = ? ORDER BY specialization",
            (expert_id,)
        )
        return [row["specialization"] for row in rows]

    def delete_specialization(self, expert_id: int, specialization: str):
        self.db.execute(
            "DELETE FROM expert_specializations WHERE expert_id = ? AND specialization = ?",
            (expert_id, specialization.strip())
        )

    # Пагинация + поиск
    def get_paginated(self, page: int = 1, per_page: int = 30, search: str = None, sort_by: str = None, sort_order: str = "ASC"):
        offset = (page - 1) * per_page
        params = []
        where = []

        if search:
            term = f"%{search.lower()}%"
            where.append("""
                LOWER(e.name) LIKE ? OR
                EXISTS (SELECT 1 FROM expert_contacts ec WHERE ec.expert_id = e.id AND (LOWER(ec.full_name) LIKE ? OR LOWER(ec.phone) LIKE ? OR LOWER(ec.email) LIKE ?)) OR
                EXISTS (SELECT 1 FROM expert_specializations es WHERE es.expert_id = e.id AND LOWER(es.specialization) LIKE ?)
            """)
            params.extend([term] * 5)  # Расширен для контактов (full_name, phone, email) + специальности

        where_sql = "WHERE " + " OR ".join(where) if where else ""
        params_for_count = params.copy()

        order_by = "ORDER BY e.name ASC"
        if sort_by == "name":
            order_by = f"ORDER BY e.name {sort_order}"

        # Запрос с агрегацией
        query = f"""
            SELECT e.*,
                   (SELECT full_name FROM expert_contacts WHERE expert_id = e.id AND is_primary = 1 LIMIT 1) AS primary_contact,
                   (SELECT phone FROM expert_contacts WHERE expert_id = e.id AND is_primary = 1 LIMIT 1) AS primary_phone,
                   (SELECT email FROM expert_contacts WHERE expert_id = e.id AND is_primary = 1 LIMIT 1) AS primary_email,
                   GROUP_CONCAT(es.specialization, ', ') AS specializations_str
            FROM experts e
            LEFT JOIN expert_specializations es ON es.expert_id = e.id
            {where_sql}
            GROUP BY e.id
            {order_by}
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])

        rows = self.db.fetch_all(query, tuple(params))
        items = [dict(row) for row in rows]

        count_query = f"SELECT COUNT(DISTINCT e.id) as cnt FROM experts e {where_sql}"
        count_row = self.db.fetch_one(count_query, tuple(params_for_count))
        total = count_row["cnt"] if count_row else 0

        return items, total

    def get_count(self) -> int:
        """Возвращает общее количество экспертов"""
        row = self.db.fetch_one("SELECT COUNT(*) as cnt FROM experts")
        return row["cnt"] if row else 0

    def get_all(self) -> list[dict]:
        """Возвращает всех экспертов без пагинации"""
        query = """
            SELECT e.*,
                   (SELECT full_name FROM expert_contacts WHERE expert_id = e.id AND is_primary = 1 LIMIT 1) AS primary_contact,
                   (SELECT phone FROM expert_contacts WHERE expert_id = e.id AND is_primary = 1 LIMIT 1) AS primary_phone,
                   (SELECT email FROM expert_contacts WHERE expert_id = e.id AND is_primary = 1 LIMIT 1) AS primary_email,
                   GROUP_CONCAT(es.specialization, ', ') AS specializations_str
            FROM experts e
            LEFT JOIN expert_specializations es ON es.expert_id = e.id
            GROUP BY e.id
            ORDER BY e.name ASC
        """
        rows = self.db.fetch_all(query)
        return [dict(row) for row in rows] if rows else []