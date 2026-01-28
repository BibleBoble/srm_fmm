"""
Менеджер для работы с историей взаимодействий в БД
"""
from managers.database import Database
from datetime import date


class InteractionsManager:
    """Класс для управления историей взаимодействий с клиентами"""

    def __init__(self):
        self.db = Database()

    def add(self, client_id, date_interaction, type_interaction, description=""):
        """
        Добавить запись в историю.

        Args:
            client_id: int - ID клиента
            date_interaction: date - дата взаимодействия
            type_interaction: str - тип (Звонок, Отправлено КП и т.д.)
            description: str - описание

        Returns:
            int - ID добавленной записи
        """
        query = """
            INSERT INTO interaction_history (client_id, date, type, description) 
            VALUES (?, ?, ?, ?)
        """
        # Преобразуем date в строку для SQLite
        date_str = date_interaction.isoformat() if isinstance(date_interaction, date) else date_interaction
        return self.db.execute(query, (client_id, date_str, type_interaction, description))

    def get_by_client(self, client_id):
        """
        Получить всю историю взаимодействий с клиентом.

        Args:
            client_id: int - ID клиента

        Returns:
            list - список записей истории (от новых к старым)
        """
        query = """
            SELECT * FROM interaction_history 
            WHERE client_id = ? 
            ORDER BY date DESC, created_at DESC
        """
        return self.db.fetch_all(query, (client_id,))

    def get_by_type(self, client_id, type_interaction):
        """
        Получить историю взаимодействий определённого типа.

        Args:
            client_id: int - ID клиента
            type_interaction: str - тип взаимодействия

        Returns:
            list - список записей
        """
        query = """
            SELECT * FROM interaction_history 
            WHERE client_id = ? AND type = ?
            ORDER BY date DESC
        """
        return self.db.fetch_all(query, (client_id, type_interaction))

    def get_last(self, client_id, limit=5):
        """
        Получить последние N записей истории.

        Args:
            client_id: int - ID клиента
            limit: int - количество записей

        Returns:
            list - последние записи
        """
        query = """
            SELECT * FROM interaction_history 
            WHERE client_id = ? 
            ORDER BY date DESC, created_at DESC
            LIMIT ?
        """
        return self.db.fetch_all(query, (client_id, limit))

    def update(self, interaction_id, date_interaction, type_interaction, description):
        """
        Обновить запись в истории.

        Args:
            interaction_id: int - ID записи
            date_interaction: date - дата
            type_interaction: str - тип
            description: str - описание
        """
        date_str = date_interaction.isoformat() if isinstance(date_interaction, date) else date_interaction
        query = """
            UPDATE interaction_history 
            SET date = ?, type = ?, description = ?
            WHERE id = ?
        """
        self.db.execute(query, (date_str, type_interaction, description, interaction_id))

    def delete(self, interaction_id):
        """
        Удалить запись из истории.

        Args:
            interaction_id: int - ID записи
        """
        query = "DELETE FROM interaction_history WHERE id = ?"
        self.db.execute(query, (interaction_id,))

    def get_count(self, client_id):
        """
        Получить количество записей в истории клиента.

        Args:
            client_id: int - ID клиента

        Returns:
            int - количество записей
        """
        query = "SELECT COUNT(*) as count FROM interaction_history WHERE client_id = ?"
        result = self.db.fetch_one(query, (client_id,))
        return result['count'] if result else 0

    def get_stats(self, client_id):
        """
        Получить статистику по типам взаимодействий.

        Args:
            client_id: int - ID клиента

        Returns:
            dict - словарь {тип: количество}
        """
        query = """
            SELECT type, COUNT(*) as count 
            FROM interaction_history 
            WHERE client_id = ?
            GROUP BY type
        """
        results = self.db.fetch_all(query, (client_id,))
        return {row['type']: row['count'] for row in results}