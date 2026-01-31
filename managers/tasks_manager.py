"""
Менеджер для работы с задачами в БД
"""
from managers.database import Database
from datetime import date, datetime
from models.task import Task


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
        """
        query = """
            SELECT 
                t.*, 
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
            # Добавляем логику для просроченных задач
            query += " AND t.completed = 0 AND t.due_date < DATE('now')"

        query += " ORDER BY t.completed ASC, t.due_date ASC"

        rows = self.db.fetch_all(query, params)

        from models.task import Task
        tasks = []
        for row in rows:
            row_dict = dict(row)
            # Создаем объект задачи через метод модели
            task = Task.from_dict(row_dict)
            # Принудительно сохраняем имя клиента из результата JOIN
            task.client_name = row_dict.get('client_name', '—')
            tasks.append(task)

        return tasks

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

    def search(self, query_text):
        """Поиск клиентов (возвращает список словарей)"""
        search_term = f"%{query_text}%"
        query = """
            SELECT * FROM clients 
            WHERE company LIKE ? OR primary_contact LIKE ?
            ORDER BY company
        """
        rows = self.db.fetch_all(query, (search_term, search_term))

        return [dict(row) for row in rows]

    def get_count(self, only_active=True):
        """Количество задач"""
        if only_active:
            res = self.db.fetch_one("SELECT COUNT(*) as c FROM tasks WHERE completed = 0")
        else:
            res = self.db.fetch_one("SELECT COUNT(*) as c FROM tasks")
        return res['c']

    def update_task(self, task_id, title, description, status, priority, due_date, client_id=None):
        """Полностью исправленный метод обновления с учетом клиента"""
        query = """
            UPDATE tasks 
            SET title = ?, 
                description = ?, 
                completed = ?, 
                priority = ?, 
                due_date = ?, 
                client_id = ?
            WHERE id = ?
        """
        # Превращаем статус во флаг 0 или 1 для базы данных
        is_done = 1 if status else 0

        # ВАЖНО: порядок аргументов в кортеже должен строго совпадать с порядком ? в query
        self.db.execute(query, (
            title,
            description,
            is_done,
            priority,
            due_date,
            client_id,
            task_id
        ))

    def get_by_id(self, task_id):
        """Получить одну задачу по её ID для смены статуса"""
        query = """
            SELECT t.*, c.company as client_name 
            FROM tasks t 
            LEFT JOIN clients c ON t.client_id = c.id 
            WHERE t.id = ?
        """
        data = self.db.fetch_one(query, (task_id,))
        return Task.from_dict(data)

    def update_task_status(self, task_id, status):
        """Метод для мгновенного переключения галочки"""
        query = "UPDATE tasks SET completed = ? WHERE id = ?"
        return self.db.execute(query, (1 if status else 0, task_id))

    def get_active_tasks(self):
        """Получить активные (не выполненные) задачи"""
        from datetime import date
        tasks = self.get_all()
        return [task for task in tasks if not task.completed]

    def get_completed_tasks(self):
        """Получить выполненные задачи"""
        tasks = self.get_all()
        return [task for task in tasks if task.completed]

    def get_overdue_tasks(self):
        """Получить просроченные задачи"""
        from datetime import date
        tasks = self.get_all()
        today = date.today()
        return [task for task in tasks
                if task.due_date and task.due_date < today and not task.completed]