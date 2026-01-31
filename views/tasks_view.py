"""
Представление раздела Задачи
"""
import tkinter as tk
from tkinter import ttk, messagebox
from views.base_view import BaseView
from datetime import date, datetime
from models.task import Task


class TasksView(BaseView):
    def __init__(self, parent_frame, tasks_mgr, clients_mgr):
        super().__init__(parent_frame)
        self.tasks_mgr = tasks_mgr
        self.clients_mgr = clients_mgr

        # Переменные для поиска и сортировки
        self.search_var = tk.StringVar()
        self.sort_var = tk.StringVar(value="Активные")

        self.search_job = None
        self.search_delay = 400

        # Создаём таблицу сразу при инициализации (как в clients_view)
        self._create_table_widgets()

    def _configure_columns(self, event=None):
        """Динамически настраивает ширину колонок задач"""
        width = self.tree.winfo_width()

        # Вычитаем ширину фиксированных колонок
        fixed_width = 80 + 120  # Статус + Срок
        remaining_width = width - fixed_width

        # Распределяем между растягиваемыми колонками (60% для названия, 40% для клиента)
        if remaining_width > 0:
            name_width = int(remaining_width * 0.6)
            client_width = int(remaining_width * 0.4)

            self.tree.column("Название", width=name_width, anchor="w", stretch=True)
            self.tree.column("Клиент", width=client_width, anchor="w", stretch=True)

    def _create_table_widgets(self):
        """Создаёт виджеты таблицы задач с чёрными вертикальными линиями"""
        self.table_container = tk.Frame(self.parent_frame, bg='white')

        # Создаём и настраиваем стиль как в clients_view
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
                        background="white",
                        foreground="#333",
                        rowheight=40,
                        fieldbackground="white",
                        borderwidth=0,
                        font=("Arial", 10))

        style.configure("Treeview.Heading",
                        background="#333333",
                        foreground="white",
                        font=("Arial", 10, "bold"),
                        padding=(10, 8),
                        borderwidth=1,
                        relief="flat")

        style.map("Treeview.Heading",
                  background=[("active", "#444444")])

        # Колонки
        columns = ("Статус", "Название", "Клиент", "Срок")
        self.tree = ttk.Treeview(
            self.table_container,
            columns=columns,
            show="headings",
            height=25,
            selectmode="browse"
        )

        # Настройка заголовков с растяжением
        self.tree.heading("Статус", text="Статус")
        self.tree.column("Статус", width=80, anchor="center", stretch=False)

        self.tree.heading("Название", text="Название задачи")
        self.tree.column("Название", width=350, anchor="w", stretch=True)  # stretch=True

        self.tree.heading("Клиент", text="Клиент")
        self.tree.column("Клиент", width=200, anchor="w", stretch=True)  # stretch=True

        self.tree.heading("Срок", text="Срок")
        self.tree.column("Срок", width=120, anchor="center", stretch=False)

        # Теги для визуального выделения
        self.tree.tag_configure('overdue', background='#FEE2E2')
        self.tree.tag_configure('even_row', background='#ffffff')
        self.tree.tag_configure('odd_row', background='#f8f9fa')
        self.tree.tag_configure('selected', background='#e8f4f8')

        # Скроллбар с кастомизацией как в clients_view
        scrollbar = ttk.Scrollbar(
            self.table_container,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Размещение
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # События
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-1>", self._on_single_click)

        # Обработчики событий для hover-эффекта
        self.tree.bind('<Enter>', self._on_tree_enter)
        self.tree.bind('<Leave>', self._on_tree_leave)
        self.tree.bind('<Motion>', self._on_tree_motion)

    def _refresh_list(self):
        """Обновляет список задач с учетом фильтра и поиска"""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Получаем задачи в зависимости от фильтра
        sort_option = self.sort_var.get()
        search_query = self.search_var.get().strip()

        if sort_option == "Активные":
            tasks = self.tasks_mgr.get_active_tasks()
        elif sort_option == "Неактивные":
            tasks = self.tasks_mgr.get_completed_tasks()
        elif sort_option == "Просроченные":
            tasks = self.tasks_mgr.get_overdue_tasks()
        else:  # "Все"
            tasks = self.tasks_mgr.get_all()

        # Применяем поиск, если есть запрос
        if search_query:
            tasks = [t for t in tasks if search_query.lower() in t.title.lower()]

        # Заполняем таблицу
        for idx, task in enumerate(tasks):
            # Определяем тег для строки
            row_tag = 'even_row' if idx % 2 == 0 else 'odd_row'

            # Проверяем на просроченность
            if task.due_date and task.due_date < date.today() and not task.completed:
                row_tag = 'overdue'

            # Получаем имя клиента
            client_name = "Без клиента"
            if task.client_id:
                client = self.clients_mgr.get_by_id(task.client_id)
                if client:
                    client_name = client.get('company', 'Без клиента')

            # Статус задачи
            status_icon = "✓" if task.completed else "◯"

            # Форматируем дату
            due_date = task.due_date.strftime("%d.%m.%Y") if task.due_date else ""

            values = (status_icon, task.title, client_name, due_date)
            self.tree.insert("", tk.END, values=values, tags=(row_tag,))

    def _on_search_change(self, *args):
        """Дебаунсинг поиска"""
        if self.search_job:
            self.parent_frame.after_cancel(self.search_job)
        self.search_job = self.parent_frame.after(self.search_delay, self._refresh_list)

    def _on_single_click(self, event):
        """Клик по чекбоксу статуса"""
        column = self.tree.identify_column(event.x)
        item_id = self.tree.identify_row(event.y)

        if column == "#1" and item_id:
            # Получаем данные из строки
            item_values = self.tree.item(item_id, 'values')
            if item_values:
                task_title = item_values[1]

                # Ищем задачу по названию
                tasks = self.tasks_mgr.get_all()
                for task in tasks:
                    if task.title == task_title:
                        # Меняем статус
                        new_status = not task.completed
                        self.tasks_mgr.update_task_status(task.id, new_status)

                        # Обновляем отображение
                        self._refresh_list()
                        break

    def _on_double_click(self, event):
        """Редактирование при двойном клике"""
        item_id = self.tree.identify_row(event.y)
        if item_id:
            # Получаем название задачи из таблицы
            item_values = self.tree.item(item_id, 'values')
            if item_values:
                task_title = item_values[1]
                # Ищем задачу по названию
                tasks = self.tasks_mgr.get_all()
                task = next((t for t in tasks if t.title == task_title), None)
                if task:
                    self._show_edit_dialog(task)

    def _on_tree_enter(self, event):
        """При входе в Treeview"""
        pass

    def _on_tree_leave(self, event):
        """При выходе из Treeview"""
        for item in self.tree.get_children():
            tags = list(self.tree.item(item, 'tags'))
            if 'selected' in tags:
                tags.remove('selected')
            self.tree.item(item, tags=tuple(tags))

    def _on_tree_motion(self, event):
        """При движении мыши над Treeview"""
        item_id = self.tree.identify_row(event.y)
        if item_id:
            for item in self.tree.get_children():
                tags = list(self.tree.item(item, 'tags'))
                if 'selected' in tags:
                    tags.remove('selected')
                self.tree.item(item, tags=tuple(tags))

            tags = list(self.tree.item(item_id, 'tags'))
            if 'selected' not in tags:
                tags.append('selected')
            self.tree.item(item_id, tags=tuple(tags))

    def show(self):
        """Отображение раздела"""
        self.clear()

        self._create_table_widgets()

        top_panel = tk.Frame(self.parent_frame, bg='#f0f0f0', height=70)
        top_panel.pack(fill=tk.X)
        top_panel.pack_propagate(False)

        # 1. Сортировка
        sort_frame = tk.Frame(top_panel, bg='#f3f4f6')
        sort_frame.pack(side=tk.LEFT, padx=(20, 10), pady=12)

        tk.Label(sort_frame, text="Фильтр:", bg='#f3f4f6', font=("Segoe UI", 9)).pack(side=tk.LEFT)

        sort_options = ["Активные", "Неактивные", "Все", "Просроченные"]
        sort_cb = ttk.Combobox(sort_frame, textvariable=self.sort_var, values=sort_options,
                               state="readonly", width=15)
        sort_cb.pack(side=tk.LEFT, padx=5)
        sort_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_list())

        # Кнопка добавления
        tk.Button(
            top_panel, text="+ Новая задача", command=self._show_add_dialog,
            bg="#41a5be", fg="black", font=("Arial", 11, "bold"), relief="flat", padx=20, pady=10, cursor="hand2"
        ).pack(side=tk.RIGHT, padx=20, pady=15)

        # Поиск
        search_frame = tk.Frame(top_panel, bg='#f0f0f0')
        search_frame.pack(side=tk.LEFT, expand=True, padx=20, pady=15)

        tk.Label(search_frame, text="🔍", font=("Arial", 14), bg='#f0f0f0', fg='#333').pack(side=tk.LEFT, padx=5)

        # Убедимся, что search_var существует
        if not hasattr(self, 'search_var'):
            self.search_var = tk.StringVar()

        self.search_var.trace_add("write", self._on_search_change)

        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=50, font=("Arial", 12),
                                relief="solid", borderwidth=1, bg='white', fg='#333')
        search_entry.pack(side=tk.LEFT, padx=5, ipady=8)

        # ИЗМЕНЕНИЕ: растягиваем таблицу на всё пространство
        self.table_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 0))
        self._refresh_list()

        # Привязываем изменение размера
        self.tree.bind('<Configure>', self._configure_columns)

    def _show_add_dialog(self):
        """Диалог создания задачи"""
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Новая задача")
        dialog.geometry("550x700")
        dialog.configure(bg='white')
        dialog.resizable(False, False)

        # Заголовок
        header = tk.Frame(dialog, bg='#333333', height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        tk.Label(header, text="➕ Новая задача", font=("Arial", 16, "bold"), fg='white', bg='#333333').pack(pady=15)

        # Контент
        content = tk.Frame(dialog, bg='white')
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # Название
        tk.Label(content, text="Что нужно сделать? *", font=("Arial", 10, "bold"), bg="white").pack(anchor='w')
        title_entry = tk.Entry(content, font=("Arial", 11), bg='#f8f9fa', relief="solid", bd=1)
        title_entry.pack(fill=tk.X, pady=(5, 15), ipady=5)

        # Клиент
        tk.Label(content, text="Клиент", font=("Arial", 10, "bold"), bg="white").pack(anchor='w')
        clients = self.clients_mgr.get_all()
        client_map = {c['company']: c['id'] for c in clients}
        client_names = sorted(list(client_map.keys()))

        client_cb = ttk.Combobox(content, values=client_names, state="readonly", font=("Arial", 10))
        client_cb.pack(fill=tk.X, pady=(5, 15), ipady=5)

        # Приоритет
        tk.Label(content, text="Приоритет", font=("Arial", 10, "bold"), bg="white").pack(anchor='w')
        priority_frame = tk.Frame(content, bg='white')
        priority_frame.pack(fill=tk.X, pady=(5, 15))

        priority_var = tk.StringVar(value="Средний")
        priorities = [("🔥 Высокий", "Высокий"), ("⚡ Средний", "Средний"), ("❄ Низкий", "Низкий")]

        for text, value in priorities:
            rb = tk.Radiobutton(priority_frame, text=text, variable=priority_var, value=value,
                                bg='white', activebackground='white', fg='#333', selectcolor='white',
                                font=("Arial", 10))
            rb.pack(side=tk.LEFT, padx=(0, 15))

        # Срок выполнения
        tk.Label(content, text="Срок выполнения", font=("Arial", 10, "bold"), bg="white").pack(anchor='w')

        date_frame = tk.Frame(content, bg='white')
        date_frame.pack(fill=tk.X, pady=(5, 15))

        date_entry = tk.Entry(date_frame, font=("Arial", 11), bg='#f8f9fa', relief="solid", bd=1)
        date_entry.insert(0, date.today().isoformat())
        date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)

        from datetime import timedelta

        def set_date_val(d):
            date_entry.delete(0, tk.END)
            date_entry.insert(0, d)

        # Кнопки даты
        tk.Button(date_frame, text="Сегодня", command=lambda: set_date_val(date.today().isoformat()),
                  bg="#e0e0e0", relief="flat").pack(side=tk.LEFT, padx=5)

        tk.Button(date_frame, text="Завтра",
                  command=lambda: set_date_val((date.today() + timedelta(days=1)).isoformat()),
                  bg="#e0e0e0", relief="flat").pack(side=tk.LEFT, padx=5)

        # Описание
        tk.Label(content, text="Подробное описание", font=("Arial", 10, "bold"), bg="white").pack(anchor='w')
        desc_entry = tk.Text(content, height=5, font=("Arial", 10), bg='#f8f9fa', relief="solid", bd=1)
        desc_entry.pack(fill=tk.X, pady=(5, 20))

        # Кнопки сохранения
        btn_frame = tk.Frame(content, bg='white')
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        def save():
            from utils.helpers import show_message
            title = title_entry.get().strip()
            if not title:
                show_message(dialog, "Внимание", "Введите название задачи", "warning")
                return

            client_name = client_cb.get()
            client_id = client_map.get(client_name) if client_name else None

            d_str = date_entry.get().strip()
            try:
                datetime.strptime(d_str, '%Y-%m-%d')
            except ValueError:
                show_message(dialog, "Ошибка", "Неверный формат даты! Используйте ГГГГ-ММ-ДД", "error")
                return

            try:
                self.tasks_mgr.add(
                    title=title,
                    description=desc_entry.get("1.0", "end-1c").strip(),
                    due_date=d_str,
                    client_id=client_id,
                    priority=priority_var.get()
                )
                show_message(dialog, "Успех", "Задача создана!", "success")
                dialog.destroy()
                self._refresh_list()
            except Exception as e:
                show_message(dialog, "Ошибка", str(e), "error")

        tk.Button(btn_frame, text="💾 Создать задачу", command=save, bg="#41a5be", fg="black",
                  font=("Arial", 11, "bold"), relief="flat", padx=20, pady=10).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Отмена", command=dialog.destroy, bg="#6c757d", fg="white",
                  font=("Arial", 11, "bold"), relief="flat", padx=20, pady=10).pack(side=tk.RIGHT)

    def _show_edit_dialog(self, task):
        """Окно редактирования с выбором клиента и удалением"""
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Редактирование задачи")
        dialog.geometry("500x680")
        dialog.configure(bg='white')
        dialog.resizable(False, False)
        dialog.grab_set()

        # Шапка
        header = tk.Frame(dialog, bg='#374151', height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="✏️ Редактировать задачу", fg='white', bg='#374151',
                 font=("Segoe UI", 12, "bold")).pack(pady=15)

        body = tk.Frame(dialog, bg='white', padx=30, pady=20)
        body.pack(fill=tk.BOTH, expand=True)

        # 1. Название
        tk.Label(body, text="Название задачи *", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        title_ent = tk.Entry(body, font=("Segoe UI", 11), relief="solid", bd=1)
        title_ent.insert(0, task.title)
        title_ent.pack(fill=tk.X, pady=(5, 15), ipady=5)

        # 2. ВЫБОР КЛИЕНТА
        tk.Label(body, text="Клиент / Компания", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        all_clients = self.clients_mgr.get_all()
        client_map = {c['company']: c['id'] for c in all_clients}
        client_names = ["Без клиента"] + sorted(list(client_map.keys()))

        client_cb = ttk.Combobox(body, values=client_names, state="readonly", font=("Segoe UI", 10))
        client_cb.pack(fill=tk.X, pady=(5, 15), ipady=5)

        # Устанавливаем текущего клиента
        current_client = "Без клиента"
        if task.client_id:
            client = self.clients_mgr.get_by_id(task.client_id)
            if client and 'company' in client:
                current_client = client['company']

        client_cb.set(current_client if current_client in client_names else "Без клиента")

        # 3. Приоритет
        tk.Label(body, text="Приоритет", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        p_var = tk.StringVar(value=task.priority)
        p_frame = tk.Frame(body, bg='white')
        p_frame.pack(fill=tk.X, pady=10)
        for p in ["Высокий", "Средний", "Низкий"]:
            tk.Radiobutton(p_frame, text=p, variable=p_var, value=p, bg='white', cursor="hand2").pack(side=tk.LEFT,
                                                                                                      padx=10)

        # 4. Описание
        tk.Label(body, text="Описание", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        desc_txt = tk.Text(body, height=4, font=("Segoe UI", 10), relief="solid", bd=1)
        desc_txt.insert("1.0", task.description if task.description else "")
        desc_txt.pack(fill=tk.X, pady=(5, 20))

        # ПОДВАЛ С КНОПКАМИ
        footer = tk.Frame(body, bg='white')
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        def save():
            sel_client = client_cb.get()
            cid = client_map.get(sel_client) if sel_client != "Без клиента" else None

            self.tasks_mgr.update_task(
                task_id=task.id,
                title=title_ent.get().strip(),
                description=desc_txt.get("1.0", "end-1c").strip(),
                priority=p_var.get(),
                client_id=cid,
                status=task.completed,
                due_date=task.due_date
            )
            dialog.destroy()
            self._refresh_list()

        tk.Button(footer, text="💾 Сохранить", bg="#10B981", fg="white", font=("Segoe UI", 10, "bold"),
                  padx=20, pady=8, relief="flat", cursor="hand2", command=save).pack(side=tk.LEFT)

        tk.Button(footer, text="🗑 Удалить задачу", bg="#EF4444", fg="white", font=("Segoe UI", 10, "bold"),
                  padx=15, pady=8, relief="flat", cursor="hand2",
                  command=lambda: [self._delete_task(task), dialog.destroy()]).pack(side=tk.RIGHT)

    @staticmethod
    def create_task_for_client(parent, tasks_mgr, clients_mgr, client_id):
        """Статический метод для создания задачи для конкретного клиента"""
        try:
            dialog = tk.Toplevel(parent)
            dialog.title("Новая задача для клиента")
            dialog.geometry("550x600")
            dialog.configure(bg='white')
            dialog.resizable(False, False)

            # Заголовок
            header = tk.Frame(dialog, bg='#333333', height=60)
            header.pack(fill=tk.X)
            tk.Label(header, text="➕ Новая задача", font=("Arial", 16, "bold"),
                     fg='white', bg='#333333').pack(pady=15)

            # Контент
            content = tk.Frame(dialog, bg='white')
            content.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

            # Название
            tk.Label(content, text="Что нужно сделать? *",
                     font=("Arial", 10, "bold"), bg="white").pack(anchor='w')
            title_entry = tk.Entry(content, font=("Arial", 11),
                                   bg='#f8f9fa', relief="solid", bd=1)
            title_entry.pack(fill=tk.X, pady=(5, 15), ipady=5)

            # Приоритет
            tk.Label(content, text="Приоритет",
                     font=("Arial", 10, "bold"), bg="white").pack(anchor='w')
            priority_frame = tk.Frame(content, bg='white')
            priority_frame.pack(fill=tk.X, pady=(5, 15))

            priority_var = tk.StringVar(value="Средний")
            priorities = [("🔥 Высокий", "Высокий"),
                          ("⚡ Средний", "Средний"),
                          ("❄ Низкий", "Низкий")]

            for text, value in priorities:
                rb = tk.Radiobutton(priority_frame, text=text,
                                    variable=priority_var, value=value,
                                    bg='white', fg='#333',
                                    font=("Arial", 10))
                rb.pack(side=tk.LEFT, padx=(0, 15))

            # Срок
            tk.Label(content, text="Срок выполнения",
                     font=("Arial", 10, "bold"), bg="white").pack(anchor='w')
            date_entry = tk.Entry(content, font=("Arial", 11),
                                  bg='#f8f9fa', relief="solid", bd=1)
            date_entry.insert(0, date.today().isoformat())
            date_entry.pack(fill=tk.X, pady=(5, 15), ipady=5)

            # Описание
            tk.Label(content, text="Подробное описание",
                     font=("Arial", 10, "bold"), bg="white").pack(anchor='w')
            desc_entry = tk.Text(content, height=4, font=("Arial", 10),
                                 bg='#f8f9fa', relief="solid", bd=1)
            desc_entry.pack(fill=tk.X, pady=(5, 20))

            def save():
                from utils.helpers import show_message
                title = title_entry.get().strip()
                if not title:
                    show_message(dialog, "Внимание", "Введите название задачи", "warning")
                    return

                d_str = date_entry.get().strip()
                try:
                    datetime.strptime(d_str, '%Y-%m-%d')
                except ValueError:
                    show_message(dialog, "Ошибка", "Неверный формат даты!", "error")
                    return

                try:
                    tasks_mgr.add(
                        title=title,
                        description=desc_entry.get("1.0", "end-1c").strip(),
                        due_date=d_str,
                        client_id=client_id,
                        priority=priority_var.get()
                    )
                    show_message(dialog, "Успех", "Задача создана!", "success")
                    dialog.destroy()
                except Exception as e:
                    show_message(dialog, "Ошибка", str(e), "error")

            # Кнопки
            btn_frame = tk.Frame(content, bg='white')
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            tk.Button(btn_frame, text="💾 Создать", command=save,
                      bg="#41a5be", fg="black", font=("Arial", 11, "bold"),
                      relief="flat", padx=20, pady=10).pack(side=tk.LEFT)
            tk.Button(btn_frame, text="Отмена", command=dialog.destroy,
                      bg="#6c757d", fg="white", font=("Arial", 11, "bold"),
                      relief="flat", padx=20, pady=10).pack(side=tk.RIGHT)

        except Exception as e:
            print(f"Ошибка при создании диалога задачи: {e}")

    def _delete_task(self, task):
        """Удалить задачу"""
        from utils.helpers import show_confirmation, show_message

        confirm = show_confirmation(
            self.parent_frame,
            "Подтверждение удаления",
            f"Удалить задачу '{task.title}'?"
        )

        if confirm:
            try:
                self.tasks_mgr.delete(task.id)
                show_message(self.parent_frame, "Успех", "Задача удалена", "success")
                self._refresh_list()
            except Exception as e:
                show_message(self.parent_frame, "Ошибка", f"Не удалось удалить задачу: {e}", "error")

    def clear(self):
        """Очищает раздел задач"""
        for widget in self.parent_frame.winfo_children():
            widget.destroy()

        self.table_container = None
        self.tree = None