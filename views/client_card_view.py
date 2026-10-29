# -*- coding: utf-8 -*-
"""
Карточка клиента с вкладками
Отображает данные клиента, контактные лица, задачи и документы
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
from pathlib import Path
import re
from datetime import date
from zipfile import ZIP_DEFLATED, ZipFile
from utils.ui_helpers import center_toplevel, confirm_close_on_focus_loss
from utils.constants import Colors
from utils.date_utils import parse_ddmmyyyy


class ClientCardView:
    """
    Карточка клиента с вкладками (Основное, Контакты, Активность, Документы)
    
    Usage:
        card = ClientCardView(parent, client_id, managers, on_edit=None, on_delete=None)
        card.show()
    """
    
    def __init__(self, parent, client_id, clients_mgr, contact_persons_mgr, 
                 contact_emails_mgr, tasks_mgr, on_edit=None, on_delete=None, on_close=None,
                 interactions_mgr=None):
        """
        Args:
            parent: родительское окно
            client_id: ID клиента
            clients_mgr: менеджер клиентов
            contact_persons_mgr: менеджер контактов
            contact_emails_mgr: менеджер email
            tasks_mgr: менеджер задач
            on_edit: callback при редактировании
            on_delete: callback при удалении
            on_close: callback при закрытии
        """
        self.parent = parent
        self.client_id = client_id
        self.clients_mgr = clients_mgr
        self.contact_persons_mgr = contact_persons_mgr
        self.contact_emails_mgr = contact_emails_mgr
        self.tasks_mgr = tasks_mgr
        self.interactions_mgr = interactions_mgr
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_close = on_close
        
        self.card_window = None
        self.contacts_table = None
        self.tasks_table = None
        self.task_card_dialogs = {}
        self.documents_tree = None
        self.documents_dir = None
        self.document_paths = {}
        self.document_directories = {}
        self.create_documents_button = None
        self.document_create_menu = None
        
    def show(self):
        """Показать карточку клиента"""
        # Загружаем данные клиента
        client = self.clients_mgr.get_by_id(self.client_id)
        if not client:
            messagebox.showerror("Ошибка", "Клиент не найден")
            return
            
        self.client_data = client
        
        # Создаем окно
        self.card_window = tk.Toplevel(self.parent)
        self.card_window._client_card_view = self
        self.card_window.title(f"Карточка клиента: {client['company']}")
        self.card_window.geometry("1100x820")
        self.card_window.minsize(1000, 740)
        self.card_window.configure(bg=Colors.LIGHT)
        
        self.card_window.protocol("WM_DELETE_WINDOW", self._on_close_click)
        confirm_close_on_focus_loss(self.card_window, self._on_close_click)
        
        self._create_header(client)
        self._create_tabs(client)
        self._create_buttons()
        center_toplevel(self.card_window)
        
    def _create_header(self, client):
        """Создать заголовок карточки"""
        header = tk.Frame(self.card_window, bg=Colors.DARK, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"🏢 {client['company']}",
            font=("Arial", 18, "bold"),
            fg=Colors.WHITE,
            bg=Colors.DARK
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        tk.Label(
            header,
            text=f"ID: {client.get('public_id') or client['id']}",
            font=("Arial", 12),
            fg=Colors.INFO,
            bg=Colors.DARK
        ).pack(side=tk.RIGHT, padx=20, pady=15)
        
    def _create_tabs(self, client):
        """Создать вкладки"""
        notebook = ttk.Notebook(self.card_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка 1: Основное
        tab_main = tk.Frame(notebook, bg='white')
        notebook.add(tab_main, text="📋 Основное")
        self._create_main_tab(tab_main, client)
        
        # Вкладка 2: Контактные лица
        tab_contacts = tk.Frame(notebook, bg='white')
        notebook.add(tab_contacts, text="👥 Контактные лица")
        self._create_contacts_tab(tab_contacts)
        
        # Вкладка 3: Задачи
        tab_tasks = tk.Frame(notebook, bg='white')
        notebook.add(tab_tasks, text="📌 Активность")
        self._create_tasks_tab(tab_tasks)

        tab_documents = tk.Frame(notebook, bg='white')
        notebook.add(tab_documents, text="📁 Документы")
        self._create_documents_tab(tab_documents, client)
        notebook.select(tab_tasks)
        
    def _create_main_tab(self, parent, client):
        """Отобразить сведения о клиенте и карточку партнёра."""
        canvas = tk.Canvas(parent, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg="white")
        content.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(content_window, width=event.width)
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(
            content,
            text="Основная информация",
            font=("Arial", 16, "bold"),
            bg='white'
        ).pack(pady=20)
        
        info_frame = tk.Frame(content, bg='white')
        info_frame.pack(padx=30, pady=10, fill=tk.BOTH)
        
        # Идентификатор и основные сведения
        self._add_info_row(
            info_frame,
            "ID клиента:",
            client.get('public_id') or client.get('id', ''),
            0
        )
        self._add_info_row(info_frame, "Компания:", client['company'], 1)
        
        # Адрес
        self._add_info_row(info_frame, "Адрес:", client['address'] or "Не указан", 2)
        
        # Примечания
        tk.Label(
            info_frame,
            text="Примечания:",
            font=("Arial", 12, "bold"),
            bg='white'
        ).grid(row=3, column=0, sticky='nw', padx=10, pady=10)
        
        notes_text = self._create_copyable_value(
            info_frame,
            client.get('notes') or "Нет примечаний",
            multiline=True,
            height=5
        )
        notes_text.grid(row=3, column=1, sticky='ew', padx=10, pady=10)
        info_frame.grid_columnconfigure(1, weight=1)
        
        self._add_info_row(info_frame, "Дата создания:", client['created_at'], 4)

        partner_frame = tk.LabelFrame(
            content,
            text="Карточка партнёра",
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#172b4d",
            padx=14,
            pady=10
        )
        partner_frame.pack(fill=tk.X, padx=30, pady=(16, 24))
        partner_frame.columnconfigure(1, weight=1)
        partner_frame.columnconfigure(3, weight=1)

        partner_rows = (
            ("Полное наименование", client.get("full_legal_name")),
            ("Юридический адрес", client.get("legal_address")),
            ("Почтовый адрес", client.get("postal_address")),
            ("ОГРН", client.get("ogrn")),
            ("ИНН/КПП", client.get("inn_kpp")),
            ("Банковские реквизиты", client.get("bank_details")),
            ("Ответственное лицо", client.get("responsible_person")),
            ("E-mail", client.get("partner_email")),
            ("Тел.", client.get("partner_phone"))
        )
        for row_index, (label, value) in enumerate(partner_rows):
            tk.Label(
                partner_frame,
                text=f"{label}:",
                font=("Arial", 10, "bold"),
                bg="white",
                fg="#243247",
                anchor="nw"
            ).grid(row=row_index, column=0, sticky="nw", padx=(4, 12), pady=6)
            value_widget = self._create_copyable_value(
                partner_frame,
                value or "Не указано",
                multiline=bool(value and ("\n" in str(value) or len(str(value)) > 65))
            )
            value_widget.grid(
                row=row_index,
                column=1,
                columnspan=3,
                sticky="ew",
                pady=6
            )

        wheel_tag = f"ClientMainTab{id(canvas)}"

        def scroll_main_tab(event):
            if getattr(event, "num", None) == 4:
                steps = -1
            elif getattr(event, "num", None) == 5:
                steps = 1
            else:
                delta = event.delta
                if abs(delta) >= 120:
                    steps = -int(delta / 120)
                else:
                    steps = -1 if delta > 0 else 1
            canvas.yview_scroll(steps, "units")
            return "break"

        canvas.bind_class(wheel_tag, "<MouseWheel>", scroll_main_tab)
        canvas.bind_class(wheel_tag, "<Button-4>", scroll_main_tab)
        canvas.bind_class(wheel_tag, "<Button-5>", scroll_main_tab)

        def attach_wheel_tag(widget):
            widget.bindtags((wheel_tag,) + widget.bindtags())
            for child in widget.winfo_children():
                attach_wheel_tag(child)
        attach_wheel_tag(canvas)
        attach_wheel_tag(canvas)
        
    def _add_info_row(self, parent, label, value, row):
        """Добавить строку информации"""
        tk.Label(
            parent,
            text=label,
            font=("Arial", 12, "bold"),
            bg='white'
        ).grid(row=row, column=0, sticky='w', padx=10, pady=10)
        
        value_widget = self._create_copyable_value(parent, value)
        value_widget.grid(row=row, column=1, sticky='ew', padx=10, pady=10)

    def _create_copyable_value(self, parent, value, multiline=False, height=2):
        """Создаёт отображаемое только для чтения значение с поддержкой копирования."""
        text = "" if value is None else str(value)
        if multiline:
            widget = tk.Text(
                parent,
                height=height,
                font=("Arial", 11),
                wrap=tk.WORD,
                relief="solid",
                borderwidth=1,
                bg=Colors.SURFACE,
                fg=Colors.TEXT,
                highlightthickness=1,
                highlightbackground=Colors.BORDER
            )
            widget.insert("1.0", text)
            widget.configure(state="disabled")
        else:
            widget = tk.Entry(
                parent,
                font=("Arial", 11),
                relief="solid",
                borderwidth=1,
                readonlybackground=Colors.SURFACE,
                fg=Colors.TEXT,
                highlightthickness=1,
                highlightbackground=Colors.BORDER
            )
            widget.insert(0, text)
            widget.configure(state="readonly")

        return widget

    def _create_contacts_tab(self, parent):
        """Вкладка 'Контактные лица'"""
        from views.clients_view import ClientContactsTable
        
        parent._is_contacts_tab = True
        parent._client_id = self.client_id
        
        # Создаем таблицу контактов
        self.contacts_table = ClientContactsTable(
            parent, 
            self.client_id, 
            self.contact_persons_mgr, 
            self.contact_emails_mgr,
            self
        )
        parent._contacts_table = self.contacts_table

    def _add_contact_to_client(self, client_id, parent_window=None):
        """Добавляет контактное лицо непосредственно из карточки клиента."""
        dialog = tk.Toplevel(parent_window or self.card_window)
        dialog.title("Добавить контакт")
        dialog.configure(bg=Colors.LIGHT)
        dialog.resizable(False, False)
        dialog.transient(parent_window or self.card_window)
        dialog.grab_set()

        fields = {}
        for row, label in enumerate(("ФИО", "Должность", "Телефон", "E-mail")):
            tk.Label(
                dialog,
                text=label,
                font=("Arial", 10, "bold"),
                bg=Colors.LIGHT,
                fg=Colors.TEXT
            ).grid(row=row, column=0, sticky="w", padx=14, pady=7)
            entry = tk.Entry(dialog, width=38, font=("Arial", 10))
            entry.grid(row=row, column=1, padx=14, pady=7, ipady=3)
            fields[label] = entry

        primary_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            dialog,
            text="Основной контакт",
            variable=primary_var,
            bg=Colors.LIGHT,
            fg=Colors.TEXT
        ).grid(row=4, column=1, sticky="w", padx=14, pady=5)

        buttons = tk.Frame(dialog, bg=Colors.LIGHT)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", padx=14, pady=12)

        def save_contact():
            full_name = fields["ФИО"].get().strip()
            if not full_name:
                messagebox.showerror(
                    "Проверка данных",
                    "Укажите ФИО контактного лица.",
                    parent=dialog
                )
                fields["ФИО"].focus_set()
                return

            try:
                contact_id = self.contact_persons_mgr.add(
                    client_id,
                    full_name,
                    position=fields["Должность"].get().strip(),
                    phone=fields["Телефон"].get().strip(),
                    is_primary=primary_var.get()
                )
                if not contact_id:
                    raise RuntimeError("Менеджер не вернул идентификатор контакта.")
                email = fields["E-mail"].get().strip()
                if email:
                    self.contact_emails_mgr.add(contact_id, email, is_primary=True)
                self.contacts_table.refresh()
                dialog.destroy()
            except Exception as error:
                messagebox.showerror(
                    "Ошибка",
                    f"Не удалось добавить контакт:\n{error}",
                    parent=dialog
                )

        tk.Button(
            buttons,
            text="Отмена",
            command=dialog.destroy,
            bg=Colors.LIGHT,
            fg=Colors.TEXT,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7
        ).pack(side=tk.RIGHT, padx=(8, 0))
        tk.Button(
            buttons,
            text="Сохранить",
            command=save_contact,
            bg=Colors.PRIMARY,
            fg=Colors.WHITE,
            activebackground=Colors.PRIMARY_HOVER,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7
        ).pack(side=tk.RIGHT)
        center_toplevel(dialog)
        fields["ФИО"].focus_set()
        
    def _create_tasks_tab(self, parent):
        """Вкладка 'Задачи'"""
        from views.clients_view import ClientTasksTable
        
        parent._is_tasks_tab = True
        parent._client_id = self.client_id
        parent._card_window = self.card_window
        
        # Создаем таблицу задач
        self.tasks_table = ClientTasksTable(
            parent, 
            self.client_id, 
            self.tasks_mgr, 
            self.clients_mgr,
            self.interactions_mgr,
            on_open_client=self._focus_client_card
        )
        parent._tasks_table = self.tasks_table

    def _focus_client_card(self, client_id):
        """Возвращает фокус к карточке клиента, из которой открыта задача."""
        if client_id != self.client_id or not self.card_window:
            raise RuntimeError("Карточка выбранного клиента не открыта.")
        if self.card_window.winfo_exists():
            self.card_window.deiconify()
            self.card_window.lift()
            self.card_window.focus_force()
            return self.card_window
        raise RuntimeError("Окно карточки клиента уже закрыто.")

    def _create_documents_tab(self, parent, client):
        """Создать список документов, найденных в каталоге клиента."""
        toolbar = tk.Frame(parent, bg='white')
        toolbar.pack(fill=tk.X, padx=16, pady=(14, 8))

        tk.Label(
            toolbar,
            text="Документы клиента",
            font=("Arial", 14, "bold"),
            bg='white',
            fg='#243247'
        ).pack(side=tk.LEFT)
        tk.Button(
            toolbar,
            text="Обновить",
            command=self._refresh_documents,
            bg="#0f766e",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6
        ).pack(side=tk.RIGHT)
        self.create_documents_button = tk.Button(
            toolbar,
            text="Создать",
            command=self._show_document_create_menu,
            bg="#0f766e",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6
        )
        self.create_documents_button.pack(side=tk.RIGHT, padx=(0, 8))

        table_frame = tk.Frame(parent, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 4))
        self.documents_tree = ttk.Treeview(
            table_frame,
            columns=("type",),
            show="tree headings",
            selectmode="browse"
        )
        self.documents_tree.heading("#0", text="Документ")
        self.documents_tree.heading("type", text="Формат")
        self.documents_tree.column("#0", width=620, anchor="w")
        self.documents_tree.column("type", width=100, anchor="center", stretch=False)

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.documents_tree.yview
        )
        self.documents_tree.configure(yscrollcommand=scrollbar.set)
        self.documents_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.documents_tree.bind("<Double-1>", self._on_document_double_click)
        self.documents_tree.bind("<Control-c>", self._copy_selected_document)
        self.documents_tree.bind("<Control-C>", self._copy_selected_document)

        self.documents_status = tk.Label(
            parent,
            text="",
            font=("Arial", 9),
            bg='white',
            fg='#64748b',
            anchor="w"
        )
        self.documents_status.pack(fill=tk.X, padx=16, pady=(0, 12))

        self.documents_dir = self._find_client_documents_dir(client)
        self._refresh_documents()

    @staticmethod
    def _find_client_documents_dir(client):
        """Найти каталог клиента по публичному коду или названию компании."""
        root = Path(__file__).resolve().parents[1] / "clients_files"
        if not root.is_dir():
            return None

        try:
            directories = sorted(
                (path for path in root.iterdir() if path.is_dir()),
                key=lambda path: path.name.casefold()
            )
        except OSError as error:
            messagebox.showerror("Ошибка", f"Не удалось прочитать папку документов:\n{error}")
            return None

        public_id = str(client.get("public_id") or "").strip()
        if public_id:
            matches = [
                path for path in directories
                if path.name == public_id or path.name.startswith(f"{public_id} ")
            ]
            return matches[0] if matches else None

        company = str(client.get("company") or "").strip().casefold()
        if not company:
            return None

        def folder_company(path):
            return re.sub(r"^\d+-\d+\s+", "", path.name).strip().casefold()

        matches = [path for path in directories if folder_company(path) == company]
        return matches[0] if matches else None

    def _refresh_documents(self):
        """Перестроить дерево документов из папки клиента и её подразделов."""
        if not self.documents_tree:
            return

        for item in self.documents_tree.get_children():
            self.documents_tree.delete(item)
        self.document_paths.clear()
        self.document_directories.clear()

        self.documents_dir = self._find_client_documents_dir(self.client_data)
        if not self.documents_dir:
            self.documents_status.config(
                text="Папка документов для этого клиента не найдена."
            )
            return

        try:
            resolved_root = self.documents_dir.resolve()
            file_count = 0
            item_index = 0

            def insert_directory(directory, parent_item=""):
                nonlocal file_count, item_index
                entries = sorted(directory.iterdir(), key=lambda path: path.name.casefold())

                for entry in entries:
                    if entry.is_symlink() or not entry.resolve().is_relative_to(resolved_root):
                        continue

                    item_id = f"document_{item_index}"
                    item_index += 1

                    if entry.is_dir():
                        self.document_directories[item_id] = entry
                        self.documents_tree.insert(
                            parent_item,
                            "end",
                            iid=item_id,
                            text=entry.name,
                            values=("Папка",),
                            tags=("folder",)
                        )
                        insert_directory(entry, item_id)
                    elif entry.is_file():
                        self.document_paths[item_id] = entry
                        self.documents_tree.insert(
                            parent_item,
                            "end",
                            iid=item_id,
                            text=entry.name,
                            values=(entry.suffix.lstrip(".").upper() or "Файл",)
                        )
                        file_count += 1

            self.documents_tree.tag_configure("folder", foreground="#172b4d")
            insert_directory(self.documents_dir)
        except OSError as error:
            self.documents_status.config(text="Не удалось загрузить список документов.")
            messagebox.showerror("Ошибка", f"Не удалось загрузить документы:\n{error}")
            return

        self.documents_status.config(
            text=f"Найдено документов: {file_count} | {self.documents_dir}"
            if file_count else f"В папке клиента пока нет документов: {self.documents_dir}"
        )

    def _ensure_client_documents_dir(self):
        """Вернуть папку клиента, создав её для нового клиента при необходимости."""
        existing_dir = self._find_client_documents_dir(self.client_data)
        if existing_dir:
            self.documents_dir = existing_dir
            return existing_dir

        root = Path(__file__).resolve().parents[1] / "clients_files"
        root.mkdir(parents=True, exist_ok=True)
        public_id = str(self.client_data.get("public_id") or self.client_id)
        company = str(self.client_data.get("company") or "Клиент")
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", f"{public_id} {company}").strip(" .")
        client_dir = root / safe_name
        client_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir = client_dir
        return client_dir

    def _show_document_create_menu(self):
        """Показать действия создания документов клиента."""
        menu = tk.Menu(self.card_window, tearoff=False)
        menu.add_command(label="Спецификацию", command=self._create_specification)
        menu.add_command(label="Акт", command=self._create_act)
        menu.add_separator()
        menu.add_command(label="Папку", command=self._create_document_folder)
        menu.add_command(label="Документ", command=self._create_document)
        self.document_create_menu = menu
        button = self.create_documents_button
        menu.post(
            button.winfo_rootx(),
            button.winfo_rooty() + button.winfo_height()
        )

    def _choose_client_subfolder(self, title):
        """Выбрать папку назначения внутри каталога текущего клиента."""
        try:
            client_dir = self._ensure_client_documents_dir()
        except OSError as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось подготовить папку клиента:\n{error}",
                parent=self.card_window
            )
            return None
        selected = filedialog.askdirectory(
            parent=self.card_window,
            title=title,
            initialdir=str(client_dir),
            mustexist=True
        )
        if not selected:
            return None

        selected_dir = Path(selected).resolve()
        try:
            selected_dir.relative_to(client_dir.resolve())
        except ValueError:
            messagebox.showerror(
                "Недопустимая папка",
                "Выберите папку внутри каталога этого клиента.",
                parent=self.card_window
            )
            return None
        return selected_dir

    def _create_document_folder(self):
        """Создать новую подпапку в выбранном каталоге клиента."""
        parent_dir = self._choose_client_subfolder("Где создать папку?")
        if not parent_dir:
            return

        folder_name = simpledialog.askstring(
            "Новая папка",
            "Введите название папки:",
            parent=self.card_window
        )
        if not folder_name or not folder_name.strip():
            return

        folder_name = folder_name.strip()
        if Path(folder_name).name != folder_name or folder_name in {".", ".."}:
            messagebox.showerror("Ошибка", "Введите только название папки без пути.")
            return

        try:
            (parent_dir / folder_name).mkdir()
            self._refresh_documents()
        except FileExistsError:
            messagebox.showerror("Ошибка", "Папка с таким названием уже существует.")
        except OSError as error:
            messagebox.showerror("Ошибка", f"Не удалось создать папку:\n{error}")

    def _create_document(self):
        """Создать пустой DOCX-файл в выбранной папке клиента."""
        target_dir = self._choose_client_subfolder("Где создать документ?")
        if not target_dir:
            return

        file_name = simpledialog.askstring(
            "Новый документ",
            "Введите название документа:",
            parent=self.card_window
        )
        if not file_name or not file_name.strip():
            return

        file_name = file_name.strip()
        if Path(file_name).name != file_name or file_name in {".", ".."}:
            messagebox.showerror("Ошибка", "Введите только название документа без пути.")
            return
        if not Path(file_name).suffix:
            file_name += ".docx"
        elif Path(file_name).suffix.casefold() != ".docx":
            messagebox.showerror("Ошибка", "Сейчас поддерживается создание документов DOCX.")
            return

        try:
            self._create_docx_placeholder(target_dir / file_name)
            self._refresh_documents()
        except FileExistsError:
            messagebox.showerror("Ошибка", "Документ с таким названием уже существует.")
        except OSError as error:
            messagebox.showerror("Ошибка", f"Не удалось создать документ:\n{error}")
        except Exception as error:
            messagebox.showerror("Ошибка", f"Не удалось создать документ:\n{error}")

    @staticmethod
    def _create_docx_placeholder(file_path):
        """Создать минимальный, открываемый DOCX-файл до подключения шаблонов."""
        created = False
        try:
            with file_path.open("xb") as output:
                created = True
                with ZipFile(output, "w", compression=ZIP_DEFLATED) as document:
                    document.writestr(
                        "[Content_Types].xml",
                        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                        '<Default Extension="xml" ContentType="application/xml"/>'
                        '<Override PartName="/word/document.xml" '
                        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                        '</Types>'
                    )
                    document.writestr(
                        "_rels/.rels",
                        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                        '<Relationship Id="rId1" '
                        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                        'Target="word/document.xml"/>'
                        '</Relationships>'
                    )
                    document.writestr(
                        "word/document.xml",
                        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                        '<w:body><w:p/><w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
                        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
                        'w:header="708" w:footer="708" w:gutter="0"/></w:sectPr></w:body>'
                        '</w:document>'
                    )
        except Exception:
            if created:
                file_path.unlink(missing_ok=True)
            raise

    @staticmethod
    def _create_pdf_placeholder(file_path, lines):
        """Создаёт PDF-копию документа с кириллическим текстом-заглушкой."""
        created = False
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfgen import canvas

            windows_dir = Path(os.environ.get("WINDIR", r"C:\Windows"))
            fonts_dir = windows_dir / "Fonts"
            font_path = next(
                (
                    candidate for candidate in (
                        fonts_dir / "arial.ttf",
                        fonts_dir / "calibri.ttf",
                        fonts_dir / "segoeui.ttf"
                    )
                    if candidate.is_file()
                ),
                None
            )
            if font_path is None:
                raise FileNotFoundError(
                    "Не найден шрифт Arial/Calibri/Segoe UI для PDF с кириллицей."
                )

            font_name = "SRMDocumentFont"
            if font_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))

            with file_path.open("xb") as output:
                created = True
                pdf = canvas.Canvas(output, pagesize=A4)
                pdf.setTitle(file_path.stem)
                pdf.setFont(font_name, 11)
                text = pdf.beginText(50, 790)
                text.setFont(font_name, 11)
                for line in lines:
                    text.textLine(str(line))
                pdf.drawText(text)
                pdf.save()
        except Exception:
            if created:
                file_path.unlink(missing_ok=True)
            raise

    def _client_document_identity(self):
        """Возвращает безопасные идентификатор и название клиента для имени файла."""
        client_id = str(self.client_data.get("public_id") or self.client_id).strip()
        company = str(self.client_data.get("company") or "Клиент").strip()
        safe_company = re.sub(r'[<>:"/\\|?*]', "_", company).strip(" .")
        safe_company = safe_company or "Клиент"
        safe_company = safe_company[:120]
        safe_id = re.sub(r'[<>:"/\\|?*]', "_", client_id).strip(" .")
        return safe_id, safe_company

    def _create_document_pair(self, docx_path, pdf_path, pdf_lines):
        """Создаёт DOCX и его PDF-копию, удаляя частичный результат при ошибке."""
        if docx_path.exists() or pdf_path.exists():
            raise FileExistsError("Файл спецификации или акта с таким именем уже существует.")
        docx_created = False
        try:
            self._create_docx_placeholder(docx_path)
            docx_created = True
            self._create_pdf_placeholder(pdf_path, pdf_lines)
        except Exception:
            if docx_created:
                docx_path.unlink(missing_ok=True)
            raise

    def _create_specification(self):
        """Создать нумерованную папку спецификации и пустой DOCX-шаблон."""
        try:
            client_dir = self._ensure_client_documents_dir()
            specifications_dir = client_dir / "спецификации"
            specifications_dir.mkdir(exist_ok=True)
            numbers = [
                int(match.group(1))
                for entry in specifications_dir.iterdir()
                if entry.is_dir()
                and (match := re.fullmatch(r"спецификация\s+(\d+)", entry.name, re.IGNORECASE))
            ]
            number = max(numbers, default=0) + 1
            specification_dir = specifications_dir / f"спецификация {number}"
            specification_dir.mkdir()
            client_id, company = self._client_document_identity()
            document_name = (
                f"спецификация {number} к договору {client_id} {company}"
            )
            lines = [
                f"Спецификация {number} к договору {client_id}",
                company
            ]
            self._create_document_pair(
                specification_dir / f"{document_name}.docx",
                specification_dir / f"{document_name}.pdf",
                lines
            )
            self._refresh_documents()
        except OSError as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось создать спецификацию:\n{error}",
                parent=self.card_window
            )
        except Exception as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось создать спецификацию:\n{error}",
                parent=self.card_window
            )
        finally:
            if "specification_dir" in locals() and specification_dir.exists():
                try:
                    if not any(specification_dir.iterdir()):
                        specification_dir.rmdir()
                except OSError as cleanup_error:
                    messagebox.showwarning(
                        "Очистка папки",
                        f"Не удалось удалить пустую папку спецификации:\n{cleanup_error}",
                        parent=self.card_window
                    )

    def _choose_specification_folder(self):
        """Показать список папок спецификаций и вернуть выбранную."""
        try:
            client_dir = self._ensure_client_documents_dir()
            specifications_dir = client_dir / "спецификации"
            if not specifications_dir.is_dir():
                messagebox.showinfo(
                    "Спецификации",
                    "Папка со спецификациями не найдена.",
                    parent=self.card_window
                )
                return None

            folders = sorted(
                (path for path in specifications_dir.iterdir() if path.is_dir()),
                key=lambda path: path.name.casefold()
            )
        except OSError as error:
            messagebox.showerror("Ошибка", f"Не удалось прочитать спецификации:\n{error}")
            return None

        if not folders:
            messagebox.showinfo(
                "Спецификации",
                "Сначала создайте спецификацию.",
                parent=self.card_window
            )
            return None

        dialog = tk.Toplevel(self.card_window)
        dialog.title("Выберите спецификацию")
        dialog.geometry("380x320")
        dialog.transient(self.card_window)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Выберите папку спецификации для акта:",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=12, pady=(12, 6))
        listbox = tk.Listbox(dialog, font=("Arial", 10), exportselection=False)
        listbox.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        for folder in folders:
            listbox.insert(tk.END, folder.name)

        result = {"folder": None}

        def select_folder(event=None):
            selection = listbox.curselection()
            if selection:
                result["folder"] = folders[selection[0]]
                dialog.destroy()

        buttons = tk.Frame(dialog)
        buttons.pack(fill=tk.X, padx=12, pady=12)
        tk.Button(buttons, text="Выбрать", command=select_folder).pack(side=tk.RIGHT, padx=(8, 0))
        tk.Button(buttons, text="Отмена", command=dialog.destroy).pack(side=tk.RIGHT)
        listbox.bind("<Double-1>", select_folder)
        listbox.selection_set(0)
        listbox.focus_set()
        center_toplevel(dialog)
        self.card_window.wait_window(dialog)
        return result["folder"]

    def _create_act(self):
        """Создать акт и PDF-копию в папке выбранной спецификации."""
        specification_dir = self._choose_specification_folder()
        if not specification_dir:
            return

        today = date.today().strftime("%d.%m.%Y")
        date_text = simpledialog.askstring(
            "Дата договора",
            "Укажите дату договора (ДД.ММ.ГГГГ):",
            initialvalue=today,
            parent=self.card_window
        )
        if date_text is None:
            return
        date_text = date_text.strip() or today
        contract_date = parse_ddmmyyyy(date_text)
        if contract_date is None:
            messagebox.showerror(
                "Неверная дата",
                "Введите дату договора в формате ДД.ММ.ГГГГ.",
                parent=self.card_window
            )
            return

        try:
            client_id, company = self._client_document_identity()
            numbers = []
            for entry in specification_dir.iterdir():
                if not entry.is_file():
                    continue
                match = re.fullmatch(
                    rf"акт\s+{re.escape(client_id)}-(\d+)\s+от\s+.+\.docx",
                    entry.name,
                    re.IGNORECASE
                )
                if not match:
                    match = re.fullmatch(
                        r"акт\s+(\d+)\.docx",
                        entry.name,
                        re.IGNORECASE
                    )
                if match:
                    numbers.append(int(match.group(1)))
            number = max(numbers, default=0) + 1
            document_name = (
                f"акт {client_id}-{number} от "
                f"{contract_date.strftime('%d.%m.%Y')} {company}"
            )
            self._create_document_pair(
                specification_dir / f"{document_name}.docx",
                specification_dir / f"{document_name}.pdf",
                [
                    f"Акт {client_id}-{number} от {contract_date.strftime('%d.%m.%Y')}",
                    company
                ]
            )
            self._refresh_documents()
        except OSError as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось создать акт:\n{error}",
                parent=self.card_window
            )
        except Exception as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось создать акт:\n{error}",
                parent=self.card_window
            )

    def _on_document_double_click(self, event):
        """Раскрыть папку по двойному щелчку или открыть выбранный файл."""
        item = self.documents_tree.identify_row(event.y)
        if not item:
            return
        if item in self.document_directories:
            is_open = self.documents_tree.item(item, "open")
            self.documents_tree.item(item, open=not is_open)
            return "break"
        self.documents_tree.selection_set(item)
        self._open_selected_document()

    def _open_selected_document(self, event=None):
        """Открыть выбранный файл приложением по умолчанию в Windows."""
        selection = self.documents_tree.selection() if self.documents_tree else ()
        if not selection:
            return

        file_path = self.document_paths.get(selection[0])
        if not file_path or not file_path.is_file():
            messagebox.showerror("Ошибка", "Выбранный документ больше не найден.")
            return

        try:
            start_file = getattr(os, "startfile", None)
            if start_file is None:
                raise OSError("Открытие документов поддерживается только в Windows.")
            start_file(str(file_path))
        except OSError as error:
            messagebox.showerror("Ошибка", f"Не удалось открыть документ:\n{error}")

    def _copy_selected_document(self, event=None):
        """Копирует путь выбранного документа или название папки."""
        selection = self.documents_tree.selection() if self.documents_tree else ()
        if not selection:
            return "break"

        item_id = selection[0]
        path = self.document_paths.get(item_id) or self.document_directories.get(item_id)
        value = str(path) if path else self.documents_tree.item(item_id, "text")
        self.documents_tree.clipboard_clear()
        self.documents_tree.clipboard_append(value)
        return "break"

    def _create_buttons(self):
        """Создать кнопки внизу"""
        buttons_container = tk.Frame(self.card_window, bg=Colors.SURFACE, height=76)
        buttons_container.pack(fill=tk.X, side=tk.BOTTOM)
        buttons_container.pack_propagate(False)
        
        buttons_frame = tk.Frame(buttons_container, bg=Colors.SURFACE)
        buttons_frame.pack(fill=tk.X, padx=20, pady=14)
        
        # Destructive actions stay on the left; primary actions align right.
        tk.Button(
            buttons_frame,
            text="Удалить",
            command=self._on_delete_click,
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
            command=self._on_close_click,
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
            command=self._on_edit_click,
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

    def _on_close_click(self):
        """Закрыть карточку и уведомить представление-владельца."""
        if self.on_close:
            self.on_close()
        self.card_window.destroy()
        
    def _on_edit_click(self):
        """Обработчик редактирования"""
        if self.on_edit:
            self.on_edit(self.client_data, self.card_window)
            
    def _on_delete_click(self):
        """Обработчик удаления"""
        if messagebox.askyesno(
            "Подтверждение", 
            f"Удалить клиента '{self.client_data['company']}'?\n\n"
            "Все связанные данные (контакты, задачи) будут удалены.",
            parent=self.card_window
        ):
            try:
                self.clients_mgr.delete(self.client_id)
                if self.on_delete:
                    self.on_delete(self.client_id)
                self.card_window.destroy()
            except Exception as e:
                messagebox.showerror(
                    "Ошибка",
                    f"Не удалось удалить: {e}",
                    parent=self.card_window
                )
                
    def refresh_contacts(self):
        """Обновить таблицу контактов"""
        if self.contacts_table:
            self.contacts_table.refresh()
            
    def refresh_tasks(self):
        """Обновить таблицу задач"""
        if self.tasks_table:
            self.tasks_table.refresh()

    def refresh(self):
        """Перезагрузить данные и содержимое карточки."""
        client = self.clients_mgr.get_by_id(self.client_id)
        if not client:
            messagebox.showerror("Ошибка", "Клиент не найден")
            return

        self.client_data = client
        for widget in self.card_window.winfo_children():
            widget.destroy()

        self._create_header(client)
        self._create_tabs(client)
        self._create_buttons()
