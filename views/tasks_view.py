"""
Представление раздела Задачи
"""
import tkinter as tk
from tkinter import ttk
from views.base_view import BaseView
from datetime import date, datetime
from views.calendar_view import CalendarDialog


class TasksView(BaseView):
    def __init__(self, parent_frame, tasks_mgr, clients_mgr):
        super().__init__(parent_frame)
        self.tasks_mgr = tasks_mgr
        self.clients_mgr = clients_mgr
        self.search_var = None
        self.filter_var = None
        self.list_frame = None

    def show(self):
        """Отображение раздела"""
        self.clear()

        # --- ВЕРХНЯЯ ПАНЕЛЬ ---
        top_panel = tk.Frame(self.parent_frame, bg='#f0f0f0', height=70)
        top_panel.pack(fill=tk.X)
        top_panel.pack_propagate(False)

        # 1. СНАЧАЛА КНОПКА (справа)
        tk.Button(
            top_panel,
            text="+ Новая задача",
            command=self._show_add_dialog,
            bg="#41a5be",
            fg="black",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=15
        ).pack(side=tk.RIGHT, padx=20, pady=15)

        # 2. ПОТОМ ПОИСК (слева)
        search_container = tk.Frame(top_panel, bg='#f0f0f0')
        search_container.pack(side=tk.LEFT, padx=20, pady=15)

        tk.Label(search_container, text="🔍", font=("Arial", 14), bg='#f0f0f0', fg='#333').pack(side=tk.LEFT)

        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._refresh_list())

        tk.Entry(search_container, textvariable=self.search_var, font=("Arial", 12), width=30).pack(side=tk.LEFT,
                                                                                                    padx=5)

        # 3. ПОТОМ ФИЛЬТР (слева)
        tk.Label(top_panel, text="Фильтр:", bg='#f0f0f0', font=("Arial", 10)).pack(side=tk.LEFT, padx=(20, 5))

        # ... код фильтра (без изменений) ...
        self.filter_map = {
            "Все задачи": "all",
            "Активные": "active",
            "Выполненные": "completed",
            "Просроченные": "overdue"
        }
        self.filter_map_reverse = {v: k for k, v in self.filter_map.items()}
        self.filter_var = tk.StringVar(value="Активные")

        filter_cb = ttk.Combobox(
            top_panel,
            textvariable=self.filter_var,
            values=list(self.filter_map.keys()),
            state="readonly",
            width=15,
            font=("Arial", 10)
        )
        filter_cb.pack(side=tk.LEFT, pady=15)  # Добавил pady для выравнивания
        filter_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_list())

        # ... остальной код (статистика и список) ...
        # --- СТАТИСТИКА ---
        stat_panel = tk.Frame(self.parent_frame, bg='#f8f9fa', height=30)
        stat_panel.pack(fill=tk.X)
        self.stat_label = tk.Label(stat_panel, text="", bg='#f8f9fa', fg='#666', font=("Arial", 10))
        self.stat_label.pack(side=tk.LEFT, padx=20)

        # --- СПИСОК ЗАДАЧ ---
        self.list_frame = tk.Frame(self.parent_frame, bg='white')
        self.list_frame.pack(fill=tk.BOTH, expand=True)

        self._refresh_list()

    def _refresh_list(self):
        """Обновить список задач"""
        # Очистка
        for w in self.list_frame.winfo_children():
            w.destroy()

        search = self.search_var.get().strip()

        # Получаем код фильтра из русского названия
        filter_text = self.filter_var.get()
        fltr = self.filter_map.get(filter_text, "all")

        if search:
            tasks = self.tasks_mgr.search(search)
        else:
            tasks = self.tasks_mgr.get_all(fltr)

        # Обновляем статистику
        active_count = self.tasks_mgr.get_count(only_active=True)
        self.stat_label.config(text=f"Активных задач: {active_count}")

        if not tasks:
            tk.Label(self.list_frame, text="Задач не найдено", font=("Arial", 14), fg="gray", bg='white').pack(pady=50)
            return

        # Canvas
        canvas = tk.Canvas(self.list_frame, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(self.list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')

        scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')

        def on_canvas_configure(event):
            canvas.itemconfig(canvas.find_all()[0], width=event.width)

        canvas.bind('<Configure>', on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Заголовки
        headers_frame = tk.Frame(scrollable_frame, bg='#333333')
        headers_frame.pack(fill=tk.X)
        cols = [("Статус", 5), ("Название", 30), ("Клиент", 20), ("Срок", 15), ("Действия", 10)]
        for col, width in cols:
            tk.Label(headers_frame, text=col, bg='#333333', fg='white', font=("Arial", 10, "bold"), width=width).pack(
                side=tk.LEFT, padx=5, pady=5)

        # Строки
        for task in tasks:
            self._create_task_row(scrollable_frame, task)

        # Прокрутка
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _create_task_row(self, parent, task):
        """Создать строку задачи"""
        row_bg = '#f0fff4' if task['completed'] else 'white'
        if not task['completed'] and task['due_date'] and task['due_date'] < date.today().isoformat():
            row_bg = '#fff0f0'  # Просрочено

        row = tk.Frame(parent, bg=row_bg, pady=5)
        row.pack(fill=tk.X, pady=1)

        # Чекбокс (кнопка)
        status_icon = "✅" if task['completed'] else "⬜"
        tk.Button(row, text=status_icon, command=lambda: self._toggle_status(task),
                  bg=row_bg, relief="flat", font=("Arial", 12), width=5).pack(side=tk.LEFT, padx=5)

        # Название и описание
        info_frame = tk.Frame(row, bg=row_bg, width=300)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        title_font = ("Arial", 11, "overstrike") if task['completed'] else ("Arial", 11, "bold")
        tk.Label(info_frame, text=task['title'], font=title_font, bg=row_bg, anchor='w').pack(fill=tk.X)
        if task['description']:
            tk.Label(info_frame, text=task['description'], font=("Arial", 9), fg="#666", bg=row_bg, anchor='w').pack(
                fill=tk.X)

        # Клиент
        client_name = task['client_name'] or "—"
        tk.Label(row, text=client_name, width=20, bg=row_bg, anchor='w').pack(side=tk.LEFT, padx=5)

        # Дата
        date_str = task['due_date'] or "—"
        date_fg = "red" if row_bg == '#fff0f0' else "black"
        tk.Label(row, text=date_str, width=15, bg=row_bg, fg=date_fg).pack(side=tk.LEFT, padx=5)

        # Кнопки
        actions = tk.Frame(row, bg=row_bg)
        actions.pack(side=tk.RIGHT, padx=10)
        tk.Button(actions, text="🗑", command=lambda: self._delete_task(task), bg="#d9534f", fg="white", width=3).pack(
            side=tk.LEFT)

    def _toggle_status(self, task):
        self.tasks_mgr.toggle_status(task['id'], task['completed'])
        self._refresh_list()

    def _delete_task(self, task):
        from utils.helpers import show_confirmation, show_message
        if show_confirmation(self.parent_frame.master, "Удаление", f"Удалить задачу '{task['title']}'?"):
            self.tasks_mgr.delete(task['id'])
            self._refresh_list()

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

        # --- 1) ПРИОРИТЕТ ---
        tk.Label(content, text="Приоритет", font=("Arial", 10, "bold"), bg="white").pack(anchor='w')
        priority_frame = tk.Frame(content, bg='white')
        priority_frame.pack(fill=tk.X, pady=(5, 15))

        priority_var = tk.StringVar(value="Средний")
        priorities = [("🔥 Высокий", "red"), ("⚡ Средний", "orange"), ("❄ Низкий", "green")]

        for text, color in priorities:
            val = text.split()[1]  # Берем слово "Высокий" без смайла для значения
            rb = tk.Radiobutton(priority_frame, text=text, variable=priority_var, value=val,
                                bg='white', activebackground='white', fg=color, selectcolor='white', font=("Arial", 10))
            rb.pack(side=tk.LEFT, padx=(0, 15))

        # --- 2) СРОК И КНОПКИ ДАТЫ ---
        tk.Label(content, text="Срок выполнения", font=("Arial", 10, "bold"), bg="white").pack(anchor='w')

        # Фрейм для строки ввода и кнопок
        date_frame = tk.Frame(content, bg='white')
        date_frame.pack(fill=tk.X, pady=(5, 15))

        # Поле ввода даты
        date_entry = tk.Entry(date_frame, font=("Arial", 11), bg='#f8f9fa', relief="solid", bd=1)
        date_entry.insert(0, date.today().isoformat())
        date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)

        # Функции для кнопок
        def set_date_val(d):
            date_entry.delete(0, tk.END)
            date_entry.insert(0, d)

        def open_calendar():
            CalendarDialog(dialog, set_date_val)

        from datetime import timedelta

        # Кнопки: Сегодня | Завтра | 📅
        tk.Button(date_frame, text="Сегодня", command=lambda: set_date_val(date.today().isoformat()),
                  bg="#e0e0e0", relief="flat").pack(side=tk.LEFT, padx=5)

        tk.Button(date_frame, text="Завтра",
                  command=lambda: set_date_val((date.today() + timedelta(days=1)).isoformat()),
                  bg="#e0e0e0", relief="flat").pack(side=tk.LEFT, padx=5)

        tk.Button(date_frame, text="📅", command=open_calendar,
                  bg="#41a5be", fg="white", relief="flat", width=3).pack(side=tk.LEFT, padx=5)

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

            client_id = client_map.get(client_cb.get())

            # Проверка даты
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