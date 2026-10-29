# -*- coding: utf-8 -*-
"""
Представление раздела "Эксперты" на базе TableViewTemplate
"""
import tkinter as tk
from tkinter import ttk, messagebox
from views.table_view_template import TableViewTemplate
from utils.helpers import show_message
from utils.constants import Colors, TableView
from utils.ui_helpers import center_toplevel


class ExpertsView(TableViewTemplate):
    """Раздел экспертов с поиском, сортировкой и пагинацией"""

    TITLE = "Эксперты"
    ADD_BUTTON_TEXT = "+ Добавить эксперта"
    SEARCH_FIELDS_TEXT = "названию, контакту, видам работ"
    COLUMNS = ("ID", "Название", "Контактное лицо", "Телефон", "Email", "Виды работ")
    COLUMN_WIDTHS = {
        "ID": 50,
        "Название": 200,
        "Контактное лицо": 180,
        "Телефон": 140,
        "Email": 200,
        "Виды работ": 250
    }
    STRETCH_COLUMNS = ["Название", "Виды работ"]
    ID_COLUMN = "ID"
    SORT_OPTIONS = [
        ("name", "По названию (А-Я)"),
        ("name:DESC", "По названию (Я-А)"),
    ]
    PAGE_SIZE = 50

    def __init__(self, parent_frame, experts_mgr):
        super().__init__(parent_frame, experts_mgr)
        self.experts_mgr = experts_mgr

    def _on_tree_enter(self, event):
        pass

    def _on_tree_leave(self, event):
        pass

    def _on_tree_motion(self, event):
        pass

    def _get_data(self, page, search, sort_by, sort_order):
        """Загрузка данных с пагинацией и поиском"""
        return self.experts_mgr.get_paginated(
            page=page,
            per_page=self.PAGE_SIZE,
            search=search or None,
            sort_by=sort_by,
            sort_order=sort_order or "ASC"
        )

    def _item_to_row_values(self, item):
        """Преобразует эксперта в строку таблицы"""
        if not isinstance(item, dict):
            item = dict(item) if hasattr(item, 'keys') else {}

        name = item.get('name', '—')
        primary_contact = item.get('primary_contact', '—')
        primary_phone = item.get('primary_phone', '—')
        primary_email = item.get('primary_email', '—')
        specializations = item.get('specializations_str', '')
        if not specializations and 'specializations' in item:
            specs = item['specializations']
            if isinstance(specs, list):
                specializations = ", ".join(specs)
            elif isinstance(specs, str):
                specializations = specs
        specializations = specializations or '—'

        return (
            item.get('id', ''),
            name,
            primary_contact or '—',
            primary_phone or '—',
            primary_email or '—',
            specializations
        )

    def _open_create_dialog(self):
        """Диалог создания эксперта"""
        dialog, content, buttons_frame = self._create_dialog(
            "➕ Новый эксперт", 
            "750x750"
        )
        
        # Основная информация
        main_fields = self._create_form_section(content, "📋 Основная информация", [
            {'name': 'name', 'label': 'Название компании', 'type': 'entry', 'required': True},
            {'name': 'notes', 'label': 'Примечания', 'type': 'text', 'required': False, 'height': 3}
        ])
        
        # --- КОНТАКТНЫЕ ЛИЦА ---
        contacts_header_frame = tk.Frame(content, bg='white')
        contacts_header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        tk.Label(contacts_header_frame, text="👥 Контактные лица", font=("Arial", 14, "bold"), bg='white',
                 fg='#333').pack(side=tk.LEFT)
        tk.Label(contacts_header_frame, text="(до 4, выберите основной)", font=("Arial", 10), bg='white',
                 fg='#999').pack(side=tk.LEFT, padx=10)

        contacts_container = tk.Frame(content, bg='white')
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
                    widget['primary_label'].config(text="ОСНОВНОЙ", fg="red", font=("Arial", 9, "bold"))
                else:
                    widget['primary_label'].config(text="", fg="black", font=("Arial", 9))

        def create_contact_fields():
            """Создает поля для контактного лица"""
            active_widgets = [w for w in contact_widgets if not w.get('deleted', False)]
            if len(active_widgets) >= 4:
                show_message(dialog, "Лимит", "Максимум 4 контактных лица", "warning")
                return None

            idx = len(contact_widgets)

            # Контейнер для контакта
            contact_box = tk.Frame(contacts_container, bg='#f8f9fa', relief="ridge", borderwidth=1)
            contact_box.pack(fill=tk.X, pady=5)

            # Верхняя панель с радио-кнопкой и меткой
            top_frame = tk.Frame(contact_box, bg='#f8f9fa')
            top_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

            radio_btn = tk.Radiobutton(
                top_frame,
                text=f"Контакт #{idx + 1}",
                variable=primary_contact_var,
                value=idx,
                bg='#f8f9fa',
                font=("Arial", 9, "bold"),
                command=update_primary_contact_ui
            )
            radio_btn.pack(side=tk.LEFT)

            primary_label = tk.Label(top_frame, text="", fg="red", font=("Arial", 9, "bold"), bg='#f8f9fa')
            primary_label.pack(side=tk.LEFT, padx=(5, 0))

            # Поля контакта
            fields_frame = tk.Frame(contact_box, bg='#f8f9fa')
            fields_frame.pack(fill=tk.X, padx=10, pady=5)

            # Поле имени
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
            return contact_widget

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

        # --- ВИДЫ РАБОТ ---
        specs_header_frame = tk.Frame(content, bg='white')
        specs_header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        tk.Label(
            specs_header_frame,
            text="🛠 Виды работ",
            font=("Arial", 14, "bold"),
            bg='white',
            fg='#333'
        ).pack(side=tk.LEFT)

        specs_container = tk.Frame(content, bg='white')
        specs_container.pack(fill=tk.X, padx=20, pady=(0, 10))

        specs = []

        add_row = tk.Frame(specs_container, bg='white')
        add_row.pack(fill=tk.X, pady=(0, 10))

        spec_entry = tk.Entry(add_row, font=("Arial", 11), relief="solid", borderwidth=1)
        spec_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        specs_list_frame = tk.Frame(specs_container, bg='white')
        specs_list_frame.pack(fill=tk.X)

        def refresh_specs():
            for w in specs_list_frame.winfo_children():
                w.destroy()
            if not specs:
                tk.Label(
                    specs_list_frame,
                    text="Виды работ не добавлены",
                    font=("Arial", 11),
                    fg="gray",
                    bg='white'
                ).pack(anchor='w', pady=2)
                return
            for s in specs:
                row = tk.Frame(specs_list_frame, bg='#f8f9fa', relief='solid', bd=1)
                row.pack(fill=tk.X, pady=3)
                tk.Label(row, text=s, font=("Arial", 11), bg='#f8f9fa', anchor='w').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=6)
                tk.Button(
                    row,
                    text="Удалить",
                    command=lambda v=s: (specs.remove(v), refresh_specs()),
                    bg="#d9534f",
                    fg="white",
                    font=("Arial", 10, "bold"),
                    relief="flat",
                    cursor="hand2",
                    padx=12,
                    pady=3
                ).pack(side=tk.RIGHT, padx=10, pady=6)

        def add_spec(_event=None):
            v = spec_entry.get().strip()
            if not v:
                return
            if any(x.lower() == v.lower() for x in specs):
                spec_entry.delete(0, tk.END)
                return
            specs.append(v)
            spec_entry.delete(0, tk.END)
            refresh_specs()

        tk.Button(
            add_row,
            text="Добавить",
            command=add_spec,
            bg="#41a5be",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=6
        ).pack(side=tk.LEFT, padx=(10, 0))

        spec_entry.bind("<Return>", add_spec)
        refresh_specs()
        
        def save_expert():
            """Сохранение нового эксперта"""
            try:
                # Валидация
                name = main_fields['name'].get().strip()
                if not name:
                    show_message(dialog, "Ошибка", "Укажите название компании", "error")
                    return
                
                # Сбор данных
                expert_data = {
                    'name': name,
                    'notes': main_fields['notes'].get('1.0', tk.END).strip(),
                    'contacts': [],
                    'specializations': specs
                }
                
                # Сбор контактных лиц
                for idx, contact_widget in enumerate(contact_widgets):
                    if contact_widget.get('deleted', False):
                        continue
                    
                    contact_name = contact_widget['name'].get().strip()
                    if not contact_name:
                        continue
                    
                    contact_data = {
                        'full_name': contact_name,
                        'position': contact_widget['position'].get().strip(),
                        'phone': contact_widget['phone'].get().strip(),
                        'email': contact_widget['email'].get().strip(),
                        'is_primary': (primary_contact_var.get() == idx)
                    }
                    expert_data['contacts'].append(contact_data)
                
                # Сохранение
                expert_id = self.experts_mgr.add_expert_with_contacts(expert_data)
                
                if expert_id:
                    show_message(dialog, "Успех", "Эксперт успешно добавлен!", "success")
                    dialog.destroy()
                    self._refresh_data()
                else:
                    show_message(dialog, "Ошибка", "Не удалось добавить эксперта", "error")
                    
            except Exception as e:
                show_message(dialog, "Ошибка", f"Произошла ошибка: {str(e)}", "error")
        
        self._create_dialog_buttons(buttons_frame, save_expert)

    def _edit_expert(self, expert_id):
        """Диалог редактирования эксперта"""
        try:
            expert = self.experts_mgr.get_expert_by_id(expert_id)
            if not expert:
                show_message(self.parent_frame, "Ошибка", f"Эксперт с ID {expert_id} не найден", "error")
                return

            dialog, content, buttons_frame = self._create_dialog(
                f"✏️ Редактирование: {expert.get('name', 'Эксперт')}",
                "750x750"
            )

            # Основная информация
            main_fields = self._create_form_section(content, "📋 Основная информация", [
                {
                    'name': 'name',
                    'label': 'Название компании',
                    'type': 'entry',
                    'required': True,
                    'default': expert.get('name', '')
                },
                {
                    'name': 'notes',
                    'label': 'Примечания',
                    'type': 'text',
                    'required': False,
                    'height': 3,
                    'default': expert.get('notes', '') or ''
                }
            ])

            # --- КОНТАКТНЫЕ ЛИЦА ---
            contacts_header_frame = tk.Frame(content, bg='white')
            contacts_header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

            tk.Label(
                contacts_header_frame,
                text="👥 Контактные лица",
                font=("Arial", 14, "bold"),
                bg='white',
                fg='#333'
            ).pack(side=tk.LEFT)
            tk.Label(
                contacts_header_frame,
                text="(до 4, выберите основной)",
                font=("Arial", 10),
                bg='white',
                fg='#999'
            ).pack(side=tk.LEFT, padx=10)

            contacts_container = tk.Frame(content, bg='white')
            contacts_container.pack(fill=tk.X, padx=20, pady=(0, 10))

            contact_widgets = []
            primary_contact_var = tk.IntVar(value=0)

            def _active_contacts():
                return [w for w in contact_widgets if not w.get('deleted', False)]

            def update_primary_contact_ui():
                selected_idx = primary_contact_var.get()

                # если выбран удалённый контакт — сбросить на первый активный
                if selected_idx < len(contact_widgets) and contact_widgets[selected_idx].get('deleted', False):
                    for i, w in enumerate(contact_widgets):
                        if not w.get('deleted', False):
                            primary_contact_var.set(i)
                            selected_idx = i
                            break

                for idx, widget in enumerate(contact_widgets):
                    if widget.get('deleted', False):
                        continue

                    widget['radio'].config(text=f"Контакт #{idx + 1}")
                    if idx == selected_idx:
                        widget['primary_label'].config(text="ОСНОВНОЙ", fg="red", font=("Arial", 9, "bold"))
                    else:
                        widget['primary_label'].config(text="", fg="black", font=("Arial", 9))

            def delete_contact_ui(widget):
                widget['deleted'] = True
                widget['box'].pack_forget()
                update_primary_contact_ui()

            def create_contact_fields(contact_data=None):
                active_widgets = _active_contacts()
                if len(active_widgets) >= 4:
                    show_message(dialog, "Лимит", "Максимум 4 контактных лица", "warning")
                    return None

                idx = len(contact_widgets)

                contact_box = tk.Frame(contacts_container, bg='#f8f9fa', relief="ridge", borderwidth=1)
                contact_box.pack(fill=tk.X, pady=5)

                top_frame = tk.Frame(contact_box, bg='#f8f9fa')
                top_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

                radio_btn = tk.Radiobutton(
                    top_frame,
                    text=f"Контакт #{idx + 1}",
                    variable=primary_contact_var,
                    value=idx,
                    bg='#f8f9fa',
                    font=("Arial", 9, "bold"),
                    command=update_primary_contact_ui
                )
                radio_btn.pack(side=tk.LEFT)

                primary_label = tk.Label(top_frame, text="", fg="red", font=("Arial", 9, "bold"), bg='#f8f9fa')
                primary_label.pack(side=tk.LEFT, padx=(5, 0))

                fields_frame = tk.Frame(contact_box, bg='#f8f9fa')
                fields_frame.pack(fill=tk.X, padx=10, pady=5)

                tk.Label(fields_frame, text="ФИО:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
                name_entry = tk.Entry(fields_frame, font=("Arial", 10), relief="solid", borderwidth=1)
                name_entry.pack(fill=tk.X, pady=2, ipady=3)

                tk.Label(fields_frame, text="Должность:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
                position_entry = tk.Entry(fields_frame, font=("Arial", 10), relief="solid", borderwidth=1)
                position_entry.pack(fill=tk.X, pady=2, ipady=3)

                tk.Label(fields_frame, text="Телефон:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
                phone_entry = tk.Entry(fields_frame, font=("Arial", 10), relief="solid", borderwidth=1)
                phone_entry.pack(fill=tk.X, pady=2, ipady=3)

                tk.Label(fields_frame, text="Email:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
                email_entry = tk.Entry(fields_frame, font=("Arial", 10), relief="solid", borderwidth=1)
                email_entry.pack(fill=tk.X, pady=2, ipady=3)

                contact_widget = {
                    'id': None,
                    'deleted': False,
                    'box': contact_box,
                    'name': name_entry,
                    'position': position_entry,
                    'phone': phone_entry,
                    'email': email_entry,
                    'radio': radio_btn,
                    'primary_label': primary_label
                }

                tk.Button(
                    top_frame,
                    text="Удалить",
                    command=lambda w=contact_widget: delete_contact_ui(w),
                    bg="#d9534f",
                    fg="white",
                    font=("Arial", 9, "bold"),
                    relief="flat",
                    cursor="hand2"
                ).pack(side=tk.RIGHT)

                # заполнение из БД
                if contact_data:
                    contact_widget['id'] = contact_data.get('id')
                    name_entry.insert(0, contact_data.get('full_name', '') or '')
                    position_entry.insert(0, contact_data.get('position', '') or '')
                    phone_entry.insert(0, contact_data.get('phone', '') or '')
                    email_entry.insert(0, contact_data.get('email', '') or '')

                contact_widgets.append(contact_widget)

                # выставляем основной контакт
                if contact_data and contact_data.get('is_primary'):
                    primary_contact_var.set(idx)

                update_primary_contact_ui()
                return contact_widget

            add_contact_btn = tk.Button(
                contacts_container,
                text="+ Добавить контакт",
                command=lambda: create_contact_fields(),
                bg="#28a745",
                fg="white",
                font=("Arial", 10),
                cursor="hand2"
            )
            add_contact_btn.pack(pady=5)

            # загрузка существующих контактов
            contacts = expert.get('contacts', []) or []
            if not isinstance(contacts, list):
                contacts = []
            if contacts:
                for c in contacts:
                    create_contact_fields(c)
            else:
                create_contact_fields()

            # --- ВИДЫ РАБОТ ---
            specs_header_frame = tk.Frame(content, bg='white')
            specs_header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

            tk.Label(
                specs_header_frame,
                text="🛠 Виды работ",
                font=("Arial", 14, "bold"),
                bg='white',
                fg='#333'
            ).pack(side=tk.LEFT)

            specs_container = tk.Frame(content, bg='white')
            specs_container.pack(fill=tk.X, padx=20, pady=(0, 10))

            specs = list(expert.get('specializations', []) or [])

            add_row = tk.Frame(specs_container, bg='white')
            add_row.pack(fill=tk.X, pady=(0, 10))

            spec_entry = tk.Entry(add_row, font=("Arial", 11), relief="solid", borderwidth=1)
            spec_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

            specs_list_frame = tk.Frame(specs_container, bg='white')
            specs_list_frame.pack(fill=tk.X)

            def refresh_specs():
                for w in specs_list_frame.winfo_children():
                    w.destroy()
                if not specs:
                    tk.Label(
                        specs_list_frame,
                        text="Виды работ не добавлены",
                        font=("Arial", 11),
                        fg="gray",
                        bg='white'
                    ).pack(anchor='w', pady=2)
                    return
                for s in specs:
                    row = tk.Frame(specs_list_frame, bg='#f8f9fa', relief='solid', bd=1)
                    row.pack(fill=tk.X, pady=3)
                    tk.Label(row, text=s, font=("Arial", 11), bg='#f8f9fa', anchor='w').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=6)
                    tk.Button(
                        row,
                        text="Удалить",
                        command=lambda v=s: (specs.remove(v), refresh_specs()),
                        bg="#d9534f",
                        fg="white",
                        font=("Arial", 10, "bold"),
                        relief="flat",
                        cursor="hand2",
                        padx=12,
                        pady=3
                    ).pack(side=tk.RIGHT, padx=10, pady=6)

            def add_spec(_event=None):
                v = spec_entry.get().strip()
                if not v:
                    return
                if any(x.lower() == v.lower() for x in specs):
                    spec_entry.delete(0, tk.END)
                    return
                specs.append(v)
                spec_entry.delete(0, tk.END)
                refresh_specs()

            tk.Button(
                add_row,
                text="Добавить",
                command=add_spec,
                bg="#41a5be",
                fg="white",
                font=("Arial", 11, "bold"),
                relief="flat",
                cursor="hand2",
                padx=16,
                pady=6
            ).pack(side=tk.LEFT, padx=(10, 0))

            spec_entry.bind("<Return>", add_spec)
            refresh_specs()

            def save():
                try:
                    name = main_fields['name'].get().strip()
                    if not name:
                        show_message(dialog, "Ошибка", "Укажите название компании", "error")
                        return

                    notes = main_fields['notes'].get('1.0', tk.END).strip()

                    contacts_payload = []
                    for idx, w in enumerate(contact_widgets):
                        if w.get('deleted', False):
                            continue

                        full_name = w['name'].get().strip()
                        position = w['position'].get().strip()
                        phone = w['phone'].get().strip()
                        email = w['email'].get().strip()

                        if not full_name:
                            # пустые контакты не сохраняем
                            continue

                        contacts_payload.append({
                            'id': w.get('id'),
                            'full_name': full_name,
                            'position': position,
                            'phone': phone,
                            'email': email,
                            'is_primary': (primary_contact_var.get() == idx)
                        })

                    success = self.experts_mgr.update_expert_with_contacts(
                        expert_id,
                        {
                            'name': name,
                            'notes': notes,
                            'contacts': contacts_payload,
                            'specializations': specs
                        }
                    )

                    if success:
                        show_message(dialog, "Успех", "Изменения сохранены!", "success")
                        dialog.destroy()
                        self._refresh_data()
                    else:
                        show_message(dialog, "Ошибка", "Не удалось сохранить изменения", "error")

                except Exception as e:
                    show_message(dialog, "Ошибка", str(e), "error")

            self._create_dialog_buttons(buttons_frame, save)

        except Exception as e:
            show_message(self.parent_frame, "Ошибка", f"Произошла ошибка: {str(e)}", "error")

    def _on_row_double_click(self, expert_id):
        """Открыть карточку эксперта"""
        self._open_expert_card_by_id(expert_id)

    def _open_expert_card_by_id(self, expert_id):
        try:
            expert = self.experts_mgr.get_expert_by_id(expert_id)
            if expert:
                self._open_expert_card(expert)
        except Exception as e:
            show_message(self.parent_frame, "Ошибка", f"Не удалось открыть карточку: {e}", "error")

    def _open_expert_card(self, expert):
        card_window = tk.Toplevel(self.parent_frame)
        card_window.title(f"Карточка эксперта: {expert.get('name', '')}")
        card_window.geometry("1100x820")
        card_window.minsize(1000, 740)
        card_window.configure(bg=Colors.LIGHT)
        center_toplevel(card_window)

        header = tk.Frame(card_window, bg=Colors.DARK, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"🏢 {expert.get('name', '—')}",
            font=("Arial", 18, "bold"),
            fg=Colors.WHITE,
            bg=Colors.DARK
        ).pack(side=tk.LEFT, padx=20, pady=15)

        tk.Label(
            header,
            text=f"ID: {expert.get('id', '')}",
            font=("Arial", 12),
            fg=Colors.INFO,
            bg=Colors.DARK
        ).pack(side=tk.RIGHT, padx=20, pady=15)

        notebook = ttk.Notebook(card_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tab_main = tk.Frame(notebook, bg='white')
        notebook.add(tab_main, text="📋 Основное")
        self._create_expert_main_tab(tab_main, expert)

        tab_contacts = tk.Frame(notebook, bg='white')
        notebook.add(tab_contacts, text="👥 Контактные лица")
        self._create_expert_contacts_tab(tab_contacts, expert.get('id'), expert.get('contacts', []), card_window)

        tab_specs = tk.Frame(notebook, bg='white')
        notebook.add(tab_specs, text="🛠 Виды работ")
        self._create_expert_specializations_tab(tab_specs, expert.get('specializations', []))

        buttons_container = tk.Frame(card_window, bg=Colors.SURFACE, height=76)
        buttons_container.pack(fill=tk.X, side=tk.BOTTOM)
        buttons_container.pack_propagate(False)

        buttons_frame = tk.Frame(buttons_container, bg=Colors.SURFACE)
        buttons_frame.pack(fill=tk.X, padx=20, pady=14)

        expert_id = expert.get('id')
        tk.Button(
            buttons_frame,
            text="Удалить",
            command=lambda: self._delete_expert_from_card(
                expert_id,
                expert.get('name', ''),
                card_window
            ),
            bg=Colors.DANGER,
            fg=Colors.WHITE,
            activebackground=Colors.DANGER_HOVER,
            activeforeground=Colors.WHITE,
            font=("Arial", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=9
        ).pack(side=tk.LEFT)

        tk.Button(
            buttons_frame,
            text="Закрыть",
            command=card_window.destroy,
            bg=Colors.LIGHT,
            fg=Colors.TEXT,
            activebackground=Colors.BORDER,
            activeforeground=Colors.TEXT,
            font=("Arial", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=9
        ).pack(side=tk.RIGHT, padx=(10, 0))

        tk.Button(
            buttons_frame,
            text="Редактировать",
            command=lambda: (card_window.destroy(), self._edit_expert(expert_id)),
            bg=Colors.PRIMARY,
            fg=Colors.WHITE,
            activebackground=Colors.PRIMARY_HOVER,
            activeforeground=Colors.WHITE,
            font=("Arial", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=9
        ).pack(side=tk.RIGHT)

    def _delete_expert_from_card(self, expert_id, expert_name, card_window):
        """Удаляет эксперта после подтверждения и обновляет таблицу."""
        if not messagebox.askyesno(
            "Подтверждение",
            f"Удалить эксперта «{expert_name}»?",
            parent=card_window
        ):
            return

        try:
            self.experts_mgr.delete_expert(expert_id)
            card_window.destroy()
            self._refresh_data()
        except Exception as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось удалить эксперта:\n{error}",
                parent=card_window if card_window.winfo_exists() else self.parent_frame
            )

    def _create_expert_main_tab(self, parent, expert):
        tk.Label(
            parent,
            text="Основная информация",
            font=("Arial", 16, "bold"),
            bg='white'
        ).pack(pady=20)

        info_frame = tk.Frame(parent, bg='white')
        info_frame.pack(padx=30, pady=10, fill=tk.BOTH)

        tk.Label(info_frame, text="Компания:", font=("Arial", 12, "bold"), bg='white').grid(row=0, column=0, sticky='w', pady=8)
        tk.Label(info_frame, text=expert.get('name', '—'), font=("Arial", 12), bg='white').grid(row=0, column=1, sticky='w', pady=8)

        notes = expert.get('notes') or ""
        tk.Label(info_frame, text="Примечания:", font=("Arial", 12, "bold"), bg='white').grid(row=1, column=0, sticky='nw', pady=8)
        tk.Label(info_frame, text=notes if notes else "Не указаны", font=("Arial", 12), bg='white', wraplength=600, justify='left').grid(row=1, column=1, sticky='w', pady=8)

        created_at = expert.get('created_at')
        if created_at is not None:
            tk.Label(info_frame, text="Дата создания:", font=("Arial", 12, "bold"), bg='white').grid(row=2, column=0, sticky='w', pady=8)
            tk.Label(info_frame, text=str(created_at), font=("Arial", 12), bg='white').grid(row=2, column=1, sticky='w', pady=8)

        info_frame.grid_columnconfigure(1, weight=1)

    def _create_expert_contacts_tab(self, parent, expert_id, contacts, card_window):
        header_frame = tk.Frame(parent, bg="#f8f9fa")
        header_frame.pack(fill=tk.X, padx=15, pady=(20, 10))

        tk.Label(
            header_frame,
            text="Контактные лица",
            font=("Arial", 16, "bold"),
            bg="#f8f9fa",
            fg="#333"
        ).pack(side=tk.LEFT)

        sort_var = tk.StringVar(value="По ФИО (А-Я)")
        sort_options = [
            "По ФИО (А-Я)",
            "По ФИО (Я-А)",
            "По должности (А-Я)",
            "По должности (Я-А)"
        ]
        sort_combo = ttk.Combobox(
            header_frame,
            textvariable=sort_var,
            values=sort_options,
            state="readonly",
            width=20,
            font=("Arial", 9)
        )
        sort_combo.pack(side=tk.RIGHT, padx=(5, 10))
        tk.Label(
            header_frame,
            text="Сортировка:",
            font=("Arial", 10),
            bg="#f8f9fa",
            fg="#666"
        ).pack(side=tk.RIGHT, padx=(0, 5))

        if expert_id:
            tk.Button(
                header_frame,
                text="+ Добавить контакт",
                command=lambda: self._edit_expert_from_contacts(expert_id, card_window),
                bg="#28a745",
                fg="white",
                font=("Arial", 11, "bold"),
                relief="flat",
                cursor="hand2"
            ).pack(side=tk.RIGHT, padx=10)

        table_frame = tk.Frame(parent, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 20))

        tree = ttk.Treeview(
            table_frame,
            columns=("ID", "ФИО", "Должность", "Телефон", "Email"),
            show="headings",
            selectmode="browse"
        )
        column_widths = {
            "ID": (50, 50),
            "ФИО": (200, 150),
            "Должность": (150, 120),
            "Телефон": (120, 100),
            "Email": (200, 150)
        }
        for column, (width, min_width) in column_widths.items():
            tree.heading(column, text=column)
            tree.column(
                column,
                width=width,
                minwidth=min_width,
                stretch=column in ("ФИО", "Должность", "Email"),
                anchor="center" if column == "ID" else "w"
            )
        tree.tag_configure(
            "primary",
            background=Colors.COMPLETED_BG,
            foreground=Colors.COMPLETED_FG
        )

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def load_contacts(*_args):
            for item in tree.get_children():
                tree.delete(item)

            reverse = sort_var.get().endswith("(Я-А)")
            sort_by_position = "должности" in sort_var.get()
            sorted_contacts = sorted(
                contacts or [],
                key=lambda contact: str(
                    contact.get("position" if sort_by_position else "full_name") or ""
                ).casefold(),
                reverse=reverse
            )
            for contact in sorted_contacts:
                contact_id = contact.get("id", "")
                tree.insert(
                    "",
                    tk.END,
                    values=(
                        contact_id,
                        contact.get("full_name") or "—",
                        contact.get("position") or "—",
                        contact.get("phone") or "—",
                        contact.get("email") or "—"
                    ),
                    tags=("primary",) if contact.get("is_primary") else ()
                )

        def edit_contacts(_event=None):
            if expert_id:
                self._edit_expert_from_contacts(expert_id, card_window)

        sort_combo.bind("<<ComboboxSelected>>", load_contacts)
        tree.bind("<Double-1>", edit_contacts)
        load_contacts()

    def _edit_expert_from_contacts(self, expert_id, card_window):
        """Open the expert form to add or edit contact details."""
        if card_window.winfo_exists():
            card_window.destroy()
        self._edit_expert(expert_id)

    def _create_expert_specializations_tab(self, parent, specializations):
        tk.Label(
            parent,
            text="Виды работ",
            font=("Arial", 16, "bold"),
            bg='white'
        ).pack(pady=(20, 10))

        if not specializations:
            tk.Label(
                parent,
                text="Виды работ не указаны",
                font=("Arial", 12),
                fg="gray",
                bg='white'
            ).pack(pady=30)
            return

        canvas = tk.Canvas(parent, bg='white')
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for spec in specializations:
            tk.Label(
                scrollable_frame,
                text=f"• {spec}",
                font=("Arial", 12),
                bg='white',
                anchor='w'
            ).pack(fill=tk.X, padx=30, pady=4)

        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mouse_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
