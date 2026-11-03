# -*- coding: utf-8 -*-
"""Утилиты для построения и сбора данных формы задачи.

Предназначено для постепенной миграции логики создания/редактирования задач из
`views/tasks_view.py` в переиспользуемые функции.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
from datetime import date, datetime, timedelta
from views.widgets.searchable_combobox import SearchableCombobox
from utils.date_utils import format_ddmmyyyy, parse_ddmmyyyy
from utils.constants import Colors, TaskPriorities
from utils.ui_helpers import center_toplevel


def build_task_form(parent, clients_mgr, defaults: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Создаёт набор виджетов для формы задачи и возвращает словарь виджетов.

    Примеры ключей в defaults: title, description, priority, client_name, due_date, completed
    """
    defaults = defaults or {}

    widgets: Dict[str, Any] = {}

    # Title
    title_var = tk.StringVar(value=defaults.get('title', ''))
    title_entry = tk.Entry(parent, textvariable=title_var, font=("Arial", 11), relief="solid", borderwidth=1)
    widgets['title'] = title_entry

    # Description
    desc_text = tk.Text(parent, height=4, font=("Arial", 11), relief="solid", borderwidth=1)
    desc_text.insert('1.0', defaults.get('description', ''))
    widgets['description'] = desc_text

    # Priority
    priority_var = tk.StringVar(value=defaults.get('priority', TaskPriorities.MEDIUM))
    priority_combo = ttk.Combobox(parent, textvariable=priority_var, values=TaskPriorities.ALL, state='readonly')
    widgets['priority'] = priority_combo

    # Client searchable combobox
    client_combo = SearchableCombobox(parent, values=_get_client_names(clients_mgr), font=("Arial", 11))
    client_combo.set(defaults.get('client_name', 'Без клиента'))
    widgets['client_combo'] = client_combo

    # Due date
    due_date_var = tk.StringVar(value=format_ddmmyyyy(defaults.get('due_date')))
    widgets['due_date_var'] = due_date_var

    # Completed flag (useful for edit forms)
    completed_var = tk.BooleanVar(value=defaults.get('completed', False))
    widgets['completed_var'] = completed_var

    return widgets


def collect_task_form_data(widgets: Dict[str, Any], clients_mgr) -> Dict[str, Any]:
    """Собирает и валидирует данные из виджетов, возвращает словарь готовых значений.

    Возвращаемые поля: title, description, priority, client_id, due_date (date|None), completed
    Бросает ValueError при ошибочной валидации.
    """
    title = widgets['title'].get().strip()
    if not title:
        raise ValueError('Укажите комментарий задачи')

    description = widgets['description'].get('1.0', tk.END).strip()
    priority = widgets['priority'].get() or TaskPriorities.MEDIUM

    client_name = widgets['client_combo'].get()
    client_id = None
    if client_name and client_name != 'Без клиента':
        client_id = clients_mgr.get_id_by_company_name(client_name)

    due_date_str = widgets['due_date_var'].get().strip()
    due_date = None
    if due_date_str:
        due_date = parse_ddmmyyyy(due_date_str)
        if due_date is None:
            raise ValueError('Неверный формат даты. Используйте ДД.ММ.ГГГГ')

    completed = bool(widgets.get('completed_var', tk.BooleanVar()).get())

    return {
        'title': title,
        'description': description,
        'priority': priority,
        'client_id': client_id,
        'due_date': due_date,
        'completed': completed
    }


def _get_client_names(clients_mgr):
    try:
        all_clients = clients_mgr.get_all()
        client_names = ['Без клиента'] + [client.get('company', '—') for client in all_clients]
        return [name for name in client_names if name and name.strip()]
    except Exception:
        return ['Без клиента']


class TaskFormDialog:
    """Единый диалог создания и редактирования задачи."""

    def __init__(
        self,
        parent,
        clients_mgr,
        on_save,
        task=None,
        fixed_client_id=None,
        on_delete=None,
        on_open_client=None
    ):
        self.parent = parent
        self.clients_mgr = clients_mgr
        self.on_save = on_save
        self.task = task
        self.fixed_client_id = fixed_client_id
        self.on_delete = on_delete
        self.on_open_client = on_open_client
        self.client_options = {}
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Редактирование задачи" if task else "Новая задача")
        self.dialog.geometry("700x760")
        self.dialog.minsize(660, 700)
        self.dialog.configure(bg=Colors.LIGHT)
        self.dialog.transient(parent.winfo_toplevel())
        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)
        self._create_widgets()
        center_toplevel(self.dialog)
        self.dialog.grab_set()
        self.title_entry.focus_set()

    def _create_widgets(self):
        header = tk.Frame(self.dialog, bg=Colors.DARK, height=62)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header,
            text="Редактирование задачи" if self.task else "Новая задача",
            font=("Arial", 17, "bold"),
            bg=Colors.DARK,
            fg=Colors.WHITE
        ).pack(side=tk.LEFT, padx=24)

        content = tk.Frame(self.dialog, bg=Colors.LIGHT, padx=24, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        content.columnconfigure(0, weight=1)

        details = tk.LabelFrame(
            content,
            text="Основная информация",
            bg=Colors.SURFACE,
            fg=Colors.TEXT,
            font=("Arial", 10, "bold"),
            padx=14,
            pady=12
        )
        details.pack(fill=tk.X, pady=(0, 14))
        details.columnconfigure(0, weight=1)

        label_options = {
            "font": ("Arial", 10, "bold"),
            "bg": Colors.SURFACE,
            "fg": Colors.TEXT
        }
        entry_options = {
            "font": ("Arial", 11),
            "relief": "solid",
            "borderwidth": 1,
            "bg": Colors.WHITE,
            "fg": Colors.TEXT,
            "insertbackground": Colors.TEXT,
            "highlightthickness": 1,
            "highlightbackground": Colors.BORDER,
            "highlightcolor": Colors.PRIMARY
        }

        tk.Label(details, text="Комментарий *", **label_options).grid(
            row=0, column=0, sticky="w"
        )
        self.title_entry = tk.Entry(details, **entry_options)
        self.title_entry.grid(row=1, column=0, sticky="ew", pady=(5, 12), ipady=5)

        quick_comments = tk.Frame(details, bg=Colors.SURFACE)
        quick_comments.grid(row=2, column=0, sticky="w", pady=(0, 12))
        for label, value in (
            ("Перезвонить", "Перезвонить"),
            ("Получить ответ", "Получить ответ"),
            ("Отправить КП", "Отправить КП")
        ):
            tk.Button(
                quick_comments,
                text=label,
                command=lambda comment=value: self._set_quick_comment(comment),
                bg=Colors.LIGHT,
                fg=Colors.TEXT,
                activebackground=Colors.BORDER,
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=5
            ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(details, text="Описание", **label_options).grid(
            row=3, column=0, sticky="w"
        )
        self.description_text = tk.Text(
            details,
            height=4,
            font=("Arial", 11),
            wrap=tk.WORD,
            relief="solid",
            borderwidth=1,
            bg=Colors.WHITE,
            fg=Colors.TEXT,
            insertbackground=Colors.TEXT,
            highlightthickness=1,
            highlightbackground=Colors.BORDER,
            highlightcolor=Colors.PRIMARY
        )
        self.description_text.grid(
            row=4, column=0, sticky="ew", pady=(5, 0)
        )

        parameters = tk.LabelFrame(
            content,
            text="Параметры задачи",
            bg=Colors.SURFACE,
            fg=Colors.TEXT,
            font=("Arial", 10, "bold"),
            padx=14,
            pady=12
        )
        parameters.pack(fill=tk.X)
        parameters.columnconfigure(0, weight=1)
        parameters.columnconfigure(1, weight=1)

        ttk_style = ttk.Style(self.dialog)
        ttk_style.configure(
            "TaskForm.TCombobox",
            padding=6,
            fieldbackground=Colors.WHITE,
            foreground=Colors.TEXT
        )

        tk.Label(parameters, text="Клиент", **label_options).grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        client_names = ["Без клиента"]
        try:
            for client in self.clients_mgr.get_all():
                company = client.get("company", "").strip()
                if company:
                    self.client_options[company] = client.get("id")
                    client_names.append(company)
        except Exception as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось загрузить список клиентов:\n{error}",
                parent=self.dialog
            )
        client_names = list(dict.fromkeys(client_names))

        self.client_var = tk.StringVar()
        self.client_combo = ttk.Combobox(
            parameters,
            textvariable=self.client_var,
            values=client_names,
            state="readonly" if self.fixed_client_id is not None else "normal",
            style="TaskForm.TCombobox"
        )
        self.client_combo.grid(
            row=1, column=0, sticky="ew", padx=(0, 10), pady=(5, 14)
        )

        tk.Label(parameters, text="Приоритет", **label_options).grid(
            row=0, column=1, sticky="w", padx=(10, 0)
        )
        self.priority_var = tk.StringVar(
            value=getattr(self.task, "priority", None) or TaskPriorities.MEDIUM
        )
        self.priority_combo = ttk.Combobox(
            parameters,
            textvariable=self.priority_var,
            values=TaskPriorities.ALL,
            state="readonly",
            style="TaskForm.TCombobox"
        )
        self.priority_combo.grid(
            row=1, column=1, sticky="ew", padx=(10, 0), pady=(5, 14)
        )

        tk.Label(parameters, text="Срок выполнения", **label_options).grid(
            row=2, column=0, sticky="w", padx=(0, 10)
        )
        date_frame = tk.Frame(parameters, bg=Colors.SURFACE)
        date_frame.grid(row=3, column=0, sticky="ew", padx=(0, 10), pady=(5, 0))
        self.due_date_var = tk.StringVar(
            value=format_ddmmyyyy(getattr(self.task, "due_date", None))
        )
        self.due_date_entry = tk.Entry(
            date_frame,
            textvariable=self.due_date_var,
            **entry_options
        )
        self.due_date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        tk.Button(
            date_frame,
            text="Выбрать дату",
            command=self._choose_date,
            bg=Colors.PRIMARY,
            fg=Colors.WHITE,
            activebackground=Colors.PRIMARY_HOVER,
            activeforeground=Colors.WHITE,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=7
        ).pack(side=tk.RIGHT, padx=(8, 0))

        quick_dates = tk.Frame(parameters, bg=Colors.SURFACE)
        quick_dates.grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0)
        )
        for label, days in (("Завтра", 1), ("Через 3 дня", 3), ("Через неделю", 7)):
            tk.Button(
                quick_dates,
                text=label,
                command=lambda offset=days: self._set_quick_date(offset),
                bg=Colors.LIGHT,
                fg=Colors.TEXT,
                activebackground=Colors.BORDER,
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=5
            ).pack(side=tk.LEFT, padx=(0, 8))

        created_at = getattr(self.task, "created_at", None) if self.task else None
        created_text = self._format_created_date(created_at)
        tk.Label(
            parameters,
            text=f"создано {created_text}",
            bg=Colors.SURFACE,
            fg=Colors.MUTED,
            font=("Arial", 9)
        ).grid(row=3, column=1, sticky="w", padx=(10, 0), pady=(5, 0))

        self._set_client_value()
        self._set_task_values()
        self._create_buttons()

    def _set_quick_date(self, days):
        """Устанавливает срок задачи относительно сегодняшней даты."""
        self.due_date_var.set((date.today() + timedelta(days=days)).strftime("%d.%m.%Y"))

    def _set_quick_comment(self, comment):
        """Подставляет типовой комментарий в поле задачи."""
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, comment)
        self.title_entry.focus_set()

    @staticmethod
    def _format_created_date(value):
        """Форматирует дату создания задачи для отображения в форме."""
        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y")
        if isinstance(value, date):
            return value.strftime("%d.%m.%Y")
        if isinstance(value, str) and value:
            for date_format in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
                "%d.%m.%Y %H:%M:%S",
                "%d.%m.%Y"
            ):
                try:
                    return datetime.strptime(value, date_format).strftime("%d.%m.%Y")
                except ValueError:
                    continue
        return "—"

    def _set_client_value(self):
        if self.fixed_client_id is not None:
            client = self.clients_mgr.get_by_id(self.fixed_client_id)
            self.client_var.set(
                client.get("company", "Без клиента") if client else "Без клиента"
            )
            self.client_combo.configure(state="disabled")
        elif self.task is not None:
            client_id = getattr(self.task, "client_id", None)
            client = self.clients_mgr.get_by_id(client_id) if client_id else None
            self.client_var.set(
                client.get("company", "Без клиента") if client else "Без клиента"
            )
        else:
            self.client_var.set("Без клиента")

    def _set_task_values(self):
        if self.task is None:
            return
        self.title_entry.insert(0, getattr(self.task, "title", "") or "")
        self.description_text.insert(
            "1.0", getattr(self.task, "description", "") or ""
        )

    def _create_buttons(self):
        buttons = tk.Frame(
            self.dialog,
            bg=Colors.SURFACE,
            padx=24,
            pady=14
        )
        buttons.pack(fill=tk.X, side=tk.BOTTOM)

        if self.on_delete is not None:
            tk.Button(
                buttons,
                text="Удалить",
                command=self.on_delete,
                bg=Colors.DANGER,
                fg=Colors.WHITE,
                activebackground=Colors.DANGER_HOVER,
                relief="flat",
                cursor="hand2",
                padx=14,
                pady=8
            ).pack(side=tk.LEFT)

        tk.Button(
            buttons,
            text="Отмена",
            command=self.dialog.destroy,
            bg=Colors.LIGHT,
            fg=Colors.TEXT,
            activebackground=Colors.BORDER,
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8
        ).pack(side=tk.RIGHT)
        tk.Button(
            buttons,
            text="Сохранить",
            command=self._submit,
            bg=Colors.PRIMARY,
            fg=Colors.WHITE,
            activebackground=Colors.PRIMARY_HOVER,
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8
        ).pack(side=tk.RIGHT, padx=(0, 10))
        if self.on_open_client is not None:
            tk.Button(
                buttons,
                text="Клиент",
                command=self._open_client,
                bg=Colors.INFO,
                fg=Colors.WHITE,
                activebackground=Colors.PRIMARY_HOVER,
                relief="flat",
                cursor="hand2",
                padx=16,
                pady=8
            ).pack(side=tk.RIGHT, padx=(0, 10))

        if self.task is not None and getattr(self.task, "is_financial", False):
            tk.Button(
                buttons,
                text="💰 Расходы",
                command=self._open_expenses,
                bg="#b45309",
                fg=Colors.WHITE,
                activebackground="#92400e",
                relief="flat",
                cursor="hand2",
                padx=16,
                pady=8
            ).pack(side=tk.RIGHT, padx=(0, 10))

    def _open_expenses(self):
        """Открыть окно расходов по работе, связанной с задачей."""
        from managers.works_manager import WorksManager
        from views.work_expenses_dialog import show_work_expenses_dialog

        work_id = getattr(self.task, "work_id", None) if self.task else None
        if not work_id:
            messagebox.showinfo(
                "Расходы",
                "Для этой задачи не указана работа.",
                parent=self.dialog
            )
            return

        works_mgr = WorksManager()
        work = works_mgr.get(work_id)
        if work is None:
            messagebox.showerror(
                "Расходы",
                "Работа не найдена в учёте.",
                parent=self.dialog
            )
            return

        self.dialog.grab_release()
        try:
            show_work_expenses_dialog(self.dialog, work, works_mgr)
        finally:
            try:
                self.dialog.grab_set()
            except tk.TclError:
                pass

    def _open_client(self):
        """Переводит фокус к карточке клиента, сохраняя открытую форму задачи."""
        client_id = self.fixed_client_id
        if client_id is None and self.task is not None:
            client_id = getattr(self.task, "client_id", None)
        if client_id is None:
            client_id = self.client_options.get(self.client_var.get())
        if client_id is None:
            messagebox.showwarning(
                "Клиент",
                "Сначала выберите клиента.",
                parent=self.dialog
            )
            return

        try:
            self.dialog.grab_release()
            client_window = self.on_open_client(client_id)
            if client_window is False:
                self.dialog.transient(self.parent.winfo_toplevel())
                self.dialog.grab_set()
                self.dialog.lift()
                return
            if client_window is not None:
                self.dialog.transient(client_window)
                self.dialog.lower(client_window)
        except Exception as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось открыть карточку клиента:\n{error}",
                parent=self.dialog
            )
            self.dialog.transient(self.parent.winfo_toplevel())
            self.dialog.grab_set()
            self.dialog.lift()

    def _choose_date(self):
        from views.calendar_view import CalendarDialog

        calendar = CalendarDialog(self.dialog, "Выберите срок выполнения")
        selected_date = calendar.show()
        if selected_date:
            self.due_date_var.set(selected_date.strftime("%d.%m.%Y"))

    def _submit(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror(
                "Проверка данных",
                "Заполните поле «Комментарий».",
                parent=self.dialog
            )
            self.title_entry.focus_set()
            return

        date_text = self.due_date_var.get().strip()
        due_date = parse_ddmmyyyy(date_text) if date_text else None
        if date_text and due_date is None:
            messagebox.showerror(
                "Проверка данных",
                "Неверная дата.",
                parent=self.dialog
            )
            self.due_date_entry.focus_set()
            return

        client_id = self.fixed_client_id
        if client_id is None:
            client_name = self.client_var.get().strip()
            if client_name and client_name != "Без клиента":
                client_id = self.client_options.get(client_name)
                if client_id is None:
                    messagebox.showerror(
                        "Проверка данных",
                        "Выберите клиента из списка.",
                        parent=self.dialog
                    )
                    self.client_combo.focus_set()
                    return

        try:
            self.on_save({
                "title": title,
                "description": self.description_text.get("1.0", tk.END).strip(),
                "priority": self.priority_var.get(),
                "client_id": client_id,
                "due_date": due_date,
                "completed": bool(getattr(self.task, "completed", False))
            })
            self.dialog.destroy()
        except ValueError as error:
            messagebox.showerror("Проверка данных", str(error), parent=self.dialog)
        except Exception as error:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось сохранить задачу:\n{error}",
                parent=self.dialog
            )