"""
Представление списка клиентов
"""
import tkinter as tk
from tkinter import ttk, messagebox
from views.base_view import BaseView
from datetime import date
from utils.helpers import show_message, show_confirmation


class ClientsView(BaseView):
    """
    Класс для отображения списка клиентов
    """

    def __init__(self, parent_frame, clients_mgr, contact_persons_mgr, contact_emails_mgr, interactions_mgr, tasks_mgr=None):
        super().__init__(parent_frame)
        self.clients_mgr = clients_mgr
        self.contact_persons_mgr = contact_persons_mgr
        self.contact_emails_mgr = contact_emails_mgr
        self.interactions_mgr = interactions_mgr
        self.tasks_mgr = tasks_mgr

        # Инициализация атрибутов для поиска
        self.search_job = None
        self.search_delay = 300  # 300 мс задержка

        if contact_emails_mgr is None:
            print("Внимание: contact_emails_mgr не передан")

    def _configure_columns(self, event=None):
        """Динамически настраивает ширину колонок"""
        # Получаем ширину таблицы
        width = self.tree.winfo_width()

        # Вычитаем ширину фиксированных колонок
        fixed_width = 50 + 100  # ID + Задачи
        remaining_width = width - fixed_width

        # Распределяем оставшуюся ширину между растягиваемыми колонками
        stretchable_columns = ["Компания", "Контактное лицо", "Должность", "Телефон", "Адрес"]
        column_width = max(150, remaining_width // len(stretchable_columns))

        for col in stretchable_columns:
            self.tree.column(col, width=column_width, anchor='w', stretch=True)

    def _create_table_widgets(self):
        """Создаёт виджеты таблицы со стилизацией под старый дизайн"""
        self.table_container = tk.Frame(self.parent_frame, bg='white')

        # Создаём Treeview
        columns = ("ID", "Компания", "Контактное лицо", "Должность", "Телефон", "Адрес", "Задачи")
        self.tree = ttk.Treeview(
            self.table_container,
            columns=columns,
            show="headings",  # Убираем "дерево" слева
            height=25,
            selectmode="browse"
        )
        # Убираем стандартные границы и полосы выделения
        style = ttk.Style()
        style.theme_use("clam")  # Более гибкая тема для кастомизации

        # Настраиваем стиль для Treeview
        style.configure("Treeview",
                        background="white",
                        foreground="#333",
                        rowheight=40,  # Высота строки как в старом дизайне
                        fieldbackground="white",
                        borderwidth=0,
                        font=("Arial", 10))

        style.configure("Treeview.Heading",
                        background="#333333",  # Тёмный фон заголовков
                        foreground="white",
                        font=("Arial", 10, "bold"),
                        padding=(10, 8),  # Отступы как в старом дизайне
                        borderwidth=1,
                        relief="flat")

        style.map("Treeview.Heading",
                  background=[("active", "#444444")])

        # Настройка заголовков
        for col in columns:
            self.tree.heading(col, text=col)
            # Настраиваем выравнивание и растяжение
            if col == "ID":
                self.tree.column(col, width=50, anchor='center', stretch=False)
            elif col == "Задачи":
                self.tree.column(col, width=100, anchor='center', stretch=False)
            else:  # Все остальные колонки растягиваем
                self.tree.column(col, width=150, anchor='w', stretch=True)  # stretch=True

        # Убираем стандартные разделители
        self.tree.configure(style="Treeview")

        # ✅ ВОССТАНОВЛЕННЫЙ МЕТОД
        self.tree.bind('<Double-Button-1>', self._on_table_double_click)
        self.tree.bind('<Button-1>', self._on_table_single_click)

        # Создаём свои теги для строк
        self.tree.tag_configure('evenrow', background='#f8f9fa')
        self.tree.tag_configure('oddrow', background='white')
        self.tree.tag_configure('selected', background='#e8f4f8')  # Цвет при наведении

        # Настраиваем полосу прокрутки
        scrollbar = ttk.Scrollbar(
            self.table_container,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Размещение
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Обработчики событий для hover-эффекта
        self.tree.bind('<Enter>', self._on_tree_enter)
        self.tree.bind('<Leave>', self._on_tree_leave)
        self.tree.bind('<Motion>', self._on_tree_motion)

    def _on_table_double_click(self, event):
        """Обработка двойного клика по строке таблицы (открытие карточки)"""
        try:
            item = self.tree.identify_row(event.y)
            if not item:
                return

            values = self.tree.item(item, 'values')
            if values and len(values) > 0:
                client_id = int(values[0])
                self._open_client_card_by_id(client_id)

        except Exception as e:
            print(f"Ошибка при двойном клике: {e}")

    def _on_table_single_click(self, event):
        """Обработка обычного клика по таблице (для кнопки 'Задачи')"""
        try:
            # Определяем, куда кликнули
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            if not item or not column:
                return

            # Только если кликнули по колонке "Задачи" (#7)
            if column == '#7':
                # Получаем ID клиента
                values = self.tree.item(item, 'values')
                if values and len(values) > 0:
                    client_id = int(values[0])
                    self._create_task_for_client(client_id)

        except Exception as e:
            print(f"Ошибка при обработке клика: {e}")

    def clear(self):
        """Очищает раздел клиентов"""
        # Получаем все виджеты в родительском фрейме
        for widget in self.parent_frame.winfo_children():
            widget.destroy()

        # Сбрасываем атрибуты, которые будут созданы заново в show()
        self.table_container = None
        self.tree = None

    def show(self):
        """Отображает раздел 'Клиенты'"""
        # Очищаем всё
        self.clear()

        # Создаём таблицу если её нет
        if not hasattr(self, 'table_container') or self.table_container is None:
            self._create_table_widgets()

        # Верхняя панель с поиском и кнопкой добавления
        top_panel = tk.Frame(self.parent_frame, bg='#f0f0f0', height=70)
        top_panel.pack(fill=tk.X)
        top_panel.pack_propagate(False)

        # Поиск слева/по центру
        search_container = tk.Frame(top_panel, bg='#f0f0f0')
        search_container.pack(side=tk.LEFT, expand=True, padx=20, pady=15)

        self.info_label = tk.Label(
            search_container,
            text=f"Клиентов: {self.clients_mgr.get_count()}",
            font=("Arial", 11, "bold"),
            bg='#f0f0f0',
            fg='#333',
            width=15
        )
        self.info_label.pack(side=tk.LEFT, padx=(0, 0))

        tk.Label(
            search_container,
            text="🔍",
            font=("Arial", 14),
            bg='#f0f0f0',
            fg='#333'
        ).pack(side=tk.LEFT, padx=5)

        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_change)

        search_entry = tk.Entry(
            search_container,
            textvariable=self.search_var,
            font=("Arial", 12),
            width=50,
            relief="solid",
            borderwidth=1,
            bg='white',
            fg='#333'
        )

        search_entry.pack(side=tk.LEFT, padx=5, ipady=8)

        tk.Label(
            search_container,
            text="Поиск по компании или контактному лицу",
            font=("Arial", 10),
            bg='#f0f0f0',
            fg='#666'
        ).pack(side=tk.LEFT, padx=10)

        # Кнопка добавления справа
        tk.Button(
            top_panel,
            text="+ Добавить клиента",
            command=self._show_add_client_dialog,
            bg="#41a5be",
            fg="black",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=20, pady=15)

        # Показываем таблицу
        self.table_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 0))

        # Заполняем таблицу данными
        self._update_table_data()

        # Привязываем изменение размера
        self.tree.bind('<Configure>', self._configure_columns)

    def _update_table_data(self, search_query=None):
        """Обновляет данные в таблице Treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Получаем данные
        if search_query:
            clients = self.clients_mgr.search(search_query)
        else:
            clients = self.clients_mgr.get_all()

        # Единообразное преобразование в словари
        for idx, client in enumerate(clients):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'

            # Преобразуем client в dict если нужно
            if not isinstance(client, dict):
                try:
                    client = dict(client)
                except:
                    client = {}

            values = (
                client.get('id', ''),
                client.get('company', '—'),
                client.get('primary_contact', '—'),
                client.get('primary_position', '—'),
                client.get('primary_phone', '—'),
                client.get('address', '—'),
                "➕ Задача"
            )

            self.tree.insert("", tk.END, values=values, tags=(tag,))

    def _on_search_change(self, *args):
        """Обработчик изменения поискового запроса с задержкой"""
        # Отменяем предыдущую отложенную задачу, если она есть
        if self.search_job:
            self.parent_frame.after_cancel(self.search_job)

        # Создаем новую отложенную задачу
        self.search_job = self.parent_frame.after(
            self.search_delay,  # Задержка
            self._perform_search  # Метод, который вызовется после задержки
        )

    def _perform_search(self):
        """Выполняет фактический поиск после задержки"""
        self.search_job = None
        search_query = self.search_var.get().strip()

        # Проверяем, что таблица существует
        if hasattr(self, 'tree') and self.tree:
            self._update_table_data(search_query)

    def _on_row_enter_grid(self, row, widgets):
        """Подсветка строки при наведении (grid версия)"""
        for widget in widgets:
            widget.config(bg='#e8f4f8')

    def _on_row_leave_grid(self, row, widgets, original_bg):
        """Снятие подсветки (grid версия)"""
        for widget in widgets:
            widget.config(bg=original_bg)

    def _open_task_card(self, task_id):
        """Открыть карточку задачи"""
        try:
            if not self.tasks_mgr:
                from tkinter import messagebox
                messagebox.showerror("Ошибка", "Менеджер задач не инициализирован")
                return

            # Получаем данные задачи
            task = self.tasks_mgr.get_by_id(task_id)
            if not task:
                from tkinter import messagebox
                messagebox.showerror("Ошибка", f"Задача с ID {task_id} не найдена")
                return

            # Преобразуем в словарь для удобства
            try:
                # Обрабатываем sqlite3.Row
                if hasattr(task, 'keys'):
                    # Это sqlite3.Row или подобный объект
                    task_data = {}
                    for key in task.keys():
                        task_data[key] = task[key]
                elif hasattr(task, '__dict__'):
                    task_data = task.__dict__
                elif hasattr(task, '_asdict'):
                    task_data = task._asdict()
                elif isinstance(task, dict):
                    task_data = task
                else:
                    # Пробуем получить атрибуты по одному
                    task_data = {}
                    attrs_to_try = ['id', 'title', 'description', 'status', 'priority',
                                    'due_date', 'created_at', 'client_id']
                    for attr in attrs_to_try:
                        try:
                            # Пробуем доступ через getattr
                            if hasattr(task, attr):
                                task_data[attr] = getattr(task, attr)
                            # Пробуем доступ по индексу/ключу
                            elif hasattr(task, '__getitem__'):
                                try:
                                    task_data[attr] = task[attr]
                                except (KeyError, IndexError):
                                    pass
                        except:
                            pass
            except Exception as e:
                print(f"Ошибка преобразования данных задачи: {e}")
                task_data = {'id': task_id, 'title': 'Задача'}

            # Получаем данные клиента для отображения
            client_data = {}
            if task_data.get('client_id'):
                try:
                    client = self.clients_mgr.get_by_id(task_data['client_id'])
                    if client:
                        if hasattr(client, 'keys'):
                            # sqlite3.Row
                            client_data = {}
                            for key in client.keys():
                                client_data[key] = client[key]
                        elif hasattr(client, '__dict__'):
                            client_data = client.__dict__
                        elif hasattr(client, '_asdict'):
                            client_data = client._asdict()
                        elif isinstance(client, dict):
                            client_data = client
                        else:
                            # Пробуем получить атрибуты
                            client_data = {}
                            for attr in ['id', 'company']:
                                if hasattr(client, attr):
                                    client_data[attr] = getattr(client, attr)
                except Exception as e:
                    print(f"Ошибка получения данных клиента: {e}")

            # Создаем окно карточки задачи
            task_window = tk.Toplevel(self.parent_frame)
            task_window.title(f"Задача: {task_data.get('title', 'Без названия')}")
            task_window.geometry("700x600")
            task_window.configure(bg='white')

            # Заголовок
            header = tk.Frame(task_window, bg='#333333', height=60)
            header.pack(fill=tk.X)
            header.pack_propagate(False)

            title_text = task_data.get('title', 'Задача')
            tk.Label(
                header,
                text=f"📋 {title_text}",
                font=("Arial", 18, "bold"),
                fg="white",
                bg='#333333'
            ).pack(side=tk.LEFT, padx=20, pady=15)

            # ID задачи
            tk.Label(
                header,
                text=f"ID: {task_id}",
                font=("Arial", 12),
                fg="#41a5be",
                bg='#333333'
            ).pack(side=tk.RIGHT, padx=20, pady=15)

            # Основной контейнер с прокруткой
            main_container = tk.Frame(task_window, bg='white')
            main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Информация о задаче
            info_frame = tk.Frame(main_container, bg='white')
            info_frame.pack(fill=tk.BOTH, expand=True)

            # Статус задачи
            tk.Label(
                info_frame,
                text="Статус:",
                font=("Arial", 12, "bold"),
                bg='white'
            ).grid(row=0, column=0, sticky='w', pady=10)

            status_colors = {
                'Новая': '#17a2b8',
                'В работе': '#007bff',
                'Выполнена': '#28a745',
                'Отложена': '#6c757d',
                'Отменена': '#dc3545'
            }

            status = task_data.get('status', 'Новая')
            status_color = status_colors.get(status, '#6c757d')

            tk.Label(
                info_frame,
                text=status,
                font=("Arial", 12, "bold"),
                bg=status_color,
                fg='white',
                relief="solid",
                bd=1,
                padx=10,
                pady=5
            ).grid(row=0, column=1, sticky='w', pady=10)

            # Приоритет
            tk.Label(
                info_frame,
                text="Приоритет:",
                font=("Arial", 12, "bold"),
                bg='white'
            ).grid(row=1, column=0, sticky='w', pady=10)

            priority = task_data.get('priority', 'Не указан')
            tk.Label(
                info_frame,
                text=priority,
                font=("Arial", 12),
                bg='white',
                fg='#666'
            ).grid(row=1, column=1, sticky='w', pady=10)

            # Срок выполнения
            tk.Label(
                info_frame,
                text="Срок выполнения:",
                font=("Arial", 12, "bold"),
                bg='white'
            ).grid(row=2, column=0, sticky='w', pady=10)

            due_date = task_data.get('due_date', 'Не указан')
            tk.Label(
                info_frame,
                text=due_date,
                font=("Arial", 12),
                bg='white',
                fg='#666'
            ).grid(row=2, column=1, sticky='w', pady=10)

            # Дата создания
            tk.Label(
                info_frame,
                text="Дата создания:",
                font=("Arial", 12, "bold"),
                bg='white'
            ).grid(row=3, column=0, sticky='w', pady=10)

            created_at = task_data.get('created_at', 'Не указана')
            tk.Label(
                info_frame,
                text=created_at,
                font=("Arial", 12),
                bg='white',
                fg='#666'
            ).grid(row=3, column=1, sticky='w', pady=10)

            # Клиент (если есть)
            if client_data and 'company' in client_data:
                tk.Label(
                    info_frame,
                    text="Клиент:",
                    font=("Arial", 12, "bold"),
                    bg='white'
                ).grid(row=4, column=0, sticky='w', pady=10)

                tk.Label(
                    info_frame,
                    text=client_data.get('company', 'Не указан'),
                    font=("Arial", 12),
                    bg='white',
                    fg='#41a5be',
                    cursor="hand2"
                ).grid(row=4, column=1, sticky='w', pady=10)

                # Делаем кликабельной ссылку на клиента
                def open_client():
                    client_id = client_data.get('id') or task_data.get('client_id')
                    if client_id:
                        self._open_client_card_by_id(client_id)
                        task_window.destroy()

                # Находим виджет с названием компании и делаем его кликабельным
                for widget in info_frame.grid_slaves(row=4, column=1):
                    if isinstance(widget, tk.Label):
                        widget.bind('<Button-1>', lambda e: open_client())
                        widget.config(cursor="hand2")

            # Описание задачи
            tk.Label(
                info_frame,
                text="Описание:",
                font=("Arial", 12, "bold"),
                bg='white'
            ).grid(row=5, column=0, sticky='nw', pady=10)

            description = task_data.get('description', 'Нет описания')
            desc_text = tk.Text(
                info_frame,
                height=8,
                width=40,
                font=("Arial", 11),
                wrap=tk.WORD,
                bg='#f8f9fa',
                relief="solid",
                borderwidth=1
            )
            desc_text.grid(row=5, column=1, sticky='w', pady=10)
            desc_text.insert('1.0', description)
            desc_text.config(state='disabled')

            # Кнопки внизу
            buttons_frame = tk.Frame(task_window, bg='#f0f0f0', height=80)
            buttons_frame.pack(fill=tk.X, side=tk.BOTTOM)
            buttons_frame.pack_propagate(False)

            btn_container = tk.Frame(buttons_frame, bg='#f0f0f0')
            btn_container.place(relx=0.5, rely=0.5, anchor='center')

            # Кнопка редактирования
            tk.Button(
                btn_container,
                text="✏ Редактировать",
                command=lambda: self._edit_task(task_id, task_window),
                bg="#28a745",
                fg="white",
                font=("Arial", 12, "bold"),
                relief="flat",
                width=15,
                height=1,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)

            # Кнопка закрытия задачи
            tk.Button(
                btn_container,
                text="✅ Завершить",
                command=lambda: self._complete_task(task_id, task_window),
                bg="#41a5be",
                fg="white",
                font=("Arial", 12, "bold"),
                relief="flat",
                width=15,
                height=1,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)

            # Кнопка удаления задачи
            tk.Button(
                btn_container,
                text="🗑 Удалить",
                command=lambda: self._delete_task(task_id, task_window),
                bg="#dc3545",
                fg="white",
                font=("Arial", 12, "bold"),
                relief="flat",
                width=15,
                height=1,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)

            # Кнопка закрытия окна
            tk.Button(
                btn_container,
                text="Закрыть",
                command=task_window.destroy,
                bg="#6c757d",
                fg="white",
                font=("Arial", 12, "bold"),
                relief="flat",
                width=15,
                height=1,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            print(f"Ошибка при открытии карточки задачи: {e}")
            import traceback
            traceback.print_exc()
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось открыть карточку задачи: {e}")

    def _delete_task(self, task_id, parent_window):
        """Удалить задачу"""
        from utils.helpers import show_confirmation, show_message

        confirm = show_confirmation(
            parent_window,
            "Удаление задачи",
            "Вы уверены, что хотите удалить эту задачу?\n\nЭто действие нельзя отменить!"
        )

        if confirm and self.tasks_mgr:
            try:
                # Удаляем задачу
                self.tasks_mgr.delete(task_id)
                show_message(parent_window, "Успех", "Задача удалена", "success")
                parent_window.destroy()

                # Здесь можно добавить обновление интерфейса
                # Например, обновить вкладку задач текущего клиента
            except Exception as e:
                show_message(parent_window, "Ошибка", f"Не удалось удалить задачу: {e}", "error")

    def _show_add_client_dialog(self):
        """Диалог добавления клиента"""

        # Создаём диалоговое окно
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Добавить клиента")
        dialog.geometry("750x750")
        dialog.configure(bg='white')
        dialog.resizable(False, False)

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

        tk.Label(info_frame, text="Название компании *", font=("Arial", 10), bg='white', fg='#333').pack(anchor='w')
        company_entry = tk.Entry(info_frame, font=("Arial", 11), relief="solid", borderwidth=1)
        company_entry.pack(fill=tk.X, pady=(5, 15), ipady=5)

        tk.Label(info_frame, text="Адрес", font=("Arial", 10), bg='white', fg='#333').pack(anchor='w')
        address_entry = tk.Entry(info_frame, font=("Arial", 11), relief="solid", borderwidth=1)
        address_entry.pack(fill=tk.X, pady=(5, 15), ipady=5)

        tk.Label(info_frame, text="Примечания", font=("Arial", 10), bg='white', fg='#333').pack(anchor='w')
        notes_text = tk.Text(info_frame, font=("Arial", 10), height=3, relief="solid", borderwidth=1, wrap=tk.WORD)
        notes_text.pack(fill=tk.X, pady=(5, 0))

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
                from utils.helpers import show_message
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

            # Кнопка удаления контакта
            def remove_contact():
                """Удаляет контактное лицо из формы"""
                contact_box.destroy()
                if contact_widget in contact_widgets:
                    contact_widgets.remove(contact_widget)

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

            contact_widgets.append(contact_widget)
            update_primary_contact_ui()

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
        tk.Button(contacts_container, text="+ Добавить контакт", command=create_contact_fields, bg="#28a745",
                  fg="white", font=("Arial", 10)).pack(pady=5)

        # --- EMAIL (ТЕПЕРЬ ТОЖЕ ДИНАМИЧЕСКИЕ) ---
        email_header_frame = tk.Frame(scrollable_content, bg='white')
        email_header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        tk.Label(email_header_frame, text="📧 Email адреса", font=("Arial", 14, "bold"), bg='white', fg='#333').pack(
            side=tk.LEFT)
        tk.Label(email_header_frame, text="(до 4, выберите основной)", font=("Arial", 10), bg='white', fg='#999').pack(
            side=tk.LEFT, padx=10)

        emails_container = tk.Frame(scrollable_content, bg='white')
        emails_container.pack(fill=tk.X, padx=20, pady=(0, 30))

        email_widgets = []
        primary_email_var = tk.IntVar(value=0)

        def update_primary_email_ui():
            selected = primary_email_var.get()
            for idx, w in enumerate(email_widgets):
                w['radio'].config(value=idx)
                w['radio'].config(text=f"Email #{idx + 1}")
                if idx == selected:
                    w['primary_label'].config(text="⭐ ОСНОВНОЙ", fg='#4CAF50')
                else:
                    w['primary_label'].config(text="", fg='#999')

        def create_email_fields():
            if len(email_widgets) >= 4:
                from utils.helpers import show_message
                show_message(dialog, "Внимание", "Максимум 4 email адреса!", "warning")
                return

            idx = len(email_widgets)
            box = tk.Frame(emails_container, bg='#f8f9fa', relief='solid', bd=1)
            box.pack(fill=tk.X, pady=5)

            header = tk.Frame(box, bg='#f8f9fa')
            header.pack(fill=tk.X, padx=10, pady=8)

            radio = tk.Radiobutton(header, text=f"Email #{idx + 1}", variable=primary_email_var, value=idx,
                                   font=("Arial", 10, "bold"), bg='#f8f9fa', selectcolor='#4CAF50',
                                   command=update_primary_email_ui)
            radio.pack(side=tk.LEFT)

            p_label = tk.Label(header, text="", font=("Arial", 9, "bold"), bg='#f8f9fa')
            p_label.pack(side=tk.LEFT, padx=5)

            def remove(b=box, w=None):
                b.destroy()
                if w in email_widgets: email_widgets.remove(w)
                if primary_email_var.get() >= len(email_widgets): primary_email_var.set(0)
                update_primary_email_ui()

            tk.Button(header, text="✖", command=lambda: remove(box, widget), bg="#dc3545", fg="white",
                      font=("Arial", 8), relief="flat").pack(side=tk.RIGHT)

            fields = tk.Frame(box, bg='#f8f9fa')
            fields.pack(fill=tk.X, padx=10, pady=(0, 8))

            tk.Label(fields, text="Email:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
            em = tk.Entry(fields, font=("Arial", 10), relief="solid", borderwidth=1)
            em.pack(fill=tk.X, pady=2, ipady=3)

            widget = {'box': box, 'email': em, 'radio': radio, 'primary_label': p_label}
            email_widgets.append(widget)
            update_primary_email_ui()
            return widget

        create_email_fields()
        tk.Button(emails_container, text="+ Добавить Email", command=create_email_fields, bg="#28a745", fg="white",
                  font=("Arial", 10)).pack(pady=5)

        # --- СОХРАНЕНИЕ ---
        # ─── СОХРАНЕНИЕ ────────────────────────────────────────────────────────────────
        def save_client():
            """Сохраняет нового клиента с расширенной валидацией"""
            from utils.helpers import show_message
            from tkinter import messagebox  # <-- ДОБАВЬТЕ
            from datetime import date  # <-- ДОБАВЬТЕ

            company = company_entry.get().strip()

            if not company:
                show_message(dialog, "Внимание", "Введите название компании!", "warning")
                company_entry.focus_set()
                return

            if len(company) < 2:
                show_message(dialog, "Внимание", "Название компании должно содержать минимум 2 символа!", "warning")
                company_entry.focus_set()
                return

            # Проверка контактных лиц
            valid_contacts = []
            for w in contact_widgets:
                name = w['name'].get().strip()
                if name:
                    if ' ' not in name and len(name) < 3:
                        show_message(
                            dialog,
                            "Внимание",
                            f"Введите полное ФИО для контакта #{contact_widgets.index(w) + 1}!",
                            "warning"
                        )
                        w['name'].focus_set()
                        return
                    valid_contacts.append(w)

            if not valid_contacts:
                show_message(dialog, "Внимание", "Введите хотя бы одно контактное лицо!", "warning")
                if contact_widgets:
                    contact_widgets[0]['name'].focus_set()
                return

            # Проверка email-ов
            for w in valid_contacts:
                email_widget = w.get('email')
                if email_widget:
                    email = email_widget.get().strip()
                    if email and ('@' not in email or '.' not in email or len(email) < 5):
                        show_message(
                            dialog,
                            "Внимание",
                            f"Некорректный формат email в контакте #{valid_contacts.index(w) + 1}",
                            "warning"
                        )
                        email_widget.focus_set()
                        return

            try:
                # 1. Создаём клиента
                client_id = self.clients_mgr.add(
                    company=company,
                    address=address_entry.get().strip(),
                    notes=notes_text.get('1.0', 'end-1c').strip()
                )

                if not client_id:
                    show_message(dialog, "Ошибка", "Не удалось создать клиента в базе", "error")
                    return

                # 2. Сохраняем контакты + email
                saved_contacts = []
                primary_contact_name = ""

                for idx, w in enumerate(valid_contacts):
                    name = w['name'].get().strip()
                    position = w['position'].get().strip()
                    phone = w['phone'].get().strip()
                    is_primary = (idx == primary_contact_var.get())

                    contact_id = self.contact_persons_mgr.add(
                        client_id=client_id,
                        full_name=name,
                        position=position,
                        phone=phone,
                        is_primary=is_primary
                    )

                    if contact_id:
                        saved_contacts.append({'id': contact_id, 'name': name})
                        if is_primary:
                            primary_contact_name = name

                        # Email
                        email_widget = w.get('email')
                        if email_widget:
                            email = email_widget.get().strip()
                            if email:
                                try:
                                    self.contact_emails_mgr.add(
                                        contact_person_id=contact_id,
                                        email=email,
                                        is_primary=True
                                    )
                                except Exception as e:
                                    print(f"Ошибка сохранения email для {name}: {e}")

                # 3. Запись в историю
                try:
                    self.interactions_mgr.add(
                        client_id=client_id,
                        date=date.today(),
                        type_interaction="Создание",
                        description=f"Клиент добавлен. Основной контакт: {primary_contact_name or 'не указан'}"
                    )
                except Exception as e:
                    print(f"Ошибка записи в историю: {e}")

                # Успех
                msg = f"Клиент успешно добавлен!\n\n" \
                      f"Компания: {company}\n" \
                      f"ID: {client_id}\n" \
                      f"Контактов: {len(saved_contacts)}\n" \
                      f"Основной: {primary_contact_name or 'не указан'}"

                show_message(dialog, "✅ Успех", msg, "success")

                dialog.destroy()

                # Обновление интерфейса
                if hasattr(self, 'info_label'):
                    self.info_label.config(text=f"Клиентов: {self.clients_mgr.get_count()}")

                self._update_table_data()  # или как у тебя называется метод обновления таблицы

                # Предложение создать задачу
                def ask_task():
                    if messagebox.askyesno("Создать задачу?", f"Создать задачу для '{company}'?"):
                        self._create_task_for_client(client_id)

                dialog.after(500, ask_task)

            except Exception as e:
                import traceback
                print("═" * 60)
                print("ОШИБКА СОХРАНЕНИЯ КЛИЕНТА:")
                print(traceback.format_exc())
                print("═" * 60)

                show_message(
                    dialog,
                    "❌ Ошибка",
                    f"Не удалось сохранить клиента.\n\n{str(e)}",
                    "error"
                )

        # Кнопки (должны быть вне функции save_client!)
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

        # Прокрутка
        def on_mw(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mw))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        company_entry.focus_set()

    def _open_client_card(self, client):
        """Открыть карточку клиента"""
        # Создаём новое окно
        card_window = tk.Toplevel(self.parent_frame)
        card_window.title(f"Карточка клиента: {client['company']}")
        card_window.geometry("900x700")
        card_window.configure(bg='white')

        # Заголовок (в стиле меню)
        header = tk.Frame(card_window, bg='#333333', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"🏢 {client['company']}",
            font=("Arial", 18, "bold"),
            fg="white",
            bg='#333333'
        ).pack(side=tk.LEFT, padx=20, pady=15)

        tk.Label(
            header,
            text=f"ID: {client['id']}",
            font=("Arial", 12),
            fg="#41a5be",
            bg='#333333'
        ).pack(side=tk.RIGHT, padx=20, pady=15)

        # Вкладки
        notebook = ttk.Notebook(card_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Вкладка 1: Основное
        tab_main = tk.Frame(notebook, bg='white')
        notebook.add(tab_main, text="📋 Основное")
        self._create_main_tab(tab_main, client)

        # Вкладка 2: Контактные лица (ВКЛЮЧАЕМ EMAIL ЗДЕСЬ)
        tab_contacts = tk.Frame(notebook, bg='white')
        notebook.add(tab_contacts, text="👥 Контактные лица")
        self._create_contacts_tab(tab_contacts, client['id'])

        # Вкладка 3: Задачи (ЗАМЕНЯЕМ ИСТОРИЮ НА ЗАДАЧИ)
        tab_tasks = tk.Frame(notebook, bg='white')
        notebook.add(tab_tasks, text="✅ Задачи")
        self._create_tasks_tab(tab_tasks, client['id'])

        # ПАНЕЛЬ КНОПОК ВНИЗУ
        buttons_container = tk.Frame(card_window, bg='#f0f0f0', height=80)
        buttons_container.pack(fill=tk.X, side=tk.BOTTOM)
        buttons_container.pack_propagate(False)

        buttons_frame = tk.Frame(buttons_container, bg='#f0f0f0')
        buttons_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Кнопка "Редактировать"
        tk.Button(
            buttons_frame,
            text="✏ Редактировать",
            command=lambda: self._edit_client(client, card_window),
            bg="#28a745",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            width=18,
            height=1,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

        # Кнопка "Удалить клиента"
        tk.Button(
            buttons_frame,
            text="🗑 Удалить",
            command=lambda: self._delete_client_from_card(client, card_window),
            bg="#d9534f",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            width=15,
            height=1,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

        # Кнопка "Создать задачу"
        tk.Button(
            buttons_frame,
            text="➕ Задача",
            command=lambda: self._create_task_for_client(client['id']),
            bg="#41a5be",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            width=15,
            height=1,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

        # Кнопка "Закрыть"
        tk.Button(
            buttons_frame,
            text="Закрыть",
            command=card_window.destroy,
            bg="#6c757d",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            width=15,
            height=1,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10, pady=10)

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

        except Exception as e:
            print(f"Ошибка при открытии карточки: {e}")
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось открыть карточку: {e}")

    def _create_main_tab(self, parent, client):
        """Вкладка 'Основное'"""
        tk.Label(
            parent,
            text="Основная информация",
            font=("Arial", 16, "bold"),
            bg='white'
        ).pack(pady=20)

        info_frame = tk.Frame(parent, bg='white')
        info_frame.pack(padx=30, pady=10, fill=tk.BOTH)

        # Компания
        self._add_info_row(info_frame, "Компания:", client['company'], 0)

        # Адрес
        self._add_info_row(info_frame, "Адрес:", client['address'] or "Не указан", 1)

        # Примечания
        tk.Label(
            info_frame,
            text="Примечания:",
            font=("Arial", 12, "bold"),
            bg='white'
        ).grid(row=2, column=0, sticky='nw', padx=10, pady=10)

        notes_text = tk.Text(
            info_frame,
            width=50,
            height=5,
            font=("Arial", 11),
            wrap=tk.WORD
        )
        notes_text.grid(row=2, column=1, sticky='w', padx=10, pady=10)
        notes_text.insert('1.0', client['notes'] or "Нет примечаний")
        notes_text.config(state='disabled')

        # Дата создания
        self._add_info_row(info_frame, "Дата создания:", client['created_at'], 3)

    def _create_contacts_tab(self, parent, client_id):
        """Вкладка 'Контактные лица' (с email)"""
        tk.Label(
            parent,
            text="Контактные лица",
            font=("Arial", 16, "bold"),
            bg='white'
        ).pack(pady=(20, 10))

        # Получаем контакты
        contacts = self.contact_persons_mgr.get_by_client(client_id)

        if not contacts:
            tk.Label(
                parent,
                text="Контактных лиц нет",
                font=("Arial", 12),
                fg="gray",
                bg='white'
            ).pack(pady=30)
            return

        # Canvas для прокрутки
        canvas = tk.Canvas(parent, bg='white')
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Список контактов с email
        for contact in contacts:
            contact_frame = tk.Frame(scrollable_frame, bg='#f8f9fa', relief='solid', bd=1)
            contact_frame.pack(padx=20, pady=10, fill=tk.X)

            # Заголовок контакта
            header_frame = tk.Frame(contact_frame, bg='#f8f9fa')
            header_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

            primary_label = " ⭐ ОСНОВНОЙ" if contact['is_primary'] else ""

            tk.Label(
                header_frame,
                text=f"👤 {contact['full_name']}{primary_label}",
                font=("Arial", 14, "bold"),
                bg='#f8f9fa'
            ).pack(side=tk.LEFT)

            # Информация о контакте
            info_frame = tk.Frame(contact_frame, bg='#f8f9fa')
            info_frame.pack(fill=tk.X, padx=20, pady=(5, 10))

            # Должность
            if contact['position']:
                tk.Label(
                    info_frame,
                    text=f"📋 Должность: {contact['position']}",
                    font=("Arial", 11),
                    bg='#f8f9fa',
                    fg='#666'
                ).pack(anchor='w', pady=2)

            # Телефон
            if contact['phone']:
                tk.Label(
                    info_frame,
                    text=f"📞 Телефон: {contact['phone']}",
                    font=("Arial", 11),
                    bg='#f8f9fa',
                    fg='#666'
                ).pack(anchor='w', pady=2)

            # Email адреса для этого контакта
            if self.contact_emails_mgr:
                try:
                    emails = self.contact_emails_mgr.get_by_contact(contact['id'])
                    if emails:
                        email_text = ", ".join([email['email'] for email in emails])
                        tk.Label(
                            info_frame,
                            text=f"📧 Email: {email_text}",
                            font=("Arial", 11),
                            bg='#f8f9fa',
                            fg='#666'
                        ).pack(anchor='w', pady=2)
                except Exception as e:
                    print(f"Ошибка при загрузке email: {e}")

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Кнопка создания нового контакта
        btn_frame = tk.Frame(parent, bg='white')
        btn_frame.pack(pady=(10, 20))

        tk.Button(
            btn_frame,
            text="➕ Добавить контактное лицо",
            command=lambda: self._add_contact_to_client(client_id, parent),
            bg="#41a5be",
            fg="white",
            font=("Arial", 11),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack()

    def _create_tasks_tab(self, parent, client_id):
        """Вкладка 'Задачи'"""
        tk.Label(
            parent,
            text="Задачи клиента",
            font=("Arial", 16, "bold"),
            bg='white'
        ).pack(pady=(20, 10))

        # Проверяем наличие менеджера задач
        if not self.tasks_mgr:
            tk.Label(
                parent,
                text="Менеджер задач не инициализирован",
                font=("Arial", 12),
                fg="red",
                bg='white'
            ).pack(pady=30)
            return

        try:
            # Получаем задачи для клиента
            tasks = self.tasks_mgr.get_by_client(client_id)

            if not tasks:
                tk.Label(
                    parent,
                    text="Задач нет",
                    font=("Arial", 12),
                    fg="gray",
                    bg='white'
                ).pack(pady=30)
                return

            # Canvas для прокрутки
            canvas = tk.Canvas(parent, bg='white')
            scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg='white')

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            # Делаем scrollable_frame шириной как canvas
            def update_scrollable_width(event):
                canvas.itemconfig(canvas_window, width=event.width)

            canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
            canvas.bind('<Configure>', update_scrollable_width)

            # Отображаем задачи
            for task in tasks:
                task_frame = tk.Frame(scrollable_frame, bg='#f8f9fa', relief='solid', bd=1)
                task_frame.pack(padx=10, pady=8, fill=tk.X, expand=True)  # Изменено: fill=tk.X, expand=True

                # Получаем атрибуты задачи
                try:
                    task_id = task.id if hasattr(task, 'id') else getattr(task, 'id', '')
                    title = task.title if hasattr(task, 'title') else getattr(task, 'title', 'Без названия')
                    status = task.status if hasattr(task, 'status') else getattr(task, 'status', 'Новая')
                    created_at = task.created_at if hasattr(task, 'created_at') else getattr(task, 'created_at', '')
                    priority = task.priority if hasattr(task, 'priority') else getattr(task, 'priority', None)
                    due_date = task.due_date if hasattr(task, 'due_date') else getattr(task, 'due_date', None)
                    description = task.description if hasattr(task, 'description') else getattr(task, 'description', '')
                except AttributeError:
                    try:
                        task_id = task['id'] if 'id' in task else ''
                        title = task['title'] if 'title' in task else 'Без названия'
                        status = task['status'] if 'status' in task else 'Новая'
                        created_at = task['created_at'] if 'created_at' in task else ''
                        priority = task.get('priority') if isinstance(task, dict) else None
                        due_date = task.get('due_date') if isinstance(task, dict) else None
                        description = task.get('description') if isinstance(task, dict) else ''
                    except (KeyError, TypeError):
                        title = str(task) if task else 'Неизвестная задача'
                        status = 'Новая'
                        created_at = ''
                        priority = None
                        due_date = None
                        description = ''

                # Сохраняем task_id для обработки клика
                task_frame.task_id = task_id
                task_frame.task_data = task

                # Статус задачи (цвет в зависимости от статуса)
                status_colors = {
                    'Новая': '#17a2b8',
                    'В работе': '#007bff',
                    'Выполнена': '#28a745',
                    'Отложена': '#6c757d',
                    'Отменена': '#dc3545'
                }

                status_color = status_colors.get(status, '#6c757d')

                # Заголовок задачи - делаем кликабельным
                header_frame = tk.Frame(task_frame, bg='#f8f9fa')
                header_frame.pack(fill=tk.X, padx=15, pady=10)

                # Создаем кнопку-заголовок вместо Label
                title_btn = tk.Label(
                    header_frame,
                    text=f"📌 {title}",
                    font=("Arial", 13, "bold"),
                    bg='#f8f9fa',
                    fg='#333',
                    cursor="hand2"
                )
                title_btn.pack(side=tk.LEFT)

                # Привязываем обработчик клика к заголовку
                title_btn.bind('<Button-1>', lambda e, t_id=task_id: self._open_task_card(t_id))

                # Также делаем всю строку кликабельной
                task_frame.bind('<Button-1>', lambda e, t_id=task_id: self._open_task_card(t_id))
                for child in task_frame.winfo_children():
                    child.bind('<Button-1>', lambda e, t_id=task_id: self._open_task_card(t_id))

                # Статус задачи
                tk.Label(
                    header_frame,
                    text=status,
                    font=("Arial", 10, "bold"),
                    bg=status_color,
                    fg='white',
                    relief="solid",
                    bd=1,
                    padx=10,
                    pady=3
                ).pack(side=tk.RIGHT)

                # Информация о задаче
                info_frame = tk.Frame(task_frame, bg='#f8f9fa')
                info_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

                # Приоритет
                priority_text = ""
                if priority:
                    priority_icons = {'Высокий': '🔴', 'Средний': '🟡', 'Низкий': '🟢'}
                    priority_text = f" | Приоритет: {priority_icons.get(priority, '')} {priority}"

                # Срок выполнения
                due_date_text = ""
                if due_date:
                    due_date_text = f" | Срок: {due_date}"

                tk.Label(
                    info_frame,
                    text=f"📅 Создана: {created_at}{priority_text}{due_date_text}",
                    font=("Arial", 10),
                    bg='#f8f9fa',
                    fg='#666'
                ).pack(anchor='w', pady=2)

                # Описание задачи
                if description:
                    desc_frame = tk.Frame(info_frame, bg='#f8f9fa')
                    desc_frame.pack(fill=tk.X, pady=(5, 0))

                    tk.Label(
                        desc_frame,
                        text="📄 Описание:",
                        font=("Arial", 10, "bold"),
                        bg='#f8f9fa',
                        fg='#555'
                    ).pack(anchor='w')

                    desc_text = tk.Text(
                        desc_frame,
                        height=min(4, len(description.split('\n')) + 1),
                        width=50,
                        font=("Arial", 10),
                        bg='#f8f9fa',
                        fg='#666',
                        wrap=tk.WORD,
                        relief="flat",
                        borderwidth=0
                    )
                    desc_text.pack(anchor='w', pady=(2, 0), fill=tk.X, expand=True)  # Расширяем по ширине
                    desc_text.insert('1.0', description)
                    desc_text.config(state='disabled')

            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        except Exception as e:
            print(f"Ошибка при создании вкладки задач: {e}")
            import traceback
            traceback.print_exc()
            tk.Label(
                parent,
                text=f"Ошибка загрузки задач: {str(e)}",
                font=("Arial", 12),
                fg="red",
                bg='white'
            ).pack(pady=30)

    def _create_task_for_client(self, client_id):
        """Создать задачу для клиента"""
        try:
            if not self.tasks_mgr:
                from tkinter import messagebox
                messagebox.showerror("Ошибка", "Менеджер задач не инициализирован")
                return

            # Получаем данные клиента
            client_data = self.clients_mgr.get_by_id(client_id)
            if not client_data:
                return

            # Пробуем использовать TasksView
            try:
                from views.tasks_view import TasksView

                # Проверяем, есть ли статический метод
                if hasattr(TasksView, 'create_task_for_client'):
                    TasksView.create_task_for_client(
                        parent=self.parent_frame,
                        tasks_mgr=self.tasks_mgr,
                        clients_mgr=self.clients_mgr,
                        client_id=client_id
                    )
                else:
                    # Пробуем создать экземпляр TasksView
                    temp_frame = tk.Frame(self.parent_frame)
                    temp_tasks_view = TasksView(
                        parent_frame=temp_frame,
                        tasks_mgr=self.tasks_mgr,
                        clients_mgr=self.clients_mgr,
                        # остальные менеджеры по необходимости
                    )

                    # Пробуем разные методы
                    if hasattr(temp_tasks_view, '_show_add_dialog_with_client'):
                        temp_tasks_view._show_add_dialog_with_client(client_id)
                    elif hasattr(temp_tasks_view, '_show_add_dialog'):
                        # Создаем диалог с передачей client_id
                        self._create_simple_task_dialog(client_id, client_data)
                    else:
                        self._create_simple_task_dialog(client_id, client_data)

            except ImportError:
                self._create_simple_task_dialog(client_id, client_data)
            except Exception as e:
                print(f"Ошибка при использовании TasksView: {e}")
                self._create_simple_task_dialog(client_id, client_data)

        except Exception as e:
            print(f"Ошибка при создании задачи: {e}")
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось создать задачу: {e}")

    def _create_simple_task_dialog(self, client_id, client_data):
        """Создать простой диалог для задачи, если TasksView недоступен"""
        from tkinter import simpledialog
        from tkinter import messagebox

        title = simpledialog.askstring("Новая задача", "Введите название задачи:")
        if title:
            try:
                self.tasks_mgr.add(
                    title=title,
                    client_id=client_id,
                    # остальные параметры по умолчанию
                )
                messagebox.showinfo("Успех", f"Задача '{title}' создана для клиента {client_data['company']}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать задачу: {e}")

    def _add_info_row(self, parent, label, value, row):
        """Добавить строку информации"""
        tk.Label(
            parent,
            text=label,
            font=("Arial", 12, "bold"),
            bg='white'
        ).grid(row=row, column=0, sticky='w', padx=10, pady=10)

        tk.Label(
            parent,
            text=value,
            font=("Arial", 12),
            bg='white',
            fg='#666'
        ).grid(row=row, column=1, sticky='w', padx=10, pady=10)

    def _delete_client(self, client):
        """Удалить клиента"""
        from utils.helpers import show_confirmation, show_message

        confirm = show_confirmation(
            self.parent_frame,
            "Подтверждение удаления",
            f"Удалить клиента '{client['company']}'?\n\nЭто действие нельзя отменить!"
        )

        if confirm:
            try:
                self.clients_mgr.delete(client['id'])
                show_message(self.parent_frame, "Успех", f"Клиент '{client['company']}' удалён", "success")
                # Автоматически обновляем список
                self._update_table_data()
            except Exception as e:
                show_message(self.parent_frame, "Ошибка", f"Не удалось удалить:\n{e}", "error")

    def _delete_client_from_card(self, client, card_window):
        """Удалить клиента из карточки"""
        from utils.helpers import show_confirmation, show_message

        # ← Передаём ГЛАВНОЕ ОКНО вместо card_window
        confirm = show_confirmation(
            self.parent_frame.master,  # ← ИЗМЕНЕНО! Было: card_window
            "Подтверждение удаления",
            f"Вы действительно хотите удалить клиента:\n\n{client['company']}?\n\nЭто действие нельзя отменить!\n\nБудут удалены:\n• Все контактные лица\n• Все email адреса\n• Вся история взаимодействий"
        )

        if confirm:
            try:
                self.clients_mgr.delete(client['id'])
                show_message(
                    self.parent_frame.master,  # ← ИЗМЕНЕНО!
                    "Успех",
                    f"Клиент '{client['company']}' удалён из базы данных",
                    "success"
                )

                # Закрываем карточку
                card_window.destroy()

                # Автоматически обновляем список
                self._update_table_data()

            except Exception as e:
                show_message(
                    self.parent_frame.master,  # ← ИЗМЕНЕНО!
                    "Ошибка",
                    f"Не удалось удалить клиента:\n{e}",
                    "error"
                )

    def _on_tree_enter(self, event):
        """При входе в Treeview"""
        pass

    def _on_tree_leave(self, event):
        """При выходе из Treeview"""
        # Снимаем подсветку со всех строк
        for item in self.tree.get_children():
            self.tree.item(item, tags=(self.tree.item(item, 'tags')[0],))

    def _on_tree_motion(self, event):
        """При движении мыши над Treeview"""
        # Определяем, над какой строкой находится курсор
        item_id = self.tree.identify_row(event.y)
        if item_id:
            # Снимаем подсветку со всех строк
            for item in self.tree.get_children():
                tags = list(self.tree.item(item, 'tags'))
                if 'selected' in tags:
                    tags.remove('selected')
                self.tree.item(item, tags=tuple(tags))

            # Подсвечиваем текущую строку
            tags = list(self.tree.item(item_id, 'tags'))
            if 'selected' not in tags:
                tags.append('selected')
            self.tree.item(item_id, tags=tuple(tags))

    def _add_contact_to_client(self, client_id, parent_window):
        """Добавить контактное лицо к клиенту"""
        from utils.helpers import show_message

        dialog = tk.Toplevel(parent_window)
        dialog.title("Добавить контактное лицо")
        dialog.geometry("500x400")
        dialog.configure(bg='white')

        tk.Label(
            dialog,
            text="Добавить контактное лицо",
            font=("Arial", 16, "bold"),
            bg='white'
        ).pack(pady=20)

        # Поля для ввода
        fields_frame = tk.Frame(dialog, bg='white')
        fields_frame.pack(padx=30, pady=10)

        tk.Label(fields_frame, text="ФИО *", font=("Arial", 10), bg='white').pack(anchor='w')
        name_entry = tk.Entry(fields_frame, font=("Arial", 11), width=40)
        name_entry.pack(fill=tk.X, pady=(5, 15))

        tk.Label(fields_frame, text="Должность", font=("Arial", 10), bg='white').pack(anchor='w')
        position_entry = tk.Entry(fields_frame, font=("Arial", 11), width=40)
        position_entry.pack(fill=tk.X, pady=(5, 15))

        tk.Label(fields_frame, text="Телефон", font=("Arial", 10), bg='white').pack(anchor='w')
        phone_entry = tk.Entry(fields_frame, font=("Arial", 11), width=40)
        phone_entry.pack(fill=tk.X, pady=(5, 15))

        tk.Label(fields_frame, text="Email", font=("Arial", 10), bg='white').pack(anchor='w')
        email_entry = tk.Entry(fields_frame, font=("Arial", 11), width=40)
        email_entry.pack(fill=tk.X, pady=(5, 15))

        # Кнопки
        buttons_frame = tk.Frame(dialog, bg='white')
        buttons_frame.pack(pady=20)

        def save_contact():
            name = name_entry.get().strip()
            if not name:
                show_message(dialog, "Ошибка", "Введите ФИО контактного лица", "error")
                return

            try:
                # Добавляем контакт
                contact_id = self.contact_persons_mgr.add(
                    client_id=client_id,
                    full_name=name,
                    position=position_entry.get().strip(),
                    phone=phone_entry.get().strip(),
                    is_primary=False  # Новый контакт не основной по умолчанию
                )

                # Добавляем email если есть
                email = email_entry.get().strip()
                if email and self.contact_emails_mgr:
                    self.contact_emails_mgr.add(contact_id, email, True)

                show_message(dialog, "Успех", "Контактное лицо добавлено", "success")
                dialog.destroy()
                parent_window.destroy()
                self._open_client_card_by_id(client_id)

            except Exception as e:
                show_message(dialog, "Ошибка", f"Не удалось добавить контакт: {e}", "error")

        tk.Button(
            buttons_frame,
            text="💾 Сохранить",
            command=save_contact,
            bg="#41a5be",
            fg="white",
            font=("Arial", 11),
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="✖ Отмена",
            command=dialog.destroy,
            bg="#6c757d",
            fg="white",
            font=("Arial", 11),
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10, pady=10)

        name_entry.focus()

    def _edit_client(self, client, parent_window):
        """Редактировать клиента с объединенными email в контактах"""

        edit_dialog = tk.Toplevel(parent_window)
        edit_dialog.title(f"Редактирование: {client['company']}")
        edit_dialog.geometry("750x800")
        edit_dialog.configure(bg='white')
        edit_dialog.resizable(False, False)

        # Заголовок
        header = tk.Frame(edit_dialog, bg='#333333', height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        tk.Label(
            header,
            text="✏ Редактирование клиента",
            font=("Arial", 18, "bold"),
            fg='white',
            bg='#333333'
        ).pack(pady=15)

        # Кнопки внизу
        buttons_container = tk.Frame(edit_dialog, bg='#f0f0f0', height=80)
        buttons_container.pack(fill=tk.X, side=tk.BOTTOM)
        buttons_container.pack_propagate(False)
        buttons_frame = tk.Frame(buttons_container, bg='#f0f0f0')
        buttons_frame.pack(pady=15)

        # Получаем данные клиента
        client_data = self.clients_mgr.get_by_id(client['id'])
        contacts_db = self.contact_persons_mgr.get_by_client(client['id'])

        # Canvas для прокрутки
        canvas = tk.Canvas(edit_dialog, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(edit_dialog, orient="vertical", command=canvas.yview)
        scrollable_content = tk.Frame(canvas, bg='white')

        scrollable_content.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_content, anchor='nw')
        canvas.bind(
            '<Configure>',
            lambda e: canvas.itemconfig(canvas_window, width=e.width)
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- ОСНОВНАЯ ИНФОРМАЦИЯ ---
        tk.Label(
            scrollable_content,
            text="📋 Основная информация",
            font=("Arial", 14, "bold"),
            bg='white',
            fg='#333'
        ).pack(anchor='w', padx=20, pady=(10, 15))

        info_frame = tk.Frame(scrollable_content, bg='white')
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        # Название компании
        tk.Label(
            info_frame,
            text="Название компании *",
            font=("Arial", 10),
            bg='white'
        ).pack(anchor='w')

        company_entry = tk.Entry(
            info_frame,
            font=("Arial", 11),
            relief="solid",
            borderwidth=1
        )
        company_entry.insert(0, client_data['company'])
        company_entry.pack(fill=tk.X, pady=5, ipady=5)

        # Адрес
        tk.Label(
            info_frame,
            text="Адрес",
            font=("Arial", 10),
            bg='white'
        ).pack(anchor='w')

        address_entry = tk.Entry(
            info_frame,
            font=("Arial", 11),
            relief="solid",
            borderwidth=1
        )
        address_entry.insert(0, client_data['address'] or "")
        address_entry.pack(fill=tk.X, pady=5, ipady=5)

        # Примечания
        tk.Label(
            info_frame,
            text="Примечания",
            font=("Arial", 10),
            bg='white'
        ).pack(anchor='w')

        notes_text = tk.Text(
            info_frame,
            font=("Arial", 10),
            height=4,
            relief="solid",
            borderwidth=1
        )
        notes_text.insert('1.0', client_data['notes'] or "")
        notes_text.pack(fill=tk.X, pady=5)

        # --- КОНТАКТНЫЕ ЛИЦА (С EMAIL) ---
        contacts_header = tk.Frame(scrollable_content, bg='white')
        contacts_header.pack(fill=tk.X, padx=20, pady=(20, 10))

        tk.Label(
            contacts_header,
            text="👥 Контактные лица",
            font=("Arial", 14, "bold"),
            bg='white',
            fg='#333'
        ).pack(side=tk.LEFT)

        tk.Label(
            contacts_header,
            text="(до 4, выберите основной)",
            font=("Arial", 10),
            bg='white',
            fg='#999'
        ).pack(side=tk.LEFT, padx=10)

        contacts_container = tk.Frame(scrollable_content, bg='white')
        contacts_container.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Переменные для хранения виджетов
        contact_widgets = []
        primary_contact_var = tk.IntVar()

        def update_contact_ui():
            """Обновляет интерфейс контактов"""
            selected_idx = primary_contact_var.get()
            active_widgets = [w for w in contact_widgets if not w.get('deleted', False)]

            for idx, widget in enumerate(active_widgets):
                widget['radio'].config(value=idx, text=f"Контакт #{idx + 1}")

                if idx == selected_idx:
                    widget['primary_label'].config(text="⭐ ОСНОВНОЙ", fg='#4CAF50')
                else:
                    widget['primary_label'].config(text="", fg='#999')

        def create_contact_widget(contact_data=None):
            """Создает виджет для контактного лица с email"""
            # Проверяем лимит
            active_widgets = [w for w in contact_widgets if not w.get('deleted', False)]
            if len(active_widgets) >= 4:
                from utils.helpers import show_message
                show_message(edit_dialog, "Лимит", "Максимум 4 контактных лица", "warning")
                return None

            idx = len(active_widgets)

            # Контейнер для контакта
            contact_box = tk.Frame(contacts_container, bg='#f8f9fa', relief='solid', bd=1)
            contact_box.pack(fill=tk.X, pady=5)

            # Заголовок
            header_frame = tk.Frame(contact_box, bg='#f8f9fa')
            header_frame.pack(fill=tk.X, padx=10, pady=8)

            # Радиокнопка для основного контакта
            radio_btn = tk.Radiobutton(
                header_frame,
                variable=primary_contact_var,
                value=idx,
                bg='#f8f9fa',
                command=update_contact_ui
            )
            radio_btn.pack(side=tk.LEFT)

            primary_indicator = tk.Label(
                header_frame,
                text="",
                font=("Arial", 9, "bold"),
                bg='#f8f9fa',
                fg='#4CAF50'
            )
            primary_indicator.pack(side=tk.LEFT)

            # Кнопка удаления
            def remove_contact():
                """Удаляет контакт из формы"""
                contact_box.destroy()
                if contact_data_widget.get('id'):
                    contact_data_widget['deleted'] = True
                elif contact_data_widget in contact_widgets:
                    contact_widgets.remove(contact_data_widget)

                # Обновляем UI
                update_contact_ui()

            tk.Button(
                header_frame,
                text="✖",
                command=remove_contact,
                bg="#dc3545",
                fg="white",
                font=("Arial", 8),
                relief="flat"
            ).pack(side=tk.RIGHT)

            # Поля для ввода
            fields_frame = tk.Frame(contact_box, bg='#f8f9fa')
            fields_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

            # ФИО
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

            # ИСПРАВЛЕНИЕ: Преобразуем sqlite3.Row в словарь или используем правильный доступ
            if contact_data:
                # Способ 1: Если это sqlite3.Row
                if hasattr(contact_data, 'keys'):
                    # Это объект с интерфейсом словаря
                    full_name = contact_data.get('full_name', '') if hasattr(contact_data, 'get') else contact_data[
                        'full_name']
                    position = contact_data.get('position', '') if hasattr(contact_data, 'get') else contact_data[
                        'position']
                    phone = contact_data.get('phone', '') if hasattr(contact_data, 'get') else contact_data['phone']
                    contact_id = contact_data.get('id') if hasattr(contact_data, 'get') else contact_data['id']
                else:
                    # Пробуем преобразовать
                    try:
                        full_name = contact_data['full_name']
                        position = contact_data['position']
                        phone = contact_data['phone']
                        contact_id = contact_data['id']
                    except (KeyError, TypeError):
                        full_name = ''
                        position = ''
                        phone = ''
                        contact_id = None

                name_entry.insert(0, full_name)

            name_entry.pack(fill=tk.X, pady=2)

            # Должность
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
            if contact_data:
                position_entry.insert(0, position)
            position_entry.pack(fill=tk.X, pady=2)

            # Телефон
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
            if contact_data:
                phone_entry.insert(0, phone)
            phone_entry.pack(fill=tk.X, pady=2)

            # EMAIL (добавляем в контакты)
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

            # Загружаем email для этого контакта (если есть)
            if contact_data and contact_id and self.contact_emails_mgr:
                try:
                    emails = self.contact_emails_mgr.get_by_contact(contact_id)
                    if emails:
                        # Преобразуем email объект
                        if hasattr(emails[0], 'get'):
                            email_val = emails[0].get('email', '')
                        else:
                            email_val = emails[0]['email'] if isinstance(emails[0], dict) else str(emails[0])
                        email_entry.insert(0, email_val)
                except Exception as e:
                    print(f"Ошибка загрузки email: {e}")

            email_entry.pack(fill=tk.X, pady=2)

            # Создаем объект виджета
            contact_data_widget = {
                'box': contact_box,
                'name': name_entry,
                'position': position_entry,
                'phone': phone_entry,
                'email': email_entry,  # Добавляем поле email
                'radio': radio_btn,
                'primary_label': primary_indicator,
                'id': contact_id if contact_data else None,
                'deleted': False
            }

            contact_widgets.append(contact_data_widget)

            # Устанавливаем основной контакт
            if contact_data:
                # Проверяем, является ли контакт основным
                is_primary = False
                if hasattr(contact_data, 'get'):
                    is_primary = contact_data.get('is_primary', False)
                elif isinstance(contact_data, dict):
                    is_primary = contact_data.get('is_primary', False)
                elif hasattr(contact_data, 'is_primary'):
                    is_primary = contact_data.is_primary

                if is_primary:
                    primary_contact_var.set(idx)

            update_contact_ui()
            return contact_data_widget

        # Загружаем существующие контакты
        for contact in contacts_db:
            create_contact_widget(contact)

        # Если контактов нет - создаем пустой
        if not contacts_db:
            create_contact_widget()

        # Кнопка добавления контакта
        tk.Button(
            contacts_container,
            text="+ Добавить контакт",
            command=create_contact_widget,
            bg="#28a745",
            fg="white",
            font=("Arial", 10)
        ).pack(pady=5)

        # --- ФУНКЦИЯ СОХРАНЕНИЯ ---
        def save_changes():
            """Сохраняет изменения клиента"""
            from utils.helpers import show_message

            company = company_entry.get().strip()
            if not company:
                show_message(edit_dialog, "Внимание", "Укажите название компании", "warning")
                return

            try:
                # 1. Обновляем основную информацию о клиенте
                self.clients_mgr.update(
                    client['id'],
                    company,
                    address_entry.get().strip(),
                    notes_text.get('1.0', 'end-1c').strip()
                )

                # 2. Обрабатываем контактные лица
                active_contacts = [w for w in contact_widgets if not w.get('deleted')]

                for idx, widget in enumerate(active_contacts):
                    name = widget['name'].get().strip()
                    if not name:
                        continue  # Пропускаем пустые контакты

                    is_primary = (idx == primary_contact_var.get())

                    # Обновляем или создаем контакт
                    if widget.get('id'):
                        # Обновляем существующий контакт
                        self.contact_persons_mgr.update(
                            widget['id'],
                            name,
                            widget['position'].get().strip(),
                            widget['phone'].get().strip(),
                            is_primary
                        )
                        contact_id = widget['id']
                    else:
                        # Создаем новый контакт
                        contact_id = self.contact_persons_mgr.add(
                            client['id'],
                            name,
                            widget['position'].get().strip(),
                            widget['phone'].get().strip(),
                            is_primary
                        )

                    # 3. Обрабатываем EMAIL для этого контакта
                    email = widget['email'].get().strip()
                    if email and self.contact_emails_mgr:
                        # Получаем существующие email для этого контакта
                        existing_emails = self.contact_emails_mgr.get_by_contact(contact_id)

                        if existing_emails:
                            # Обновляем первый (основной) email
                            self.contact_emails_mgr.update(
                                existing_emails[0]['id'],
                                email,
                                True  # Первый email всегда основной
                            )
                        else:
                            # Создаем новый email
                            self.contact_emails_mgr.add(contact_id, email, True)

                # 4. Удаляем помеченные контакты
                for widget in contact_widgets:
                    if widget.get('deleted') and widget.get('id'):
                        self.contact_persons_mgr.delete(widget['id'])

                show_message(edit_dialog, "Успех", "Изменения сохранены!", "success")

                # Закрываем окна и обновляем данные
                edit_dialog.destroy()
                parent_window.destroy()
                self._update_table_data()

                # Открываем обновленную карточку клиента
                updated_client = self.clients_mgr.get_by_id(client['id'])
                if updated_client:
                    client_dict = dict(updated_client)
                    prim = self.contact_persons_mgr.get_primary(client['id'])

                    if prim:
                        client_dict['primary_contact'] = prim['full_name']
                        client_dict['primary_position'] = prim['position']
                        client_dict['primary_phone'] = prim['phone']
                    else:
                        client_dict['primary_contact'] = ""
                        client_dict['primary_position'] = ""
                        client_dict['primary_phone'] = ""

                    self._open_client_card(client_dict)

            except Exception as e:
                show_message(edit_dialog, "Ошибка", str(e), "error")

        # --- КНОПКИ СОХРАНЕНИЯ ---
        buttons_frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Button(
            buttons_frame,
            text="💾 Сохранить",
            command=save_changes,
            bg="#41a5be",
            fg="black",
            font=("Arial", 12, "bold"),
            relief="flat",
            width=15,
            height=1,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="✖ Отмена",
            command=edit_dialog.destroy,
            bg="#6c757d",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            width=15,
            height=1,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

        # --- ПРОКРУТКА КОЛЕСОМ МЫШИ ---
        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mouse_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Фокус на поле компании
        company_entry.focus_set()
        company_entry.select_range(0, tk.END)

    def _on_task_double_click(self, event):
        """Обработка двойного клика по задаче"""
        try:
            item = self.tree.identify_row(event.y)
            if not item:
                return

            values = self.tree.item(item, 'values')
            if values and len(values) > 0:
                # Находим ID задачи через название
                task_title = values[1]  # Название задачи
                # Нужно будет доработать поиск по названию
                # или хранить ID в скрытой колонке
                self._show_edit_dialog_by_title(task_title)
        except Exception as e:
            print(f"Ошибка при двойном клике: {e}")

    def _edit_task(self, task_id, parent_window):
        """Редактировать задачу"""
        # Здесь можно реализовать редактирование задачи
        # Это может быть отдельный диалог или вызов метода из TasksView
        from tkinter import messagebox
        messagebox.showinfo("Редактирование", f"Редактирование задачи {task_id}")
        # Для полной реализации нужно интегрировать с TasksView

    def _complete_task(self, task_id, parent_window):
        """Завершить задачу"""
        from utils.helpers import show_confirmation, show_message

        confirm = show_confirmation(
            parent_window,
            "Завершение задачи",
            "Вы уверены, что хотите отметить задачу как выполненную?"
        )

        if confirm and self.tasks_mgr:
            try:
                # Обновляем статус задачи
                success = self.tasks_mgr.update_status(task_id, 'Выполнена')
                if success:
                    show_message(parent_window, "Успех", "Задача отмечена как выполненная", "success")
                    parent_window.destroy()
                else:
                    show_message(parent_window, "Ошибка", "Не удалось обновить статус задачи", "error")
            except Exception as e:
                show_message(parent_window, "Ошибка", f"Не удалось завершить задачу: {e}", "error")


