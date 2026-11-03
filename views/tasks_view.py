# -*- coding: utf-8 -*-
"""
Представление раздела "Задачи" на базе TableViewTemplate
"""
import tkinter as tk
from tkinter import ttk, messagebox
from views.table_view_template import TableViewTemplate
from utils.helpers import show_message
from utils.constants import Colors, TableView, TaskPriorities, get_priority_icon, Sizes
from datetime import date, datetime
from models.task import Task
from views.calendar_view import CalendarDialog

from views.widgets.searchable_combobox import SearchableCombobox
from utils.date_utils import format_ddmmyyyy, parse_ddmmyyyy
from views.tasks.forms import TaskFormDialog, build_task_form, collect_task_form_data


class TasksView(TableViewTemplate):
    """Раздел задач с поиском, сортировкой и пагинацией"""

    TITLE = "Задачи"
    ADD_BUTTON_TEXT = "+ Добавить задачу"
    SEARCH_FIELDS_TEXT = "коммент., опис., клиенту"
    COLUMNS = ("ID", "Статус", "Комментарий", "Клиент", "Приоритет", "Срок", "Действие")
    COLUMN_WIDTHS = {
        "ID": 60,
        "Статус": 115,
        "Комментарий": 220,
        "Клиент": 150,
        "Приоритет": 100,
        "Срок": 100,
        "Действие": 120
    }
    STRETCH_COLUMNS = ["Комментарий", "Клиент"]
    ID_COLUMN = "ID"
    SORT_OPTIONS = [
        ("due_date", "По сроку (ближайшие)"),
        ("due_date:DESC", "По сроку (дальние)"),
        ("title", "По комментарию (А-Я)"),
        ("title:DESC", "По комментарию (Я-А)"),
        ("priority", "По приоритету (высокий→низкий)"),
        ("priority:DESC", "По приоритету (низкий→высокий)"),
        ("created_at:DESC", "По дате создания (новые)"),
        ("created_at", "По дате создания (старые)")
    ]
    PAGE_SIZE = 50

    def __init__(self, parent_frame, tasks_mgr, clients_mgr):
        super().__init__(parent_frame, tasks_mgr)
        self.tasks_mgr = tasks_mgr
        self.clients_mgr = clients_mgr
        self.open_client_callback = None
        self._row_borders = []
        self._border_redraw_pending = False
        self._border_redraw_job = None
        self._action_buttons = {}
        self._action_redraw_job = None

    def _on_tree_enter(self, event):
        pass

    def _on_tree_leave(self, event):
        pass

    def _on_tree_motion(self, event):
        pass

    def _create_table(self):
        """Создаёт Treeview таблицу с дополнительной обработкой клика на статус"""
        if self._action_redraw_job is not None:
            try:
                self.parent_frame.after_cancel(self._action_redraw_job)
            except tk.TclError:
                pass
        self._action_redraw_job = None
        for button in self._action_buttons.values():
            try:
                button.destroy()
            except tk.TclError:
                pass
        self._action_buttons.clear()
        if self._border_redraw_job is not None:
            try:
                self.parent_frame.after_cancel(self._border_redraw_job)
            except tk.TclError:
                pass
        self._border_redraw_job = None
        self._border_redraw_pending = False
        self._row_borders = []
        super()._create_table()
        self.tree.tag_configure(
            "task_completed",
            background=Colors.TASK_COMPLETED_BG,
            foreground=Colors.TASK_TEXT
        )
        self.tree.tag_configure(
            "task_overdue",
            background=Colors.TASK_OVERDUE_BG,
            foreground=Colors.TASK_TEXT
        )
        self.tree.tag_configure(
            "task_current",
            background=Colors.TASK_CURRENT_BG,
            foreground=Colors.TASK_TEXT
        )
        self.tree.configure(yscrollcommand=self._on_vertical_scroll)
        self.tree.bind("<Configure>", self._schedule_row_borders, add="+")
        self.tree.bind("<MouseWheel>", self._schedule_row_borders, add="+")
        self.tree.bind("<Configure>", self._schedule_action_buttons, add="+")
        self.tree.bind("<MouseWheel>", self._schedule_action_buttons, add="+")
        self.tree.bind('<Button-1>', self._on_single_click)

    def _refresh_data(self):
        super()._refresh_data()
        if self.tree is not None:
            self._schedule_row_borders()
            self._schedule_action_buttons()

    def _on_vertical_scroll(self, first, last):
        self.scrollbar.set(first, last)
        self._schedule_row_borders()
        self._schedule_action_buttons()

    def _schedule_action_buttons(self, event=None):
        if self.tree is None or self._action_redraw_job is not None:
            return
        self._action_redraw_job = self.tree.after_idle(self._draw_action_buttons)

    def _draw_action_buttons(self):
        self._action_redraw_job = None
        for item_id in self.tree.get_children(""):
            bounds = self.tree.bbox(item_id, "Действие")
            if not bounds:
                button = self._action_buttons.get(item_id)
                if button:
                    button.place_forget()
                continue

            values = self.tree.item(item_id, "values")
            task_id = values[0]
            completed = values[6] == "Выполнено"
            button = self._action_buttons.get(item_id)
            if button is None:
                button = tk.Button(
                    self.tree,
                    relief="flat",
                    font=("Arial", 9, "bold"),
                    padx=5,
                    pady=1
                )
                self._action_buttons[item_id] = button

            button.configure(
                text="Выполнено" if completed else "✓ Выполнить",
                state="disabled" if completed else "normal",
                bg=Colors.TASK_COMPLETED_BG if completed else Colors.PRIMARY,
                fg=Colors.TEXT if completed else Colors.WHITE,
                activebackground=Colors.PRIMARY_HOVER,
                activeforeground=Colors.WHITE,
                cursor="" if completed else "hand2",
                command=lambda current_id=task_id: self._complete_task(current_id)
            )
            x, y, width, height = bounds
            button.place(x=x + 3, y=y + 2, width=max(width - 6, 1), height=max(height - 4, 1))

        for item_id, button in tuple(self._action_buttons.items()):
            if item_id not in self.tree.get_children(""):
                button.destroy()
                del self._action_buttons[item_id]

    def _schedule_row_borders(self, event=None):
        if self.tree is None or self._border_redraw_pending:
            return
        self._border_redraw_pending = True
        self._border_redraw_job = self.tree.after_idle(self._draw_row_borders)

    def _draw_row_borders(self):
        self._border_redraw_job = None
        self._border_redraw_pending = False
        visible_rows = []
        for item_id in self.tree.get_children(""):
            bounds = self.tree.bbox(item_id)
            if bounds:
                visible_rows.append(bounds[1] + bounds[3] - 1)

        while len(self._row_borders) < len(visible_rows):
            border = tk.Frame(
                self.tree,
                bg=Colors.TASK_ROW_BORDER,
                height=1,
                bd=0,
                highlightthickness=0
            )
            border.bind("<Button-1>", self._forward_border_click)
            self._row_borders.append(border)

        for index, border in enumerate(self._row_borders):
            if index >= len(visible_rows):
                border.place_forget()
                continue
            y = visible_rows[index]
            border.place(x=0, y=y, width=self.tree.winfo_width(), height=1)

    def _forward_border_click(self, event):
        self._forward_tree_event(event, "<Button-1>")
        return "break"

    def _forward_tree_event(self, event, sequence):
        self.tree.event_generate(
            sequence,
            x=event.x_root - self.tree.winfo_rootx(),
            y=event.y_root - self.tree.winfo_rooty(),
            state=event.state
        )

    def _get_row_tags(self, item, idx):
        """Возвращает единый тег подсветки всей строки по текущему статусу."""
        if item.completed:
            return ("task_completed",)

        due_date = item.due_date
        if isinstance(due_date, datetime):
            due_date = due_date.date()
        if isinstance(due_date, date) and due_date < date.today():
            return ("task_overdue",)

        return ("task_current",)

    def _create_ui(self):
        """Создаёт интерфейс раздела с фильтром статуса и финансов."""
        super()._create_ui()

        if getattr(self, "search_entry", None) is not None:
            self.search_entry.configure(width=18)
        if getattr(self, "sort_combo", None) is not None:
            self.sort_combo.configure(width=10)
        if getattr(self, "sort_label", None) is not None:
            self.sort_label.configure(text="Сорт.:")
        if getattr(self, "search_hint_label", None) is not None:
            self.search_hint_label.pack_forget()

        search_container = self.search_container
        tk.Label(
            search_container,
            text="Статус:",
            font=TableView.LABEL_FONT,
            bg=TableView.TOP_PANEL_BG,
            fg=TableView.LABEL_FG
        ).pack(side=tk.LEFT, padx=(15, 5))

        self.status_filter_var = tk.StringVar(value="Активные")
        status_combo = ttk.Combobox(
            search_container,
            textvariable=self.status_filter_var,
            values=["Все", "Активные", "Выполненные"],
            state="readonly",
            width=10,
            font=TableView.LABEL_FONT
        )
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_data())

        self.show_financial_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.top_panel,
            text="Финансовые",
            variable=self.show_financial_var,
            command=self._refresh_data,
            bg=TableView.TOP_PANEL_BG,
            fg=TableView.LABEL_FG,
            activebackground=TableView.TOP_PANEL_BG,
            activeforeground=TableView.LABEL_FG,
            selectcolor=TableView.TABLE_BG,
            font=TableView.LABEL_FONT
        ).pack(side=tk.LEFT, padx=(8, 0), pady=6)

    def _on_single_click(self, event):
        """Обрабатывает одинарный клик по таблице"""
        # Определяем колонку и строку
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        if not item or not column:
            return
            
        if column == "#4" and self.open_client_callback is not None:
            values = self.tree.item(item, "values")
            try:
                task = self.tasks_mgr.get_by_id(int(values[0]))
                client_id = getattr(task, "client_id", None) if task else None
                if client_id is not None:
                    self.open_client_callback(client_id)
                else:
                    messagebox.showwarning(
                        "Клиент",
                        "У этой задачи не указан клиент.",
                        parent=self.parent_frame.winfo_toplevel()
                    )
            except (ValueError, IndexError, TypeError) as error:
                messagebox.showerror(
                    "Ошибка",
                    f"Не удалось определить клиента задачи:\n{error}",
                    parent=self.parent_frame.winfo_toplevel()
                )
            except Exception as error:
                messagebox.showerror(
                    "Ошибка",
                    f"Не удалось открыть карточку клиента:\n{error}",
                    parent=self.parent_frame.winfo_toplevel()
                )
            return "break"

        # Кнопка действия находится в последней колонке.
        if column == "#7":
            # Получаем ID задачи из первой колонки
            values = self.tree.item(item, 'values')
            if not values:
                return
                
            try:
                task_id = int(values[0])
                task = self.tasks_mgr.get_by_id(task_id)
                if task and not task.completed:
                    self.tasks_mgr.update_task_status(task_id, True)
                    self._refresh_data()
                    self._refresh_related_client_task_tables()
            except (ValueError, IndexError):
                pass
            except Exception as error:
                messagebox.showerror(
                    "Ошибка",
                    f"Не удалось изменить статус задачи:\n{error}",
                    parent=self.parent_frame
                )

    def _toggle_task_status(self, task_id):
        """Переключает статус задачи (выполнена/не выполнена)"""
        try:
            task = self.tasks_mgr.get_by_id(task_id)
            if not task:
                return
                
            # Переключаем статус
            new_status = not task.completed
            self.tasks_mgr.update_task_status(task_id, new_status)
            
            # Обновляем таблицу
            self._refresh_data()
            
        except Exception as e:
            print(f"Ошибка при изменении статуса задачи: {e}")

    def _complete_task(self, task_id):
        """Отмечает задачу выполненной из кнопки в её строке."""
        try:
            task = self.tasks_mgr.get_by_id(task_id)
            if task and not task.completed:
                self.tasks_mgr.update_task_status(task_id, True)
                self._refresh_data()
        except Exception as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось завершить задачу:\n{error}",
                parent=self.parent_frame
            )

    def _get_data(self, page, search, sort_by, sort_order):
        """Загрузка данных с пагинацией, поиском, фильтрацией и сортировкой"""
        try:
            # Получаем все задачи
            if search:
                tasks = self.tasks_mgr.search(search)
            else:
                tasks = self.tasks_mgr.get_all()
            
            # Применяем фильтр по статусу
            status_filter = getattr(self, 'status_filter_var', None)
            if status_filter:
                filter_value = status_filter.get()
                if filter_value == "Активные":
                    tasks = [task for task in tasks if not task.completed]
                elif filter_value == "Выполненные":
                    tasks = [task for task in tasks if task.completed]

            # Финансовые задачи скрыты, пока не включён чекбокс.
            show_financial = getattr(self, "show_financial_var", None)
            if show_financial is not None and not show_financial.get():
                tasks = [
                    task for task in tasks
                    if not getattr(task, "is_financial", False)
                ]
            
            # Применяем сортировку
            if sort_by:
                tasks = self._apply_sort(tasks, sort_by, sort_order)
            
            # Эмуляция пагинации
            total = len(tasks)
            start_idx = (page - 1) * self.PAGE_SIZE
            end_idx = start_idx + self.PAGE_SIZE
            paginated_tasks = tasks[start_idx:end_idx]
            
            return paginated_tasks, total
            
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            return [], 0

    def _apply_sort(self, tasks, sort_by, sort_order):
        """Применяет сортировку к списку задач"""
        reverse = sort_order == "DESC"
        
        if sort_by == "title":
            tasks.sort(key=lambda x: x.title.lower() if x.title else "", reverse=reverse)
        elif sort_by == "due_date":
            tasks.sort(key=lambda x: x.due_date or date.max, reverse=reverse)
        elif sort_by == "priority":
            priority_order = {"Высокий": 0, "Средний": 1, "Низкий": 2}
            tasks.sort(key=lambda x: priority_order.get(x.priority, 3), reverse=reverse)
        elif sort_by == "status":
            tasks.sort(key=lambda x: x.completed, reverse=reverse)
        elif sort_by == "created_at":
            tasks.sort(
                key=lambda task: getattr(task, "created_at", datetime.min),
                reverse=reverse
            )
            
        return tasks

    def _item_to_row_values(self, item):
        """Преобразует задачу в строку таблицы"""
        if not isinstance(item, Task):
            return ("", "", "", "", "", "", "")
        
        # Статус
        status_icon = "✓ Выполнена" if item.completed else "○ Активна"
        
        # Клиент
        client_name = getattr(item, 'client_name', None)
        if not client_name and item.client_id:
            client = self.clients_mgr.get_by_id(item.client_id)
            client_name = client.get('company', '—') if client else '—'
        elif not client_name:
            client_name = '—'
        
        # Приоритет с иконкой
        priority_icon = get_priority_icon(item.priority)
        priority_display = f"{priority_icon} {item.priority}" if item.priority else "—"
        
        # Срок
        due_date = format_ddmmyyyy(item.due_date)
        
        return (
            str(item.id),
            status_icon,
            item.title,
            client_name,
            priority_display,
            due_date,
            "Выполнено" if item.completed else ""
        )

    def _open_create_dialog(self):
        """Открывает общую форму создания задачи."""
        def save_task(data):
            from services.task_service import TaskService

            task_id = TaskService(self.tasks_mgr, self.clients_mgr).create_task(data)
            if data["completed"]:
                self.tasks_mgr.update_task_status(task_id, True)
            self._refresh_data()

        TaskFormDialog(
            self.parent_frame,
            self.clients_mgr,
            save_task,
            on_open_client=self.open_client_callback
        )

    def _legacy_open_create_dialog(self):
        """Старая форма создания задачи, оставленная для обратной совместимости."""
        dialog, content, buttons_frame = self._create_dialog(
            "➕ Новая задача",
            "600x550"
        )

        # Используем build_task_form для создания виджетов
        widgets = build_task_form(content, self.clients_mgr, defaults=None)

        # Упакуем виджеты в удобный вид
        tk.Label(content, text="📋 Основная информация", font=("Arial", 12, "bold"), bg='white').pack(anchor='w', padx=20, pady=(10, 5))
        tk.Label(content, text="Название задачи", bg='white').pack(anchor='w', padx=20)
        widgets['title'].pack(fill=tk.X, padx=20, pady=(2, 8))
        tk.Label(content, text="Описание", bg='white').pack(anchor='w', padx=20)
        widgets['description'].pack(fill=tk.X, padx=20, pady=(2, 8))

        tk.Label(content, text="⚙ Дополнительные параметры", font=("Arial", 12, "bold"), bg='white').pack(anchor='w', padx=20, pady=(10, 5))
        tk.Label(content, text="Приоритет", bg='white').pack(anchor='w', padx=20)
        widgets['priority'].pack(fill=tk.X, padx=20, pady=(2, 8))

        tk.Label(content, text="Клиент", bg='white').pack(anchor='w', padx=20)
        widgets['client_combo'].pack_side(side=tk.LEFT, fill=tk.X, expand=True, padx=20, pady=(2, 8))

        # Дата с календарём
        tk.Label(content, text="Срок выполнения", bg='white').pack(anchor='w', padx=20)
        date_frame = tk.Frame(content, bg='white')
        date_frame.pack(fill=tk.X, padx=20, pady=(2, 8))
        due_entry = tk.Entry(date_frame, textvariable=widgets['due_date_var'], font=("Arial", 11), relief="solid", borderwidth=1)
        due_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def show_calendar():
            cal_dialog = CalendarDialog(dialog, "Выберите срок выполнения")
            selected_date = cal_dialog.show()
            if selected_date:
                widgets['due_date_var'].set(selected_date.strftime("%d.%m.%Y"))

        tk.Button(date_frame, text="📅", command=show_calendar, bg="#41a5be", fg="white", font=("Arial", 10), width=3).pack(side=tk.RIGHT, padx=(5, 0))

        def save_task():
            try:
                data = collect_task_form_data(widgets, self.clients_mgr)
                # Создаём задачу через менеджер
                self.tasks_mgr.add(
                    title=data['title'],
                    description=data['description'],
                    due_date=data['due_date'],
                    client_id=data['client_id'],
                    priority=data['priority']
                )
                show_message(dialog, "Успех", "Задача успешно создана!", "success")
                dialog.destroy()
                self._refresh_data()
            except ValueError as ve:
                show_message(dialog, "Ошибка", str(ve), "error")
            except Exception as e:
                show_message(dialog, "Ошибка", f"Произошла ошибка: {str(e)}", "error")

        self._create_dialog_buttons(buttons_frame, save_task)
     
    def _on_row_double_click(self, task_id):
        """Открыть диалог редактирования задачи"""
        self._edit_task(task_id)

    def _get_client_options(self):
        """Получить список клиентов для ComboBox"""
        try:
            all_clients = self.clients_mgr.get_all()
            client_names = ["Без клиента"] + [client.get('company', '—') for client in all_clients]
            return [name for name in client_names if name and name.strip()]
        except:
            return ["Без клиента"]

    def _edit_task(self, task_id):
        """Открывает общую форму редактирования задачи."""
        task = self.tasks_mgr.get_by_id(task_id)
        if not task:
            messagebox.showerror(
                "Ошибка",
                f"Задача с ID {task_id} не найдена.",
                parent=self.parent_frame
            )
            return

        def save_task(data):
            from services.task_service import TaskService

            data["status"] = data.pop("completed")
            TaskService(self.tasks_mgr, self.clients_mgr).update_task(task_id, data)
            self._refresh_data()
            self._refresh_related_client_task_tables()

        def delete_task():
            if not messagebox.askyesno(
                "Подтверждение",
                "Удалить задачу?",
                parent=dialog.dialog
            ):
                return
            self.tasks_mgr.delete(task_id)
            dialog.dialog.destroy()
            self._refresh_data()
            self._refresh_related_client_task_tables()

        dialog = TaskFormDialog(
            self.parent_frame,
            self.clients_mgr,
            save_task,
            task=task,
            on_delete=delete_task,
            on_open_client=self.open_client_callback
        )

    def _refresh_related_client_task_tables(self):
        """Обновляет таблицы задач клиентов, если они открыты."""
        def refresh_tables(widget):
            task_table = getattr(widget, "_tasks_table", None)
            if task_table is not None and hasattr(task_table, "refresh"):
                task_table.refresh()
            for child in widget.winfo_children():
                refresh_tables(child)

        refresh_tables(self.parent_frame.winfo_toplevel())

    def _legacy_edit_task(self, task_id):
        """Старая форма редактирования задачи, оставленная для совместимости."""
        try:
            task = self.tasks_mgr.get_by_id(task_id)
            if not task:
                show_message(self.parent_frame, "Ошибка", f"Задача с ID {task_id} не найдена", "error")
                return

            dialog, content, buttons_frame = self._create_dialog(
                f"✏️ Редактирование: {task.title}",
                "600x600"
            )

            defaults = {
                'title': task.title,
                'description': task.description or '',
                'priority': task.priority or TaskPriorities.MEDIUM,
                'client_name': self._get_current_client_name(task),
                'due_date': task.due_date,
                'completed': task.completed
            }

            widgets = build_task_form(content, self.clients_mgr, defaults=defaults)

            # Упаковка виджетов
            tk.Label(content, text="📋 Основная информация", font=("Arial", 12, "bold"), bg='white').pack(anchor='w', padx=20, pady=(10, 5))
            tk.Label(content, text="Название задачи", bg='white').pack(anchor='w', padx=20)
            widgets['title'].pack(fill=tk.X, padx=20, pady=(2, 8))
            tk.Label(content, text="Описание", bg='white').pack(anchor='w', padx=20)
            widgets['description'].pack(fill=tk.X, padx=20, pady=(2, 8))

            tk.Label(content, text="⚙ Дополнительные параметры", font=("Arial", 12, "bold"), bg='white').pack(anchor='w', padx=20, pady=(10, 5))
            tk.Label(content, text="Приоритет", bg='white').pack(anchor='w', padx=20)
            widgets['priority'].pack(fill=tk.X, padx=20, pady=(2, 8))

            tk.Label(content, text="Клиент", bg='white').pack(anchor='w', padx=20)
            widgets['client_combo'].pack_side(side=tk.LEFT, fill=tk.X, expand=True, padx=20, pady=(2, 8))

            tk.Label(content, text="Срок выполнения", bg='white').pack(anchor='w', padx=20)
            date_frame = tk.Frame(content, bg='white')
            date_frame.pack(fill=tk.X, padx=20, pady=(2, 8))
            due_entry = tk.Entry(date_frame, textvariable=widgets['due_date_var'], font=("Arial", 11), relief="solid", borderwidth=1)
            due_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            def show_edit_calendar():
                cal_dialog = CalendarDialog(dialog, "Выберите срок выполнения")
                selected_date = cal_dialog.show()
                if selected_date:
                    widgets['due_date_var'].set(selected_date.strftime("%d.%m.%Y"))

            tk.Button(date_frame, text="📅", command=show_edit_calendar, bg="#41a5be", fg="white", font=("Arial", 10), width=3).pack(side=tk.RIGHT, padx=(5, 0))

            # Статус
            status_frame = tk.Frame(content, bg='white')
            status_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
            tk.Checkbutton(status_frame, text="✓ Задача выполнена", variable=widgets['completed_var'], bg='white', font=("Arial", 11, "bold")).pack(anchor='w')

            def save_task():
                try:
                    data = collect_task_form_data(widgets, self.clients_mgr)
                    # Обновляем через менеджер
                    self.tasks_mgr.update_task(
                        task_id,
                        data['title'],
                        data['description'],
                        data['completed'],
                        data['priority'],
                        data['due_date'],
                        data['client_id']
                    )
                    show_message(dialog, "Успех", "Изменения сохранены!", "success")
                    dialog.destroy()
                    self._refresh_data()
                except ValueError as ve:
                    show_message(dialog, "Ошибка", str(ve), "error")
                except Exception as e:
                    show_message(dialog, "Ошибка", f"Произошла ошибка: {str(e)}", "error")

            def delete_task():
                if messagebox.askyesno("Подтверждение", "Удалить задачу?", parent=dialog):
                    self.tasks_mgr.delete(task_id)
                    show_message(dialog, "Успех", "Задача удалена!", "success")
                    dialog.destroy()
                    self._refresh_data()

            # Кнопки
            tk.Button(buttons_frame, text="💾 Сохранить", command=save_task, bg="#28a745", fg="white", font=("Arial", 12, "bold"), cursor="hand2", padx=20, pady=10).pack(side=tk.LEFT, padx=5)
            tk.Button(buttons_frame, text="🗑️ Удалить", command=delete_task, bg="#dc3545", fg="white", font=("Arial", 12, "bold"), cursor="hand2", padx=20, pady=10).pack(side=tk.LEFT, padx=5)
            tk.Button(buttons_frame, text="✖ Отмена", command=dialog.destroy, bg="#6c757d", fg="white", font=("Arial", 12, "bold"), cursor="hand2", padx=20, pady=10).pack(side=tk.LEFT, padx=5)

        except Exception as e:
             show_message(self.parent_frame, "Ошибка", f"Произошла ошибка: {str(e)}", "error")

    def _get_current_client_name(self, task):
        """Получить имя текущего клиента задачи"""
        if hasattr(task, 'client_name') and task.client_name:
            return task.client_name
        
        if task.client_id:
            client = self.clients_mgr.get_by_id(task.client_id)
            if client:
                return client.get('company', 'Без клиента')
        
        return "Без клиента"
