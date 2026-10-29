# -*- coding: utf-8 -*-
"""
Список клиентов с таблицей, поиском и пагинацией
Наследуется от TableViewTemplate
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from views.table_view_template import TableViewTemplate
from services.task_service import TaskService
from utils.constants import TableView, Sizes
from utils.ui_helpers import center_toplevel


class ClientListView(TableViewTemplate):
    """
    Табличное представление списка клиентов
    
    Features:
    - Поиск по компании и контактному лицу
    - Сортировка
    - Пагинация
    - Быстрое создание задачи из таблицы
    """
    
    TITLE = "Клиенты"
    ADD_BUTTON_TEXT = "+ Добавить клиента"
    SEARCH_FIELDS_TEXT = "компании или контактному лицу"
    COLUMNS = ("ID", "Компания", "Контактное лицо", "Должность", "Телефон", "Адрес", "Задачи")
    COLUMN_WIDTHS = {
        "ID": 50,
        "Компания": 200,
        "Контактное лицо": 180,
        "Должность": 150,
        "Телефон": 120,
        "Адрес": 200,
        "Задачи": 100
    }
    STRETCH_COLUMNS = ["Компания", "Контактное лицо", "Должность", "Телефон", "Адрес"]
    ID_COLUMN = "ID"
    PAGE_SIZE = 50
    
    SORT_OPTIONS = [
        ("company", "По компании (А-Я)"),
        ("company:DESC", "По компании (Я-А)"),
        ("primary_contact", "По контакту (А-Я)"),
        ("primary_contact:DESC", "По контакту (Я-А)"),
        ("created_at", "По дате создания (новые)"),
        ("created_at:DESC", "По дате создания (старые)")
    ]
    
    def __init__(self, parent_frame, clients_mgr, tasks_mgr=None, 
                 on_client_click=None, on_add_client=None, on_create_task=None):
        """
        Args:
            parent_frame: родительский фрейм
            clients_mgr: менеджер клиентов
            tasks_mgr: менеджер задач (опционально)
            on_client_click: callback при клике на клиента (client_id)
            on_add_client: callback при нажатии "Добавить"
            on_create_task: callback при создании задачи (client_id)
        """
        super().__init__(parent_frame, clients_mgr)
        self.clients_mgr = clients_mgr
        self.tasks_mgr = tasks_mgr
        self.on_client_click = on_client_click
        self.on_add_client = on_add_client
        self.on_create_task = on_create_task
        
    def _create_table(self):
        """Создать таблицу с обработкой клика на колонку 'Задачи'"""
        super()._create_table()
        
        # Добавляем обработку одинарного клика на колонку "Задачи"
        self.tree.bind('<Button-1>', self._on_single_click)
        
    def _on_single_click(self, event):
        """Обработка клика по таблице"""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        if not item or not column:
            return
            
        # Клик на колонку "Задачи" (#7)
        if column == "#7":
            values = self.tree.item(item, 'values')
            if not values:
                return
                
            try:
                client_id = int(values[0])
                if self.on_create_task:
                    self.on_create_task(client_id)
                else:
                    self._create_task_for_client(client_id)
            except (ValueError, IndexError):
                pass
                
    def _create_task_for_client(self, client_id):
        """Создать задачу для клиента (встроенная реализация)"""
        if not self.tasks_mgr:
            messagebox.showerror("Ошибка", "Менеджер задач не инициализирован")
            return
            
        try:
            client = self.clients_mgr.get_by_id(client_id)
            if not client:
                return
                
            task_window = tk.Toplevel(self.parent_frame)
            task_window.title("➕ Новая задача")
            task_window.geometry("600x550")
            task_window.configure(bg='white')
            task_window.resizable(False, False)
            center_toplevel(task_window)
            
            task_window.transient(self.parent_frame.winfo_toplevel())
            task_window.grab_set()
            task_window.focus_set()
            
            # Форма
            main_frame = tk.Frame(task_window, bg='white')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # Название
            tk.Label(main_frame, text="Название задачи *", font=("Arial", 10, "bold"), bg='white').pack(anchor='w')
            title_entry = tk.Entry(main_frame, font=("Arial", 11), width=50)
            title_entry.pack(fill=tk.X, pady=(5, 15))
            
            # Описание
            tk.Label(main_frame, text="Описание", font=("Arial", 10, "bold"), bg='white').pack(anchor='w')
            desc_text = tk.Text(main_frame, font=("Arial", 11), height=4, width=50)
            desc_text.pack(fill=tk.X, pady=(5, 15))
            
            # Клиент
            tk.Label(main_frame, text="Клиент", font=("Arial", 10, "bold"), bg='white').pack(anchor='w')
            client_var = tk.StringVar(value=client['company'])
            client_entry = tk.Entry(main_frame, textvariable=client_var, font=("Arial", 11), state='readonly')
            client_entry.pack(fill=tk.X, pady=(5, 15))
            
            # Приоритет
            tk.Label(main_frame, text="Приоритет", font=("Arial", 10, "bold"), bg='white').pack(anchor='w')
            priority_var = tk.StringVar(value="Средний")
            ttk.Combobox(main_frame, textvariable=priority_var,
                        values=["Низкий", "Средний", "Высокий"],
                        state="readonly", width=20).pack(fill=tk.X, pady=(5, 15))
            
            # Срок
            tk.Label(main_frame, text="Срок выполнения", font=("Arial", 10, "bold"), bg='white').pack(anchor='w')
            date_frame = tk.Frame(main_frame, bg='white')
            date_frame.pack(fill=tk.X, pady=(5, 15))
            
            due_date_var = tk.StringVar(value=datetime.now().strftime("%d.%m.%Y"))
            due_date_entry = tk.Entry(date_frame, textvariable=due_date_var, font=("Arial", 11))
            due_date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            from views.calendar_view import CalendarDialog
            def show_calendar():
                cal_dialog = CalendarDialog(task_window, "Выберите срок")
                selected_date = cal_dialog.show()
                if selected_date:
                    due_date_var.set(selected_date.strftime("%d.%m.%Y"))
            
            tk.Button(date_frame, text="📅", command=show_calendar,
                     bg="#41a5be", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
            
            # Кнопки
            buttons_frame = tk.Frame(main_frame, bg='white')
            buttons_frame.pack(fill=tk.X, pady=(20, 0))
            
            def save_task():
                title = title_entry.get().strip()
                if not title:
                    messagebox.showerror("Ошибка", "Укажите название задачи")
                    return
                    
                task_service = TaskService(self.tasks_mgr, self.clients_mgr)
                task_data = {
                    'title': title,
                    'description': desc_text.get('1.0', tk.END).strip(),
                    'client_id': client_id,
                    'priority': priority_var.get(),
                    'due_date': due_date_var.get()
                }
                
                try:
                    task_service.create_task(task_data)
                    task_window.destroy()
                    messagebox.showinfo("Успех", "Задача создана!")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось создать задачу: {e}")
            
            tk.Button(buttons_frame, text="Сохранить", command=save_task,
                     bg="#28a745", fg="white", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=5)
            tk.Button(buttons_frame, text="Отмена", command=task_window.destroy,
                     bg="#6c757d", fg="white", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=5)
            
            title_entry.focus_set()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать задачу: {e}")
            
    def _get_data(self, page, search, sort_by, sort_order):
        """Загрузка данных для таблицы"""
        try:
            if search:
                clients = self.clients_mgr.search(search.lower())
            else:
                clients = self.clients_mgr.get_all()
            
            # Сортировка
            if sort_by:
                clients = self._apply_sort(clients, sort_by, sort_order)
            
            # Пагинация
            total = len(clients)
            start_idx = (page - 1) * self.PAGE_SIZE
            end_idx = start_idx + self.PAGE_SIZE
            paginated_clients = clients[start_idx:end_idx]
            
            return paginated_clients, total
            
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            return [], 0
            
    def _apply_sort(self, clients, sort_by, sort_order):
        """Применить сортировку"""
        reverse = sort_order == "DESC"
        
        if sort_by == "company":
            clients.sort(key=lambda x: x.get('company', '').lower(), reverse=reverse)
        elif sort_by == "primary_contact":
            clients.sort(key=lambda x: x.get('primary_contact', '').lower(), reverse=reverse)
        elif sort_by == "created_at":
            clients.sort(key=lambda x: x.get('created_at', ''), reverse=reverse)
            
        return clients
        
    def _item_to_row_values(self, item):
        """Преобразовать клиента в строку таблицы"""
        if not isinstance(item, dict):
            return ("", "", "", "", "", "", "")
        
        return (
            item.get('id', ''),
            item.get('company', '—'),
            item.get('primary_contact', '—'),
            item.get('primary_position', '—'),
            item.get('primary_phone', '—'),
            item.get('address', '—'),
            "➕ Задача"
        )
        
    def _open_create_dialog(self):
        """Открыть диалог создания клиента"""
        if self.on_add_client:
            self.on_add_client()
            
    def _on_row_double_click(self, client_id):
        """Обработка двойного клика по строке"""
        if self.on_client_click:
            self.on_client_click(client_id)
            
    def refresh(self):
        """Обновить данные таблицы"""
        self._refresh_data()
