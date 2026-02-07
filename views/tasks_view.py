# -*- coding: utf-8 -*-
"""
Представление раздела "Задачи" на базе TableViewTemplate
"""
import tkinter as tk
from tkinter import ttk, messagebox
from views.table_view_template import TableViewTemplate
from utils.helpers import show_message
from utils.constants import TableView, TaskPriorities, get_priority_icon, Sizes
from datetime import date, datetime
from models.task import Task
from views.calendar_view import CalendarDialog


class SearchableCombobox:
    """Комбобокс с поиском и автодополнением"""
    
    def __init__(self, parent, values=None, font=("Arial", 11), **kwargs):
        self.parent = parent
        self.values = values or []
        self.filtered_values = self.values.copy()
        self.listbox_visible = False
        
        # Создаем frame для entry
        self.frame = tk.Frame(parent, bg='white')
        
        # Entry для ввода с поиском
        self.var = tk.StringVar()
        self.entry = tk.Entry(
            self.frame,
            textvariable=self.var,
            font=font,
            relief="solid",
            borderwidth=1,
            **kwargs
        )
        self.entry.pack(fill=tk.X, expand=True)
        
        # Listbox для отображения результатов (создается в родительском окне)
        self.listbox_frame = tk.Toplevel(parent)
        self.listbox_frame.withdraw()  # Изначально скрыт
        self.listbox_frame.overrideredirect(True)  # Убираем рамку окна
        
        self.listbox = tk.Listbox(
            self.listbox_frame,
            font=font,
            bg='white',
            selectbackground='#41a5be',
            selectforeground='white',
            height=6,
            relief="solid",
            borderwidth=1,
            highlightthickness=0
        )
        
        # Scrollbar для списка
        scrollbar = tk.Scrollbar(self.listbox_frame, orient="vertical")
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязываем события
        self.var.trace('w', self._on_type)
        self.entry.bind('<FocusIn>', self._on_focus_in)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<KeyRelease>', self._on_key_release)
        self.entry.bind('<Return>', self._on_select)
        self.entry.bind('<Escape>', self._hide_list)
        self.entry.bind('<Down>', self._on_down)
        self.entry.bind('<Up>', self._on_up)
        self.listbox.bind('<Button-1>', self._on_listbox_click)
        self.listbox.bind('<Return>', self._on_select)
        self.listbox.bind('<Escape>', self._hide_list)
        
        # Глобальная привязка для скрытия при клике вне
        self.listbox_frame.bind('<FocusOut>', self._on_focus_out)
        
    def _on_type(self, *args):
        """Фильтрация при вводе текста"""
        text = self.var.get().lower()
        
        if not text:
            self.filtered_values = self.values.copy()
        else:
            self.filtered_values = [
                val for val in self.values 
                if text in val.lower()
            ]
        
        self._update_listbox()
        if self.filtered_values:
            self._show_list()
        else:
            self._hide_list()
        
    def _update_listbox(self):
        """Обновление содержимого listbox"""
        self.listbox.delete(0, tk.END)
        for value in self.filtered_values:
            self.listbox.insert(tk.END, value)
            
    def _show_list(self):
        """Показать список"""
        if not self.filtered_values:
            return
            
        # Позиционируем список под entry
        try:
            x = self.entry.winfo_rootx()
            y = self.entry.winfo_rooty() + self.entry.winfo_height()
            width = self.entry.winfo_width()
            
            self.listbox_frame.geometry(f"{width}x{min(150, len(self.filtered_values) * 25)}+{x}+{y}")
            self.listbox_frame.deiconify()
            self.listbox_frame.lift()
            self.listbox_visible = True
        except:
            pass
            
    def _hide_list(self, event=None):
        """Скрыть список"""
        try:
            self.listbox_frame.withdraw()
            self.listbox_visible = False
        except:
            pass
        
    def _on_focus_in(self, event=None):
        """При получении фокуса"""
        if self.var.get():
            self._show_list()
            
    def _on_focus_out(self, event=None):
        """При потере фокуса"""
        # Задержка чтобы успеть кликнуть на список
        self.parent.after(150, self._hide_list)
        
    def _on_key_release(self, event):
        """При отпускании клавиши"""
        if event.keysym in ('Up', 'Down', 'Return', 'Escape'):
            return
        self._on_type()
        
    def _on_down(self, event):
        """Стрелка вниз"""
        if not self.listbox_visible:
            self._show_list()
        else:
            current = self.listbox.curselection()
            if current:
                next_index = (current[0] + 1) % len(self.filtered_values)
            else:
                next_index = 0
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(next_index)
            self.listbox.see(next_index)
        return "break"
        
    def _on_up(self, event):
        """Стрелка вверх"""
        if self.listbox_visible:
            current = self.listbox.curselection()
            if current:
                prev_index = (current[0] - 1) % len(self.filtered_values)
            else:
                prev_index = len(self.filtered_values) - 1
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(prev_index)
            self.listbox.see(prev_index)
        return "break"
        
    def _on_select(self, event=None):
        """Выбор элемента"""
        selection = self.listbox.curselection()
        if selection:
            selected_value = self.listbox.get(selection[0])
            self.var.set(selected_value)
        self._hide_list()
        
    def _on_listbox_click(self, event=None):
        """Клик по элементу списка"""
        self._on_select()
        
    def get(self):
        """Получить текущее значение"""
        return self.var.get()
        
    def set(self, value):
        """Установить значение"""
        self.var.set(value)
        
    def pack(self, **kwargs):
        """Упаковка основного frame"""
        self.frame.pack(**kwargs)
        
    def pack_side(self, side=tk.LEFT, **kwargs):
        """Упаковка на стороне"""
        self.frame.pack(side=side, **kwargs)


class TasksView(TableViewTemplate):
    """Раздел задач с поиском, сортировкой и пагинацией"""

    TITLE = "Задачи"
    ADD_BUTTON_TEXT = "+ Добавить задачу"
    SEARCH_FIELDS_TEXT = "названию, описанию, клиенту"
    COLUMNS = ("ID", "Статус", "Название", "Клиент", "Приоритет", "Срок")
    COLUMN_WIDTHS = {
        "ID": 50,
        "Статус": 80,
        "Название": 180,
        "Клиент": 150,
        "Приоритет": 100,
        "Срок": 100
    }
    STRETCH_COLUMNS = ["Название", "Клиент"]
    ID_COLUMN = "ID"
    SORT_OPTIONS = [
        ("due_date", "По сроку (ближайшие)"),
        ("due_date:DESC", "По сроку (дальние)"),
        ("title", "По названию (А-Я)"),
        ("title:DESC", "По названию (Я-А)"),
        ("priority", "По приоритету (высокий→низкий)"),
        ("priority:DESC", "По приоритету (низкий→высокий)"),
        ("status", "По статусу (активные)"),
        ("status:DESC", "По статусу (выполненные)"),
        ("created_date", "По дате создания (новые)"),
        ("created_date:DESC", "По дате создания (старые)")
    ]
    PAGE_SIZE = 50

    def __init__(self, parent_frame, tasks_mgr, clients_mgr):
        super().__init__(parent_frame, tasks_mgr)
        self.tasks_mgr = tasks_mgr
        self.clients_mgr = clients_mgr

    def _on_tree_enter(self, event):
        pass

    def _on_tree_leave(self, event):
        pass

    def _on_tree_motion(self, event):
        pass

    def _create_table(self):
        """Создаёт Treeview таблицу с дополнительной обработкой клика на статус"""
        # Вызываем родительский метод
        super()._create_table()
        
        # Добавляем обработку одинарного клика на статус
        self.tree.bind('<Button-1>', self._on_single_click)

    def _create_ui(self):
        """Создаёт весь интерфейс с улучшенной сортировкой и фильтрами"""
        # Вызываем родительский метод для базового создания
        super()._create_ui()
        
        # Теперь добавляем наши элементы фильтрации
        # Находим верхнюю панель
        top_panel = None
        for widget in self.parent_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                # Проверяем высоту (верхняя панель обычно ~70px)
                try:
                    if widget.winfo_height() == Sizes.TOP_PANEL_HEIGHT or widget.winfo_reqheight() == Sizes.TOP_PANEL_HEIGHT:
                        top_panel = widget
                        break
                except:
                    # Если не можем определить высоту, берем первый Frame
                    if top_panel is None:
                        top_panel = widget
        
        if not top_panel:
            return
        
        # Находим контейнер с поиском для добавления наших элементов
        search_container = None
        for widget in top_panel.winfo_children():
            if isinstance(widget, tk.Frame):
                search_container = widget
                break
        
        if not search_container:
            return
        
        # Добавляем фильтр статуса
        tk.Label(
            search_container,
            text="Статус:",
            font=TableView.LABEL_FONT,
            bg=TableView.TOP_PANEL_BG,
            fg=TableView.LABEL_FG
        ).pack(side=tk.LEFT, padx=(15, 5), pady=Sizes.TOP_PANEL_PADDING_Y)
        
        self.status_filter_var = tk.StringVar(value="Активные")
        status_combo = ttk.Combobox(
            search_container,
            textvariable=self.status_filter_var,
            values=["Все", "Активные", "Выполненные"],
            state="readonly",
            width=12,
            font=TableView.LABEL_FONT
        )
        status_combo.pack(side=tk.LEFT, padx=5, pady=Sizes.TOP_PANEL_PADDING_Y)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_data())

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
            
        # Проверяем что кликнули на колонку "Статус" (вторая колонка)
        if column == "#2":  # #2 это вторая колонка (ID, Статус, ...)
            # Получаем ID задачи из первой колонки
            values = self.tree.item(item, 'values')
            if not values:
                return
                
            try:
                task_id = int(values[0])
                self._toggle_task_status(task_id)
            except (ValueError, IndexError):
                pass

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
        elif sort_by == "created_date":
            # Если у задач есть поле created_date, используем его, иначе текущую дату
            tasks.sort(key=lambda x: getattr(x, 'created_date', date.min), reverse=reverse)
            
        return tasks

    def _item_to_row_values(self, item):
        """Преобразует задачу в строку таблицы"""
        if not isinstance(item, Task):
            return ("", "", "", "", "", "")
        
        # Статус
        status_icon = "✓" if item.completed else "◯"
        
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
        due_date = item.due_date.strftime("%d.%m.%Y") if item.due_date else ""
        
        return (
            str(item.id),
            status_icon,
            item.title,
            client_name,
            priority_display,
            due_date
        )

    def _open_create_dialog(self):
        """Диалог создания задачи"""
        dialog, content, buttons_frame = self._create_dialog(
            "➕ Новая задача", 
            "600x550"
        )
        
        # Основная информация
        main_fields = self._create_form_section(content, "📋 Основная информация", [
            {'name': 'title', 'label': 'Название задачи', 'type': 'entry', 'required': True},
            {'name': 'description', 'label': 'Описание', 'type': 'text', 'required': False, 'height': 4}
        ])
        
        # Дополнительная информация
        additional_fields = self._create_form_section(content, "⚙ Дополнительные параметры", [
            {
                'name': 'priority', 
                'label': 'Приоритет', 
                'type': 'combobox', 
                'required': False,
                'options': TaskPriorities.ALL,
                'default': TaskPriorities.MEDIUM
            }
        ])
        
        # Кастомное поле для клиента с поиском
        client_frame = tk.Frame(content, bg='white')
        client_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        tk.Label(
            client_frame,
            text="Клиент",
            font=("Arial", 10),
            bg='white',
            fg='#333'
        ).pack(anchor='w')
        
        client_input_frame = tk.Frame(client_frame, bg='white')
        client_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        client_var = tk.StringVar(value="Без клиента")
        client_combo = SearchableCombobox(
            client_input_frame,
            values=self._get_client_options(),
            font=("Arial", 11)
        )
        client_combo.pack_side(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Поле даты с календарем
        date_frame = tk.Frame(content, bg='white')
        date_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Label(
            date_frame,
            text="Срок выполнения",
            font=("Arial", 10),
            bg='white',
            fg='#333'
        ).pack(anchor='w')
        
        date_input_frame = tk.Frame(date_frame, bg='white')
        date_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        due_date_var = tk.StringVar(value=date.today().strftime("%d.%m.%Y"))
        due_date_entry = tk.Entry(
            date_input_frame,
            textvariable=due_date_var,
            font=("Arial", 11),
            relief="solid",
            borderwidth=1
        )
        due_date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def show_calendar():
            """Показать календарь для выбора даты"""
            cal_dialog = CalendarDialog(dialog, "Выберите срок выполнения")
            selected_date = cal_dialog.show()
            if selected_date:
                due_date_var.set(selected_date.strftime("%d.%m.%Y"))
        
        tk.Button(
            date_input_frame,
            text="📅",
            command=show_calendar,
            bg="#41a5be",
            fg="white",
            font=("Arial", 10),
            width=3
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        def save_task():
            """Сохранение новой задачи"""
            try:
                # Валидация
                title = main_fields['title'].get().strip()
                if not title:
                    show_message(dialog, "Ошибка", "Укажите название задачи", "error")
                    return
                
                # Сбор данных
                description = main_fields['description'].get('1.0', tk.END).strip()
                
                # Клиент
                client_name = client_var.get()
                client_id = None
                if client_name and client_name != "Без клиента":
                    all_clients = self.clients_mgr.get_all()
                    for client in all_clients:
                        if client.get('company') == client_name:
                            client_id = client.get('id')
                            break
                
                # Приоритет
                priority = additional_fields['priority'].get() or TaskPriorities.MEDIUM
                
                # Срок
                due_date_str = due_date_var.get().strip()
                due_date = None
                if due_date_str:
                    try:
                        due_date = datetime.strptime(due_date_str, "%d.%m.%Y").date()
                    except ValueError:
                        show_message(dialog, "Ошибка", "Неверный формат даты. Используйте ДД.ММ.ГГГГ", "error")
                        return
                
                # Создаем задачу через менеджер с отдельными параметрами
                self.tasks_mgr.add(
                    title=title,
                    description=description,
                    priority=priority,
                    client_id=client_id,
                    due_date=due_date
                )
                
                show_message(dialog, "Успех", "Задача успешно создана!", "success")
                dialog.destroy()
                self._refresh_data()
                
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
        """Диалог редактирования задачи"""
        try:
            task = self.tasks_mgr.get_by_id(task_id)
            if not task:
                show_message(self.parent_frame, "Ошибка", f"Задача с ID {task_id} не найдена", "error")
                return

            dialog, content, buttons_frame = self._create_dialog(
                f"✏️ Редактирование: {task.title}",
                "600x600"
            )

            # Основная информация
            main_fields = self._create_form_section(content, "📋 Основная информация", [
                {
                    'name': 'title',
                    'label': 'Название задачи',
                    'type': 'entry',
                    'required': True,
                    'default': task.title
                },
                {
                    'name': 'description',
                    'label': 'Описание',
                    'type': 'text',
                    'required': False,
                    'height': 4,
                    'default': task.description or ''
                }
            ])

            # Дополнительная информация
            additional_fields = self._create_form_section(content, "⚙ Дополнительные параметры", [
                {
                    'name': 'priority',
                    'label': 'Приоритет',
                    'type': 'combobox',
                    'required': False,
                    'options': TaskPriorities.ALL,
                    'default': task.priority or TaskPriorities.MEDIUM
                }
            ])
            
            # Кастомное поле для клиента с поиском
            client_frame = tk.Frame(content, bg='white')
            client_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
            
            tk.Label(
                client_frame,
                text="Клиент",
                font=("Arial", 10),
                bg='white',
                fg='#333'
            ).pack(anchor='w')
            
            client_input_frame = tk.Frame(client_frame, bg='white')
            client_input_frame.pack(fill=tk.X, pady=(5, 0))
            
            edit_client_var = tk.StringVar(value=self._get_current_client_name(task))
            edit_client_combo = SearchableCombobox(
                client_input_frame,
                values=self._get_client_options(),
                font=("Arial", 11)
            )
            edit_client_combo.pack_side(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Поле даты с календарем
            date_frame = tk.Frame(content, bg='white')
            date_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
            
            tk.Label(
                date_frame,
                text="Срок выполнения",
                font=("Arial", 10),
                bg='white',
                fg='#333'
            ).pack(anchor='w')
            
            date_input_frame = tk.Frame(date_frame, bg='white')
            date_input_frame.pack(fill=tk.X, pady=(5, 0))
            
            edit_due_date_var = tk.StringVar(value=task.due_date.strftime("%d.%m.%Y") if task.due_date else "")
            edit_due_date_entry = tk.Entry(
                date_input_frame,
                textvariable=edit_due_date_var,
                font=("Arial", 11),
                relief="solid",
                borderwidth=1
            )
            edit_due_date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            def show_edit_calendar():
                """Показать календарь для выбора даты"""
                cal_dialog = CalendarDialog(dialog, "Выберите срок выполнения")
                selected_date = cal_dialog.show()
                if selected_date:
                    edit_due_date_var.set(selected_date.strftime("%d.%m.%Y"))
            
            tk.Button(
                date_input_frame,
                text="📅",
                command=show_edit_calendar,
                bg="#41a5be",
                fg="white",
                font=("Arial", 10),
                width=3
            ).pack(side=tk.RIGHT, padx=(5, 0))

            # Статус выполнения
            status_frame = tk.Frame(content, bg='white')
            status_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
            
            completed_var = tk.BooleanVar(value=task.completed)
            tk.Checkbutton(
                status_frame,
                text="✓ Задача выполнена",
                variable=completed_var,
                bg='white',
                font=("Arial", 11, "bold")
            ).pack(anchor='w')

            def save_task():
                """Сохранение изменений"""
                try:
                    # Валидация
                    title = main_fields['title'].get().strip()
                    if not title:
                        show_message(dialog, "Ошибка", "Укажите название задачи", "error")
                        return

                    # Сбор данных
                    description = main_fields['description'].get('1.0', tk.END).strip()
                    
                    # Клиент
                    client_name = edit_client_var.get()
                    client_id = None
                    if client_name and client_name != "Без клиента":
                        all_clients = self.clients_mgr.get_all()
                        for client in all_clients:
                            if client.get('company') == client_name:
                                client_id = client.get('id')
                                break

                    # Приоритет
                    priority = additional_fields['priority'].get() or TaskPriorities.MEDIUM

                    # Срок
                    due_date_str = edit_due_date_var.get().strip()
                    due_date = None
                    if due_date_str:
                        try:
                            due_date = datetime.strptime(due_date_str, "%d.%m.%Y").date()
                        except ValueError:
                            show_message(dialog, "Ошибка", "Неверный формат даты. Используйте ДД.ММ.ГГГГ", "error")
                            return

                    # Обновляем задачу через менеджер
                    self.tasks_mgr.update_task(
                        task_id=task_id,
                        title=title,
                        description=description,
                        status=completed_var.get(),
                        priority=priority,
                        due_date=due_date,
                        client_id=client_id
                    )

                    show_message(dialog, "Успех", "Изменения сохранены!", "success")
                    dialog.destroy()
                    self._refresh_data()

                except Exception as e:
                    show_message(dialog, "Ошибка", f"Произошла ошибка: {str(e)}", "error")

            def delete_task():
                """Удаление задачи"""
                if messagebox.askyesno("Подтверждение", "Удалить задачу?", parent=dialog):
                    self.tasks_mgr.delete(task_id)
                    show_message(dialog, "Успех", "Задача удалена!", "success")
                    dialog.destroy()
                    self._refresh_data()

            # Кнопки
            tk.Button(
                buttons_frame,
                text="💾 Сохранить",
                command=save_task,
                bg="#28a745",
                fg="white",
                font=("Arial", 12, "bold"),
                cursor="hand2",
                padx=20,
                pady=10
            ).pack(side=tk.LEFT, padx=5)

            tk.Button(
                buttons_frame,
                text="🗑️ Удалить",
                command=delete_task,
                bg="#dc3545",
                fg="white",
                font=("Arial", 12, "bold"),
                cursor="hand2",
                padx=20,
                pady=10
            ).pack(side=tk.LEFT, padx=5)

            tk.Button(
                buttons_frame,
                text="✖ Отмена",
                command=dialog.destroy,
                bg="#6c757d",
                fg="white",
                font=("Arial", 12, "bold"),
                cursor="hand2",
                padx=20,
                pady=10
            ).pack(side=tk.LEFT, padx=5)

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
