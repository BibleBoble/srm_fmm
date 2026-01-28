"""
Менеджер для работы с задачами в БД
"""
from managers.database import Database
from datetime import date, datetime


class TasksManager:
    """Класс для управления задачами"""

    def __init__(self):
        self.db = Database()

    def add(self, title, description="", due_date=None, client_id=None, priority="Средний"):
        query = """
            INSERT INTO tasks (title, description, due_date, client_id, priority, completed) 
            VALUES (?, ?, ?, ?, ?, 0)
        """
        return self.db.execute(query, (title, description, due_date, client_id, priority))

    def get_all(self, filter_type="all"):
        """
        Получить задачи с данными о клиентах

        Args:
            filter_type: 'all', 'active', 'completed', 'overdue'
        """
        query = """
            SELECT 
                t.id, t.title, t.description, t.due_date, t.completed, t.created_at,
                t.client_id,
                c.company as client_name
            FROM tasks t
            LEFT JOIN clients c ON t.client_id = c.id
            WHERE 1=1
        """
        params = []

        if filter_type == 'active':
            query += " AND t.completed = 0"
        elif filter_type == 'completed':
            query += " AND t.completed = 1"
        elif filter_type == 'overdue':
            query += " AND t.completed = 0 AND t.due_date < ?"
            params.append(date.today().isoformat())

        query += " ORDER BY t.completed ASC, t.due_date ASC"

        return self.db.fetch_all(query, tuple(params))

    def update(self, task_id, title, description, due_date, client_id):
        """Обновить задачу"""
        query = """
            UPDATE tasks 
            SET title = ?, description = ?, due_date = ?, client_id = ?
            WHERE id = ?
        """
        self.db.execute(query, (title, description, due_date, client_id, task_id))

    def toggle_status(self, task_id, current_status):
        """Переключить статус (Выполнено/Не выполнено)"""
        new_status = 0 if current_status else 1
        query = "UPDATE tasks SET completed = ? WHERE id = ?"
        self.db.execute(query, (new_status, task_id))
        return new_status

    def delete(self, task_id):
        """Удалить задачу"""
        query = "DELETE FROM tasks WHERE id = ?"
        self.db.execute(query, (task_id,))

    def search(self, text):
        """Поиск по названию или клиенту"""
        search = f"%{text}%"
        query = """
            SELECT 
                t.id, t.title, t.description, t.due_date, t.completed, t.created_at,
                t.client_id,
                c.company as client_name
            FROM tasks t
            LEFT JOIN clients c ON t.client_id = c.id
            WHERE t.title LIKE ? OR c.company LIKE ?
            ORDER BY t.completed ASC, t.due_date ASC
        """
        return self.db.fetch_all(query, (search, search))

    def get_count(self, only_active=True):
        """Количество задач"""
        if only_active:
            res = self.db.fetch_one("SELECT COUNT(*) as c FROM tasks WHERE completed = 0")
        else:
            res = self.db.fetch_one("SELECT COUNT(*) as c FROM tasks")
        return res['c']