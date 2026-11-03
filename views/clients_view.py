# -*- coding: utf-8 -*-
"""
Представление раздела "Клиенты" на базе TableViewTemplate
Рефакторинг: разделено на 3 класса (SRP)
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from views.table_view_template import TableViewTemplate
from views.calendar_view import CalendarDialog
from views.client_card_view import ClientCardView

from utils.client_card_reader import read_client_card
from utils.constants import Colors, TableView
from utils.formatters import DateFormatter, PriorityFormatter, StatusFormatter
from utils.parsers import safe_get
from datetime import date, datetime, timedelta
from services.client_service import ClientService
from services.task_service import TaskService
from utils.ui_helpers import center_toplevel


def _copy_selected_tree_row(event):
    """Копирует выбранную строку Treeview в буфер обмена."""
    return _copy_tree_selection(event.widget)


def _copy_tree_selection(tree):
    """Копирует значения выбранной строки в буфер обмена."""
    selection = tree.selection()
    if not selection:
        return "break"

    values = tree.item(selection[0], "values")
    if "Действие" in tree["columns"]:
        values = values[:-1]
    if values:
        tree.clipboard_clear()
        tree.clipboard_append("\t".join(str(value) for value in values))
    return "break"


def _show_tree_copy_menu(event):
    """Выбирает строку под курсором и показывает копирование."""
    tree = event.widget
    item = tree.identify_row(event.y)
    if not item:
        return
    tree.selection_set(item)
    tree.focus(item)
    menu = tk.Menu(tree, tearoff=False)
    menu.add_command(
        label="Копировать строку",
        command=lambda: _copy_tree_selection(tree)
    )
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


class ClientTasksTable:
    """Таблица задач для конкретного клиента"""

    def __init__(
        self,
        parent,
        client_id,
        tasks_mgr,
        clients_mgr,
        interactions_mgr=None,
        on_open_client=None
    ):
        self.parent = parent
        self.client_id = client_id
        self.tasks_mgr = tasks_mgr
        self.clients_mgr = clients_mgr
        self.interactions_mgr = interactions_mgr
        self.on_open_client = on_open_client
        self.task_service = TaskService(tasks_mgr, clients_mgr)
        self.tree = None
        self.scrollbar = None
        self._action_buttons = {}
        self._action_redraw_job = None
        self._activity_items = {}

        self._create_ui()
    
    def _create_ui(self):
        """Создает интерфейс таблицы"""
        # Заголовок
        header_frame = tk.Frame(self.parent, bg='#f8f9fa')
        header_frame.pack(fill=tk.X, padx=15, pady=(20, 10))
        
        tk.Label(
            header_frame,
            text="Активность клиента",
            font=("Arial", 16, "bold"),
            bg='#f8f9fa',
            fg='#333'
        ).pack(side=tk.LEFT)
        
        # Контейнер для элементов справа
        right_container = tk.Frame(header_frame, bg='#f8f9fa')
        right_container.pack(side=tk.RIGHT)
        
        # Сортировка
        tk.Label(
            right_container,
            text="Сортировка:",
            font=("Arial", 10),
            bg='#f8f9fa',
            fg='#666'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.sort_var = tk.StringVar(value="Все")
        sort_options = [
            "Все",
            "Активные", 
            "Выполненные",
           ]
        
        sort_combo = ttk.Combobox(
            right_container,
            textvariable=self.sort_var,
            values=sort_options,
            state="readonly",
            width=20,
            font=("Arial", 9)
        )
        sort_combo.pack(side=tk.LEFT, padx=(0, 10))
        sort_combo.bind("<<ComboboxSelected>>", self._on_sort_change)
        tk.Button(
            right_container,
            text="+ Добавить задачу",
            command=self._add_task,
            bg=Colors.PRIMARY,
            fg=Colors.WHITE,
            activebackground=Colors.PRIMARY_HOVER,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6
        ).pack(side=tk.LEFT, padx=(10, 0))
        tk.Button(
            right_container,
            text="+ Добавить комментарий",
            command=self._add_activity_comment,
            bg=Colors.LIGHT,
            fg=Colors.TEXT,
            activebackground=Colors.BORDER,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6
        ).pack(side=tk.LEFT, padx=(8, 0))
        
        # Создаем таблицу
        self._create_table()
        
        # Загружаем данные
        self._load_tasks()
    
    def _create_table(self):
        """Создает Treeview таблицу"""
        # Фрейм для таблицы с прокруткой
        table_frame = tk.Frame(self.parent)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 20))
        
        # Создаем Treeview
        self.tree = ttk.Treeview(
            table_frame,
            columns=("ID", "Статус", "Комментарий", "Приоритет", "Срок", "Действие"),
            show="headings",
            selectmode="browse"
        )
        
        # Настройка колонок
        self.tree.heading("ID", text="ID")
        self.tree.heading("Статус", text="Статус")
        self.tree.heading("Комментарий", text="Комментарий")
        self.tree.heading("Приоритет", text="Приоритет")
        self.tree.heading("Срок", text="Срок")
        self.tree.heading("Действие", text="Действие")
        
        # Ширина колонок
        self.tree.column("ID", width=50, minwidth=50)
        self.tree.column("Статус", width=100, minwidth=80)
        self.tree.column("Комментарий", width=240, minwidth=150, stretch=True)
        self.tree.column("Приоритет", width=100, minwidth=80)
        self.tree.column("Срок", width=100, minwidth=80)
        self.tree.column("Действие", width=115, minwidth=105, anchor="center", stretch=False)
        
        # Прокрутка
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar = scrollbar
        self.tree.configure(yscrollcommand=self._on_vertical_scroll)
        
        # Размещение
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Обработчики
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind("<Control-c>", _copy_selected_tree_row)
        self.tree.bind("<Control-C>", _copy_selected_tree_row)
        self.tree.bind("<Button-3>", _show_tree_copy_menu)
        self.tree.bind("<Configure>", self._schedule_action_buttons, add="+")
        self.tree.bind("<MouseWheel>", self._schedule_action_buttons, add="+")
        
        # Цвета строк задач
        self._setup_tag_styles()
    
    def _setup_tag_styles(self):
        """Настраивает стили строк задач."""
        style = ttk.Style()
        
        # Исправление для tag_configure в Windows
        def fixed_map(option):
            return [elm for elm in style.map('Treeview', query_opt=option) 
                   if elm[:2] != ('!disabled', '!selected')]
        
        style.map('Treeview', foreground=fixed_map('foreground'), 
                  background=fixed_map('background'))
        
        self.tree.tag_configure("evenrow", background=TableView.ROW_EVEN, foreground=Colors.TASK_TEXT)
        self.tree.tag_configure("oddrow", background=TableView.ROW_ODD, foreground=Colors.TASK_TEXT)
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
        self.tree.tag_configure("task_current", background=Colors.TASK_CURRENT_BG, foreground=Colors.TASK_TEXT)

    @staticmethod
    def _get_task_row_tags(task, index):
        """Определяет актуальную цветовую метку задачи по её состоянию."""
        if safe_get(task, "completed", False):
            return ("task_completed",)

        due_date = safe_get(task, "due_date")
        if isinstance(due_date, datetime):
            due_date = due_date.date()
        elif isinstance(due_date, str):
            for date_format in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"):
                try:
                    due_date = datetime.strptime(due_date, date_format).date()
                    break
                except ValueError:
                    continue

        if isinstance(due_date, date) and due_date < date.today():
            return ("task_overdue",)
        return ("task_current",)
    
    def _apply_sorting(self, tasks, sort_option):
        """Применяет сортировку и фильтрацию к задачам через TaskService"""
        try:
            # Сначала применяем фильтрацию по статусу
            if sort_option == "Активные":
                tasks = self.task_service.tasks_mgr.get_filtered_by_status('Активная')
                tasks = [t for t in tasks if safe_get(t, 'client_id') == self.client_id]
            elif sort_option == "Выполненные":
                tasks = self.task_service.tasks_mgr.get_filtered_by_status('Выполнена')
                tasks = [t for t in tasks if safe_get(t, 'client_id') == self.client_id]
            elif sort_option == "Все":
                tasks = self.task_service.get_tasks_for_client(self.client_id)
            else:
                # Применяем сортировку для других опций
                if sort_option == "По сроку (ближайшие)":
                    tasks = self.task_service.get_sorted_tasks('due_date', reverse=False)
                    tasks = [t for t in tasks if safe_get(t, 'client_id') == self.client_id]
                elif sort_option == "По сроку (дальние)":
                    tasks = self.task_service.get_sorted_tasks('due_date', reverse=True)
                    tasks = [t for t in tasks if safe_get(t, 'client_id') == self.client_id]
                elif sort_option == "По названию (А-Я)":
                    tasks = sorted(tasks, key=lambda t: safe_get(t, 'title', '').lower())
                elif sort_option == "По названию (Я-А)":
                    tasks = sorted(tasks, key=lambda t: safe_get(t, 'title', '').lower(), reverse=True)
                elif sort_option == "По приоритету (высокий→низкий)":
                    tasks = self.task_service.get_sorted_tasks('priority', reverse=False)
                    tasks = [t for t in tasks if safe_get(t, 'client_id') == self.client_id]
                elif sort_option == "По приоритету (низкий→высокий)":
                    tasks = self.task_service.get_sorted_tasks('priority', reverse=True)
                    tasks = [t for t in tasks if safe_get(t, 'client_id') == self.client_id]

            # По умолчанию для "Активные" и "Выполненные" сортируем по сроку
            if sort_option in ["Активные", "Выполненные", "Все"]:
                tasks = sorted(tasks, key=lambda t: safe_get(t, 'due_date') or datetime.max)

            return tasks
        except:
            return tasks
    
    def _on_sort_change(self, event=None):
        """Обработчик изменения сортировки"""
        self._load_tasks()

    def _on_vertical_scroll(self, first, last):
        self.scrollbar.set(first, last)
        self._schedule_action_buttons()

    def _schedule_action_buttons(self, event=None):
        if self.tree is None or self._action_redraw_job is not None:
            return
        self._action_redraw_job = self.tree.after_idle(self._draw_action_buttons)

    def _draw_action_buttons(self):
        self._action_redraw_job = None
        try:
            if not self.tree.winfo_exists():
                return
        except tk.TclError:
            return

        current_ids = set(self.tree.get_children(""))
        for item_id in current_ids:
            bounds = self.tree.bbox(item_id, "Действие")
            button = self._action_buttons.get(item_id)
            if not bounds:
                if button:
                    button.place_forget()
                continue

            activity = self._activity_items.get(item_id)
            if not activity or activity["kind"] != "task":
                if button:
                    button.place_forget()
                continue
            task_id = safe_get(activity["item"], "id")
            completed = bool(safe_get(activity["item"], "completed", False))
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
            button.place(
                x=x + 3,
                y=y + 2,
                width=max(width - 6, 1),
                height=max(height - 4, 1)
            )

        for item_id, button in tuple(self._action_buttons.items()):
            if item_id not in current_ids:
                button.destroy()
                del self._action_buttons[item_id]
    
    def _load_tasks(self):
        """Показывает задачи и комментарии клиента в единой ленте."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._activity_items.clear()
        for button in self._action_buttons.values():
            button.destroy()
        self._action_buttons.clear()

        if not self.tasks_mgr:
            self._schedule_action_buttons()
            return

        try:
            tasks = self._apply_sorting(
                self.task_service.get_tasks_for_client(self.client_id),
                self.sort_var.get()
            )
            activities = [
                {"kind": "task", "item": task}
                for task in tasks
            ]
            if self.interactions_mgr:
                activities.extend(
                    {"kind": "comment", "item": dict(interaction)}
                    for interaction in self.interactions_mgr.get_by_client(self.client_id)
                )
            activities.sort(
                key=lambda activity: str(
                    safe_get(activity["item"], "created_at")
                    or safe_get(activity["item"], "date")
                    or ""
                ),
                reverse=True
            )

            for index, activity in enumerate(activities):
                item = activity["item"]
                if activity["kind"] == "task":
                    task_id = safe_get(item, "id", "")
                    title = safe_get(item, "title", "")
                    status = StatusFormatter.normalize(safe_get(item, "status", "Новая"))
                    priority_str = PriorityFormatter.format(
                        safe_get(item, "priority", ""),
                        with_icon=True
                    )
                    due_date_str = DateFormatter.format_date(safe_get(item, "due_date", ""))
                    action = "Выполнено" if safe_get(item, "completed", False) else ""
                    tags = self._get_task_row_tags(item, index)
                    row_values = (task_id, status, title, priority_str, due_date_str, action)
                    activity_key = f"task:{task_id}"
                else:
                    interaction_id = safe_get(item, "id", "")
                    activity_key = f"comment:{interaction_id}"
                    row_values = (
                        f"З-{interaction_id}",
                        safe_get(item, "type", "Комментарий"),
                        safe_get(item, "description", ""),
                        "",
                        DateFormatter.format_date(safe_get(item, "date", "")),
                        ""
                    )
                    tags = ("oddrow" if index % 2 else "evenrow",)
                tree_item = self.tree.insert(
                    "",
                    "end",
                    iid=activity_key,
                    values=row_values,
                    tags=tags
                )
                self._activity_items[tree_item] = activity
        except Exception as e:
            print(f"Ошибка при загрузке задач: {e}")
        self._schedule_action_buttons()
    
    def _on_double_click(self, event):
        """Обработчик двойного клика - открытие диалога редактирования"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            activity = self._activity_items.get(item)
            if activity and activity["kind"] == "task":
                task_id = safe_get(activity["item"], "id")
                self._open_task_form(task_id)
            elif activity and activity["kind"] == "comment":
                self._open_activity_comment(activity["item"])
    
    def _complete_task(self, task_id):
        """Отмечает задачу выполненной по кнопке в её строке."""
        try:
            task = self.tasks_mgr.get_by_id(task_id)
            if task and not safe_get(task, "completed", False):
                self.tasks_mgr.update_task_status(task_id, True)
                self._load_tasks()
        except Exception as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось завершить задачу:\n{error}",
                parent=self.parent.winfo_toplevel()
            )
    
    def _add_task(self):
        """Добавляет новую задачу для клиента"""
        self._open_task_form()

    def _add_activity_comment(self):
        """Добавляет заметку клиента в историю активности."""
        self._open_activity_comment()

    def _open_activity_comment(self, interaction=None):
        """Создаёт или редактирует запись в истории активности."""
        if not self.interactions_mgr:
            messagebox.showerror(
                "Ошибка",
                "Не удалось подключить историю активности.",
                parent=self.parent.winfo_toplevel()
            )
            return

        is_editing = interaction is not None
        dialog = tk.Toplevel(self.parent.winfo_toplevel())
        dialog.title("Редактирование активности" if is_editing else "Комментарий к активности")
        dialog.geometry("560x390")
        dialog.minsize(460, 320)
        dialog.configure(bg=Colors.LIGHT)
        dialog.transient(self.parent.winfo_toplevel())

        content = tk.Frame(dialog, bg=Colors.SURFACE, padx=18, pady=16)
        content.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        tk.Label(
            content,
            text="Дата",
            font=("Arial", 10, "bold"),
            bg=Colors.SURFACE,
            fg=Colors.TEXT
        ).pack(anchor="w", pady=(0, 5))
        date_entry = ttk.Entry(content)
        date_entry.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            content,
            text="Тип",
            font=("Arial", 10, "bold"),
            bg=Colors.SURFACE,
            fg=Colors.TEXT
        ).pack(anchor="w", pady=(0, 5))
        type_entry = ttk.Entry(content)
        type_entry.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            content,
            text="Комментарий",
            font=("Arial", 10, "bold"),
            bg=Colors.SURFACE,
            fg=Colors.TEXT
        ).pack(anchor="w", pady=(0, 5))
        comment_text = tk.Text(
            content,
            height=8,
            wrap=tk.WORD,
            font=("Arial", 10),
            relief="solid",
            borderwidth=1
        )
        comment_text.pack(fill=tk.BOTH, expand=True)

        if is_editing:
            raw_date = str(safe_get(interaction, "date", "") or "")
            try:
                date_value = date.fromisoformat(raw_date[:10]).strftime("%d.%m.%Y")
            except ValueError:
                date_value = raw_date
            date_entry.insert(0, date_value)
            type_entry.insert(0, safe_get(interaction, "type", "Комментарий") or "Комментарий")
            comment_text.insert("1.0", safe_get(interaction, "description", "") or "")
        else:
            date_entry.insert(0, date.today().strftime("%d.%m.%Y"))
            type_entry.insert(0, "Комментарий")

        buttons = tk.Frame(content, bg=Colors.SURFACE)
        buttons.pack(fill=tk.X, pady=(12, 0))

        def save_comment():
            description = comment_text.get("1.0", "end-1c").strip()
            interaction_type = type_entry.get().strip()
            try:
                interaction_date = datetime.strptime(
                    date_entry.get().strip(),
                    "%d.%m.%Y"
                ).date()
            except ValueError:
                messagebox.showwarning("Неверная дата", "Введите дату в формате ДД.ММ.ГГГГ.", parent=dialog)
                date_entry.focus_set()
                return

            if not interaction_type:
                messagebox.showwarning("Активность", "Укажите тип активности.", parent=dialog)
                type_entry.focus_set()
                return
            if not description:
                messagebox.showwarning("Комментарий", "Введите текст комментария.", parent=dialog)
                comment_text.focus_set()
                return

            try:
                if is_editing:
                    self.interactions_mgr.update(
                        safe_get(interaction, "id"),
                        interaction_date,
                        interaction_type,
                        description
                    )
                else:
                    self.interactions_mgr.add(
                        self.client_id,
                        interaction_date,
                        interaction_type,
                        description
                    )
            except Exception as error:
                messagebox.showerror(
                    "Ошибка",
                    f"Не удалось сохранить активность:\n{error}",
                    parent=dialog
                )
                return
            dialog.destroy()
            self._load_tasks()

        tk.Button(
            buttons,
            text="Отмена",
            command=dialog.destroy,
            bg=Colors.LIGHT,
            fg=Colors.TEXT,
            relief="flat",
            padx=14,
            pady=6
        ).pack(side=tk.RIGHT, padx=(8, 0))
        tk.Button(
            buttons,
            text="Сохранить",
            command=save_comment,
            bg=Colors.PRIMARY,
            fg=Colors.WHITE,
            activebackground=Colors.PRIMARY_HOVER,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6
        ).pack(side=tk.RIGHT)
        center_toplevel(dialog)
        date_entry.focus_set()

    def _open_task_form(self, task_id=None):
        """Открывает общую форму создания или редактирования задачи."""
        from views.tasks.forms import TaskFormDialog

        task = self.tasks_mgr.get_by_id(task_id) if task_id is not None else None
        if task_id is not None and task is None:
            messagebox.showerror(
                "Ошибка",
                f"Задача с ID {task_id} не найдена.",
                parent=self.parent.winfo_toplevel()
            )
            return

        def save_task(data):
            if task is None:
                new_task_id = self.task_service.create_task(data)
                if data["completed"]:
                    self.tasks_mgr.update_task_status(new_task_id, True)
            else:
                data["status"] = data.pop("completed")
                self.task_service.update_task(task_id, data)
            self._load_tasks()

        TaskFormDialog(
            self.parent,
            self.clients_mgr,
            save_task,
            task=task,
            fixed_client_id=self.client_id,
            on_open_client=self.on_open_client
        )
    
    def _create_task_for_client(self, client_id):
        """Создает задачу для клиента"""
        try:
            # Проверяем, что tasks_mgr инициализирован
            if not self.tasks_mgr:
                from tkinter import messagebox
                messagebox.showerror("Ошибка", "Менеджер задач не инициализирован")
                return

            task_window = tk.Toplevel(self.parent)
            task_window.title("➕ Новая задача")
            task_window.geometry("600x550")
            task_window.configure(bg='white')
            task_window.resizable(False, False)
            center_toplevel(task_window)
            
            # Делаем окно модальным и поверх родительского
            task_window.transient(self.parent.winfo_toplevel())
            task_window.grab_set()
            task_window.focus_set()

            # Основная информация
            main_frame = tk.Frame(task_window, bg='white')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Название
            tk.Label(main_frame, text="📋 Основная информация", font=("Arial", 12, "bold"), bg='white', fg='#333').pack(anchor='w', pady=(0, 10))
            
            tk.Label(main_frame, text="Название задачи *", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
            title_entry = tk.Entry(main_frame, font=("Arial", 11), width=50, relief="solid", borderwidth=1)
            title_entry.pack(fill=tk.X, pady=(5, 15))

            # Описание
            tk.Label(main_frame, text="Описание", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
            desc_text = tk.Text(main_frame, font=("Arial", 11), height=4, width=50, relief="solid", borderwidth=1)
            desc_text.pack(fill=tk.X, pady=(5, 15))

            # Клиент
            tk.Label(main_frame, text="Клиент", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
            client_frame = tk.Frame(main_frame, bg='white')
            client_frame.pack(fill=tk.X, pady=(5, 15))
            
            # Получаем информацию о клиенте
            client_info = self.clients_mgr.get_by_id(client_id)
            client_name = client_info.get('company', 'Без названия') if client_info else 'Неизвестный клиент'
            
            client_var = tk.StringVar(value=client_name)
            client_entry = tk.Entry(client_frame, textvariable=client_var, font=("Arial", 11), relief="solid", borderwidth=1)
            client_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            client_entry.config(state='readonly')  # Делаем поле только для чтения

            # Дополнительные параметры
            tk.Label(main_frame, text="⚙ Дополнительные параметры", font=("Arial", 12, "bold"), bg='white', fg='#333').pack(anchor='w', pady=(0, 10))
            
            # Приоритет
            tk.Label(main_frame, text="Приоритет", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
            priority_var = tk.StringVar(value="Средний")
            priority_combo = ttk.Combobox(main_frame, textvariable=priority_var,
                                        values=["Низкий", "Средний", "Высокий"],
                                        state="readonly", width=20)
            priority_combo.pack(fill=tk.X, pady=(5, 15))

            # Срок выполнения
            tk.Label(main_frame, text="Срок выполнения", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
            date_frame = tk.Frame(main_frame, bg='white')
            date_frame.pack(fill=tk.X, pady=(5, 15))
            
            due_date_var = tk.StringVar(value=datetime.now().strftime("%d.%m.%Y"))
            due_date_entry = tk.Entry(date_frame, textvariable=due_date_var, font=("Arial", 11), relief="solid", borderwidth=1)
            due_date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            def show_calendar():
                """Показать календарь для выбора даты"""
                cal_dialog = CalendarDialog(task_window, "Выберите срок выполнения")
                selected_date = cal_dialog.show()
                if selected_date:
                    due_date_var.set(selected_date.strftime("%d.%m.%Y"))
            
            tk.Button(
                date_frame,
                text="📅",
                command=show_calendar,
                bg="#41a5be",
                fg="white",
                font=("Arial", 10),
                relief="flat",
                cursor="hand2"
            ).pack(side=tk.RIGHT, padx=(5, 0))

            # Кнопки
            buttons_frame = tk.Frame(main_frame, bg='white')
            buttons_frame.pack(fill=tk.X, pady=(20, 0))

            def save_task():
                title = title_entry.get().strip()
                if not title:
                    messagebox.showerror("Ошибка", "Укажите название задачи")
                    return

                description = desc_text.get('1.0', tk.END).strip()
                priority = priority_var.get()
                due_date = due_date_var.get().strip()

                # Создаем задачу через TaskService
                try:
                    task_data = {
                        'title': title,
                        'description': description,
                        'client_id': client_id,
                        'priority': priority,
                        'due_date': due_date
                    }
                    self.task_service.create_task(task_data)

                    task_window.destroy()

                    # Обновляем таблицу
                    self._load_tasks()

                except ValueError as e:
                    messagebox.showerror("Ошибка валидации", str(e))
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось создать задачу: {e}")

            tk.Button(buttons_frame, text="Сохранить", command=save_task,
                     bg="#28a745", fg="white", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=(0, 10))
            tk.Button(buttons_frame, text="Отмена", command=task_window.destroy,
                     bg="#6c757d", fg="white", font=("Arial", 11, "bold")).pack(side=tk.LEFT)

            title_entry.focus_set()

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось создать задачу: {e}")
    
    def _edit_task(self, task_id):
        """Диалог редактирования задачи"""
        try:
            task = self.tasks_mgr.get_by_id(task_id)
            if not task:
                from tkinter import messagebox
                messagebox.showerror("Ошибка", f"Задача с ID {task_id} не найдена")
                return

            dialog = tk.Toplevel(self.parent)
            dialog.title("Редактирование задачи")
            dialog.geometry("620x580")
            dialog.configure(bg=Colors.LIGHT)
            dialog.resizable(False, False)
            dialog.transient(self.parent.winfo_toplevel())
            center_toplevel(dialog)

            header = tk.Frame(dialog, bg=Colors.DARK, height=64)
            header.pack(fill=tk.X)
            header.pack_propagate(False)
            tk.Label(
                header,
                text="Редактирование задачи",
                font=("Arial", 17, "bold"),
                bg=Colors.DARK,
                fg=Colors.WHITE
            ).pack(side=tk.LEFT, padx=24, pady=16)

            main_frame = tk.Frame(dialog, bg=Colors.LIGHT)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

            label_options = {
                "font": ("Arial", 10, "bold"),
                "bg": Colors.LIGHT,
                "fg": Colors.TEXT
            }
            entry_options = {
                "font": ("Arial", 11),
                "relief": "solid",
                "borderwidth": 1,
                "bg": Colors.SURFACE,
                "fg": Colors.TEXT,
                "insertbackground": Colors.TEXT,
                "highlightthickness": 1,
                "highlightbackground": Colors.BORDER,
                "highlightcolor": Colors.PRIMARY
            }

            tk.Label(main_frame, text="Название задачи", **label_options).pack(anchor="w")
            title_entry = tk.Entry(main_frame, **entry_options)
            title_entry.pack(fill=tk.X, pady=(6, 16), ipady=6)
            title_entry.insert(0, task.title)

            tk.Label(main_frame, text="Описание", **label_options).pack(anchor="w")
            desc_text = tk.Text(
                main_frame,
                height=5,
                font=("Arial", 11),
                wrap=tk.WORD,
                relief="solid",
                borderwidth=1,
                bg=Colors.SURFACE,
                fg=Colors.TEXT,
                insertbackground=Colors.TEXT,
                highlightthickness=1,
                highlightbackground=Colors.BORDER,
                highlightcolor=Colors.PRIMARY
            )
            desc_text.pack(fill=tk.X, pady=(6, 16))
            if task.description:
                desc_text.insert('1.0', task.description)

            style = ttk.Style(dialog)
            style.configure(
                "ClientTaskEdit.TCombobox",
                padding=6,
                fieldbackground=Colors.SURFACE,
                foreground=Colors.TEXT
            )

            params_frame = tk.Frame(main_frame, bg=Colors.LIGHT)
            params_frame.pack(fill=tk.X, pady=(0, 16))
            params_frame.columnconfigure(0, weight=1)
            params_frame.columnconfigure(1, weight=1)

            status_frame = tk.Frame(params_frame, bg=Colors.LIGHT)
            status_frame.grid(row=0, column=0, sticky="ew", padx=(0, 12))
            tk.Label(status_frame, text="Статус", **label_options).pack(anchor="w")
            status_var = tk.StringVar(value=task.status if task.status in ["Активная", "Выполнена"] else "Активная")
            status_combo = ttk.Combobox(
                status_frame,
                textvariable=status_var,
                values=["Активная", "Выполнена"],
                state="readonly",
                style="ClientTaskEdit.TCombobox"
            )
            status_combo.pack(fill=tk.X, pady=(6, 0))

            priority_frame = tk.Frame(params_frame, bg=Colors.LIGHT)
            priority_frame.grid(row=0, column=1, sticky="ew", padx=(12, 0))
            tk.Label(priority_frame, text="Приоритет", **label_options).pack(anchor="w")
            priority_var = tk.StringVar(value=task.priority or "Средний")
            priority_combo = ttk.Combobox(
                priority_frame,
                textvariable=priority_var,
                values=["Низкий", "Средний", "Высокий"],
                state="readonly",
                style="ClientTaskEdit.TCombobox"
            )
            priority_combo.pack(fill=tk.X, pady=(6, 0))

            due_frame = tk.Frame(main_frame, bg=Colors.LIGHT)
            due_frame.pack(fill=tk.X)
            tk.Label(due_frame, text="Срок выполнения", **label_options).pack(anchor="w")
            date_input_frame = tk.Frame(due_frame, bg=Colors.LIGHT)
            date_input_frame.pack(fill=tk.X, pady=(6, 0))

            current_due_date = getattr(task, 'due_date', None)
            due_date_var = tk.StringVar(value=DateFormatter.format_date(current_due_date))
            due_date_entry = tk.Entry(date_input_frame, textvariable=due_date_var, **entry_options)
            due_date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)

            def show_edit_calendar():
                cal_dialog = CalendarDialog(dialog, "Выберите срок выполнения")
                selected_date = cal_dialog.show()
                if selected_date:
                    due_date_var.set(selected_date.strftime("%d.%m.%Y"))

            tk.Button(
                date_input_frame,
                text="Выбрать дату",
                command=show_edit_calendar,
                bg=Colors.PRIMARY,
                fg=Colors.WHITE,
                activebackground=Colors.PRIMARY_HOVER,
                activeforeground=Colors.WHITE,
                font=("Arial", 10, "bold"),
                relief="flat",
                cursor="hand2",
                padx=14,
                pady=8
            ).pack(side=tk.RIGHT, padx=(10, 0))

            quick_dates_frame = tk.Frame(main_frame, bg=Colors.LIGHT)
            quick_dates_frame.pack(fill=tk.X, pady=(8, 14))
            for label, days in (("Завтра", 1), ("Через 3 дня", 3), ("Через неделю", 7)):
                tk.Button(
                    quick_dates_frame,
                    text=label,
                    command=lambda offset=days: due_date_var.set(
                        (date.today() + timedelta(days=offset)).strftime("%d.%m.%Y")
                    ),
                    bg=Colors.LIGHT,
                    fg=Colors.TEXT,
                    activebackground=Colors.BORDER,
                    relief="flat",
                    cursor="hand2",
                    padx=10,
                    pady=5
                ).pack(side=tk.LEFT, padx=(0, 8))

            buttons_frame = tk.Frame(dialog, bg=Colors.SURFACE, padx=24, pady=16)
            buttons_frame.pack(fill=tk.X, side=tk.BOTTOM)

            def save_task():
                title = title_entry.get().strip()
                if not title:
                    from tkinter import messagebox
                    messagebox.showerror("Ошибка", "Укажите название задачи")
                    return

                description = desc_text.get('1.0', tk.END).strip()
                status = status_var.get()
                priority = priority_var.get()
                due_date = due_date_var.get().strip()

                # Обновляем задачу через TaskService
                try:
                    task_data = {
                        'title': title,
                        'description': description,
                        'status': status,
                        'priority': priority,
                        'due_date': due_date,
                        'client_id': safe_get(task, 'client_id')
                    }
                    self.task_service.update_task(task_id, task_data)

                    dialog.destroy()

                    # Обновляем таблицу задач
                    self._load_tasks()

                except ValueError as e:
                    from tkinter import messagebox
                    messagebox.showerror("Ошибка валидации", str(e))
                except Exception as e:
                    from tkinter import messagebox
                    messagebox.showerror("Ошибка", f"Не удалось обновить задачу: {e}")

            tk.Button(
                buttons_frame,
                text="Сохранить изменения",
                command=save_task,
                bg=Colors.PRIMARY,
                fg=Colors.WHITE,
                activebackground=Colors.PRIMARY_HOVER,
                activeforeground=Colors.WHITE,
                font=("Arial", 10, "bold"),
                relief="flat",
                cursor="hand2",
                padx=18,
                pady=9
            ).pack(side=tk.RIGHT, padx=(10, 0))
            tk.Button(
                buttons_frame,
                text="Отмена",
                command=dialog.destroy,
                bg=Colors.LIGHT,
                fg=Colors.TEXT,
                activebackground=Colors.BORDER,
                activeforeground=Colors.TEXT,
                font=("Arial", 10, "bold"),
                relief="flat",
                cursor="hand2",
                padx=18,
                pady=9
            ).pack(side=tk.RIGHT)

            title_entry.focus_set()
            dialog.grab_set()
            dialog.focus_set()

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось открыть задачу: {e}")

    def refresh(self):
        """Обновляет данные в таблице"""
        self._load_tasks()


class ClientContactsTable:
    """Таблица контактов для конкретного клиента"""
    
    def __init__(self, parent, client_id, contact_persons_mgr, contact_emails_mgr, clients_view):
        self.parent = parent
        self.client_id = client_id
        self.contact_persons_mgr = contact_persons_mgr
        self.contact_emails_mgr = contact_emails_mgr
        self.clients_view = clients_view  # Ссылка на ClientsView для вызова методов
        self.tree = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Создает интерфейс таблицы"""
        # Заголовок
        header_frame = tk.Frame(self.parent, bg='#f8f9fa')
        header_frame.pack(fill=tk.X, padx=15, pady=(20, 10))
        
        tk.Label(
            header_frame,
            text="Контактные лица",
            font=("Arial", 16, "bold"),
            bg='#f8f9fa',
            fg='#333'
        ).pack(side=tk.LEFT)
        
        # Контейнер для элементов справа
        right_container = tk.Frame(header_frame, bg='#f8f9fa')
        right_container.pack(side=tk.RIGHT)
        
        # Сортировка
        tk.Label(
            right_container,
            text="Сортировка:",
            font=("Arial", 10),
            bg='#f8f9fa',
            fg='#666'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.sort_var = tk.StringVar(value="По ФИО (А-Я)")
        sort_options = [
            "По ФИО (А-Я)",
            "По ФИО (Я-А)", 
            "По должности (А-Я)",
            "По должности (Я-А)"
        ]
        
        sort_combo = ttk.Combobox(
            right_container,
            textvariable=self.sort_var,
            values=sort_options,
            state="readonly",
            width=20,
            font=("Arial", 9)
        )
        sort_combo.pack(side=tk.LEFT, padx=(0, 10))
        sort_combo.bind("<<ComboboxSelected>>", self._on_sort_change)
        
        # Кнопка добавления контакта
        add_btn = tk.Button(
            right_container,
            text="+ Добавить контакт",
            command=self._add_contact,
            bg="#28a745",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2"
        )
        add_btn.pack(side=tk.LEFT, padx=10)
        
        # Создаем таблицу
        self._create_table()
        
        # Загружаем данные
        self._load_contacts()
    
    def _create_table(self):
        """Создает Treeview таблицу"""
        # Фрейм для таблицы с прокруткой
        table_frame = tk.Frame(self.parent)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 20))
        
        # Создаем Treeview
        self.tree = ttk.Treeview(
            table_frame,
            columns=("ID", "ФИО", "Должность", "Телефон", "Email"),
            show="headings",
            selectmode="browse"
        )
        
        # Настройка колонок
        self.tree.heading("ID", text="ID")
        self.tree.heading("ФИО", text="ФИО")
        self.tree.heading("Должность", text="Должность")
        self.tree.heading("Телефон", text="Телефон")
        self.tree.heading("Email", text="Email")
        
        # Ширина колонок
        self.tree.column("ID", width=50, minwidth=50)
        self.tree.column("ФИО", width=200, minwidth=150)
        self.tree.column("Должность", width=150, minwidth=120)
        self.tree.column("Телефон", width=120, minwidth=100)
        self.tree.column("Email", width=200, minwidth=150)
        
        # Прокрутка
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Обработчики
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-1>', self._on_single_click)
        self.tree.bind("<Control-c>", _copy_selected_tree_row)
        self.tree.bind("<Control-C>", _copy_selected_tree_row)
        self.tree.bind("<Button-3>", _show_tree_copy_menu)
        
        # Стиль для основного контакта
        self._setup_tag_styles()
    
    def _setup_tag_styles(self):
        """Настраивает стили для разных типов контактов"""
        style = ttk.Style()
        
        # Исправление для tag_configure в Windows
        def fixed_map(option):
            return [elm for elm in style.map('Treeview', query_opt=option) 
                   if elm[:2] != ('!disabled', '!selected')]
        
        style.map('Treeview', foreground=fixed_map('foreground'), 
                  background=fixed_map('background'))
        
        # Выделяем основной контакт зеленым цветом как в таблице клиентов
        self.tree.tag_configure(
            "primary",
            background=Colors.COMPLETED_BG,
            foreground=Colors.COMPLETED_FG
        )
    
    def _apply_sorting(self, contacts, sort_option):
        """Применяет сортировку к контактам через менеджер"""
        try:
            if sort_option == "По ФИО (А-Я)":
                contacts = self.contact_persons_mgr.get_sorted_by_name(reverse=False)
                contacts = [c for c in contacts if safe_get(c, 'client_id') == self.client_id]
            elif sort_option == "По ФИО (Я-А)":
                contacts = self.contact_persons_mgr.get_sorted_by_name(reverse=True)
                contacts = [c for c in contacts if safe_get(c, 'client_id') == self.client_id]
            elif sort_option == "По должности (А-Я)":
                contacts = self.contact_persons_mgr.get_sorted_by_position(reverse=False)
                contacts = [c for c in contacts if safe_get(c, 'client_id') == self.client_id]
            elif sort_option == "По должности (Я-А)":
                contacts = self.contact_persons_mgr.get_sorted_by_position(reverse=True)
                contacts = [c for c in contacts if safe_get(c, 'client_id') == self.client_id]
            return contacts
        except:
            return contacts

    def _on_sort_change(self, event=None):
        """Обработчик изменения сортировки"""
        self._load_contacts()

    def _load_contacts(self):
        """Загружает контакты клиента в таблицу с использованием safe_get"""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.contact_persons_mgr:
            return

        try:
            # Получаем контакты клиента
            contacts = self.contact_persons_mgr.get_by_client(self.client_id)

            # Применяем сортировку
            sort_option = self.sort_var.get()
            contacts = self._apply_sorting(contacts, sort_option)

            for contact in contacts:
                contact_id = safe_get(contact, 'id', '')
                full_name = safe_get(contact, 'full_name', '')
                position = safe_get(contact, 'position', '')
                phone = safe_get(contact, 'phone', '')

                # Получаем email для контакта
                email = ""
                if self.contact_emails_mgr:
                    try:
                        emails = self.contact_emails_mgr.get_by_contact(contact_id)
                        if emails:
                            email = emails[0]['email']
                    except Exception as e:
                        print(f"Ошибка загрузки email для контакта {contact_id}: {e}")
                
                # Добавляем в таблицу
                is_primary = contact['is_primary'] if isinstance(contact['is_primary'], bool) else bool(contact['is_primary'])
                tags = ('primary',) if is_primary else ()
                
                self.tree.insert(
                    "", 
                    "end",
                    values=(contact_id, full_name, position, phone, email),
                    tags=tags
                )
        
        except Exception as e:
            print(f"Ошибка при загрузке контактов: {e}")
    
    def _on_double_click(self, event):
        """Обработчик двойного клика - открытие диалога редактирования"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, "values")
            if values:
                contact_id = values[0]
                # Открываем диалог редактирования контакта
                self._edit_contact(contact_id)
    
    def _on_single_click(self, event):
        """Обработчик одинарного клика - ничего не делает"""
        pass
    
    def _add_contact(self):
        """Добавляет новый контакт для клиента"""
        self.clients_view._add_contact_to_client(self.client_id, self.parent)
    
    def _edit_contact(self, contact_id):
        """Открывает диалог редактирования контакта"""
        # Находим родительское окно карточки клиента
        parent_window = self.parent.winfo_toplevel()
        
        # Создаем диалог редактирования контакта
        self.clients_view._edit_contact(contact_id, parent_window)
        
        # Обновляем таблицу контактов после редактирования
        self.refresh()
    
    def refresh(self):
        """Обновляет данные в таблице"""
        self._load_contacts()


class ClientsView(TableViewTemplate):
    """Раздел клиентов с поиском, сортировкой и пагинацией"""

    TITLE = "Клиенты"
    ADD_BUTTON_TEXT = "+ Добавить клиента"
    SEARCH_FIELDS_TEXT = "компании или контактному лицу"
    COLUMNS = ("_internal_id", "ID", "Компания", "Контактное лицо", "Должность", "Телефон", "Адрес", "Задачи")
    COLUMN_WIDTHS = {
        "_internal_id": 0,
        "ID": 110,
        "Компания": 200,
        "Контактное лицо": 180,
        "Должность": 150,
        "Телефон": 120,
        "Адрес": 200,
        "Задачи": 100
    }
    STRETCH_COLUMNS = ["Компания", "Контактное лицо", "Должность", "Телефон", "Адрес"]
    ID_COLUMN = "_internal_id"
    PAGE_SIZE = 50
    
    SORT_OPTIONS = [
        ("company", "По компании (А-Я)"),
        ("company:DESC", "По компании (Я-А)"),
        ("primary_contact", "По контакту (А-Я)"),
        ("primary_contact:DESC", "По контакту (Я-А)"),
        ("created_at", "По дате создания (новые)"),
        ("created_at:DESC", "По дате создания (старые)")
    ]

    def __init__(self, parent_frame, clients_mgr, contact_persons_mgr, contact_emails_mgr, interactions_mgr, tasks_mgr=None, document_service=None):
        super().__init__(parent_frame, clients_mgr)
        self.clients_mgr = clients_mgr
        self.contact_persons_mgr = contact_persons_mgr
        self.contact_emails_mgr = contact_emails_mgr
        self.interactions_mgr = interactions_mgr
        self.tasks_mgr = tasks_mgr
        self.document_service = document_service
        
        # Инициализация сервиса
        self.client_service = ClientService(clients_mgr, contact_persons_mgr, contact_emails_mgr, interactions_mgr)
        
        # Переменные для отслеживания открытых окон
        self.add_client_dialog = None
        self.edit_client_dialogs = {}  # client_id -> dialog
        self.client_card_dialogs = {}  # client_id -> dialog
        self.add_contact_dialogs = {}  # client_id -> dialog

    def _on_tree_enter(self, event):
        pass

    def _on_tree_leave(self, event):
        pass

    def _on_tree_motion(self, event):
        pass

    def _create_table(self):
        """Создаёт Treeview таблицу с дополнительной обработкой клика на задачи"""
        # Вызываем родительский метод
        super()._create_table()
        self.tree["displaycolumns"] = self.COLUMNS[1:]
        self.tree.column("_internal_id", width=0, minwidth=0, stretch=False)
        
        # Добавляем обработку одинарного клика на колонку "Задачи"
        self.tree.bind('<Button-1>', self._on_single_click)

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
            
        values = self.tree.item(item, 'values')
        if not values:
            return

        # Имя компании открывает карточку клиента.
        if column == "#2":
            try:
                self._open_client_card_by_id(int(values[0]))
            except (TypeError, ValueError, IndexError):
                messagebox.showerror(
                    "Ошибка",
                    "Не удалось определить клиента для открытия.",
                    parent=self.parent_frame.winfo_toplevel()
                )
            return "break"

        # Кнопка задач позволяет быстро добавить задачу этому клиенту.
        if column == "#7":  # Public ID is visible; database ID stays in the hidden first column.
            try:
                client_id = int(values[0])
                self._create_task_for_client(client_id)
            except (ValueError, IndexError):
                pass

    def _create_task_for_client(self, client_id):
        """Открывает общую форму создания задачи для выбранного клиента."""
        if not self.tasks_mgr:
            messagebox.showerror(
                "Ошибка",
                "Менеджер задач не инициализирован.",
                parent=self.parent_frame.winfo_toplevel()
            )
            return

        from views.tasks.forms import TaskFormDialog

        def save_task(data):
            task_data = dict(data, client_id=client_id)
            task_id = TaskService(self.tasks_mgr, self.clients_mgr).create_task(task_data)
            if data["completed"]:
                self.tasks_mgr.update_task_status(task_id, True)
            self._refresh_data()

        TaskFormDialog(
            self.parent_frame,
            self.clients_mgr,
            save_task,
            fixed_client_id=client_id,
            on_open_client=self._open_client_card_by_id
        )

    def _get_data(self, page, search, sort_by, sort_order):
        """Загрузка данных с пагинацией и поиском"""
        try:
            # Получаем данные с поиском или без
            if search:
                clients = self.clients_mgr.search(search.lower())
            else:
                clients = self.clients_mgr.get_all()
            
            # Применяем сортировку
            if sort_by:
                clients = self._apply_sort(clients, sort_by, sort_order)
            
            # Эмуляция пагинации
            total = len(clients)
            start_idx = (page - 1) * self.PAGE_SIZE
            end_idx = start_idx + self.PAGE_SIZE
            paginated_clients = clients[start_idx:end_idx]
            
            return paginated_clients, total
            
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            return [], 0

    def _apply_sort(self, clients, sort_by, sort_order):
        """Применяет сортировку к списку клиентов"""
        reverse = sort_order == "DESC"
        
        if sort_by == "company":
            clients.sort(key=lambda x: x.get('company', '').lower(), reverse=reverse)
        elif sort_by == "primary_contact":
            clients.sort(key=lambda x: x.get('primary_contact', '').lower(), reverse=reverse)
        elif sort_by == "created_at":
            clients.sort(key=lambda x: x.get('created_at', ''), reverse=reverse)
            
        return clients

    def _item_to_row_values(self, item):
        """Преобразует клиента в строку таблицы"""
        if not isinstance(item, dict):
            return ("", "", "", "", "", "", "", "")
        
        values = (
            item.get('id', ''),
            item.get('public_id') or item.get('id', ''),
            item.get('company', '—'),
            item.get('primary_contact', '—'),
            item.get('primary_position', '—'),
            item.get('primary_phone', '—'),
            item.get('address', '—'),
            "➕ Задача"  # Кнопка для создания задачи
        )
        
        return values

    def _open_create_dialog(self):
        """Диалог создания нового клиента"""
        self._show_add_client_dialog()

    def _on_row_double_click(self, client_id):
        """Обработка двойного клика по строке - открытие карточки клиента"""
        self._open_client_card_by_id(client_id)

    @staticmethod
    def _create_partner_fields(parent, client=None):
        """Создать редактируемые поля карточки партнёра."""
        client = client or {}
        partner_frame = tk.LabelFrame(
            parent,
            text="Карточка партнёра",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#172b4d",
            padx=12,
            pady=8
        )
        partner_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        partner_frame.columnconfigure(1, weight=1)
        partner_frame.columnconfigure(3, weight=1)

        fields = {}
        rows = (
            (("full_legal_name", "Полное наименование"), ("ogrn", "ОГРН")),
            (("legal_address", "Юридический адрес"), ("inn_kpp", "ИНН/КПП")),
            (("postal_address", "Почтовый адрес"), ("responsible_person", "Ответственное лицо")),
            (("partner_email", "E-mail"), ("partner_phone", "Тел.")),
        )
        for row_index, field_pair in enumerate(rows):
            for pair_index, (field_name, label_text) in enumerate(field_pair):
                label_column = pair_index * 2
                entry = tk.Entry(
                    partner_frame,
                    font=("Arial", 10),
                    relief="solid",
                    borderwidth=1
                )
                entry.insert(0, client.get(field_name, "") or "")
                tk.Label(
                    partner_frame,
                    text=label_text,
                    font=("Arial", 9, "bold"),
                    bg="white",
                    fg="#243247"
                ).grid(row=row_index, column=label_column, sticky="w", padx=(4, 8), pady=5)
                entry.grid(
                    row=row_index,
                    column=label_column + 1,
                    sticky="ew",
                    padx=(0, 14 if pair_index == 0 else 4),
                    pady=5,
                    ipady=3
                )
                fields[field_name] = entry

        bank_label = tk.Label(
            partner_frame,
            text="Банковские реквизиты",
            font=("Arial", 9, "bold"),
            bg="white",
            fg="#243247"
        )
        bank_label.grid(row=4, column=0, sticky="nw", padx=(4, 8), pady=5)
        bank_text = tk.Text(
            partner_frame,
            font=("Arial", 10),
            height=3,
            relief="solid",
            borderwidth=1,
            wrap=tk.WORD
        )
        bank_text.grid(row=4, column=1, columnspan=3, sticky="ew", padx=(0, 4), pady=5)
        bank_text.insert("1.0", client.get("bank_details", "") or "")
        fields["bank_details"] = bank_text
        return fields

    @staticmethod
    def _collect_partner_fields(fields):
        """Собрать значения полей карточки партнёра."""
        values = {}
        for field_name, widget in fields.items():
            if isinstance(widget, tk.Text):
                values[field_name] = widget.get("1.0", "end-1c").strip()
            else:
                values[field_name] = widget.get().strip()
        return values

    def _load_client_card_into_form(
        self, dialog, company_entry, address_entry, partner_fields
    ):
        """Выбрать карточку клиента и заполнить поля формы."""
        downloads = Path.home() / "Downloads"
        initial_dir = downloads if downloads.is_dir() else Path.home()
        path = filedialog.askopenfilename(
            parent=dialog,
            title="Выберите карточку клиента",
            initialdir=str(initial_dir),
            filetypes=(
                ("Документы Word", "*.docx *.doc"),
                ("Все файлы", "*.*")
            )
        )
        if not path:
            return

        try:
            data = read_client_card(path)
        except Exception as error:
            messagebox.showerror(
                "Карточка клиента",
                f"Не удалось прочитать карточку:\n{error}",
                parent=dialog
            )
            self._restore_client_dialog(dialog, company_entry)
            return

        filled = self._apply_client_card(
            data, company_entry, address_entry, partner_fields
        )
        if not filled:
            messagebox.showinfo(
                "Карточка клиента",
                "В карточке не найдены данные для заполнения.",
                parent=dialog
            )
        else:
            base_title = dialog.title().split(" — ")[0]
            dialog.title(f"{base_title} — данные из {path.name}")

        # Форма остаётся открытой: пользователь проверяет и дополняет поля.
        self._restore_client_dialog(dialog, company_entry)

    @staticmethod
    def _restore_client_dialog(dialog, focus_widget=None):
        """Вернуть фокус и модальность форме после системных диалогов."""
        try:
            dialog.deiconify()
            dialog.lift()
            dialog.focus_force()
            dialog.grab_set()
        except tk.TclError:
            return
        if focus_widget is not None:
            focus_widget.focus_set()

    @staticmethod
    def _apply_client_card(data, company_entry, address_entry, partner_fields):
        """Заполнить поля формы данными из карточки."""
        filled = 0

        def set_entry(widget, value):
            nonlocal filled
            if not value:
                return
            widget.delete(0, tk.END)
            widget.insert(0, value)
            filled += 1

        set_entry(company_entry, data.get("company"))
        set_entry(address_entry, data.get("address"))

        for key, widget in partner_fields.items():
            value = data.get(key)
            if not value:
                continue
            if isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
                widget.insert("1.0", value)
                filled += 1
            else:
                set_entry(widget, value)
        return filled

    def _show_add_client_dialog(self):
        """Диалог добавления клиента с расширенным функционалом"""
        # Проверяем, не открыто ли уже окно добавления клиента
        if self.add_client_dialog and tk.Toplevel.winfo_exists(self.add_client_dialog):
            self.add_client_dialog.lift()
            self.add_client_dialog.focus_force()
            return
        
        # Создаём диалоговое окно
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Добавить клиента")
        dialog.geometry("900x800")
        dialog.minsize(760, 650)
        dialog.configure(bg='white')
        dialog.resizable(False, False)
        center_toplevel(dialog)
        
        # Сохраняем ссылку на окно
        self.add_client_dialog = dialog
        
        # Очищаем ссылку при закрытии
        def on_dialog_close():
            self.add_client_dialog = None
            dialog.destroy()
        
        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
        dialog.transient(self.parent_frame.winfo_toplevel())
        dialog.grab_set()

        # Заголовок
        header = tk.Frame(dialog, bg='#333333', height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="➕ Новый клиент",
            font=("Arial", 18, "bold"),
            fg='white',
            bg='#333333'
        ).pack(pady=15)

        # Кнопки (упаковываем первыми)
        buttons_container = tk.Frame(dialog, bg='#f0f0f0', height=80)
        buttons_container.pack(fill=tk.X, side=tk.BOTTOM)
        buttons_container.pack_propagate(False)

        buttons_frame = tk.Frame(buttons_container, bg='#f0f0f0')
        buttons_frame.pack(pady=15)

        # Canvas
        canvas_container = tk.Frame(dialog, bg='white')
        canvas_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(canvas_container, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)

        scrollable_content = tk.Frame(canvas, bg='white')

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_content.bind('<Configure>', on_frame_configure)

        canvas_window = canvas.create_window((0, 0), window=scrollable_content, anchor='nw')

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind('<Configure>', on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Основная информация ---
        tk.Label(scrollable_content, text="📋 Основная информация", font=("Arial", 14, "bold"), bg='white',
                 fg='#333').pack(anchor='w', padx=20, pady=(15, 10))

        info_frame = tk.Frame(scrollable_content, bg='white')
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        tk.Label(info_frame, text="Название компании *", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
        company_entry = tk.Entry(info_frame, font=("Arial", 11), relief="solid", borderwidth=1)
        company_entry.pack(fill=tk.X, pady=(5, 15), ipady=5)

        tk.Label(info_frame, text="Адрес", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
        address_entry = tk.Entry(info_frame, font=("Arial", 11), relief="solid", borderwidth=1)
        address_entry.pack(fill=tk.X, pady=(5, 15), ipady=5)

        tk.Label(info_frame, text="Примечания", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
        notes_text = tk.Text(info_frame, font=("Arial", 10), height=3, relief="solid", borderwidth=1, wrap=tk.WORD)
        notes_text.pack(fill=tk.X, pady=(5, 0))

        partner_fields = self._create_partner_fields(scrollable_content)

        # --- КОНТАКТНЫЕ ЛИЦА ---
        contacts_header_frame = tk.Frame(scrollable_content, bg='white')
        contacts_header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        tk.Label(contacts_header_frame, text="👥 Контактные лица", font=("Arial", 14, "bold"), bg='white',
                 fg='#333').pack(side=tk.LEFT)
        tk.Label(contacts_header_frame, text="(до 4, выберите основной)", font=("Arial", 10), bg='white',
                 fg='#999').pack(side=tk.LEFT, padx=10)

        contacts_container = tk.Frame(scrollable_content, bg='white')
        contacts_container.pack(fill=tk.X, padx=20, pady=(0, 10))

        contact_widgets = []
        primary_contact_var = tk.IntVar(value=0)

        def update_primary_contact_ui():
            """Обновляет отображение основного контакта"""
            selected_idx = primary_contact_var.get()

            for idx, widget in enumerate(contact_widgets):
                # Обновляем текст радио-кнопки
                widget['radio'].config(text=f"Контакт #{idx + 1}")

                # Обновляем метку "ОСНОВНОЙ"
                if idx == selected_idx:
                    widget['primary_label'].config(text="⭐ ОСНОВНОЙ", fg='#4CAF50')
                else:
                    widget['primary_label'].config(text="", fg='#999')

        def create_contact_fields():
            """Создает поля для ввода контактного лица"""
            if len(contact_widgets) >= 4:
                show_message(dialog, "Внимание", "Максимум 4 контактных лица!", "warning")
                return

            idx = len(contact_widgets)

            # Создаем контейнер для контакта
            contact_box = tk.Frame(contacts_container, bg='#f8f9fa', relief='solid', bd=1)
            contact_box.pack(fill=tk.X, pady=5)

            # Заголовок с радио-кнопкой и кнопкой удаления
            header_frame = tk.Frame(contact_box, bg='#f8f9fa')
            header_frame.pack(fill=tk.X, padx=10, pady=8)

            # Радио-кнопка для выбора основного контакта
            radio_btn = tk.Radiobutton(
                header_frame,
                text=f"Контакт #{idx + 1}",
                variable=primary_contact_var,
                value=idx,
                font=("Arial", 10, "bold"),
                bg='#f8f9fa',
                selectcolor='#4CAF50',
                command=update_primary_contact_ui
            )
            radio_btn.pack(side=tk.LEFT)

            # Метка для обозначения основного контакта
            primary_label = tk.Label(
                header_frame,
                text="",
                font=("Arial", 9, "bold"),
                bg='#f8f9fa'
            )
            primary_label.pack(side=tk.LEFT, padx=5)
            # Поля для ввода данных контакта
            fields_frame = tk.Frame(contact_box, bg='#f8f9fa')
            fields_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

            # Поле ФИО
            tk.Label(
                fields_frame,
                text="ФИО:",
                font=("Arial", 9),
                bg='#f8f9fa'
            ).pack(anchor='w')

            name_entry = tk.Entry(
                fields_frame,
                font=("Arial", 10),
                relief="solid",
                borderwidth=1
            )
            name_entry.pack(fill=tk.X, pady=2, ipady=3)

            # Поле должности
            tk.Label(
                fields_frame,
                text="Должность:",
                font=("Arial", 9),
                bg='#f8f9fa'
            ).pack(anchor='w')

            position_entry = tk.Entry(
                fields_frame,
                font=("Arial", 10),
                relief="solid",
                borderwidth=1
            )
            position_entry.pack(fill=tk.X, pady=2, ipady=3)

            # Поле телефона
            tk.Label(
                fields_frame,
                text="Телефон:",
                font=("Arial", 9),
                bg='#f8f9fa'
            ).pack(anchor='w')

            phone_entry = tk.Entry(
                fields_frame,
                font=("Arial", 10),
                relief="solid",
                borderwidth=1
            )
            phone_entry.pack(fill=tk.X, pady=2, ipady=3)

            # Поле email
            tk.Label(
                fields_frame,
                text="Email:",
                font=("Arial", 9),
                bg='#f8f9fa'
            ).pack(anchor='w')

            email_entry = tk.Entry(
                fields_frame,
                font=("Arial", 10),
                relief="solid",
                borderwidth=1
            )
            email_entry.pack(fill=tk.X, pady=2, ipady=3)

            # Создаем объект виджета контакта
            contact_widget = {
                'box': contact_box,
                'name': name_entry,
                'position': position_entry,
                'phone': phone_entry,
                'email': email_entry,
                'radio': radio_btn,
                'primary_label': primary_label
            }

            # Кнопка удаления контакта (добавляется после создания contact_widget)
            def remove_contact(widget=contact_widget):
                """Удаляет контактное лицо из формы"""
                contact_box.destroy()
                if widget in contact_widgets:
                    contact_widgets.remove(widget)

                # Обновляем индексы оставшихся контактов
                for i, w in enumerate(contact_widgets):
                    w['radio'].config(value=i, text=f"Контакт #{i + 1}")

                # Если удалили основной контакт, выбираем новый
                if primary_contact_var.get() >= len(contact_widgets):
                    if contact_widgets:
                        primary_contact_var.set(0)
                    else:
                        primary_contact_var.set(-1)

                update_primary_contact_ui()

            remove_btn = tk.Button(
                header_frame,
                text="✖",
                command=remove_contact,
                bg="#dc3545",
                fg="white",
                font=("Arial", 8),
                relief="flat",
                cursor="hand2"
            )
            remove_btn.pack(side=tk.RIGHT)

            contact_widgets.append(contact_widget)
            update_primary_contact_ui()
            bind_form_interactions(contact_box)

        def bind_form_interactions(widget):
            """Обеспечивает прокрутку внутри области формы клиента."""
            def on_mouse_wheel(event):
                pointer_x, pointer_y = event.x_root, event.y_root
                canvas_left = canvas.winfo_rootx()
                canvas_top = canvas.winfo_rooty()
                canvas_right = canvas_left + canvas.winfo_width()
                canvas_bottom = canvas_top + canvas.winfo_height()
                if canvas_left <= pointer_x <= canvas_right and canvas_top <= pointer_y <= canvas_bottom:
                    canvas.yview_scroll(int(-event.delta / 120), "units")
                    return "break"

            if isinstance(widget, (tk.Entry, tk.Text)):
                widget.bind("<MouseWheel>", on_mouse_wheel)
            else:
                widget.bind("<MouseWheel>", on_mouse_wheel)

            for child in widget.winfo_children():
                bind_form_interactions(child)

        # Кнопка для добавления дополнительных контактов
        add_contact_btn = tk.Button(
            contacts_container,
            text="+ Добавить контакт",
            command=create_contact_fields,
            bg="#28a745",
            fg="white",
            font=("Arial", 10),
            cursor="hand2"
        )
        add_contact_btn.pack(pady=5)

        create_contact_fields()  # Первый контакт
        bind_form_interactions(scrollable_content)

        # --- СОХРАНЕНИЕ ---
        def save_client():
            """Сохраняет нового клиента через сервис"""
            # Собираем данные формы
            form_data = {
                'company': company_entry.get().strip(),
                'address': address_entry.get().strip(),
                'notes': notes_text.get('1.0', 'end-1c').strip(),
                **self._collect_partner_fields(partner_fields),
                'contacts': []
            }

            # Собираем контакты
            for idx, w in enumerate(contact_widgets):
                contact_data = {
                    'full_name': w['name'].get().strip(),
                    'position': w['position'].get().strip(),
                    'phone': w['phone'].get().strip(),
                    'email': w['email'].get().strip(),
                    'is_primary': (idx == primary_contact_var.get())
                }
                form_data['contacts'].append(contact_data)

            try:
                client_id = self.client_service.create_client_with_contacts(form_data)
                created_client = self.clients_mgr.get_by_id(client_id)
                display_id = self.clients_mgr.get_display_id(created_client) or client_id
                # Сначала обновляем таблицу
                self._refresh_data()
                messagebox.showinfo(
                    "Успех",
                    f"Клиент #{display_id} создан",
                    parent=dialog
                )
                on_dialog_close()
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=dialog)
            except Exception as e:
                messagebox.showerror(
                    "Ошибка",
                    f"Не удалось сохранить клиента: {e}",
                    parent=dialog
                )

        # Кнопки (должны быть вне функции save_client!)
        tk.Button(
            buttons_frame,
            text="💾 Сохранить",
            command=save_client,
            bg=Colors.PRIMARY,
            fg=Colors.WHITE,
            activebackground=Colors.PRIMARY_HOVER,
            activeforeground=Colors.WHITE,
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            padx=40, pady=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="✖ Отмена",
            command=on_dialog_close,
            bg=Colors.LIGHT,
            fg=Colors.TEXT,
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            padx=40, pady=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="📄 Карточка",
            command=lambda: self._load_client_card_into_form(
                dialog, company_entry, address_entry, partner_fields
            ),
            bg="#e9ecef",
            fg=Colors.TEXT,
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            padx=40, pady=10
        ).pack(side=tk.LEFT, padx=10)

        company_entry.focus_set()

    def _open_client_card_by_id(self, client_id):
        """Открыть карточку клиента по ID"""
        try:
            client_data = self.clients_mgr.get_by_id(client_id)

            if client_data:
                if hasattr(client_data, 'keys'):
                    client = {key: client_data[key] for key in client_data.keys()}
                else:
                    try:
                        client = dict(client_data)
                    except:
                        client = {}

                # Получаем основной контакт
                try:
                    prim = self.contact_persons_mgr.get_primary(client_id)
                    if prim:
                        client['primary_contact'] = prim.get('full_name', '')
                        client['primary_position'] = prim.get('position', '')
                        client['primary_phone'] = prim.get('phone', '')
                    else:
                        client['primary_contact'] = ""
                        client['primary_position'] = ""
                        client['primary_phone'] = ""
                except Exception as e:
                    print(f"Ошибка при получении основного контакта: {e}")
                    client['primary_contact'] = ""
                    client['primary_position'] = ""
                    client['primary_phone'] = ""

                self._open_client_card(client)
                return self.client_card_dialogs.get(client_id)
            messagebox.showwarning(
                "Клиент",
                "Клиент не найден.",
                parent=self.parent_frame.winfo_toplevel()
            )
            return False

        except Exception as e:
            print(f"Ошибка при открытии карточки: {e}")
            messagebox.showerror("Ошибка", f"Не удалось открыть карточку: {e}")
            return False

    def _open_client_card(self, client):
        """Открыть карточку клиента используя ClientCardView"""
        client_id = client['id']

        # Проверяем, не открыта ли уже карточка этого клиента
        if client_id in self.client_card_dialogs:
            existing_dialog = self.client_card_dialogs[client_id]
            if existing_dialog and tk.Toplevel.winfo_exists(existing_dialog):
                existing_dialog.lift()
                existing_dialog.focus_force()
                return

        # Создаем карточку клиента
        card = ClientCardView(
            parent=self.parent_frame,
            client_id=client_id,
            clients_mgr=self.clients_mgr,
            contact_persons_mgr=self.contact_persons_mgr,
            contact_emails_mgr=self.contact_emails_mgr,
            tasks_mgr=self.tasks_mgr,
            interactions_mgr=self.interactions_mgr,
            document_service=self.document_service,
            on_edit=lambda data, window: self._edit_client(data, window),
            on_delete=self._on_client_deleted,
            on_close=lambda: self._on_client_card_closed(client_id)
        )
        
        # Показываем карточку
        card.show()
        
        # Сохраняем ссылку на окно
        if card.card_window:
            self.client_card_dialogs[client_id] = card.card_window

    def _on_client_deleted(self, client_id):
        """Обработчик удаления клиента из карточки"""
        # Удаляем из словаря открытых карточек
        if client_id in self.client_card_dialogs:
            del self.client_card_dialogs[client_id]
        # Обновляем таблицу клиентов
        self._refresh_data()

    def _on_client_card_closed(self, client_id):
        """Обработчик закрытия карточки клиента"""
        if client_id in self.client_card_dialogs:
            del self.client_card_dialogs[client_id]

    def _add_contact_to_client(self, client_id, parent_window=None):
        """Открыть диалог добавления контактного лица для клиента"""
        try:
            dialog = tk.Toplevel(parent_window or self.parent_frame)
            dialog.title("Добавить контакт")
            dialog.transient(parent_window or self.parent_frame)
            dialog.grab_set()

            tk.Label(dialog, text="ФИО", font=("Arial", 11)).grid(row=0, column=0, sticky='w', padx=10, pady=5)
            name_entry = tk.Entry(dialog, width=40)
            name_entry.grid(row=0, column=1, padx=10, pady=5)

            tk.Label(dialog, text="Должность", font=("Arial", 11)).grid(row=1, column=0, sticky='w', padx=10, pady=5)
            pos_entry = tk.Entry(dialog, width=40)
            pos_entry.grid(row=1, column=1, padx=10, pady=5)

            tk.Label(dialog, text="Телефон", font=("Arial", 11)).grid(row=2, column=0, sticky='w', padx=10, pady=5)
            phone_entry = tk.Entry(dialog, width=40)
            phone_entry.grid(row=2, column=1, padx=10, pady=5)

            is_primary_var = tk.IntVar(value=0)
            tk.Checkbutton(dialog, text="Основной контакт", variable=is_primary_var, bg='white').grid(row=3, column=1, sticky='w', padx=10, pady=5)

            def on_save():
                full_name = name_entry.get().strip()
                position = pos_entry.get().strip()
                phone = phone_entry.get().strip()
                is_primary = bool(is_primary_var.get())

                if not full_name:
                    messagebox.showerror("Ошибка", "ФИО контакта обязательно")
                    return

                try:
                    self.contact_persons_mgr.add(client_id, full_name, position=position, phone=phone, is_primary=is_primary)
                    messagebox.showinfo("Успех", "Контакт добавлен")
                    dialog.destroy()
                    self._refresh_data()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось добавить контакт:\n{e}")

            btn_frame = tk.Frame(dialog)
            btn_frame.grid(row=10, column=0, columnspan=2, pady=10)
            tk.Button(btn_frame, text="Сохранить", command=on_save, bg="#28a745", fg='white').pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            center_toplevel(dialog)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть диалог добавления контакта:\n{e}")

    def _edit_contact(self, contact_id, parent_window=None):
        """Открыть диалог редактирования контактного лица"""
        try:
            contact = self.contact_persons_mgr.get_by_id(contact_id)
            if not contact:
                messagebox.showerror("Ошибка", f"Контакт с ID {contact_id} не найден")
                return

            dialog = tk.Toplevel(parent_window or self.parent_frame)
            dialog.title("Редактировать контакт")
            dialog.transient(parent_window or self.parent_frame)
            dialog.grab_set()

            tk.Label(dialog, text="ФИО", font=("Arial", 11)).grid(row=0, column=0, sticky='w', padx=10, pady=5)
            name_entry = tk.Entry(dialog, width=40)
            name_entry.insert(0, contact.get('full_name', ''))
            name_entry.grid(row=0, column=1, padx=10, pady=5)

            tk.Label(dialog, text="Должность", font=("Arial", 11)).grid(row=1, column=0, sticky='w', padx=10, pady=5)
            pos_entry = tk.Entry(dialog, width=40)
            pos_entry.insert(0, contact.get('position', ''))
            pos_entry.grid(row=1, column=1, padx=10, pady=5)

            tk.Label(dialog, text="Телефон", font=("Arial", 11)).grid(row=2, column=0, sticky='w', padx=10, pady=5)
            phone_entry = tk.Entry(dialog, width=40)
            phone_entry.insert(0, contact.get('phone', ''))
            phone_entry.grid(row=2, column=1, padx=10, pady=5)

            is_primary_var = tk.IntVar(value=1 if contact.get('is_primary') else 0)
            tk.Checkbutton(dialog, text="Основной контакт", variable=is_primary_var, bg='white').grid(row=3, column=1, sticky='w', padx=10, pady=5)

            def on_save():
                full_name = name_entry.get().strip()
                position = pos_entry.get().strip()
                phone = phone_entry.get().strip()
                is_primary = bool(is_primary_var.get())

                if not full_name:
                    messagebox.showerror("Ошибка", "ФИО контакта обязательно")
                    return

                try:
                    self.contact_persons_mgr.update(contact_id, full_name, position, phone, is_primary)
                    messagebox.showinfo("Успех", "Контакт обновлён")
                    dialog.destroy()
                    self._refresh_data()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось обновить контакт:\n{e}")

            btn_frame = tk.Frame(dialog)
            btn_frame.grid(row=10, column=0, columnspan=2, pady=10)
            tk.Button(btn_frame, text="Сохранить", command=on_save, bg="#007bff", fg='white').pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            center_toplevel(dialog)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть диалог редактирования контакта:\n{e}")

    def _edit_client(self, client, parent_window):
        """Диалог редактирования клиента с контактами"""
        # Проверяем, не открыто ли уже окно редактирования этого клиента
        client_id = client['id']
        if client_id in self.edit_client_dialogs:
            existing_dialog = self.edit_client_dialogs[client_id]
            if existing_dialog and tk.Toplevel.winfo_exists(existing_dialog):
                existing_dialog.lift()
                existing_dialog.focus_force()
                return

        # Создаём диалоговое окно
        dialog = tk.Toplevel(parent_window)
        dialog.title(f"Редактировать клиента: {client['company']}")
        dialog.geometry("750x750")
        dialog.configure(bg='white')
        dialog.resizable(False, False)
        center_toplevel(dialog)

        # Сохраняем ссылку на окно
        self.edit_client_dialogs[client_id] = dialog

        # Очищаем ссылку при закрытии
        def on_dialog_close():
            if client_id in self.edit_client_dialogs:
                del self.edit_client_dialogs[client_id]
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)

        # Заголовок
        header = tk.Frame(dialog, bg='#333333', height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="✏ Редактировать клиента",
            font=("Arial", 18, "bold"),
            fg='white',
            bg='#333333'
        ).pack(pady=15)

        # Кнопки (упаковываем первыми)
        buttons_container = tk.Frame(dialog, bg='#f0f0f0', height=80)
        buttons_container.pack(fill=tk.X, side=tk.BOTTOM)
        buttons_container.pack_propagate(False)

        buttons_frame = tk.Frame(buttons_container, bg='#f0f0f0')
        buttons_frame.pack(pady=15)

        # Canvas для прокрутки
        canvas_container = tk.Frame(dialog, bg='white')
        canvas_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(canvas_container, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)

        scrollable_content = tk.Frame(canvas, bg='white')

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_content.bind('<Configure>', on_frame_configure)

        canvas_window = canvas.create_window((0, 0), window=scrollable_content, anchor='nw')

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind('<Configure>', on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Основная информация ---
        tk.Label(scrollable_content, text="📋 Основная информация", font=("Arial", 14, "bold"), bg='white',
                 fg='#333').pack(anchor='w', padx=20, pady=(15, 10))

        info_frame = tk.Frame(scrollable_content, bg='white')
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        tk.Label(info_frame, text="Название компании *", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
        company_entry = tk.Entry(info_frame, font=("Arial", 11), relief="solid", borderwidth=1)
        company_entry.insert(0, client.get('company', ''))
        company_entry.pack(fill=tk.X, pady=(5, 15), ipady=5)

        tk.Label(info_frame, text="Адрес", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
        address_entry = tk.Entry(info_frame, font=("Arial", 11), relief="solid", borderwidth=1)
        address_entry.insert(0, client.get('address', ''))
        address_entry.pack(fill=tk.X, pady=(5, 15), ipady=5)

        tk.Label(info_frame, text="Примечания", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
        notes_text = tk.Text(info_frame, font=("Arial", 10), height=3, relief="solid", borderwidth=1, wrap=tk.WORD)
        notes_text.insert('1.0', client.get('notes', ''))
        notes_text.pack(fill=tk.X, pady=(5, 0))

        partner_fields = self._create_partner_fields(scrollable_content, client)

        # --- КОНТАКТНЫЕ ЛИЦА ---
        contacts_header_frame = tk.Frame(scrollable_content, bg='white')
        contacts_header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        tk.Label(contacts_header_frame, text="👥 Контактные лица", font=("Arial", 14, "bold"), bg='white',
                 fg='#333').pack(side=tk.LEFT)
        tk.Label(contacts_header_frame, text="(до 4, выберите основной)", font=("Arial", 10), bg='white',
                 fg='#999').pack(side=tk.LEFT, padx=10)

        contacts_container = tk.Frame(scrollable_content, bg='white')
        contacts_container.pack(fill=tk.X, padx=20, pady=(0, 10))

        contact_widgets = []
        primary_contact_var = tk.IntVar(value=0)

        def update_primary_contact_ui():
            """Обновляет отображение основного контакта"""
            selected_idx = primary_contact_var.get()

            for idx, widget in enumerate(contact_widgets):
                widget['radio'].config(text=f"Контакт #{idx + 1}")
                if idx == selected_idx:
                    widget['primary_label'].config(text="⭐ ОСНОВНОЙ", fg='#4CAF50')
                else:
                    widget['primary_label'].config(text="", fg='#999')

        def create_contact_fields(contact_data=None):
            """Создает поля для ввода контактного лица"""
            if len(contact_widgets) >= 4:
                show_message(dialog, "Внимание", "Максимум 4 контактных лица!", "warning")
                return

            idx = len(contact_widgets)

            contact_box = tk.Frame(contacts_container, bg='#f8f9fa', relief='solid', bd=1)
            contact_box.pack(fill=tk.X, pady=5)

            header_frame = tk.Frame(contact_box, bg='#f8f9fa')
            header_frame.pack(fill=tk.X, padx=10, pady=8)

            radio_btn = tk.Radiobutton(
                header_frame,
                text=f"Контакт #{idx + 1}",
                variable=primary_contact_var,
                value=idx,
                font=("Arial", 10, "bold"),
                bg='#f8f9fa',
                selectcolor='#4CAF50',
                command=update_primary_contact_ui
            )
            radio_btn.pack(side=tk.LEFT)

            primary_label = tk.Label(
                header_frame,
                text="",
                font=("Arial", 9, "bold"),
                bg='#f8f9fa'
            )
            primary_label.pack(side=tk.LEFT, padx=5)

            fields_frame = tk.Frame(contact_box, bg='#f8f9fa')
            fields_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

            tk.Label(fields_frame, text="ФИО:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
            name_entry = tk.Entry(fields_frame, font=("Arial", 10), relief="solid", borderwidth=1)
            name_entry.pack(fill=tk.X, pady=2, ipady=3)
            if contact_data:
                name_entry.insert(0, contact_data.get('full_name', ''))

            tk.Label(fields_frame, text="Должность:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
            position_entry = tk.Entry(fields_frame, font=("Arial", 10), relief="solid", borderwidth=1)
            position_entry.pack(fill=tk.X, pady=2, ipady=3)
            if contact_data:
                position_entry.insert(0, contact_data.get('position', ''))

            tk.Label(fields_frame, text="Телефон:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
            phone_entry = tk.Entry(fields_frame, font=("Arial", 10), relief="solid", borderwidth=1)
            phone_entry.pack(fill=tk.X, pady=2, ipady=3)
            if contact_data:
                phone_entry.insert(0, contact_data.get('phone', ''))

            tk.Label(fields_frame, text="Email:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
            email_entry = tk.Entry(fields_frame, font=("Arial", 10), relief="solid", borderwidth=1)
            email_entry.pack(fill=tk.X, pady=2, ipady=3)
            if contact_data:
                emails = contact_data.get('emails', [])
                email = next(
                    (item.get('email', '') for item in emails if item.get('is_primary')),
                    emails[0].get('email', '') if emails else contact_data.get('email', '')
                )
                email_entry.insert(0, email)

            # Создаем объект виджета контакта
            contact_widget = {
                'box': contact_box,
                'name': name_entry,
                'position': position_entry,
                'phone': phone_entry,
                'email': email_entry,
                'radio': radio_btn,
                'primary_label': primary_label,
                'id': contact_data.get('id') if contact_data else None
            }

            def remove_contact(widget=contact_widget):
                contact_box.destroy()
                if widget in contact_widgets:
                    contact_widgets.remove(widget)
                for i, w in enumerate(contact_widgets):
                    w['radio'].config(value=i, text=f"Контакт #{i + 1}")
                if primary_contact_var.get() >= len(contact_widgets):
                    if contact_widgets:
                        primary_contact_var.set(0)
                    else:
                        primary_contact_var.set(-1)
                update_primary_contact_ui()

            remove_btn = tk.Button(
                header_frame,
                text="✖",
                command=remove_contact,
                bg="#dc3545",
                fg="white",
                font=("Arial", 8),
                relief="flat",
                cursor="hand2"
            )
            remove_btn.pack(side=tk.RIGHT)

            contact_widgets.append(contact_widget)
            update_primary_contact_ui()

        # Загружаем существующие контакты
        existing_contacts = self.contact_persons_mgr.get_by_client_with_emails(client_id)
        if existing_contacts:
            for contact in existing_contacts:
                create_contact_fields(contact)
        else:
            create_contact_fields()

        add_contact_btn = tk.Button(
            contacts_container,
            text="+ Добавить контакт",
            command=create_contact_fields,
            bg="#28a745",
            fg="white",
            font=("Arial", 10),
            cursor="hand2"
        )
        add_contact_btn.pack(pady=5)

        # --- СОХРАНЕНИЕ ---
        def save_client():
            """Сохраняет изменения клиента через сервис"""
            form_data = {
                'company': company_entry.get().strip(),
                'address': address_entry.get().strip(),
                'notes': notes_text.get('1.0', 'end-1c').strip(),
                **self._collect_partner_fields(partner_fields),
                'contacts': []
            }

            for idx, w in enumerate(contact_widgets):
                contact_data = {
                    'id': w['id'],
                    'full_name': w['name'].get().strip(),
                    'position': w['position'].get().strip(),
                    'phone': w['phone'].get().strip(),
                    'email': w['email'].get().strip(),
                    'is_primary': (idx == primary_contact_var.get())
                }
                form_data['contacts'].append(contact_data)

            try:
                self.client_service.update_client_with_contacts(client_id, form_data)
                # Сначала обновляем таблицу
                self._refresh_data()
                card_view = getattr(parent_window, '_client_card_view', None)
                if card_view:
                    card_view.refresh()
                updated_client = self.clients_mgr.get_by_id(client_id)
                display_id = self.clients_mgr.get_display_id(updated_client) or client_id
                messagebox.showinfo("Успех", f"Клиент #{display_id} обновлен")
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e))
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить клиента: {e}")

        tk.Button(
            buttons_frame,
            text="💾 Сохранить",
            command=save_client,
            bg="#41a5be",
            fg="black",
            font=("Arial", 12, "bold"),
            padx=40, pady=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="✖ Отмена",
            command=dialog.destroy,
            bg="#6c757d",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=40, pady=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="📄 Карточка",
            command=lambda: self._load_client_card_into_form(
                dialog, company_entry, address_entry, partner_fields
            ),
            bg="#e9ecef",
            fg="#212529",
            font=("Arial", 12, "bold"),
            padx=40, pady=10
        ).pack(side=tk.LEFT, padx=10)

        def on_mw(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mw))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        company_entry.focus_set()
