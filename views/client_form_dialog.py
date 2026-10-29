# -*- coding: utf-8 -*-
"""
Диалог формы создания/редактирования клиента
Отвечает только за UI формы и валидацию полей
"""
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from utils.helpers import show_message
from utils.ui_helpers import center_toplevel
from utils.partner_card_reader import read_partner_card


class ClientFormDialog:
    """
    Диалог для создания или редактирования клиента
    
    Usage:
        # Создание
        dialog = ClientFormDialog(parent, on_save=callback)
        dialog.show()
        
        # Редактирование
        dialog = ClientFormDialog(parent, client_data=data, on_save=callback)
        dialog.show()
    """
    
    def __init__(self, parent, client_service, on_save=None, client_data=None):
        """
        Args:
            parent: родительское окно
            client_service: сервис для сохранения клиента
            on_save: callback после сохранения (client_id)
            client_data: данные клиента для редактирования (None для создания)
        """
        self.parent = parent
        self.client_service = client_service
        self.on_save = on_save
        self.client_data = client_data or {}
        self.dialog = None
        self.contact_widgets = []
        self.partner_field_widgets = {}
        self.saved_client_id = None  # ID сохранённого клиента
        
    def show(self):
        """Показать диалог"""
        is_edit = bool(self.client_data.get('id'))
        title = "Редактировать клиента" if is_edit else "Добавить клиента"
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(title)
        self.dialog.geometry("750x750")
        self.dialog.configure(bg='white')
        self.dialog.resizable(False, False)
        
        # Делаем модальным
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self._create_header(title)
        self._create_content()
        self._create_buttons()
        center_toplevel(self.dialog)
        
    def _create_header(self, title):
        """Создать заголовок"""
        header = tk.Frame(self.dialog, bg='#333333', height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"{'✏️' if self.client_data.get('id') else '➕'} {title}",
            font=("Arial", 18, "bold"),
            fg='white',
            bg='#333333'
        ).pack(pady=15)
        
    def _create_content(self):
        """Создать содержимое формы"""
        import_bar = tk.Frame(self.dialog, bg="white")
        import_bar.pack(fill=tk.X, padx=20, pady=(10, 0))
        tk.Button(
            import_bar,
            text="Загрузить карточку клиента (Word)",
            command=self._import_partner_card,
            bg="#0f766e",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6
        ).pack(side=tk.LEFT)

        # Canvas для прокрутки
        canvas_container = tk.Frame(self.dialog, bg='white')
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_container, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        
        self.scrollable_content = tk.Frame(canvas, bg='white')
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        self.scrollable_content.bind('<Configure>', on_frame_configure)
        
        canvas_window = canvas.create_window((0, 0), window=self.scrollable_content, anchor='nw')
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind('<Configure>', on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Прокрутка колесиком
        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mouse_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        self._create_main_info_section()
        self._create_partner_section()
        self._create_contacts_section()
        
    def _create_main_info_section(self):
        """Секция основной информации"""
        tk.Label(
            self.scrollable_content, 
            text="📋 Основная информация", 
            font=("Arial", 14, "bold"), 
            bg='white',
            fg='#333'
        ).pack(anchor='w', padx=20, pady=(15, 10))
        
        info_frame = tk.Frame(self.scrollable_content, bg='white')
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Название компании
        tk.Label(info_frame, text="Название компании *", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
        self.company_entry = tk.Entry(info_frame, font=("Arial", 11), relief="solid", borderwidth=1)
        self.company_entry.pack(fill=tk.X, pady=(5, 15), ipady=5)
        
        # Адрес
        tk.Label(info_frame, text="Адрес", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
        self.address_entry = tk.Entry(info_frame, font=("Arial", 11), relief="solid", borderwidth=1)
        self.address_entry.pack(fill=tk.X, pady=(5, 15), ipady=5)
        
        # Примечания
        tk.Label(info_frame, text="Примечания", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
        self.notes_text = tk.Text(info_frame, font=("Arial", 10), height=3, relief="solid", borderwidth=1, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.X, pady=(5, 0))
        
        # Заполняем данные если редактирование
        if self.client_data:
            self.company_entry.insert(0, self.client_data.get('company', ''))
            self.address_entry.insert(0, self.client_data.get('address', ''))
            notes = self.client_data.get('notes', '')
            if notes:
                self.notes_text.insert('1.0', notes)

    def _create_partner_section(self):
        """Добавить реквизиты партнёра и импорт из файла Word."""
        section = tk.LabelFrame(
            self.scrollable_content,
            text="Карточка партнёра",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#333",
            padx=12,
            pady=10
        )
        section.pack(fill=tk.X, padx=20, pady=(0, 18))
        section.columnconfigure(1, weight=1)

        fields = (
            ("full_legal_name", "Полное юридическое наименование"),
            ("legal_address", "Юридический адрес"),
            ("postal_address", "Почтовый адрес"),
            ("ogrn", "ОГРН"),
            ("inn_kpp", "ИНН/КПП"),
            ("responsible_person", "Ответственное лицо"),
            ("partner_email", "E-mail"),
            ("partner_phone", "Телефон")
        )
        for row, (key, label) in enumerate(fields, start=1):
            tk.Label(
                section,
                text=label,
                font=("Arial", 9),
                bg="white",
                anchor="w"
            ).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=3)
            entry = tk.Entry(section, font=("Arial", 10), relief="solid", borderwidth=1)
            entry.grid(row=row, column=1, sticky="ew", pady=3, ipady=2)
            self.partner_field_widgets[key] = entry
            entry.insert(0, str(self.client_data.get(key) or ""))

        bank_row = len(fields) + 1
        tk.Label(
            section,
            text="Банковские реквизиты",
            font=("Arial", 9),
            bg="white",
            anchor="nw"
        ).grid(row=bank_row, column=0, sticky="nw", padx=(0, 10), pady=3)
        bank_text = tk.Text(
            section,
            height=4,
            font=("Arial", 10),
            relief="solid",
            borderwidth=1,
            wrap=tk.WORD
        )
        bank_text.grid(row=bank_row, column=1, sticky="ew", pady=3)
        bank_text.insert("1.0", str(self.client_data.get("bank_details") or ""))
        self.partner_field_widgets["bank_details"] = bank_text

    def _import_partner_card(self):
        """Выбрать карточку клиента и заполнить распознанные реквизиты."""
        downloads_dir = Path.home() / "Downloads"
        if not downloads_dir.is_dir():
            downloads_dir = Path.home()
        selected_path = filedialog.askopenfilename(
            parent=self.dialog,
            title="Выберите карточку клиента",
            initialdir=str(downloads_dir),
            filetypes=(
                ("Документы Word", "*.docx *.doc"),
                ("Документ Word DOCX", "*.docx"),
                ("Документ Word DOC", "*.doc"),
                ("Все файлы", "*.*")
            )
        )
        if not selected_path:
            return

        try:
            partner_data = read_partner_card(Path(selected_path))
        except (OSError, RuntimeError, ValueError) as error:
            messagebox.showerror(
                "Импорт карточки партнёра",
                str(error),
                parent=self.dialog
            )
            return

        if partner_data.get("company"):
            self.company_entry.delete(0, tk.END)
            self.company_entry.insert(0, partner_data["company"])
        if partner_data.get("legal_address"):
            self.address_entry.delete(0, tk.END)
            self.address_entry.insert(0, partner_data["legal_address"])

        for key, widget in self.partner_field_widgets.items():
            value = partner_data.get(key)
            if not value:
                continue
            if isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
                widget.insert("1.0", value)
            else:
                widget.delete(0, tk.END)
                widget.insert(0, value)

        responsible_person = partner_data.get("responsible_person")
        if responsible_person:
            if not self.contact_widgets:
                self._add_contact_field()
            contact = self.contact_widgets[0]
            contact["name"].delete(0, tk.END)
            contact["name"].insert(0, responsible_person)
            contact["position"].delete(0, tk.END)
            contact["position"].insert(
                0,
                partner_data.get("responsible_position")
                or "Директор"
            )
            if partner_data.get("partner_email"):
                contact["email"].delete(0, tk.END)
                contact["email"].insert(0, partner_data["partner_email"])
            if partner_data.get("partner_phone"):
                contact["phone"].delete(0, tk.END)
                contact["phone"].insert(0, partner_data["partner_phone"])

        messagebox.showinfo(
            "Импорт карточки партнёра",
            f"Считано полей: {len(partner_data)}.",
            parent=self.dialog
        )
                
    def _create_contacts_section(self):
        """Секция контактных лиц"""
        contacts_header_frame = tk.Frame(self.scrollable_content, bg='white')
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
        
        self.contacts_container = tk.Frame(self.scrollable_content, bg='white')
        self.contacts_container.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.primary_contact_var = tk.IntVar(value=0)
        
        # Кнопка добавления контакта
        tk.Button(
            self.scrollable_content,
            text="➕ Добавить контакт",
            command=self._add_contact_field,
            bg="#28a745",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            cursor="hand2"
        ).pack(anchor='w', padx=20, pady=(0, 20))
        
        # Если редактирование - добавляем существующие контакты
        # (в реальности нужно загружать контакты отдельно)
        
        # Добавляем первый пустой контакт по умолчанию
        if not self.client_data.get('id'):
            self._add_contact_field()
            
    def _add_contact_field(self, contact_data=None):
        """Добавить поля для контакта"""
        if len(self.contact_widgets) >= 4:
            show_message(self.dialog, "Внимание", "Максимум 4 контактных лица!", "warning")
            return
            
        idx = len(self.contact_widgets)
        
        # Контейнер контакта
        contact_box = tk.Frame(self.contacts_container, bg='#f8f9fa', relief='solid', bd=1)
        contact_box.pack(fill=tk.X, pady=5)
        
        # Заголовок с радио-кнопкой
        header_frame = tk.Frame(contact_box, bg='#f8f9fa')
        header_frame.pack(fill=tk.X, padx=10, pady=8)
        
        radio_btn = tk.Radiobutton(
            header_frame,
            text=f"Контакт #{idx + 1}",
            variable=self.primary_contact_var,
            value=idx,
            font=("Arial", 10, "bold"),
            bg='#f8f9fa',
            selectcolor='#4CAF50',
            command=self._update_primary_labels
        )
        radio_btn.pack(side=tk.LEFT)
        
        primary_label = tk.Label(
            header_frame,
            text="⭐ ОСНОВНОЙ" if idx == 0 else "",
            font=("Arial", 9, "bold"),
            bg='#f8f9fa',
            fg='#4CAF50' if idx == 0 else '#999'
        )
        primary_label.pack(side=tk.LEFT, padx=5)
        
        # Кнопка удаления
        if idx > 0:
            tk.Button(
                header_frame,
                text="✕",
                command=lambda: self._remove_contact_field(contact_box),
                bg='#f8f9fa',
                fg='#d9534f',
                font=("Arial", 10, "bold"),
                relief="flat",
                cursor="hand2",
                width=3
            ).pack(side=tk.RIGHT)
        
        # Поля ввода
        fields_frame = tk.Frame(contact_box, bg='#f8f9fa')
        fields_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
        
        # ФИО
        tk.Label(fields_frame, text="ФИО:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
        name_entry = tk.Entry(fields_frame, font=("Arial", 10), relief="solid", borderwidth=1)
        name_entry.pack(fill=tk.X, pady=2, ipady=3)
        if contact_data:
            name_entry.insert(0, contact_data.get('full_name', ''))
        
        # Должность
        tk.Label(fields_frame, text="Должность:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
        position_entry = tk.Entry(fields_frame, font=("Arial", 10), relief="solid", borderwidth=1)
        position_entry.pack(fill=tk.X, pady=2, ipady=3)
        if contact_data:
            position_entry.insert(0, contact_data.get('position', ''))
        
        # Телефон
        tk.Label(fields_frame, text="Телефон:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
        phone_entry = tk.Entry(fields_frame, font=("Arial", 10), relief="solid", borderwidth=1)
        phone_entry.pack(fill=tk.X, pady=2, ipady=3)
        if contact_data:
            phone_entry.insert(0, contact_data.get('phone', ''))
        
        # Email
        tk.Label(fields_frame, text="Email:", font=("Arial", 9), bg='#f8f9fa').pack(anchor='w')
        email_entry = tk.Entry(fields_frame, font=("Arial", 10), relief="solid", borderwidth=1)
        email_entry.pack(fill=tk.X, pady=2, ipady=3)
        if contact_data:
            email_entry.insert(0, contact_data.get('email', ''))
        
        widget_data = {
            'box': contact_box,
            'radio': radio_btn,
            'primary_label': primary_label,
            'name': name_entry,
            'position': position_entry,
            'phone': phone_entry,
            'email': email_entry
        }
        
        self.contact_widgets.append(widget_data)
        
    def _remove_contact_field(self, contact_box):
        """Удалить поля контакта"""
        for i, widget in enumerate(self.contact_widgets):
            if widget['box'] == contact_box:
                self.contact_widgets.pop(i)
                contact_box.destroy()
                break
        self._update_contact_numbers()
        
    def _update_contact_numbers(self):
        """Обновить нумерацию контактов"""
        for idx, widget in enumerate(self.contact_widgets):
            widget['radio'].config(text=f"Контакт #{idx + 1}", value=idx)
        self._update_primary_labels()
        
    def _update_primary_labels(self):
        """Обновить метки основного контакта"""
        selected = self.primary_contact_var.get()
        for idx, widget in enumerate(self.contact_widgets):
            if idx == selected:
                widget['primary_label'].config(text="⭐ ОСНОВНОЙ", fg='#4CAF50')
            else:
                widget['primary_label'].config(text="", fg='#999')
                
    def _create_buttons(self):
        """Создать кнопки внизу"""
        buttons_container = tk.Frame(self.dialog, bg='#f0f0f0', height=80)
        buttons_container.pack(fill=tk.X, side=tk.BOTTOM)
        buttons_container.pack_propagate(False)
        
        buttons_frame = tk.Frame(buttons_container, bg='#f0f0f0')
        buttons_frame.pack(pady=15)
        
        # Сохранить
        tk.Button(
            buttons_frame,
            text="💾 Сохранить",
            command=self._save,
            bg="#28a745",
            fg="white",
            font=("Arial", 12, "bold"),
            cursor="hand2",
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
        
        # Отмена
        tk.Button(
            buttons_frame,
            text="✖ Отмена",
            command=self.dialog.destroy,
            bg="#6c757d",
            fg="white",
            font=("Arial", 12, "bold"),
            cursor="hand2",
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
        
    def _save(self):
        """Сохранить клиента"""
        # Валидация
        company = self.company_entry.get().strip()
        if not company:
            messagebox.showerror("Ошибка", "Название компании обязательно")
            return
            
        # Сбор контактов
        contacts = []
        for widget in self.contact_widgets:
            name = widget['name'].get().strip()
            if name:
                contacts.append({
                    'full_name': name,
                    'position': widget['position'].get().strip(),
                    'phone': widget['phone'].get().strip(),
                    'email': widget['email'].get().strip(),
                    'is_primary': self.contact_widgets.index(widget) == self.primary_contact_var.get()
                })
                
        if not contacts:
            messagebox.showerror("Ошибка", "Нужен хотя бы один контакт")
            return
            
        # Данные клиента
        client_data = {
            'company': company,
            'address': self.address_entry.get().strip(),
            'notes': self.notes_text.get('1.0', tk.END).strip(),
            'contacts': contacts,
            'full_legal_name': self.partner_field_widgets["full_legal_name"].get().strip(),
            'legal_address': self.partner_field_widgets["legal_address"].get().strip(),
            'postal_address': self.partner_field_widgets["postal_address"].get().strip(),
            'ogrn': self.partner_field_widgets["ogrn"].get().strip(),
            'inn_kpp': self.partner_field_widgets["inn_kpp"].get().strip(),
            'responsible_person': self.partner_field_widgets["responsible_person"].get().strip(),
            'partner_email': self.partner_field_widgets["partner_email"].get().strip(),
            'partner_phone': self.partner_field_widgets["partner_phone"].get().strip(),
            'bank_details': self.partner_field_widgets["bank_details"].get("1.0", "end-1c").strip()
        }
        
        try:
            if self.client_data.get('id'):
                # Редактирование
                self.client_service.update_client_with_contacts(
                    self.client_data['id'], 
                    client_data
                )
                client_id = self.client_data['id']
            else:
                # Создание
                client_id = self.client_service.create_client_with_contacts(client_data)
            
            # Сохраняем ID для возможности получения результата
            self.saved_client_id = client_id
                
            if self.on_save:
                self.on_save(client_id)
                
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Ошибка валидации", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
