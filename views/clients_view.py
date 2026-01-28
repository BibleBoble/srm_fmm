"""
Представление списка клиентов
"""
import tkinter as tk
from tkinter import ttk, messagebox
from views.base_view import BaseView
from datetime import date


class ClientsView(BaseView):
    """
    Класс для отображения списка клиентов
    """

    def __init__(self, parent_frame, clients_mgr, contact_persons_mgr, emails_mgr, interactions_mgr):
        super().__init__(parent_frame)
        self.clients_mgr = clients_mgr
        self.contact_persons_mgr = contact_persons_mgr
        self.emails_mgr = emails_mgr
        self.interactions_mgr = interactions_mgr
        self.search_var = None
        self.list_frame = None

    def show(self):
        """Отображает раздел 'Клиенты'"""
        self.clear()

        # Верхняя панель с поиском и кнопкой добавления
        top_panel = tk.Frame(self.parent_frame, bg='#f0f0f0', height=70)
        top_panel.pack(fill=tk.X)
        top_panel.pack_propagate(False)

        # Поиск слева/по центру
        search_container = tk.Frame(top_panel, bg='#f0f0f0')
        search_container.pack(side=tk.LEFT, expand=True, padx=20, pady=15)

        tk.Label(
            search_container,
            text="🔍",
            font=("Arial", 14),
            bg='#f0f0f0',
            fg='#333'
        ).pack(side=tk.LEFT, padx=5)

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._on_search_change())

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

        # Информационная панель
        info_panel = tk.Frame(self.parent_frame, bg='#f8f9fa', height=40)
        info_panel.pack(fill=tk.X)
        info_panel.pack_propagate(False)

        self.info_label = tk.Label(
            info_panel,
            text=f"Всего клиентов: {self.clients_mgr.get_count()}",
            font=("Arial", 11),
            bg='#f8f9fa',
            fg='#333'
        )
        self.info_label.pack(side=tk.LEFT, padx=20, pady=8)

        # Фрейм для списка клиентов
        self.list_frame = tk.Frame(self.parent_frame, bg='white')
        self.list_frame.pack(fill=tk.BOTH, expand=True)

        # Показываем список сразу
        self._show_clients_list()
    def _on_search_change(self):
        """Обработчик изменения поискового запроса"""
        self._show_clients_list()

    def _show_clients_list(self, search_query=None):
        """Показать список клиентов"""
        # Очищаем фрейм
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        # Получаем поисковый запрос
        if search_query is None and self.search_var:
            search_query = self.search_var.get().strip()

        # Получаем клиентов
        if search_query:
            clients = self.clients_mgr.search(search_query)
        else:
            clients = self.clients_mgr.get_all()

        # Обновляем счётчик
        if hasattr(self, 'info_label'):
            total = self.clients_mgr.get_count()
            if search_query:
                self.info_label.config(text=f"Найдено: {len(clients)} из {total}")
            else:
                self.info_label.config(text=f"Всего клиентов: {total}")

        if not clients:
            tk.Label(
                self.list_frame,
                text="📭 Клиентов не найдено" if search_query else "📭 База клиентов пустая\n\nНажмите '+ Добавить клиента'",
                font=("Arial", 14),
                fg="gray",
                bg='white',
                justify=tk.CENTER
            ).pack(pady=100)
            return

        # Canvas для прокрутки
        canvas = tk.Canvas(self.list_frame, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(self.list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Настройка ширины колонок
        column_widths = [5, 25, 20, 15, 15, 25, 12]  # Ширина каждой колонки

        # Заголовки таблицы
        headers = ["ID", "Компания", "Контактное лицо", "Должность", "Телефон", "Адрес", "Действия"]

        for col, (header, width) in enumerate(zip(headers, column_widths)):
            lbl = tk.Label(
                scrollable_frame,
                text=header,
                font=("Arial", 10, "bold"),
                bg='#333333',
                fg='white',
                width=width,
                padx=5,
                pady=12,
                anchor='w' if col > 0 else 'center'
            )
            lbl.grid(row=0, column=col, sticky='ew')

        # Данные клиентов
        for row_idx, client in enumerate(clients, start=1):
            # Чередующиеся цвета строк
            row_bg = '#f8f9fa' if row_idx % 2 == 0 else 'white'

            # ID
            id_label = tk.Label(
                scrollable_frame,
                text=client['id'],
                bg=row_bg,
                fg='#666',
                font=("Arial", 9),
                width=column_widths[0],
                padx=5,
                pady=10,
                anchor='center'
            )
            id_label.grid(row=row_idx, column=0, sticky='ew')

            # Компания
            company_label = tk.Label(
                scrollable_frame,
                text=client['company'],
                bg=row_bg,
                fg='#333',
                font=("Arial", 10, "bold"),
                anchor='w',
                width=column_widths[1],
                padx=5
            )
            company_label.grid(row=row_idx, column=1, sticky='ew')

            # Контактное лицо
            contact_label = tk.Label(
                scrollable_frame,
                text=client['primary_contact'] or "—",
                bg=row_bg,
                fg='#333',
                font=("Arial", 9),
                anchor='w',
                width=column_widths[2],
                padx=5
            )
            contact_label.grid(row=row_idx, column=2, sticky='ew')

            # Должность
            position_label = tk.Label(
                scrollable_frame,
                text=client['primary_position'] or "—",
                bg=row_bg,
                fg='#666',
                font=("Arial", 9),
                anchor='w',
                width=column_widths[3],
                padx=5
            )
            position_label.grid(row=row_idx, column=3, sticky='ew')

            # Телефон
            phone_label = tk.Label(
                scrollable_frame,
                text=client['primary_phone'] or "—",
                bg=row_bg,
                fg='#333',
                font=("Arial", 9),
                anchor='w',
                width=column_widths[4],
                padx=5
            )
            phone_label.grid(row=row_idx, column=4, sticky='ew')

            # Адрес
            address_label = tk.Label(
                scrollable_frame,
                text=client['address'] or "—",
                bg=row_bg,
                fg='#666',
                font=("Arial", 9),
                anchor='w',
                width=column_widths[5],
                padx=5
            )
            address_label.grid(row=row_idx, column=5, sticky='ew')

            # Кнопка действия (только "Карточка")
            actions_frame = tk.Frame(scrollable_frame, bg=row_bg)
            actions_frame.grid(row=row_idx, column=6, sticky='ew', padx=10)

            # Кнопка "Открыть карточку" (увеличенный шрифт)
            tk.Button(
                actions_frame,
                text="📋 Открыть",
                command=lambda c=client: self._open_client_card(c),
                bg="#41a5be",
                fg="black",
                font=("Arial", 11, "bold"),  # ← Увеличен шрифт с 10 до 11
                relief="flat",
                cursor="hand2",
                borderwidth=0,
                padx=10,
                pady=5
            ).pack(pady=5)

            # Hover эффект для всей строки
            widgets_in_row = [id_label, company_label, contact_label,
                              position_label, phone_label, address_label, actions_frame]

            for widget in widgets_in_row:
                widget.bind('<Enter>', lambda e, r=row_idx, w=widgets_in_row: self._on_row_enter_grid(r, w))
                widget.bind('<Leave>',
                            lambda e, r=row_idx, w=widgets_in_row, bg=row_bg: self._on_row_leave_grid(r, w, bg))

        # Размещаем Canvas
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_row_enter_grid(self, row, widgets):
        """Подсветка строки при наведении (grid версия)"""
        for widget in widgets:
            widget.config(bg='#e8f4f8')

    def _on_row_leave_grid(self, row, widgets, original_bg):
        """Снятие подсветки (grid версия)"""
        for widget in widgets:
            widget.config(bg=original_bg)

    def _on_row_enter_grid(self, row, widgets):
        """Подсветка строки при наведении (grid версия)"""
        for widget in widgets:
            widget.config(bg='#e8f4f8')

    def _on_row_leave_grid(self, row, widgets, original_bg):
        """Снятие подсветки (grid версия)"""
        for widget in widgets:
            widget.config(bg=original_bg)

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
            selected = primary_contact_var.get()
            for idx, w in enumerate(contact_widgets):
                w['radio'].config(value=idx)
                w['radio'].config(text=f"Контакт #{idx + 1}")
                if idx == selected:
                    w['primary_label'].config(text="⭐ ОСНОВНОЙ", fg='#4CAF50')
                else:
                    w['primary_label'].config(text="", fg='#999')

        def create_contact_fields():
            if len(contact_widgets) >= 4:
                from utils.helpers import show_message
                show_message(dialog, "Внимание", "Максимум 4 контактных лица!", "warning")
                return

            idx = len(contact_widgets)
            box = tk.Frame(contacts_container, bg='#f8f9fa', relief='solid', bd=1)
            box.pack(fill=tk.X, pady=5)

            header = tk.Frame(box, bg='#f8f9fa')
            header.pack(fill=tk.X, padx=10, pady=8)

            radio = tk.Radiobutton(header, text=f"Контакт #{idx + 1}", variable=primary_contact_var, value=idx,
                                   font=("Arial", 10, "bold"), bg='#f8f9fa', selectcolor='#4CAF50',
                                   command=update_primary_contact_ui)
            radio.pack(side=tk.LEFT)

            p_label = tk.Label(header, text="", font=("Arial", 9, "bold"), bg='#f8f9fa')
            p_label.pack(side=tk.LEFT, padx=5)

            def remove(b=box, w=None):
                b.destroy()
                if w in contact_widgets: contact_widgets.remove(w)
                if primary_contact_var.get() >= len(contact_widgets): primary_contact_var.set(0)
                update_primary_contact_ui()

            tk.Button(header, text="✖", command=lambda: remove(box, widget), bg="#dc3545", fg="white",
                      font=("Arial", 8), relief="flat").pack(side=tk.RIGHT)

            fields = tk.Frame(box, bg='#f8f9fa')
            fields.pack(fill=tk.X, padx=10, pady=(0, 8))

            tk.Label(fields, text="ФИО:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
            name = tk.Entry(fields, font=("Arial", 10), relief="solid", borderwidth=1)
            name.pack(fill=tk.X, pady=2, ipady=3)

            tk.Label(fields, text="Должность:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
            pos = tk.Entry(fields, font=("Arial", 10), relief="solid", borderwidth=1)
            pos.pack(fill=tk.X, pady=2, ipady=3)

            tk.Label(fields, text="Телефон:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
            ph = tk.Entry(fields, font=("Arial", 10), relief="solid", borderwidth=1)
            ph.pack(fill=tk.X, pady=2, ipady=3)

            widget = {'box': box, 'name': name, 'position': pos, 'phone': ph, 'radio': radio, 'primary_label': p_label}
            contact_widgets.append(widget)
            update_primary_contact_ui()
            return widget

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
        def save_client():
            from utils.helpers import show_message
            company = company_entry.get().strip()

            if not company:
                show_message(dialog, "Внимание", "Введите название компании!", "warning")
                return

            # Проверка контактов
            valid_contacts = [w for w in contact_widgets if w['name'].get().strip()]
            if not valid_contacts:
                show_message(dialog, "Внимание", "Введите хотя бы одно контактное лицо!", "warning")
                return

            try:
                client_id = self.clients_mgr.add(
                    company=company,
                    address=address_entry.get().strip(),
                    notes=notes_text.get('1.0', 'end-1c').strip()
                )

                # Сохраняем контакты
                for idx, w in enumerate(contact_widgets):
                    name = w['name'].get().strip()
                    if name:
                        is_prim = (idx == primary_contact_var.get())
                        self.contact_persons_mgr.add(client_id, name, w['position'].get().strip(),
                                                     w['phone'].get().strip(), is_prim)

                # Сохраняем Email
                for idx, w in enumerate(email_widgets):
                    mail = w['email'].get().strip()
                    if mail:
                        is_prim = (idx == primary_email_var.get())
                        self.emails_mgr.add(client_id, mail, is_prim)

                from datetime import date
                self.interactions_mgr.add(client_id, date.today(), "Звонок", "Клиент добавлен")

                show_message(dialog, "Успех", f"Клиент '{company}' добавлен!", "success")
                dialog.destroy()
                self._show_clients_list()

            except Exception as e:
                show_message(dialog, "Ошибка", str(e), "error")

        tk.Button(buttons_frame, text="💾 Сохранить", command=save_client, bg="#41a5be", fg="black",
                  font=("Arial", 12, "bold"), padx=40, pady=10).pack(side=tk.LEFT, padx=10)
        tk.Button(buttons_frame, text="✖ Отмена", command=dialog.destroy, bg="#6c757d", fg="white",
                  font=("Arial", 12, "bold"), padx=40, pady=10).pack(side=tk.LEFT, padx=10)

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

        # Вкладка 2: Контактные лица
        tab_contacts = tk.Frame(notebook, bg='white')
        notebook.add(tab_contacts, text="👥 Контактные лица")
        self._create_contacts_tab(tab_contacts, client['id'])

        # Вкладка 3: Email
        tab_emails = tk.Frame(notebook, bg='white')
        notebook.add(tab_emails, text="📧 Email")
        self._create_emails_tab(tab_emails, client['id'])

        # Вкладка 4: История
        tab_history = tk.Frame(notebook, bg='white')
        notebook.add(tab_history, text="📅 История")
        self._create_history_tab(tab_history, client['id'])

        # ============================================
        # ПАНЕЛЬ КНОПОК ВНИЗУ
        # ============================================
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
        ).pack(side=tk.LEFT, padx=10)

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
        """Вкладка 'Контактные лица'"""
        tk.Label(
            parent,
            text="Контактные лица",
            font=("Arial", 16, "bold"),
            bg='white'
        ).pack(pady=20)

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

        # Список контактов
        for contact in contacts:
            contact_frame = tk.Frame(parent, bg='#f8f9fa', relief='solid', bd=1)
            contact_frame.pack(padx=20, pady=10, fill=tk.X)

            primary_label = " ⭐ ОСНОВНОЙ" if contact['is_primary'] else ""

            tk.Label(
                contact_frame,
                text=f"{contact['full_name']}{primary_label}",
                font=("Arial", 14, "bold"),
                bg='#f8f9fa'
            ).pack(anchor='w', padx=15, pady=8)

            tk.Label(
                contact_frame,
                text=f"Должность: {contact['position'] or 'Не указана'}",
                font=("Arial", 11),
                bg='#f8f9fa',
                fg='#666'
            ).pack(anchor='w', padx=15)

            tk.Label(
                contact_frame,
                text=f"Телефон: {contact['phone'] or 'Не указан'}",
                font=("Arial", 11),
                bg='#f8f9fa',
                fg='#666'
            ).pack(anchor='w', padx=15, pady=(0, 8))

    def _create_emails_tab(self, parent, client_id):
        """Вкладка 'Email'"""
        tk.Label(
            parent,
            text="Email адреса",
            font=("Arial", 16, "bold"),
            bg='white'
        ).pack(pady=20)

        # Получаем email
        emails = self.emails_mgr.get_by_client(client_id)

        if not emails:
            tk.Label(
                parent,
                text="Email адресов нет",
                font=("Arial", 12),
                fg="gray",
                bg='white'
            ).pack(pady=30)
            return

        # Список email
        for email in emails:
            email_frame = tk.Frame(parent, bg='#f8f9fa', relief='solid', bd=1)
            email_frame.pack(padx=20, pady=10, fill=tk.X)

            primary_label = " ⭐ ОСНОВНОЙ" if email['is_primary'] else ""

            tk.Label(
                email_frame,
                text=f"📧 {email['email']}{primary_label}",
                font=("Arial", 12),
                bg='#f8f9fa'
            ).pack(anchor='w', padx=15, pady=12)

    def _create_history_tab(self, parent, client_id):
        """Вкладка 'История'"""
        tk.Label(
            parent,
            text="История взаимодействий",
            font=("Arial", 16, "bold"),
            bg='white'
        ).pack(pady=20)

        # Получаем историю
        history = self.interactions_mgr.get_by_client(client_id)

        if not history:
            tk.Label(
                parent,
                text="История пуста",
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

        # Список записей
        for record in history:
            record_frame = tk.Frame(scrollable_frame, bg='#f8f9fa', relief='solid', bd=1)
            record_frame.pack(padx=20, pady=8, fill=tk.X)

            # Иконка по типу
            type_icons = {
                "Звонок": "📞",
                "Отправлено КП": "📄",
                "Запуск работы": "🚀",
                "Работа выполнена": "✅"
            }
            icon = type_icons.get(record['type'], "📌")

            tk.Label(
                record_frame,
                text=f"{icon} {record['type']} — {record['date']}",
                font=("Arial", 12, "bold"),
                bg='#f8f9fa'
            ).pack(anchor='w', padx=15, pady=8)

            if record['description']:
                tk.Label(
                    record_frame,
                    text=record['description'],
                    font=("Arial", 10),
                    bg='#f8f9fa',
                    fg='#666',
                    wraplength=700,
                    justify='left'
                ).pack(anchor='w', padx=15, pady=(0, 8))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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
                self._show_clients_list()
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
                self._show_clients_list()

            except Exception as e:
                show_message(
                    self.parent_frame.master,  # ← ИЗМЕНЕНО!
                    "Ошибка",
                    f"Не удалось удалить клиента:\n{e}",
                    "error"
                )

    def _edit_client(self, client, parent_window):
        """Редактировать клиента"""

        edit_dialog = tk.Toplevel(parent_window)
        edit_dialog.title(f"Редактирование: {client['company']}")
        edit_dialog.geometry("750x800")
        edit_dialog.configure(bg='white')
        edit_dialog.resizable(False, False)

        header = tk.Frame(edit_dialog, bg='#333333', height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        tk.Label(header, text="✏ Редактирование клиента", font=("Arial", 18, "bold"), fg='white', bg='#333333').pack(
            pady=15)

        buttons_container = tk.Frame(edit_dialog, bg='#f0f0f0', height=80)
        buttons_container.pack(fill=tk.X, side=tk.BOTTOM)
        buttons_container.pack_propagate(False)
        buttons_frame = tk.Frame(buttons_container, bg='#f0f0f0')
        buttons_frame.pack(pady=15)

        client_data = self.clients_mgr.get_by_id(client['id'])
        contacts_db = self.contact_persons_mgr.get_by_client(client['id'])
        emails_db = self.emails_mgr.get_by_client(client['id'])

        # Canvas
        canvas = tk.Canvas(edit_dialog, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(edit_dialog, orient="vertical", command=canvas.yview)
        scrollable_content = tk.Frame(canvas, bg='white')
        scrollable_content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scrollable_content, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Основная информация ---
        tk.Label(scrollable_content, text="📋 Основная информация", font=("Arial", 14, "bold"), bg='white',
                 fg='#333').pack(anchor='w', padx=20, pady=(10, 15))
        info_frame = tk.Frame(scrollable_content, bg='white')
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        tk.Label(info_frame, text="Название компании *", font=("Arial", 10), bg='white').pack(anchor='w')
        company_entry = tk.Entry(info_frame, font=("Arial", 11), relief="solid", borderwidth=1)
        company_entry.insert(0, client_data['company'])
        company_entry.pack(fill=tk.X, pady=5, ipady=5)

        tk.Label(info_frame, text="Адрес", font=("Arial", 10), bg='white').pack(anchor='w')
        address_entry = tk.Entry(info_frame, font=("Arial", 11), relief="solid", borderwidth=1)
        address_entry.insert(0, client_data['address'] or "")
        address_entry.pack(fill=tk.X, pady=5, ipady=5)

        tk.Label(info_frame, text="Примечания", font=("Arial", 10), bg='white').pack(anchor='w')
        notes_text = tk.Text(info_frame, font=("Arial", 10), height=4, relief="solid", borderwidth=1)
        notes_text.insert('1.0', client_data['notes'] or "")
        notes_text.pack(fill=tk.X, pady=5)

        # --- КОНТАКТЫ (ДИНАМИКА) ---
        contacts_header = tk.Frame(scrollable_content, bg='white')
        contacts_header.pack(fill=tk.X, padx=20, pady=(20, 10))
        tk.Label(contacts_header, text="👥 Контактные лица", font=("Arial", 14, "bold"), bg='white', fg='#333').pack(
            side=tk.LEFT)
        tk.Label(contacts_header, text="(до 4)", font=("Arial", 10), bg='white', fg='#999').pack(side=tk.LEFT, padx=10)
        contacts_container = tk.Frame(scrollable_content, bg='white')
        contacts_container.pack(fill=tk.X, padx=20, pady=(0, 10))

        contact_widgets = []
        primary_contact_var = tk.IntVar()

        def update_contact_ui():
            sel = primary_contact_var.get()
            active = [w for w in contact_widgets if not w.get('deleted')]
            for idx, w in enumerate(active):
                w['radio'].config(value=idx, text=f"Контакт #{idx + 1}")
                if idx == sel:
                    w['p_label'].config(text="⭐ ОСНОВНОЙ")
                else:
                    w['p_label'].config(text="")

        def create_contact(data=None):
            active = [w for w in contact_widgets if not w.get('deleted')]
            if len(active) >= 4:
                from utils.helpers import show_message
                show_message(edit_dialog, "Лимит", "Максимум 4 контакта", "warning")
                return

            idx = len(active)
            box = tk.Frame(contacts_container, bg='#f8f9fa', relief='solid', bd=1)
            box.pack(fill=tk.X, pady=5)

            head = tk.Frame(box, bg='#f8f9fa')
            head.pack(fill=tk.X, padx=10, pady=8)

            rad = tk.Radiobutton(head, variable=primary_contact_var, value=idx, bg='#f8f9fa', command=update_contact_ui)
            rad.pack(side=tk.LEFT)
            lbl = tk.Label(head, text="", font=("Arial", 9, "bold"), bg='#f8f9fa', fg='#4CAF50')
            lbl.pack(side=tk.LEFT)

            def remove(b=box, w=None):
                if w.get('id'): w['deleted'] = True
                b.destroy()
                if not w.get('id') and w in contact_widgets: contact_widgets.remove(w)

                # Сброс основного если удалили его
                rem = [x for x in contact_widgets if not x.get('deleted')]
                if primary_contact_var.get() >= len(rem): primary_contact_var.set(0)
                update_contact_ui()

            tk.Button(head, text="✖", command=lambda: remove(box, widget), bg="#dc3545", fg="white",
                      font=("Arial", 8)).pack(side=tk.RIGHT)

            flds = tk.Frame(box, bg='#f8f9fa')
            flds.pack(fill=tk.X, padx=10, pady=(0, 8))

            tk.Label(flds, text="ФИО:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
            name = tk.Entry(flds, font=("Arial", 10), relief="solid", borderwidth=1)
            if data: name.insert(0, data['full_name'])
            name.pack(fill=tk.X, pady=2)

            tk.Label(flds, text="Должность:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
            pos = tk.Entry(flds, font=("Arial", 10), relief="solid", borderwidth=1)
            if data: pos.insert(0, data['position'] or "")
            pos.pack(fill=tk.X, pady=2)

            tk.Label(flds, text="Телефон:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
            ph = tk.Entry(flds, font=("Arial", 10), relief="solid", borderwidth=1)
            if data: ph.insert(0, data['phone'] or "")
            ph.pack(fill=tk.X, pady=2)

            widget = {'box': box, 'name': name, 'position': pos, 'phone': ph, 'radio': rad, 'p_label': lbl,
                      'id': data['id'] if data else None, 'deleted': False}
            contact_widgets.append(widget)
            if data and data['is_primary']: primary_contact_var.set(idx)
            update_contact_ui()
            return widget

        for c in contacts_db: create_contact(c)
        if not contacts_db: create_contact()
        tk.Button(contacts_container, text="+ Добавить контакт", command=create_contact, bg="#28a745", fg="white").pack(
            pady=5)

        # --- EMAIL (ДИНАМИКА) ---
        email_header = tk.Frame(scrollable_content, bg='white')
        email_header.pack(fill=tk.X, padx=20, pady=(20, 10))
        tk.Label(email_header, text="📧 Email адреса", font=("Arial", 14, "bold"), bg='white', fg='#333').pack(
            side=tk.LEFT)
        tk.Label(email_header, text="(до 4)", font=("Arial", 10), bg='white', fg='#999').pack(side=tk.LEFT, padx=10)
        emails_container = tk.Frame(scrollable_content, bg='white')
        emails_container.pack(fill=tk.X, padx=20, pady=(0, 30))

        email_widgets = []
        primary_email_var = tk.IntVar()

        def update_email_ui():
            sel = primary_email_var.get()
            active = [w for w in email_widgets if not w.get('deleted')]
            for idx, w in enumerate(active):
                w['radio'].config(value=idx, text=f"Email #{idx + 1}")
                if idx == sel:
                    w['p_label'].config(text="⭐ ОСНОВНОЙ")
                else:
                    w['p_label'].config(text="")

        def create_email(data=None):
            active = [w for w in email_widgets if not w.get('deleted')]
            if len(active) >= 4:
                from utils.helpers import show_message
                show_message(edit_dialog, "Лимит", "Максимум 4 email", "warning")
                return

            idx = len(active)
            box = tk.Frame(emails_container, bg='#f8f9fa', relief='solid', bd=1)
            box.pack(fill=tk.X, pady=5)

            head = tk.Frame(box, bg='#f8f9fa')
            head.pack(fill=tk.X, padx=10, pady=8)

            rad = tk.Radiobutton(head, variable=primary_email_var, value=idx, bg='#f8f9fa', command=update_email_ui)
            rad.pack(side=tk.LEFT)
            lbl = tk.Label(head, text="", font=("Arial", 9, "bold"), bg='#f8f9fa', fg='#4CAF50')
            lbl.pack(side=tk.LEFT)

            def remove(b=box, w=None):
                if w.get('id'): w['deleted'] = True
                b.destroy()
                if not w.get('id') and w in email_widgets: email_widgets.remove(w)
                rem = [x for x in email_widgets if not x.get('deleted')]
                if primary_email_var.get() >= len(rem): primary_email_var.set(0)
                update_email_ui()

            tk.Button(head, text="✖", command=lambda: remove(box, widget), bg="#dc3545", fg="white",
                      font=("Arial", 8)).pack(side=tk.RIGHT)

            flds = tk.Frame(box, bg='#f8f9fa')
            flds.pack(fill=tk.X, padx=10, pady=(0, 8))

            tk.Label(flds, text="Email:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
            em = tk.Entry(flds, font=("Arial", 10), relief="solid", borderwidth=1)
            if data: em.insert(0, data['email'])
            em.pack(fill=tk.X, pady=2)

            widget = {'box': box, 'email': em, 'radio': rad, 'p_label': lbl, 'id': data['id'] if data else None,
                      'deleted': False}
            email_widgets.append(widget)
            if data and data['is_primary']: primary_email_var.set(idx)
            update_email_ui()
            return widget

        for e in emails_db: create_email(e)
        if not emails_db: create_email()
        tk.Button(emails_container, text="+ Добавить Email", command=create_email, bg="#28a745", fg="white").pack(
            pady=5)

        # --- СОХРАНЕНИЕ ---
        def save_changes():
            from utils.helpers import show_message
            company = company_entry.get().strip()
            if not company: return show_message(edit_dialog, "Внимание", "Укажите компанию", "warning")

            try:
                self.clients_mgr.update(client['id'], company, address_entry.get().strip(),
                                        notes_text.get('1.0', 'end-1c').strip())

                # Контакты
                curr = 0
                for w in contact_widgets:
                    if w.get('deleted'):
                        if w.get('id'): self.contact_persons_mgr.delete(w['id'])
                    else:
                        nm = w['name'].get().strip()
                        if nm:
                            is_p = (curr == primary_contact_var.get())
                            if w.get('id'):
                                self.contact_persons_mgr.update(w['id'], nm, w['position'].get(), w['phone'].get(),
                                                                is_p)
                            else:
                                self.contact_persons_mgr.add(client['id'], nm, w['position'].get(), w['phone'].get(),
                                                             is_p)
                        curr += 1

                # Email
                curr = 0
                for w in email_widgets:
                    if w.get('deleted'):
                        if w.get('id'): self.emails_mgr.delete(w['id'])
                    else:
                        mail = w['email'].get().strip()
                        if mail:
                            is_p = (curr == primary_email_var.get())
                            if w.get('id'):
                                self.emails_mgr.update(w['id'], mail, is_p)
                            else:
                                self.emails_mgr.add(client['id'], mail, is_p)
                        curr += 1

                show_message(edit_dialog, "Успех", "Сохранено!", "success")
                edit_dialog.destroy()
                parent_window.destroy()
                self._show_clients_list()

                # Открыть заново
                upd = self.clients_mgr.get_by_id(client['id'])
                if upd:
                    # Преобразовать Row в dict
                    d_client = dict(upd)
                    # Добавить данные о primary контакте вручную для совместимости с методом open
                    prim = self.contact_persons_mgr.get_primary(upd['id'])
                    if prim:
                        d_client['primary_contact'] = prim['full_name']
                        d_client['primary_position'] = prim['position']
                        d_client['primary_phone'] = prim['phone']
                    else:
                        d_client['primary_contact'] = ""
                        d_client['primary_position'] = ""
                        d_client['primary_phone'] = ""

                    self._open_client_card(d_client)

            except Exception as ex:
                show_message(edit_dialog, "Ошибка", str(ex), "error")

            # ============================================
            # КНОПКИ (В НИЖНЕМ КОНТЕЙНЕРЕ)
            # ============================================

            # Центрируем фрейм с кнопками внутри контейнера

        buttons_frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Button(
            buttons_frame,
            text="💾 Сохранить",
            command=save_changes,
            bg="#41a5be",
            fg="black",
            font=("Arial", 12, "bold"),
            relief="flat",
            width=15,  # Фиксированная ширина
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
            width=15,  # Фиксированная ширина
            height=1,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

        def on_mw(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mw))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))