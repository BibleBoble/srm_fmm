# -*- coding: utf-8 -*-
"""
Карточка клиента с вкладками
Отображает данные клиента, контактные лица, задачи и документы
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import shutil
import tempfile
from pathlib import Path
import re
from datetime import date
from decimal import Decimal
from zipfile import ZIP_DEFLATED, ZipFile
from managers.contracts_manager import ContractsManager
from managers.experts_manager import ExpertsManager
from managers.works_manager import WorksManager
from views.document_generation_dialog import show_document_input_dialog
from views.work_expenses_dialog import show_work_expenses_dialog
from utils.python_document_generator import PythonDocumentGenerator
from utils.money_to_words import amount_to_russian_words
from utils.specification_reader import (
    read_specification_customer,
    read_specification_items,
    read_specification_summary,
)
from utils.ui_helpers import center_toplevel
from utils.constants import Colors
from utils.date_utils import parse_ddmmyyyy


def _format_iso_date(value):
    """Показать дату ISO (2026-11-03) в формате ДД.ММ.ГГГГ."""
    if not value:
        return "—"
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(value))
    if match:
        return f"{match.group(3)}.{match.group(2)}.{match.group(1)}"
    return str(value)


class ClientCardView:
    """
    Карточка клиента с вкладками (Основное, Контакты, Активность, Документы)
    
    Usage:
        card = ClientCardView(parent, client_id, managers, on_edit=None, on_delete=None)
        card.show()
    """
    
    def __init__(self, parent, client_id, clients_mgr, contact_persons_mgr, 
                 contact_emails_mgr, tasks_mgr, on_edit=None, on_delete=None, on_close=None,
                 interactions_mgr=None, document_service=None):
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
            document_service: сервис фонового формирования PDF
        """
        self.parent = parent
        self.client_id = client_id
        self.clients_mgr = clients_mgr
        self.contact_persons_mgr = contact_persons_mgr
        self.contact_emails_mgr = contact_emails_mgr
        self.tasks_mgr = tasks_mgr
        self.interactions_mgr = interactions_mgr
        self.document_service = document_service
        self.contracts_mgr = ContractsManager()
        self.works_mgr = WorksManager()
        self.experts_mgr = ExpertsManager()
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_close = on_close
        
        self.card_window = None
        self.contacts_table = None
        self.tasks_table = None
        self.documents_tree = None
        self.documents_dir = None
        self.document_paths = {}
        self.document_directories = {}
        self._preview_dir = None
        self.works_tree = None
        self.works_status = None
        self.work_directories = {}
        self.work_sources = {}
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

        tab_works = tk.Frame(notebook, bg='white')
        notebook.add(tab_works, text="✅ Выполненные работы")
        self._create_completed_works_tab(tab_works)

        notebook.bind(
            "<<NotebookTabChanged>>",
            lambda event: self._refresh_completed_works()
            if notebook.select() == str(tab_works)
            else None
        )
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

    def _create_completed_works_tab(self, parent):
        """Show one work row for every saved specification."""
        toolbar = tk.Frame(parent, bg="white")
        toolbar.pack(fill=tk.X, padx=16, pady=(14, 8))
        tk.Label(
            toolbar,
            text="Работы по спецификациям",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#243247"
        ).pack(side=tk.LEFT)
        actions = tk.Frame(toolbar, bg="white")
        actions.pack(side=tk.RIGHT)
        for text, command, color in (
            ("Обновить", self._refresh_completed_works, "#0f766e"),
            ("🧾 Расходы", self._open_expenses_dialog, "#b45309"),
            ("💰 Оплата", self._open_payment_dialog, "#1d4ed8"),
        ):
            tk.Button(
                actions,
                text=text,
                command=command,
                bg=color,
                fg="white",
                relief="flat",
                cursor="hand2",
                padx=12,
                pady=6
            ).pack(side=tk.LEFT, padx=(0, 10))

        table_frame = tk.Frame(parent, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 4))
        works_style = ttk.Style()
        works_style.configure("Works.Treeview", rowheight=24)
        works_style.map(
            "Works.Treeview",
            background=[("selected", "#cfe8ff")],
            foreground=[("selected", "#0b2e4f")]
        )
        self.works_tree = ttk.Treeview(
            table_frame,
            columns=("number", "name", "cost", "paid", "status"),
            show="headings",
            selectmode="browse",
            style="Works.Treeview"
        )
        for column, heading in (
            ("number", "Номер работы"),
            ("name", "Наименование"),
            ("cost", "Стоимость, руб."),
            ("paid", "Оплачено, руб."),
            ("status", "Статус")
        ):
            self.works_tree.heading(column, text=heading)
        self.works_tree.column("number", width=110, anchor="center", stretch=False)
        self.works_tree.column("name", width=400, anchor="w")
        self.works_tree.column("cost", width=140, anchor="e", stretch=False)
        self.works_tree.column("paid", width=140, anchor="e", stretch=False)
        self.works_tree.column("status", width=130, anchor="center", stretch=False)
        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.works_tree.yview
        )
        self.works_tree.configure(yscrollcommand=scrollbar.set)
        self.works_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.works_tree.tag_configure(
            "launched",
            background="#fff7d6",
            foreground="#8a5a00"
        )
        self.works_tree.tag_configure(
            "completed",
            background="#e4f5e9",
            foreground="#176b35"
        )
        self.works_tree.tag_configure(
            "unreadable",
            background="#fde8e7",
            foreground="#a12622"
        )
        self.works_tree.bind("<Double-1>", self._open_work_folder)

        self.works_status = tk.Label(
            parent,
            text="",
            font=("Arial", 9),
            bg="white",
            fg="#64748b",
            anchor="w"
        )
        self.works_status.pack(fill=tk.X, padx=16, pady=(0, 12))
        self._refresh_completed_works()

    def _refresh_completed_works(self):
        """Rebuild the work list from specification folders and their acts."""
        if not self.works_tree:
            return

        for item in self.works_tree.get_children():
            self.works_tree.delete(item)
        self.work_directories.clear()
        self.work_sources.clear()
        try:
            self.works_mgr.sync_from_documents()
        except Exception:  # noqa: BLE001 - учёт работ не должен ломать вкладку
            pass

        client_dir = self._find_client_documents_dir(self.client_data)
        specifications_dir = client_dir / "спецификации" if client_dir else None
        if specifications_dir is None or not specifications_dir.is_dir():
            self.works_status.config(text="Спецификации клиента не найдены.")
            return

        folder_pattern = re.compile(r"спецификация\s+(\d+)", re.IGNORECASE)
        specification_folders = []
        unreadable_count = 0
        try:
            for path in specifications_dir.iterdir():
                match = folder_pattern.fullmatch(path.name)
                if path.is_dir() and not path.is_symlink() and match:
                    specification_folders.append((int(match.group(1)), path))
        except OSError as error:
            self.works_status.config(text="Не удалось прочитать папки спецификаций.")
            messagebox.showerror(
                "Работы клиента",
                f"Не удалось загрузить список работ:\n{error}",
                parent=self.card_window
            )
            return

        item_index = 0
        for number, folder in sorted(specification_folders):
            source_path = None
            try:
                document_pattern = re.compile(
                    rf"^спецификация\s*(?:№\s*)?{number}(?:\b|$)",
                    re.IGNORECASE
                )
                specification_files = sorted(
                    (
                        path for path in folder.iterdir()
                        if path.is_file()
                        and not path.is_symlink()
                        and path.suffix.casefold() == ".docx"
                        and not path.name.casefold().startswith("~$")
                        and document_pattern.match(path.stem)
                    ),
                    key=lambda path: path.name.casefold()
                )
                if not specification_files:
                    raise ValueError("Файл спецификации DOCX не найден.")

                summary = read_specification_summary(specification_files[0])
                service_name = "; ".join(summary.services)
                cost = f"{summary.total:,.2f}".replace(",", " ").replace(".", ",")
                source_path = specification_files[0]
                unreadable = False
            except (OSError, ValueError) as error:
                service_name = "Не удалось прочитать спецификацию"
                cost = "—"
                source_path = None
                unreadable = True
                unreadable_count += 1

            has_act = False
            try:
                has_act = any(
                    path.is_file()
                    and not path.is_symlink()
                    and path.suffix.casefold() in {".docx", ".pdf"}
                    and path.name.casefold().startswith("акт")
                    and not path.name.casefold().startswith("~$")
                    for path in folder.iterdir()
                )
                status = "Выполнена" if has_act else "Запущена"
            except OSError:
                unreadable = True
                unreadable_count += 1
                status = "Не определён"
            work = None
            if source_path is not None:
                try:
                    work = self.works_mgr.get_by_source(source_path)
                except Exception:  # noqa: BLE001 - показываем без данных оплаты
                    work = None

            paid_value = "—"
            if work is not None:
                paid_value = (
                    f"{float(work.get('paid_amount') or 0):,.2f}"
                    .replace(",", " ")
                    .replace(".", ",")
                )
            display_status = (
                WorksManager.display_status(work) if work is not None else status
            )

            row_id = f"work_{item_index}"
            item_index += 1
            self.work_directories[row_id] = folder
            if source_path is not None:
                self.work_sources[row_id] = source_path
            self.works_tree.insert(
                "",
                "end",
                iid=row_id,
                values=(
                    str(number),
                    service_name,
                    cost,
                    paid_value,
                    display_status
                ),
                tags=(
                    "unreadable" if unreadable
                    else "completed" if has_act
                    else "launched",
                )
            )

        status_text = f"Найдено работ: {len(specification_folders)}"
        if unreadable_count:
            status_text += (
                f" | Проблем с чтением спецификации/статуса: {unreadable_count}"
            )
        self.works_status.config(text=status_text)

    def _open_work_folder(self, event):
        """Открыть папку спецификации по двойному щелчку."""
        row_id = self.works_tree.identify_row(event.y)
        folder = self.work_directories.get(row_id)
        if not folder:
            return "break"
        try:
            os.startfile(str(folder))
        except OSError as error:
            messagebox.showerror(
                "Работы клиента",
                f"Не удалось открыть папку спецификации:\n{error}",
                parent=self.card_window
            )
        return "break"

    def _selected_work(self):
        """Работа, выбранная в таблице «Выполненные работы»."""
        selection = self.works_tree.selection() if self.works_tree else ()
        if not selection and self.works_tree:
            children = self.works_tree.get_children()
            if children:
                self.works_tree.selection_set(children[0])
                selection = (children[0],)
        if not selection:
            if self.works_status is not None:
                self.works_status.config(text="Нет работ для выбора.")
            return None

        source_path = self.work_sources.get(selection[0])
        if not source_path:
            messagebox.showerror(
                "Работы клиента",
                "Работа не найдена в учёте. Нажмите «Обновить».",
                parent=self.card_window
            )
            return None

        try:
            work = self.works_mgr.get_by_source(source_path)
        except Exception as error:  # noqa: BLE001 - показываем пользователю
            messagebox.showerror(
                "Работы клиента", str(error), parent=self.card_window
            )
            return None
        if work is None:
            messagebox.showerror(
                "Работы клиента",
                "Работа не найдена в учёте. Нажмите «Обновить».",
                parent=self.card_window
            )
        return work

    def _open_payment_dialog(self):
        """Ввести сумму и дату оплаты по выбранной работе."""
        work = self._selected_work()
        if work is None:
            return

        dialog = tk.Toplevel(self.card_window)
        dialog.title("Оплата работы")
        dialog.geometry("430x250")
        dialog.transient(self.card_window)
        dialog.grab_set()

        ttk.Label(
            dialog, text="Работа:", font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=16, pady=(14, 2))
        ttk.Label(
            dialog, text=work["title"][:90], wraplength=390
        ).pack(anchor="w", padx=16)

        ttk.Label(dialog, text="Оплачено, руб.:").pack(
            anchor="w", padx=16, pady=(10, 2)
        )
        amount_var = tk.StringVar(
            value=f"{float(work.get('paid_amount') or 0):.2f}"
        )
        amount_row = ttk.Frame(dialog)
        amount_row.pack(fill=tk.X, padx=16)
        ttk.Entry(
            amount_row, textvariable=amount_var, width=14
        ).pack(side=tk.LEFT)
        ttk.Button(
            amount_row,
            text="Вся сумма",
            command=lambda: amount_var.set(
                f"{float(work.get('amount') or 0):.2f}"
            )
        ).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(dialog, text="Дата оплаты (ДД.ММ.ГГГГ):").pack(
            anchor="w", padx=16, pady=(8, 2)
        )
        saved_paid_date = work.get("paid_date")
        date_var = tk.StringVar(
            value=(
                _format_iso_date(saved_paid_date)
                if saved_paid_date
                else date.today().strftime("%d.%m.%Y")
            )
        )
        ttk.Entry(dialog, textvariable=date_var).pack(fill=tk.X, padx=16)

        def save():
            try:
                amount = Decimal(
                    amount_var.get().replace(" ", "").replace(",", ".")
                )
            except Exception:  # noqa: BLE001 - проверка ввода
                messagebox.showerror(
                    "Оплата", "Некорректная сумма.", parent=dialog
                )
                return
            paid_date = parse_ddmmyyyy(date_var.get())
            if paid_date is None:
                messagebox.showerror(
                    "Оплата",
                    "Введите дату в формате ДД.ММ.ГГГГ.",
                    parent=dialog
                )
                return
            self.works_mgr.set_payment(
                work["id"], amount, paid_date.isoformat()
            )
            dialog.destroy()
            self._refresh_completed_works()

        buttons = ttk.Frame(dialog)
        buttons.pack(fill=tk.X, padx=16, pady=12)
        ttk.Button(buttons, text="Отмена", command=dialog.destroy).pack(
            side=tk.RIGHT
        )
        ttk.Button(buttons, text="Сохранить", command=save).pack(
            side=tk.RIGHT, padx=(0, 8)
        )
        center_toplevel(dialog)

    def _open_expenses_dialog(self):
        """Список и ввод расходов по выбранной работе."""
        work = self._selected_work()
        if work is None:
            return
        show_work_expenses_dialog(
            self.card_window, work, self.works_mgr, self.experts_mgr
        )

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

        company = str(client.get("company") or "").strip()
        if not company:
            return None

        def normalize(value):
            return re.sub(r"\s+", " ", str(value)).strip(" .").casefold()

        def folder_company(path):
            stripped = re.sub(r"^\d+(?:-\d+)?\s+", "", path.name)
            return normalize(stripped)

        company = normalize(company)
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
                    if entry.name.startswith("~$"):
                        try:
                            entry.unlink()
                        except OSError:
                            pass
                        continue
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
        menu.add_command(
            label="Комплект: договор + спецификация + акт",
            command=self._create_document_package
        )
        menu.add_separator()
        menu.add_command(label="Договор", command=self._create_contract)
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

    def _client_document_identity(self):
        """Возвращает безопасные идентификатор и название клиента для имени файла."""
        client_id = str(self.client_data.get("public_id") or self.client_id).strip()
        company = str(self.client_data.get("company") or "Клиент").strip()
        safe_company = re.sub(r'[<>:"/\\|?*]', "_", company).strip(" .")
        safe_company = safe_company or "Клиент"
        safe_company = safe_company[:120]
        safe_id = re.sub(r'[<>:"/\\|?*]', "_", client_id).strip(" .")
        return safe_id, safe_company

    @staticmethod
    def _document_initials(full_name):
        parts = str(full_name or "").split()
        if len(parts) < 2:
            return ""
        patronymic_endings = ("ович", "евич", "ич", "овна", "евна", "ична")
        surname_endings = (
            "ов", "ев", "ёв", "ин", "ын", "ский", "цкий", "ая", "ова", "ева"
        )
        if len(parts) == 2:
            first_is_surname = parts[0].casefold().endswith(surname_endings)
            second_is_surname = parts[1].casefold().endswith(surname_endings)
            if second_is_surname and not first_is_surname:
                return f"{parts[1]} {parts[0][0]}."
        if len(parts) >= 3 and parts[2].casefold().endswith(patronymic_endings):
            surname, given_names = parts[0], parts[1:3]
        elif len(parts) >= 3 and parts[1].casefold().endswith(patronymic_endings):
            surname, given_names = parts[2], parts[:2]
        else:
            surname, given_names = parts[0], parts[1:3]
        initials = "".join(f"{part[0]}." for part in given_names if part)
        return f"{surname} {initials}".strip()

    @staticmethod
    def _decline_person_name_part(value, feminine=False):
        """Поставить часть ФИО в родительный падеж."""
        name = value.strip()
        if not name:
            return name
        lowered = name.casefold()
        irregular_forms = {"павел": "павла", "лев": "льва"}
        if not feminine and lowered in irregular_forms:
            declined = irregular_forms[lowered]
            return declined[:1].upper() + declined[1:] if name[:1].isupper() else declined

        if feminine:
            if lowered.endswith(("ова", "ева", "ёва", "ина", "ына")):
                return name[:-1] + "ой"
            if lowered.endswith(("ская", "цкая", "ая", "яя")):
                return name[:-2] + "ой"
            if lowered.endswith("а"):
                return name[:-1] + "ы"
            if lowered.endswith("я"):
                return name[:-1] + "и"
            if lowered.endswith("ь"):
                return name[:-1] + "и"
            return name

        if lowered.endswith(("ский", "цкий", "ой")):
            return name[:-2] + "ого"
        if lowered.endswith(("ов", "ев", "ёв", "ин", "ын", "ич")):
            return name + "а"
        if lowered.endswith("ий"):
            return name[:-2] + "ия"
        if lowered.endswith(("й", "ь")):
            return name[:-1] + "я"
        if lowered.endswith("я"):
            return name[:-1] + "и"
        if lowered.endswith("а"):
            return name[:-1] + "ы"
        if lowered[-1:].isalpha():
            return name + "а"
        return name

    @classmethod
    def _document_name_genitive(cls, full_name):
        """Поставить ФИО в родительный падеж, определяя пол по отчеству."""
        parts = str(full_name or "").split()
        if len(parts) < 3:
            return str(full_name or "").strip()

        patronymic_male = ("ович", "евич", "ич")
        patronymic_female = ("овна", "евна", "ична", "инична")
        female = False

        second = parts[1].casefold()
        third = parts[2].casefold()
        if third.endswith(patronymic_male + patronymic_female):
            female = third.endswith(patronymic_female)
        elif second.endswith(patronymic_male + patronymic_female):
            female = second.endswith(patronymic_female)
        else:
            return str(full_name).strip()

        # Порядок слов сохраняем: «Пушкин В.В.» -> «Пушкина Василия Васильевича».
        return " ".join(
            cls._decline_person_name_part(part, female)
            for part in parts[:3]
        )

    @staticmethod
    def _document_position_genitive(position):
        """Поставить должность подписанта в родительный падеж."""
        position = str(position or "").strip()
        forms = {
            "генеральный директор": "Генерального директора",
            "директор": "Директора",
            "индивидуальный предприниматель": "Индивидуального предпринимателя",
            "президент": "Президента",
            "заместитель директора": "Заместителя директора",
        }
        return forms.get(position.casefold(), position)

    def _document_form_fields(self, document_type):
        """Подготовить поля документа с реквизитами из карточки клиента."""
        client = self.client_data
        company = str(client.get("company") or "").strip()
        responsible_person = str(
            client.get("responsible_person")
            or client.get("primary_contact")
            or ""
        ).strip()
        responsible_position = str(
            client.get("primary_position")
            or client.get("responsible_position")
            or ""
        ).casefold()
        common_fields = [
            {
                "key": "document_date",
                "label": "Дата документа (ДД.ММ.ГГГГ)",
                "value": date.today().strftime("%d.%m.%Y"),
                "required": True
            },
            {
                "key": "company",
                "label": "Наименование компании",
                "value": company,
                "required": True
            },
            {
                "key": "responsible_person",
                "label": "Ответственное лицо",
                "value": responsible_person,
                "required": True
            },
            {
                "key": "inn_kpp",
                "label": "ИНН/КПП",
                "value": str(client.get("inn_kpp") or "").strip(),
                "required": True
            },
            {
                "key": "legal_address",
                "label": "Юридический адрес",
                "value": str(client.get("legal_address") or client.get("address") or "").strip(),
                "required": True
            },
            {
                "key": "postal_address",
                "label": "Почтовый адрес",
                "value": str(client.get("postal_address") or client.get("legal_address") or "").strip(),
                "required": False
            },
            {
                "key": "email",
                "label": "E-mail",
                "value": str(client.get("partner_email") or "").strip(),
                "required": False
            },
            {
                "key": "phone",
                "label": "Телефон",
                "value": str(client.get("partner_phone") or "").strip(),
                "required": False
            },
            {
                "key": "signature_position",
                "label": "Должность подписанта со стороны клиента",
                "value": str(
                    client.get("signature_position")
                    or (
                        "Генеральный директор"
                        if "генеральн" in responsible_position
                        else "Директор"
                    )
                ),
                "choices": ("Директор", "Генеральный директор"),
                "required": True
            },
            {
                "key": "signature_short_name",
                "label": "Фамилия и инициалы подписанта",
                "value": self._document_initials(responsible_person),
                "required": True
            }
        ]
        if document_type == "contract":
            return [
                common_fields[0],
                common_fields[1],
                common_fields[2],
                common_fields[3],
                common_fields[4],
                common_fields[5],
                common_fields[6],
                common_fields[7],
                common_fields[8],
                common_fields[9],
                {
                    "key": "bank_details",
                    "label": "Банковские реквизиты",
                    "value": str(client.get("bank_details") or "").strip(),
                    "required": True,
                    "multiline": True
                }
            ]

        document_fields = list(common_fields)
        if document_type == "specification":
            document_fields.insert(1, {
                "key": "contract_date",
                "label": "Дата заключения договора (ДД.ММ.ГГГГ)",
                "value": self._contract_date_default(),
                "required": True
            })
        return document_fields

    @staticmethod
    def _company_names(company):
        """Полное и сокращённое наименование компании.

        В тексте договора «ООО» раскрывается до «Общество с ограниченной
        ответственностью», а в разделе реквизитов остаётся сокращение.
        """
        text = str(company or "").strip()
        if not text:
            return "", ""

        forms = {
            "ООО": "Общество с ограниченной ответственностью",
            "АО": "Акционерное общество",
            "ПАО": "Публичное акционерное общество",
            "ЗАО": "Закрытое акционерное общество",
            "ОАО": "Открытое акционерное общество",
        }
        match = re.match(r"^(ООО|ИП|АО|ПАО|ЗАО|ОАО)\s+(.+)$", text, re.IGNORECASE)
        if not match:
            name = text
            quoted = name
            if not (name.startswith(("«", '"')) and name.endswith(("»", '"'))):
                quoted = f"«{name}»"
            return quoted, quoted

        abbreviation = match.group(1).upper()
        name = match.group(2).strip()
        if abbreviation == "ИП":
            # ИП — это физическое лицо, кавычки не нужны.
            return f"Индивидуальный предприниматель {name}", f"ИП {name}"

        if name.startswith(("«", '"')) and name.endswith(("»", '"')):
            quoted = name
        else:
            quoted = f"«{name}»"

        full_prefix = forms.get(abbreviation, abbreviation)
        return f"{full_prefix} {quoted}", f"{abbreviation} {quoted}"

    def _contract_date_default(self):
        """Дата договора по умолчанию — текущая дата (её можно изменить)."""
        return date.today().strftime("%d.%m.%Y")

    @staticmethod
    def _format_russian_date(value, include_suffix=True):
        months = (
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        )
        suffix = " г" if include_suffix else ""
        return f"{value.day:02d} {months[value.month - 1]} {value.year}{suffix}"

    @staticmethod
    def _plural_days(days):
        """Правильная форма слова «день» для числа."""
        last_two = days % 100
        if 11 <= last_two <= 14:
            return "дней"
        last = days % 10
        if last == 1:
            return "день"
        if last in (2, 3, 4):
            return "дня"
        return "дней"

    @classmethod
    def _format_service_term(cls, term):
        """Привести срок услуги к правильной форме: 1 день, 2 дня, 5 дней."""
        text = str(term).strip()
        match = re.match(r"^(\d+)\s*(.*)$", text)
        if not match:
            return text

        days = int(match.group(1))
        tail = match.group(2).casefold().replace(".", "").strip()
        words = set(tail.split())
        allowed = {
            "день", "дня", "дней", "дн", "дню",
            "рабочий", "рабочих", "рабочие",
            "календарный", "календарных", "календарные",
        }
        if words - allowed:
            return text

        day_form = cls._plural_days(days)
        if any(word.startswith("рабоч") for word in words):
            adjective = "рабочий" if day_form == "день" else "рабочих"
            return f"{days} {adjective} {day_form}"
        if any(word.startswith("календарн") for word in words):
            adjective = "календарный" if day_form == "день" else "календарных"
            return f"{days} {adjective} {day_form}"
        return f"{days} {day_form}"

    def _document_replacements(
        self,
        document_type,
        number,
        values,
        line_items,
        person_genitive_override=None,
        position_genitive_override=None
    ):
        """Сформировать значения шаблона и форматированные строки услуг."""
        document_date = parse_ddmmyyyy(values["document_date"])
        if document_date is None:
            raise ValueError("Введите дату документа в формате ДД.ММ.ГГГГ.")

        responsible_person = str(values.get("responsible_person", "")).strip()
        if person_genitive_override is None and len(responsible_person.split()) < 3:
            raise ValueError(
                "Укажите фамилию, имя и отчество ответственного лица полностью."
            )

        contract_date = None
        if document_type == "specification":
            contract_date = parse_ddmmyyyy(values.get("contract_date", ""))
            if contract_date is None:
                raise ValueError(
                    "Введите дату заключения договора в формате ДД.ММ.ГГГГ."
                )

        client_id, _ = self._client_document_identity()
        postal_address = values["postal_address"] or values["legal_address"]
        phone = values["phone"]
        phone_block = f"тел.: {phone}" if phone else ""
        formatted_items = [
            {
                "name": item["name"],
                "term": self._format_service_term(item["term"]),
                "amount": f"{Decimal(item['amount']):.2f}".replace(".", ",")
            }
            for item in line_items
        ]
        total = sum(
            (Decimal(item["amount"]) for item in line_items),
            Decimal("0.00")
        )
        total_text = f"{total:.2f}".replace(".", ",")
        amount_words = amount_to_russian_words(total)
        position = values["signature_position"]
        genitive_position = (
            position_genitive_override
            or self._document_position_genitive(position)
        )
        person_genitive = (
            person_genitive_override
            or self._document_name_genitive(responsible_person)
        )
        customer_person = (
            responsible_person
            if document_type == "contract"
            else (person_genitive or responsible_person)
        )
        signature_short_name = str(
            values.get("signature_short_name") or ""
        ).strip()
        if not signature_short_name:
            signature_short_name = self._document_initials(responsible_person)
        full_company, short_company = self._company_names(values["company"])
        replacements = {
            "[ID]": client_id,
            "[название компании]": full_company,
            "[название компании кратко]": short_company,
            "[ответственное лицо]": customer_person,
            "[инн/кпп]": values["inn_kpp"],
            "[юридический адрес]": values["legal_address"],
            "[потовый адрес, если не указан, то юридический адрес]": postal_address,
            "[E-mail(синий текст с подчеркиванием)]": values["email"],
            "[указывать при наличии (тел.: [тел.])]": phone_block,
            "[должность]": position,
            "[Должность]": genitive_position,
            "[ответственное лицо в формате (Гущин С.А.)]": signature_short_name,
        }

        if document_type == "contract":
            russian_date = self._format_russian_date(document_date)
            compact_date = (
                f"{document_date.day:02d}"
                f"{self._format_russian_date(document_date, False).split(' ', 1)[1]}"
            )
            replacements.update({
                "[дата в формате (15 декабря 2025)]":
                    f"{document_date.day} "
                    f"{self._format_russian_date(document_date, False).split(' ', 1)[1]} ",
                "[дата в формате (01 октября 2026 г)]": russian_date,
                "[дата в формате(01октября 2026года)]": f"{compact_date}года",
                "[дата в формате (01октября 2026г)]": f"{compact_date}г",
                "[форма организации в формате (Общество с ограниченной ответственностью «название компании»)]":
                    full_company,
                "[должность в формате (Директора)]": genitive_position,
                "[ответсвенное лицо в формате (Коровкина Евгения Сергеевича)]":
                    person_genitive,
                "[тел. в формате (тел +7 (4855) 26-17-19, 26-77-60)]":
                    f"тел. {phone}" if phone else "",
                "[название компании в формате( ООО «Техно-Центр»)]": short_company,
                "[инн/кпп в формате (7610015191/761001001)]": values["inn_kpp"],
                "[банковские реквизиты]": values["bank_details"],
            })
        else:
            russian_date = self._format_russian_date(document_date)
            replacements.update({
                "[порядковый номер]": str(number),
                "[дата в формате (01 октября 2026 г)]": russian_date,
                "[дата (01 октября 2026 г)]": russian_date,
                "[дата в формате (01октября 2026г)]":
                    f"{document_date.day:02d}{self._format_russian_date(document_date, False).split(' ', 1)[1]}г",
                "[дата в формате(01октября 2026года)]":
                    f"{document_date.day:02d}{self._format_russian_date(document_date, False).split(' ', 1)[1]}года",
                "[дата в формате (01.10.2026 )]": document_date.strftime("%d.%m.%Y"),
                "[считать сумму]": total_text,
                "[сумма в формате 00,00]": total_text,
                "[сумма прописью в формате (Двадцать тысяч рублей 00 копеек)(жирный текст)]":
                    amount_words,
            })
            if contract_date is not None:
                contract_month = self._format_russian_date(
                    contract_date,
                    include_suffix=False
                ).split(" ", 1)[1]
                replacements.update({
                    "[29октября 2026г]":
                        f"{contract_date.day:02d}{contract_month}г",
                    "[дата заключения договора]":
                        self._format_russian_date(contract_date)
                })

        return replacements, formatted_items, document_date

    @staticmethod
    def _amount_to_decimal(value):
        """Привести сумму из формы или шаблона к Decimal."""
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(
                str(value).replace("\u00a0", "").replace(" ", "").replace(",", ".")
            )
        except Exception:  # noqa: BLE001 - некорректная сумма не ломает предпросмотр
            return Decimal("0.00")

    def _confirm_document(
        self,
        title,
        values,
        line_items,
        document_date,
        number,
        preview_callback=None
    ):
        """Показать сводку документа и дождаться подтверждения."""
        dialog = tk.Toplevel(self.card_window)
        dialog.title(f"Проверка: {title}")
        dialog.geometry("620x520")
        dialog.minsize(520, 420)
        dialog.transient(self.card_window)
        dialog.grab_set()

        content = ttk.Frame(dialog, padding=16)
        content.pack(fill=tk.BOTH, expand=True)

        info = [
            ("Документ", title),
            ("Номер", str(number)),
            ("Дата", document_date.strftime("%d.%m.%Y")),
            ("Компания", values.get("company", "")),
            ("Подписант", values.get("responsible_person", "")),
        ]
        for row, (label, value) in enumerate(info):
            ttk.Label(
                content,
                text=f"{label}:",
                font=("Arial", 10, "bold")
            ).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=3)
            ttk.Label(content, text=value or "—", wraplength=420).grid(
                row=row, column=1, sticky="w", pady=3
            )

        next_row = len(info)
        if line_items:
            ttk.Label(
                content,
                text="Услуги",
                font=("Arial", 10, "bold")
            ).grid(row=next_row, column=0, columnspan=2, sticky="w", pady=(12, 4))
            next_row += 1

            tree = ttk.Treeview(
                content,
                columns=("name", "term", "amount"),
                show="headings",
                height=min(len(line_items), 8)
            )
            tree.heading("name", text="Наименование")
            tree.heading("term", text="Срок")
            tree.heading("amount", text="Сумма, руб.")
            tree.column("name", width=320, anchor="w")
            tree.column("term", width=120, anchor="center")
            tree.column("amount", width=120, anchor="e")
            for item in line_items:
                tree.insert(
                    "",
                    "end",
                    values=(
                        item["name"],
                        item["term"],
                        f"{self._amount_to_decimal(item['amount']):.2f}".replace(".", ",")
                    )
                )
            tree.grid(row=next_row, column=0, columnspan=2, sticky="nsew")
            next_row += 1

            total = sum(
                (self._amount_to_decimal(item["amount"]) for item in line_items),
                Decimal("0.00")
            )
            ttk.Label(
                content,
                text="Итого: " + f"{total:.2f}".replace(".", ",") + " ₽",
                font=("Arial", 10, "bold")
            ).grid(row=next_row, column=0, columnspan=2, sticky="e", pady=(8, 0))
            next_row += 1
            content.grid_rowconfigure(next_row - 2, weight=1)

        ttk.Label(
            content,
            text="DOCX создаётся сразу, PDF формируется в фоне.",
            foreground="#64748b"
        ).grid(row=next_row, column=0, columnspan=2, sticky="w", pady=(12, 0))

        result = {"confirmed": False}

        def confirm():
            result["confirmed"] = True
            dialog.destroy()

        buttons = ttk.Frame(dialog, padding=(16, 8))
        buttons.pack(fill=tk.X)
        if preview_callback is not None:
            ttk.Button(
                buttons,
                text="Предпросмотр (жёлтым)",
                command=preview_callback
            ).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Отмена", command=dialog.destroy).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="Создать", command=confirm).pack(
            side=tk.RIGHT, padx=(0, 8)
        )
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        center_toplevel(dialog)
        self.card_window.wait_window(dialog)
        return result["confirmed"]

    def _start_pdf_conversion(self, pairs):
        """Отправить готовые DOCX на фоновую конвертацию в PDF."""
        if self.document_service is None:
            return
        try:
            self.documents_status.config(text="PDF формируется в фоне…")
        except tk.TclError:
            pass
        self.document_service.convert_pdf(pairs, on_done=self._on_pdf_ready)

    def _on_pdf_ready(self, success, error):
        """Показать результат фоновой конвертации."""
        try:
            if success:
                self.documents_status.config(text="Готово: DOCX и PDF.")
            else:
                self.documents_status.config(text="DOCX готов, PDF не создан.")
                messagebox.showwarning(
                    "PDF",
                    "Документ DOCX создан, но PDF не удалось сформировать:\n"
                    f"{error}",
                    parent=self.card_window
                )
            self._refresh_documents()
            self._refresh_completed_works()
        except tk.TclError:
            pass

    def _open_document_client_folder(self):
        try:
            client_dir = self._ensure_client_documents_dir()
            os.startfile(str(client_dir))
        except OSError as error:
            messagebox.showerror(
                "Папка клиента",
                f"Не удалось открыть папку клиента:\n{error}",
                parent=self.card_window
            )

    def _create_template_document(self, document_type, target_dir, number, create_target_dir=False):
        """Подготовить данные, подтвердить их и сразу сохранить DOCX."""
        titles = {
            "contract": "Договор",
            "specification": "Спецификация",
            "act": "Акт"
        }
        template_names = {
            "contract": "шаблон договора.docx",
            "specification": "шаблон спецификации.docx",
            "act": "шаблон акта.docx"
        }
        template_path = (
            Path(__file__).resolve().parents[1]
            / "clients_files"
            / template_names[document_type]
        )

        values = None
        raw_items = None
        while True:
            input_data = show_document_input_dialog(
                self.card_window,
                f"Создание: {titles[document_type].lower()}",
                self._document_form_fields(document_type),
                include_line_items=document_type != "contract",
                open_client_folder=lambda: self._open_document_client_folder(),
                initial_values=values,
                initial_line_items=raw_items
            )
            if input_data is None:
                return

            values = input_data["values"]
            raw_items = input_data["line_items"]
            try:
                replacements, line_items, document_date = self._document_replacements(
                    document_type,
                    number,
                    values,
                    raw_items
                )
                docx_path, pdf_path = self._document_paths(
                    document_type,
                    target_dir,
                    number,
                    document_date,
                    values
                )
            except ValueError as error:
                # Ошибка заполнения: форма открывается снова с теми же данными.
                messagebox.showerror(
                    "Проверка данных",
                    str(error),
                    parent=self.card_window
                )
                continue
            except FileExistsError as error:
                messagebox.showerror(
                    "Документ уже существует",
                    str(error),
                    parent=self.card_window
                )
                return
            break

        generator = PythonDocumentGenerator(
            template_path,
            replacements,
            line_items=line_items,
            line_table_index=1 if document_type != "contract" else None
        )

        if not self._confirm_document(
            titles[document_type],
            values,
            line_items,
            document_date,
            number,
            preview_callback=lambda: self._show_highlighted_preview(
                [(titles[document_type], generator)]
            )
        ):
            generator.close()
            return

        directory_created = False
        try:
            if create_target_dir and not target_dir.exists():
                target_dir.mkdir(parents=True, exist_ok=True)
                directory_created = True
            generator.save_docx(docx_path)
        except Exception as error:
            if directory_created:
                self._remove_empty_directory(target_dir)
            messagebox.showerror(
                "Ошибка создания документа",
                f"Не удалось подготовить документ:\n{error}",
                parent=self.card_window
            )
            return
        finally:
            generator.close()

        if document_type == "contract":
            self._save_contract_date(document_date)
            self._save_signature_position(values.get("signature_position"))

        self._after_documents_created(docx_path, pdf_path)

    def _document_paths(self, document_type, target_dir, number, document_date, values):
        """Вернуть пути DOCX/PDF и проверить, что документы ещё не созданы."""
        client_id, company = self._client_document_identity()
        if document_type == "contract":
            file_name = f"договор {client_id} от {document_date:%d.%m.%Y} {company}"
        elif document_type == "specification":
            file_name = f"спецификация {number} к договору {client_id} {company}"
        else:
            file_name = f"акт {client_id}-{number} от {document_date:%d.%m.%Y} {company}"

        docx_path = target_dir / f"{file_name}.docx"
        pdf_path = target_dir / f"{file_name}.pdf"
        if docx_path.exists() or pdf_path.exists():
            raise FileExistsError("Документ с таким именем уже существует.")
        return docx_path, pdf_path

    def _after_documents_created(self, docx_path, pdf_path):
        """Обновить карточку, открыть DOCX и запустить PDF в фоне."""
        self._refresh_documents()
        self._refresh_completed_works()
        self._start_pdf_conversion([(docx_path, pdf_path)])
        try:
            os.startfile(str(docx_path))
        except OSError:
            pass

    def _show_highlighted_preview(self, generators):
        """Открыть предпросмотр с жёлтой подсветкой вставленных значений."""
        try:
            if self._preview_dir is not None:
                shutil.rmtree(self._preview_dir, ignore_errors=True)
            self._preview_dir = Path(tempfile.mkdtemp(prefix="srm-preview-"))
            paths = []
            for name, generator in generators:
                safe_name = re.sub(r'[<>:"/\\|?*]', "_", name).strip(" .")
                path = self._preview_dir / f"{safe_name or 'документ'}.docx"
                path.write_bytes(generator.render(highlight=True))
                paths.append(path)
            os.startfile(str(paths[0] if len(paths) == 1 else self._preview_dir))
        except Exception as error:
            messagebox.showerror(
                "Предпросмотр",
                f"Не удалось открыть предпросмотр:\n{error}",
                parent=self.card_window
            )

    def _save_contract_date(self, document_date):
        """Сохранить дату договора, чтобы подставлять её в спецификации."""
        try:
            public_id, _company = self._client_document_identity()
            self.contracts_mgr.save_contract(
                self.client_id, document_date, number_id=public_id
            )
        except Exception as error:  # noqa: BLE001 - дата не блокирует создание
            print(f"Не удалось сохранить дату договора: {error}")

    def _save_signature_position(self, position):
        """Запомнить выбранную должность подписанта для следующих документов."""
        position = str(position or "").strip()
        if not position:
            return
        try:
            self.clients_mgr.set_signature_position(self.client_id, position)
            self.client_data["signature_position"] = position
        except Exception as error:  # noqa: BLE001 - выбор не блокирует создание
            print(f"Не удалось сохранить должность подписанта: {error}")

    @staticmethod
    def _remove_empty_directory(directory):
        try:
            if directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()
        except OSError:
            pass

    def _create_contract(self):
        """Создать договор по шаблону и сохранить DOCX и PDF после проверки."""
        try:
            client_dir = self._ensure_client_documents_dir()
            self._create_template_document(
                "contract",
                client_dir / "договоры",
                str(self._client_document_identity()[0]),
                create_target_dir=True
            )
        except Exception as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось создать договор:\n{error}",
                parent=self.card_window
            )

    def _create_specification(self):
        """Создать нумерованную папку спецификации и документы по шаблону."""
        try:
            client_dir = self._ensure_client_documents_dir()
            specifications_dir = client_dir / "спецификации"
            entries = (
                specifications_dir.iterdir()
                if specifications_dir.is_dir()
                else ()
            )
            numbers = [
                int(match.group(1))
                for entry in entries
                if entry.is_dir()
                and (match := re.fullmatch(r"спецификация\s+(\d+)", entry.name, re.IGNORECASE))
            ]
            number = max(numbers, default=0) + 1
            specification_dir = specifications_dir / f"спецификация {number}"
            self._create_template_document(
                "specification",
                specification_dir,
                number,
                create_target_dir=True
            )
        except Exception as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось создать спецификацию:\n{error}",
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
        """Создать акт: услуги берутся из спецификации, пользователь вводит дату."""
        specification_dir = self._choose_specification_folder()
        if not specification_dir:
            return

        generator = None
        try:
            specification_file = self._find_specification_file(specification_dir)
            items, _ = read_specification_items(specification_file)
            number = self._next_act_number(specification_dir)

            document_date = self._ask_document_date("Дата акта")
            if document_date is None:
                return

            values = {
                field["key"]: field.get("value", "")
                for field in self._document_form_fields("act")
            }
            values["document_date"] = document_date.strftime("%d.%m.%Y")

            try:
                customer = read_specification_customer(specification_file)
            except Exception:  # noqa: BLE001 - акт строится и без этих данных
                customer = {}

            replacements, line_items, document_date = self._document_replacements(
                "act",
                number,
                values,
                items,
                person_genitive_override=(
                    customer.get("person_genitive")
                    or str(values.get("responsible_person", "")).strip()
                ),
                position_genitive_override=customer.get("position_genitive") or None
            )
            docx_path, pdf_path = self._document_paths(
                "act", specification_dir, number, document_date, values
            )
            generator = PythonDocumentGenerator(
                Path(__file__).resolve().parents[1]
                / "clients_files"
                / "шаблон акта.docx",
                replacements,
                line_items=line_items,
                line_table_index=1
            )
            if not self._confirm_document(
                "Акт",
                values,
                line_items,
                document_date,
                number,
                preview_callback=lambda: self._show_highlighted_preview(
                    [("Акт", generator)]
                )
            ):
                return
            generator.save_docx(docx_path)
        except Exception as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось создать акт:\n{error}",
                parent=self.card_window
            )
            return
        finally:
            if generator is not None:
                generator.close()

        self._create_financial_task(number, docx_path, specification_file)
        self._after_documents_created(docx_path, pdf_path)

    def _create_financial_task(self, act_number, act_path, specification_file):
        """Создать финансовую задачу по созданному акту."""
        if self.tasks_mgr is None:
            return
        try:
            public_id, _company = self._client_document_identity()
            contract_number = ""
            try:
                contract_date = self.contracts_mgr.get_last_contract_date(
                    self.client_id
                )
            except Exception:  # noqa: BLE001 - номер договора не критичен
                contract_date = None
            if contract_date:
                contract_number = f"{public_id}-{contract_date:%Y%m%d}"

            title = (
                f"Заполнить финансовую отчётность к документу акт "
                f"{public_id}-{act_number}"
            )
            if contract_number:
                title += f" + {contract_number}"

            work_id = None
            try:
                self.works_mgr.sync_from_documents()
                work = self.works_mgr.get_by_source(
                    str(specification_file.resolve())
                )
                work_id = work["id"] if work else None
            except Exception:  # noqa: BLE001 - задача создаётся и без работы
                work_id = None

            self.tasks_mgr.add(
                title=title,
                description=f"Акт: {act_path.name}",
                client_id=self.client_id,
                priority="Высокий",
                is_financial=1,
                work_id=work_id
            )
        except Exception as error:  # noqa: BLE001 - не блокирует создание акта
            print(f"Не удалось создать финансовую задачу: {error}")

    @staticmethod
    def _find_specification_file(specification_dir):
        """Найти DOCX спецификации в папке, игнорируя временные файлы Word."""
        for path in sorted(
            specification_dir.iterdir(),
            key=lambda item: item.name.casefold()
        ):
            if not path.is_file() or path.suffix.casefold() != ".docx":
                continue
            if path.name.startswith("~$"):
                continue
            if path.name.casefold().startswith("спецификация"):
                return path
        raise ValueError(
            "В папке спецификации не найден DOCX-файл спецификации."
        )

    def _next_act_number(self, specification_dir):
        client_id, _ = self._client_document_identity()
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
        return max(numbers, default=0) + 1

    def _ask_document_date(self, title="Дата документа"):
        """Запросить только дату документа."""
        dialog = tk.Toplevel(self.card_window)
        dialog.title(title)
        dialog.geometry("320x150")
        dialog.transient(self.card_window)
        dialog.grab_set()

        ttk.Label(dialog, text="Дата (ДД.ММ.ГГГГ):").pack(
            anchor="w", padx=16, pady=(16, 4)
        )
        value = tk.StringVar(value=date.today().strftime("%d.%m.%Y"))
        entry = ttk.Entry(dialog, textvariable=value)
        entry.pack(fill=tk.X, padx=16)
        entry.focus_set()
        entry.selection_range(0, tk.END)

        result = {}

        def submit():
            parsed = parse_ddmmyyyy(value.get().strip())
            if parsed is None:
                messagebox.showerror(
                    "Дата",
                    "Введите дату в формате ДД.ММ.ГГГГ.",
                    parent=dialog
                )
                return
            result["date"] = parsed
            dialog.destroy()

        buttons = ttk.Frame(dialog)
        buttons.pack(fill=tk.X, padx=16, pady=12)
        ttk.Button(buttons, text="Отмена", command=dialog.destroy).pack(side=tk.RIGHT)
        ttk.Button(buttons, text="Создать", command=submit).pack(
            side=tk.RIGHT, padx=(0, 8)
        )
        dialog.bind("<Return>", lambda event: submit())
        center_toplevel(dialog)
        self.card_window.wait_window(dialog)
        return result.get("date")

    def _create_document_package(self):
        """Создать договор, спецификацию и акт за один проход."""
        try:
            client_dir = self._ensure_client_documents_dir()
            specifications_dir = client_dir / "спецификации"
            number = self._next_specification_number(specifications_dir)
        except Exception as error:
            messagebox.showerror(
                "Комплект документов",
                f"Не удалось подготовить папку клиента:\n{error}",
                parent=self.card_window
            )
            return

        contract_dir = client_dir / "договоры"
        specification_dir = specifications_dir / f"спецификация {number}"
        act_number = 1

        values = None
        raw_items = None
        while True:
            input_data = show_document_input_dialog(
                self.card_window,
                "Создание комплекта документов",
                self._package_form_fields(),
                include_line_items=True,
                open_client_folder=lambda: self._open_document_client_folder(),
                initial_values=values,
                initial_line_items=raw_items
            )
            if input_data is None:
                return

            values = input_data["values"]
            raw_items = input_data["line_items"]
            try:
                replacements_by_type = {
                    "contract": self._document_replacements(
                        "contract", number, values, raw_items
                    ),
                    "specification": self._document_replacements(
                        "specification", number, values, raw_items
                    ),
                    "act": self._document_replacements(
                        "act", act_number, values, raw_items
                    ),
                }
                document_date = replacements_by_type["contract"][2]
                contract_docx, contract_pdf = self._document_paths(
                    "contract", contract_dir, number, document_date, values
                )
                specification_docx, specification_pdf = self._document_paths(
                    "specification", specification_dir, number, document_date, values
                )
                act_docx, act_pdf = self._document_paths(
                    "act", specification_dir, act_number, document_date, values
                )
            except ValueError as error:
                messagebox.showerror(
                    "Проверка данных",
                    str(error),
                    parent=self.card_window
                )
                continue
            except FileExistsError as error:
                messagebox.showerror(
                    "Документ уже существует",
                    str(error),
                    parent=self.card_window
                )
                return
            break

        templates_dir = Path(__file__).resolve().parents[1] / "clients_files"
        jobs = (
            ("Договор", "contract", "шаблон договора.docx", contract_docx, None),
            ("Спецификация", "specification", "шаблон спецификации.docx", specification_docx, 1),
            ("Акт", "act", "шаблон акта.docx", act_docx, 1),
        )

        generators = []
        for title, document_type, template_name, docx_path, table_index in jobs:
            replacements, line_items, _ = replacements_by_type[document_type]
            generators.append((
                title,
                docx_path,
                PythonDocumentGenerator(
                    templates_dir / template_name,
                    replacements,
                    line_items=line_items,
                    line_table_index=table_index
                )
            ))

        if not self._confirm_document(
            "Комплект: договор, спецификация, акт",
            values,
            replacements_by_type["contract"][1],
            document_date,
            number,
            preview_callback=lambda: self._show_highlighted_preview(
                [(title, generator) for title, _, generator in generators]
            )
        ):
            for _, _, generator in generators:
                generator.close()
            return

        created = []
        try:
            contract_dir.mkdir(parents=True, exist_ok=True)
            specification_dir.mkdir(parents=True, exist_ok=True)
            for _, docx_path, generator in generators:
                generator.save_docx(docx_path)
                created.append(docx_path)
        except Exception as error:
            for path in created:
                path.unlink(missing_ok=True)
            messagebox.showerror(
                "Комплект документов",
                f"Не удалось создать комплект:\n{error}",
                parent=self.card_window
            )
            return
        finally:
            for _, _, generator in generators:
                generator.close()

        self._save_contract_date(document_date)
        self._save_signature_position(values.get("signature_position"))
        self._refresh_documents()
        self._refresh_completed_works()
        self._start_pdf_conversion([
            (contract_docx, contract_pdf),
            (specification_docx, specification_pdf),
            (act_docx, act_pdf),
        ])
        try:
            os.startfile(str(specification_dir))
        except OSError:
            pass

    @staticmethod
    def _next_specification_number(specifications_dir):
        """Определить следующий номер спецификации в папке клиента."""
        numbers = []
        if specifications_dir.is_dir():
            for entry in specifications_dir.iterdir():
                if not entry.is_dir():
                    continue
                match = re.fullmatch(
                    r"спецификация\s+(\d+)",
                    entry.name,
                    re.IGNORECASE
                )
                if match:
                    numbers.append(int(match.group(1)))
        return max(numbers, default=0) + 1

    def _package_form_fields(self):
        """Поля формы комплекта: договор + данные спецификации."""
        contract_fields = self._document_form_fields("contract")
        specification_fields = self._document_form_fields("specification")
        contract_keys = {field["key"] for field in contract_fields}
        extra_fields = [
            field for field in specification_fields
            if field["key"] not in contract_keys
        ]

        fields = [contract_fields[0]]
        fields.extend(
            field for field in extra_fields if field["key"] == "contract_date"
        )
        fields.extend(
            field for field in contract_fields[1:]
            if field["key"] != "signature_short_name"
        )
        fields.extend(
            field for field in extra_fields if field["key"] != "contract_date"
        )
        return fields

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
