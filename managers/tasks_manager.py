"""
Менеджер для работы с задачами в БД
"""
from managers.database import Database
from datetime import date
from models.task import Task
from utils.formatters import StatusFormatter

class TasksManager:
    """Класс для управления задачами"""

    def __init__(self):
        self.db = Database()

    def add(self, title, description="", due_date=None, client_id=None,
            priority="Средний", is_financial=0, work_id=None):
        query = """
            INSERT INTO tasks
                (title, description, due_date, client_id, priority,
                 is_financial, work_id, completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """
        return self.db.execute(
            query,
            (title, description, due_date, client_id, priority,
             int(bool(is_financial)), work_id)
        )

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

    def get_by_client(self, client_id):
        """Получить все задачи клиента"""
        try:
            # ИСПРАВЛЕНО: используем self.db вместо self.cursor
            query = """
                SELECT t.*, c.company as client_name 
                FROM tasks t
                LEFT JOIN clients c ON t.client_id = c.id
                WHERE t.client_id = ? 
                ORDER BY t.created_at DESC
            """
            rows = self.db.fetch_all(query, (client_id,))

            tasks = []
            for row in rows:
                # Преобразуем sqlite3.Row в словарь
                if hasattr(row, 'keys'):
                    row_dict = {}
                    for key in row.keys():
                        row_dict[key] = row[key]
                    task = Task.from_dict(row_dict)
                    task.client_name = row_dict.get('client_name', '—')
                else:
                    task = Task.from_dict(dict(row))
                    task.client_name = dict(row).get('client_name', '—')

                tasks.append(task)

            return tasks
        except Exception as e:
            print(f"Ошибка при получении задач клиента: {e}")
            return []

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
        """Ищет задачи по комментарию, описанию и названию клиента."""
        tokens = [tok.strip() for tok in str(query_text).split() if tok.strip()]
        if not tokens:
            return []

        where_clauses = []
        params = []
        for tok in tokens:
            where_clauses.append(
                "("
                "FUZZY_CONTAINS(t.title, ?) = 1 OR "
                "FUZZY_CONTAINS(t.description, ?) = 1 OR "
                "FUZZY_CONTAINS(c.company, ?) = 1"
                ")"
            )
            params.extend((tok, tok, tok))

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT
                t.*,
                c.company as client_name
            FROM tasks t
            LEFT JOIN clients c ON t.client_id = c.id
            WHERE {where_sql}
            ORDER BY t.completed ASC, t.due_date ASC
        """
        rows = self.db.fetch_all(query, params)

        from models.task import Task
        tasks = []
        for row in rows:
            row_dict = dict(row)
            task = Task.from_dict(row_dict)
            task.client_name = row_dict.get('client_name', '—')
            tasks.append(task)

        return tasks

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
        """Получить задачу по ID"""
        try:
            # ИСПРАВЛЕНО: используем self.db вместо self.cursor
            query = """
                   SELECT t.*, c.company as client_name 
                   FROM tasks t
                   LEFT JOIN clients c ON t.client_id = c.id
                   WHERE t.id = ?
               """
            data = self.db.fetch_one(query, (task_id,))

            if not data:
                return None

            # Преобразуем sqlite3.Row в словарь если нужно
            if hasattr(data, 'keys'):
                # Это sqlite3.Row
                data_dict = {}
                for key in data.keys():
                    data_dict[key] = data[key]
                data = data_dict

            task = Task.from_dict(data)
            task.client_name = data.get('client_name', '—')
            return task

        except Exception as e:
            print(f"Ошибка при получении задачи: {e}")
            return None

    def update_task_status(self, task_id, status):
        """Метод для мгновенного переключения галочки"""
        query = "UPDATE tasks SET completed = ? WHERE id = ?"
        return self.db.execute(query, (1 if status else 0, task_id))

    def update_status(self, task_id, status_str):
        """Обновить статус задачи строковым значением"""
        # Преобразуем строковый статус в булево значение для БД
        status_map = {
            'Выполнена': True,
            'Новая': False,
            'В работе': False,
            'Отложена': False,
            'Отменена': False
        }
        is_completed = status_map.get(status_str, False)

        query = "UPDATE tasks SET completed = ?, status = ? WHERE id = ?"
        return self.db.execute(query, (1 if is_completed else 0, status_str, task_id))

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

    def get_sorted_by_priority(self, reverse: bool = False):
        """Получить задачи отсортированные по приоритету"""
        tasks = self.get_all()
        priority_order = {'Высокий': 0, 'Средний': 1, 'Низкий': 2}
        tasks.sort(key=lambda t: priority_order.get(t.priority, 3), reverse=reverse)
        return tasks

    def get_sorted_by_due_date(self, reverse: bool = False):
        """Получить задачи отсортированные по сроку выполнения"""
        tasks = self.get_all()
        tasks.sort(key=lambda t: (t.due_date is None, t.due_date), reverse=reverse)
        return tasks

    def get_filtered_by_status(self, status: str):
        """Получить задачи по статусу ('Активная', 'Выполнена')"""
        normalized_status = StatusFormatter.normalize(status)
        tasks = self.get_all()
        if normalized_status == 'Активная':
            return [task for task in tasks if not task.completed]
        elif normalized_status == 'Выполнена':
            return [task for task in tasks if task.completed]
        return tasks

    def get_filtered_by_client(self, client_id: int, status: str = None):
        """Получить задачи клиента, опционально по статусу"""
        tasks = self.get_by_client(client_id)
        if status:
            normalized_status = StatusFormatter.normalize(status)
            if normalized_status == 'Активная':
                return [task for task in tasks if not task.completed]
            elif normalized_status == 'Выполнена':
                return [task for task in tasks if task.completed]
        return tasks