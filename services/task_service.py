# -*- coding: utf-8 -*-
"""
Бизнес-сервис для операций с задачами
"""
from datetime import date, datetime
from typing import Dict, Any, List


class TaskService:
    """
    Сервис для операций с задачами
    Инкапсулирует бизнес-логику, независимую от UI
    """

    def __init__(self, tasks_mgr, clients_mgr=None):
        self.tasks_mgr = tasks_mgr
        self.clients_mgr = clients_mgr

    @staticmethod
    def _normalize_due_date(value):
        """Normalize supported UI date formats to SQLite's ISO date format."""
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if not isinstance(value, str):
            raise ValueError("Некорректный формат срока задачи")

        value = value.strip()
        if not value:
            return None

        for date_format in ("%Y-%m-%d", "%d.%m.%Y"):
            try:
                return datetime.strptime(value, date_format).date().isoformat()
            except ValueError:
                continue
        raise ValueError("Укажите срок в формате ДД.ММ.ГГГГ")

    def create_task(self, task_data: Dict[str, Any]) -> int:
        """
        Создать новую задачу

        Args:
            task_data: {
                'title': str (обязательно),
                'description': str,
                'due_date': str или date,
                'priority': str ('Низкий', 'Средний', 'Высокий'),
                'client_id': int (опционально)
            }

        Returns:
            task_id: int

        Raises:
            ValueError: если валидация не пройдена
        """
        # 1. Валидация
        title = task_data.get('title', '').strip()
        if not title:
            raise ValueError("Комментарий задачи обязателен")
        description = (task_data.get('description') or '').strip()
        client_id = task_data.get('client_id')
        if len(title) < 3:
            raise ValueError("Комментарий должен содержать минимум 3 символа")
        if len(title) > 255:
            raise ValueError("Комментарий слишком длинный (макс 255 символов)")

        # 2. Валидация приоритета
        priority = task_data.get('priority', 'Средний')
        valid_priorities = ['Низкий', 'Средний', 'Высокий']
        if priority not in valid_priorities:
            priority = 'Средний'

        # 3. Форматирование даты
        due_date = self._normalize_due_date(task_data.get('due_date'))

        # 4. Создаём задачу
        task_id = self.tasks_mgr.add(
            title=title,
            description=description,
            due_date=due_date,
            client_id=client_id,
            priority=priority
        )

        if not task_id:
            raise RuntimeError("Не удалось создать задачу в БД")

        return task_id

    def update_task(self, task_id: int, task_data: Dict[str, Any]) -> bool:
        """
        Обновить задачу

        Args:
            task_id: ID задачи
            task_data: данные задачи (аналогично create_task)

        Returns:
            True если успешно

        Raises:
            ValueError: если валидация не пройдена
        """
        # Валидация
        title = task_data.get('title', '').strip()
        if not title:
            raise ValueError("Комментарий задачи обязателен")
        description = (task_data.get('description') or '').strip()
        priority = task_data.get('priority') or 'Средний'
        client_id = task_data.get('client_id')

        # Преобразуем статус в булево значение
        status = task_data.get('status', False)
        if isinstance(status, str):
            is_completed = status == 'Выполнена'
        else:
            is_completed = bool(status)

        # Форматирование даты
        due_date = self._normalize_due_date(task_data.get('due_date'))

        # Обновляем задачу
        self.tasks_mgr.update_task(
            task_id=task_id,
            title=title,
            description=description,
            status=is_completed,
            priority=priority,
            due_date=due_date,
            client_id=client_id
        )

        saved_task = self.tasks_mgr.get_by_id(task_id)
        expected_status = (
            status == "Выполнена"
            if isinstance(status, str)
            else bool(status)
        )
        if (
            not saved_task
            or saved_task.title != title
            or saved_task.description != description
            or bool(saved_task.completed) != expected_status
            or saved_task.priority != priority
            or self._normalize_due_date(saved_task.due_date) != due_date
            or saved_task.client_id != client_id
        ):
            raise RuntimeError("Изменения задачи не были сохранены в базе данных")

        return True

    def delete_task(self, task_id: int) -> bool:
        """Удалить задачу"""
        try:
            self.tasks_mgr.delete(task_id)
            return True
        except Exception as e:
            raise RuntimeError(f"Не удалось удалить задачу: {e}")

    def toggle_task_status(self, task_id: int) -> str:
        """
        Переключить статус задачи

        Args:
            task_id: ID задачи

        Returns:
            Новый статус ('Активная' или 'Выполнена')
        """
        task = self.tasks_mgr.get_by_id(task_id)
        if not task:
            raise ValueError("Задача не найдена")

        # Определяем текущий статус
        current_status = getattr(task, 'completed', False)
        if isinstance(current_status, str):
            current_status = current_status == 'Выполнена'

        # Переключаем
        new_completed = not current_status
        new_status = 'Выполнена' if new_completed else 'Активная'

        # Обновляем в БД
        self.tasks_mgr.update_task_status(task_id, new_completed)

        return new_status

    def get_tasks_for_client(self, client_id: int, status_filter: str = None) -> List[Any]:
        """
        Получить задачи клиента с опциональной фильтрацией по статусу

        Args:
            client_id: ID клиента
            status_filter: 'Активная', 'Выполнена' или None (все)

        Returns:
            Список задач
        """
        return self.tasks_mgr.get_filtered_by_client(client_id, status_filter)

    def get_sorted_tasks(self, sort_by: str = 'due_date', reverse: bool = False) -> List[Any]:
        """
        Получить отсортированные задачи

        Args:
            sort_by: 'due_date', 'priority'
            reverse: обратный порядок

        Returns:
            Список задач
        """
        if sort_by == 'priority':
            return self.tasks_mgr.get_sorted_by_priority(reverse)
        elif sort_by == 'due_date':
            return self.tasks_mgr.get_sorted_by_due_date(reverse)
        else:
            return self.tasks_mgr.get_all()

    def get_task_statistics(self) -> Dict[str, int]:
        """
        Получить статистику по задачам

        Returns:
            Словарь со статистикой
        """
        all_tasks = self.tasks_mgr.get_all()

        total = len(all_tasks)
        active = sum(1 for t in all_tasks if not getattr(t, 'completed', False))
        completed = total - active

        # Просроченные задачи
        today = date.today()
        overdue = sum(
            1 for t in all_tasks
            if not getattr(t, 'completed', False)
            and getattr(t, 'due_date', None)
            and getattr(t, 'due_date') < today
        )

        return {
            'total': total,
            'active': active,
            'completed': completed,
            'overdue': overdue
        }
