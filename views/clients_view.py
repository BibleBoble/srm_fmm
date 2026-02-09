# -*- coding: utf-8 -*-
"""
Представление раздела "Клиенты" на базе TableViewTemplate
"""
import tkinter as tk
from tkinter import ttk, messagebox
from views.table_view_template import TableViewTemplate
from views.calendar_view import CalendarDialog
from utils.helpers import show_message, show_confirmation
from utils.constants import TableView, Sizes
from datetime import date, datetime


class ClientTasksTable:
    """Таблица задач для конкретного клиента"""
    
    def __init__(self, parent, client_id, tasks_mgr, clients_mgr):
        self.parent = parent
        self.client_id = client_id
        self.tasks_mgr = tasks_mgr
        self.clients_mgr = clients_mgr
        self.tree = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Создает интерфейс таблицы"""
        # Заголовок
        header_frame = tk.Frame(self.parent, bg='#f8f9fa')
        header_frame.pack(fill=tk.X, padx=15, pady=(20, 10))
        
        tk.Label(
            header_frame,
            text="Задачи клиента",
            font=("Arial", 16, "bold"),
            bg='#f8f9fa',
            fg='#333'
        ).pack(side=tk.LEFT)
        
        # Контейнер для элементов справа
        right_container = tk.Frame(header_frame, bg='#f8f9fa')
        right_container.pack(side=tk.RIGHT)
        
        # Сортировка
        tk.Label(
            right_container,
            text="Сортировка:",
            font=("Arial", 10),
            bg='#f8f9fa',
            fg='#666'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.sort_var = tk.StringVar(value="Активные")
        sort_options = [
            "Все",
            "Активные", 
            "Выполненные",
           ]
        
        sort_combo = ttk.Combobox(
            right_container,
            textvariable=self.sort_var,
            values=sort_options,
            state="readonly",
            width=20,
            font=("Arial", 9)
        )
        sort_combo.pack(side=tk.LEFT, padx=(0, 10))
        sort_combo.bind("<<ComboboxSelected>>", self._on_sort_change)
        
        # Кнопка добавления задачи
        add_btn = tk.Button(
            right_container,
            text="+ Добавить задачу",
            command=self._add_task,
            bg="#28a745",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2"
        )
        add_btn.pack(side=tk.LEFT, padx=10)
        
        # Создаем таблицу
        self._create_table()
        
        # Загружаем данные
        self._load_tasks()
    
    def _create_table(self):
        """Создает Treeview таблицу"""
        # Фрейм для таблицы с прокруткой
        table_frame = tk.Frame(self.parent)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 20))
        
        # Создаем Treeview
        self.tree = ttk.Treeview(
            table_frame,
            columns=("ID", "Статус", "Название", "Приоритет", "Срок"),
            show="headings",
            selectmode="browse"
        )
        
        # Настройка колонок
        self.tree.heading("ID", text="ID")
        self.tree.heading("Статус", text="Статус")
        self.tree.heading("Название", text="Название")
        self.tree.heading("Приоритет", text="Приоритет")
        self.tree.heading("Срок", text="Срок")
        
        # Ширина колонок
        self.tree.column("ID", width=50, minwidth=50)
        self.tree.column("Статус", width=100, minwidth=80)
        self.tree.column("Название", width=200, minwidth=150)
        self.tree.column("Приоритет", width=100, minwidth=80)
        self.tree.column("Срок", width=100, minwidth=80)
        
        # Прокрутка
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Обработчики
        self.tree.bind('<Double-1>', self._on_double_click)
        
        # Стиль для основного контакта
        self._setup_tag_styles()
    
    def _setup_tag_styles(self):
        """Настраивает стили для разных типов контактов"""
        style = ttk.Style()
        
        # Исправление для tag_configure в Windows
        def fixed_map(option):
            return [elm for elm in style.map('Treeview', query_opt=option) 
                   if elm[:2] != ('!disabled', '!selected')]
        
        style.map('Treeview', foreground=fixed_map('foreground'), 
                  background=fixed_map('background'))
        
        # Выделяем основной контакт зеленым цветом как в таблице клиентов
        self.tree.tag_configure("primary", background="#d4edda")
    
    def _apply_sorting(self, tasks, sort_option):
        """Применяет сортировку и фильтрацию к задачам"""
        try:
            # Сначала применяем фильтрацию
            if sort_option == "Активные":
                tasks = [task for task in tasks if self._get_status(task) == 'Активная']
            elif sort_option == "Выполненные":
                tasks = [task for task in tasks if self._get_status(task) == 'Выполнена']
            elif sort_option == "Все":
                pass  # Показываем все задачи
            else:
                # Применяем сортировку для других опций
                if sort_option == "По сроку (ближайшие)":
                    tasks = sorted(tasks, key=lambda t: self._get_due_date(t) or datetime.max)
                elif sort_option == "По сроку (дальние)":
                    tasks = sorted(tasks, key=lambda t: self._get_due_date(t) or datetime.min, reverse=True)
                elif sort_option == "По названию (А-Я)":
                    tasks = sorted(tasks, key=lambda t: self._get_title(t).lower())
                elif sort_option == "По названию (Я-А)":
                    tasks = sorted(tasks, key=lambda t: self._get_title(t).lower(), reverse=True)
                elif sort_option == "По приоритету (высокий→низкий)":
                    priority_order = {'Высокий': 1, 'Средний': 2, 'Низкий': 3}
                    tasks = sorted(tasks, key=lambda t: priority_order.get(self._get_priority(t), 4))
                elif sort_option == "По приоритету (низкий→высокий)":
                    priority_order = {'Высокий': 3, 'Средний': 2, 'Низкий': 1}
                    tasks = sorted(tasks, key=lambda t: priority_order.get(self._get_priority(t), 4))
            
            # По умолчанию для "Активные" и "Выполненные" сортируем по сроку
            if sort_option in ["Активные", "Выполненные", "Все"]:
                tasks = sorted(tasks, key=lambda t: self._get_due_date(t) or datetime.max)
            
            return tasks
        except:
            return tasks
    
    def _get_title(self, task):
        """Получает название задачи"""
        return task.title if hasattr(task, 'title') else task.get('title', '')
    
    def _get_status(self, task):
        """Получает статус задачи"""
        status = task.status if hasattr(task, 'status') else task.get('status', 'Активная')
        # Преобразуем старые статусы в новые
        if status in ['Новая', 'В работе', 'Отложена']:
            return 'Активная'
        elif status == 'Выполнена':
            return 'Выполнена'
        else:
            return 'Активная'  # По умолчанию
    
    def _get_priority(self, task):
        """Получает приоритет задачи"""
        return task.priority if hasattr(task, 'priority') else task.get('priority', '')
    
    def _get_due_date(self, task):
        """Получает срок выполнения задачи"""
        due_date = task.due_date if hasattr(task, 'due_date') else task.get('due_date', None)
        if due_date:
            if isinstance(due_date, str):
                try:
                    # Пробуем разные форматы даты
                    for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d.%m.%Y %H:%M:%S"]:
                        try:
                            return datetime.strptime(due_date, fmt)
                        except:
                            continue
                    return None
                except:
                    return None
            return due_date
        return None
    
    def _on_sort_change(self, event=None):
        """Обработчик изменения сортировки"""
        self._load_tasks()
    
    def _load_tasks(self):
        """Загружает задачи клиента в таблицу"""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.tasks_mgr:
            return
        
        try:
            # Получаем задачи клиента
            tasks = self.tasks_mgr.get_by_client(self.client_id)
            
            # Применяем сортировку
            sort_option = self.sort_var.get()
            tasks = self._apply_sorting(tasks, sort_option)
            
            for task in tasks:
                task_id = task.id if hasattr(task, 'id') else task.get('id', '')
                title = task.title if hasattr(task, 'title') else task.get('title', '')
                status = task.status if hasattr(task, 'status') else task.get('status', 'Новая')
                priority = task.priority if hasattr(task, 'priority') else task.get('priority', '')
                due_date = task.due_date if hasattr(task, 'due_date') else task.get('due_date', '')
                
                # Форматируем дату
                due_date_str = ""
                if due_date:
                    try:
                        if isinstance(due_date, str):
                            due_date_str = due_date
                        else:
                            due_date_str = due_date.strftime("%d.%m.%Y")
                    except:
                        due_date_str = str(due_date)
                
                # Иконки приоритета
                priority_icons = {'Высокий': '🔴', 'Средний': '🟡', 'Низкий': '🟢'}
                priority_str = f"{priority_icons.get(priority, '')} {priority}" if priority else ""
                
                # Добавляем в таблицу
                self.tree.insert(
                    "", 
                    "end",
                    values=(task_id, status, title, priority_str, due_date_str),
                    tags=(status,)
                )
        
        except Exception as e:
            print(f"Ошибка при загрузке задач: {e}")
    
    def _on_double_click(self, event):
        """Обработчик двойного клика - открытие диалога редактирования"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, "values")
            if values:
                task_id = values[0]
                # Открываем диалог редактирования задачи
                self._edit_task(task_id)
    
    def _on_single_click(self, event):
        """Обработчик одинарного клика на статус"""
        # Определяем колонку и элемент
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            
            if column == "#1" and item:  # Колонка статуса
                values = self.tree.item(item, "values")
                if values:
                    task_id = values[0]
                    current_status = values[1]
                    # Меняем статус
                    self._toggle_status(item, task_id, current_status)
    
    def _toggle_status(self, item, task_id, current_status):
        """Переключает статус задачи"""
        # Переключаем между двумя статусами
        next_status = "Выполнена" if current_status == "Активная" else "Активная"
        
        try:
            # Обновляем в базе данных
            is_completed = (next_status == "Выполнена")
            self.tasks_mgr.update_status(task_id, is_completed)
            
            # Обновляем в таблице
            values = list(self.tree.item(item, "values"))
            values[1] = next_status
            self.tree.item(item, values=values, tags=(next_status,))
            
        except Exception as e:
            print(f"Ошибка при обновлении статуса: {e}")
    
    def _add_task(self):
        """Добавляет новую задачу для клиента"""
        self._create_task_for_client(self.client_id)
    
    def _create_task_for_client(self, client_id):
        """Создает задачу для клиента"""
        try:
            task_window = tk.Toplevel(self.parent)
            task_window.title("➕ Новая задача")
            task_window.geometry("600x550")
            task_window.configure(bg='white')
            task_window.resizable(False, False)
            
            # Делаем окно модальным и поверх родительского
            task_window.transient(self.parent.winfo_toplevel())
            task_window.grab_set()
            task_window.focus_set()

            # Основная информация
            main_frame = tk.Frame(task_window, bg='white')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Название
            tk.Label(main_frame, text="📋 Основная информация", font=("Arial", 12, "bold"), bg='white', fg='#333').pack(anchor='w', pady=(0, 10))
            
            tk.Label(main_frame, text="Название задачи *", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
            title_entry = tk.Entry(main_frame, font=("Arial", 11), width=50, relief="solid", borderwidth=1)
            title_entry.pack(fill=tk.X, pady=(5, 15))

            # Описание
            tk.Label(main_frame, text="Описание", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
            desc_text = tk.Text(main_frame, font=("Arial", 11), height=4, width=50, relief="solid", borderwidth=1)
            desc_text.pack(fill=tk.X, pady=(5, 15))

            # Клиент
            tk.Label(main_frame, text="Клиент", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
            client_frame = tk.Frame(main_frame, bg='white')
            client_frame.pack(fill=tk.X, pady=(5, 15))
            
            # Получаем информацию о клиенте
            client_info = self.clients_mgr.get_by_id(client_id)
            client_name = client_info.get('company', 'Без названия') if client_info else 'Неизвестный клиент'
            
            client_var = tk.StringVar(value=client_name)
            client_entry = tk.Entry(client_frame, textvariable=client_var, font=("Arial", 11), relief="solid", borderwidth=1)
            client_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            client_entry.config(state='readonly')  # Делаем поле только для чтения

            # Дополнительные параметры
            tk.Label(main_frame, text="⚙ Дополнительные параметры", font=("Arial", 12, "bold"), bg='white', fg='#333').pack(anchor='w', pady=(0, 10))
            
            # Приоритет
            tk.Label(main_frame, text="Приоритет", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
            priority_var = tk.StringVar(value="Средний")
            priority_combo = ttk.Combobox(main_frame, textvariable=priority_var,
                                        values=["Низкий", "Средний", "Высокий"],
                                        state="readonly", width=20)
            priority_combo.pack(fill=tk.X, pady=(5, 15))

            # Срок выполнения
            tk.Label(main_frame, text="Срок выполнения", font=("Arial", 10, "bold"), bg='white', fg='#333').pack(anchor='w')
            date_frame = tk.Frame(main_frame, bg='white')
            date_frame.pack(fill=tk.X, pady=(5, 15))
            
            due_date_var = tk.StringVar(value=datetime.now().strftime("%d.%m.%Y"))
            due_date_entry = tk.Entry(date_frame, textvariable=due_date_var, font=("Arial", 11), relief="solid", borderwidth=1)
            due_date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            def show_calendar():
                """Показать календарь для выбора даты"""
                cal_dialog = CalendarDialog(task_window, "Выберите срок выполнения")
                selected_date = cal_dialog.show()
                if selected_date:
                    due_date_var.set(selected_date.strftime("%d.%m.%Y"))
            
            tk.Button(
                date_frame,
                text="📅",
                command=show_calendar,
                bg="#41a5be",
                fg="white",
                font=("Arial", 10),
                relief="flat",
                cursor="hand2"
            ).pack(side=tk.RIGHT, padx=(5, 0))

            # Кнопки
            buttons_frame = tk.Frame(main_frame, bg='white')
            buttons_frame.pack(fill=tk.X, pady=(20, 0))

            def save_task():
                title = title_entry.get().strip()
                if not title:
                    from tkinter import messagebox
                    messagebox.showerror("Ошибка", "Укажите название задачи")
                    return

                description = desc_text.get('1.0', tk.END).strip()
                priority = priority_var.get()
                due_date = due_date_var.get().strip()
                
                # Создаем задачу через менеджер
                self.tasks_mgr.add(
                    title=title,
                    description=description,
                    client_id=client_id,
                    priority=priority,
                    due_date=due_date
                )
                
                task_window.destroy()
                
                # Обновляем таблицу
                self._load_tasks()
                
                # Также обновляем вкладку задач в карточке клиента
                self._refresh_tasks_tab()

            tk.Button(buttons_frame, text="Сохранить", command=save_task, 
                     bg="#28a745", fg="white", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=(0, 10))
            tk.Button(buttons_frame, text="Отмена", command=task_window.destroy,
                     bg="#6c757d", fg="white", font=("Arial", 11, "bold")).pack(side=tk.LEFT)

            title_entry.focus_set()

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось создать задачу: {e}")
    
    def _edit_task(self, task_id):
        """Диалог редактирования задачи"""
        try:
            task = self.tasks_mgr.get_by_id(task_id)
            if not task:
                from tkinter import messagebox
                messagebox.showerror("Ошибка", f"Задача с ID {task_id} не найдена")
                return

            dialog = tk.Toplevel(self.parent)
            dialog.title(f"✏️ Редактирование: {task.title}")
            dialog.geometry("500x450")  # Увеличили высоту с 400 до 450
            dialog.configure(bg='white')
            dialog.resizable(False, False)
            
            # Делаем окно модальным и поверх родительского
            dialog.transient(self.parent.winfo_toplevel())
            dialog.grab_set()
            dialog.focus_set()

            # Основная информация
            main_frame = tk.Frame(dialog, bg='white')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Название
            tk.Label(main_frame, text="Название задачи:", font=("Arial", 11, "bold"), bg='white').pack(anchor='w')
            title_entry = tk.Entry(main_frame, font=("Arial", 11), width=50)
            title_entry.pack(fill=tk.X, pady=(5, 15))
            title_entry.insert(0, task.title)

            # Описание
            tk.Label(main_frame, text="Описание:", font=("Arial", 11, "bold"), bg='white').pack(anchor='w')
            desc_text = tk.Text(main_frame, font=("Arial", 11), height=6, width=50)
            desc_text.pack(fill=tk.X, pady=(5, 15))
            if task.description:
                desc_text.insert('1.0', task.description)

            # Статус и приоритет
            params_frame = tk.Frame(main_frame, bg='white')
            params_frame.pack(fill=tk.X, pady=(0, 15))

            # Статус
            status_frame = tk.Frame(params_frame, bg='white')
            status_frame.pack(side=tk.LEFT, padx=(0, 20))
            tk.Label(status_frame, text="Статус:", font=("Arial", 11, "bold"), bg='white').pack(anchor='w')
            
            status_var = tk.StringVar(value=task.status if task.status in ["Активная", "Выполнена"] else "Активная")
            status_combo = ttk.Combobox(status_frame, textvariable=status_var, 
                                      values=["Активная", "Выполнена"],
                                      state="readonly", width=15)
            status_combo.pack(pady=(5, 0))

            # Приоритет
            priority_frame = tk.Frame(params_frame, bg='white')
            priority_frame.pack(side=tk.LEFT)
            tk.Label(priority_frame, text="Приоритет:", font=("Arial", 11, "bold"), bg='white').pack(anchor='w')
            
            priority_var = tk.StringVar(value=task.priority or "Средний")
            priority_combo = ttk.Combobox(priority_frame, textvariable=priority_var,
                                        values=["Низкий", "Средний", "Высокий"],
                                        state="readonly", width=15)
            priority_combo.pack(pady=(5, 0))

            # Срок выполнения
            due_frame = tk.Frame(main_frame, bg='white')
            due_frame.pack(fill=tk.X, pady=(0, 15))
            
            tk.Label(due_frame, text="Срок выполнения:", font=("Arial", 11, "bold"), bg='white').pack(anchor='w')
            date_input_frame = tk.Frame(due_frame, bg='white')
            date_input_frame.pack(fill=tk.X, pady=(5, 0))
            
            # Получаем текущий срок задачи
            current_due_date = getattr(task, 'due_date', None)
            if current_due_date:
                if isinstance(current_due_date, str):
                    due_date_str = current_due_date
                else:
                    due_date_str = current_due_date.strftime("%d.%m.%Y") if current_due_date else ""
            else:
                due_date_str = datetime.now().strftime("%d.%m.%Y")
            
            due_date_var = tk.StringVar(value=due_date_str)
            due_date_entry = tk.Entry(date_input_frame, textvariable=due_date_var, font=("Arial", 11))
            due_date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            def show_edit_calendar():
                """Показать календарь для выбора даты"""
                cal_dialog = CalendarDialog(dialog, "Выберите срок выполнения")
                selected_date = cal_dialog.show()
                if selected_date:
                    due_date_var.set(selected_date.strftime("%d.%m.%Y"))
            
            tk.Button(
                date_input_frame,
                text="📅",
                command=show_edit_calendar,
                bg="#41a5be",
                fg="white",
                font=("Arial", 10),
                relief="flat",
                cursor="hand2"
            ).pack(side=tk.RIGHT, padx=(5, 0))

            # Кнопки
            buttons_frame = tk.Frame(main_frame, bg='white')
            buttons_frame.pack(fill=tk.X, pady=(20, 0))

            def save_task():
                title = title_entry.get().strip()
                if not title:
                    from tkinter import messagebox
                    messagebox.showerror("Ошибка", "Укажите название задачи")
                    return

                description = desc_text.get('1.0', tk.END).strip()
                status = status_var.get()
                priority = priority_var.get()
                due_date = due_date_var.get().strip()

                # Обновляем задачу
                # Превращаем статус в булево значение для базы данных
                is_completed = status == 'Выполнена'
                
                self.tasks_mgr.update_task(
                    task_id=task_id,
                    title=title,
                    description=description,
                    status=is_completed,
                    priority=priority,
                    due_date=due_date,
                    client_id=getattr(task, 'client_id', '')
                )

                dialog.destroy()
                
                # Обновляем таблицу задач
                self._load_tasks()
                
                # Также обновляем вкладку задач в карточке клиента
                parent_window = self.parent.winfo_toplevel()

                def find_clients_view(widget):
                    if hasattr(widget, '_refresh_tasks_tab'):
                        return widget
                    for child in widget.winfo_children():
                        result = find_clients_view(child)
                        if result:
                            return result
                    return None

                clients_view = find_clients_view(parent_window)
                if clients_view:
                    clients_view._refresh_tasks_tab(parent_window)

            tk.Button(buttons_frame, text="Сохранить", command=save_task,
                     bg="#28a745", fg="white", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=(0, 10))
            tk.Button(buttons_frame, text="Отмена", command=dialog.destroy,
                     bg="#6c757d", fg="white", font=("Arial", 11, "bold")).pack(side=tk.LEFT)

            title_entry.focus_set()

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось открыть задачу: {e}")

    def _open_task_card(self, task_id):
        """Открывает карточку задачи"""
        # Находим родительское окно и вызываем метод ClientsView
        parent_window = self.parent.winfo_toplevel()
        # Ищем экземпляр ClientsView в родительских виджетах
        def find_clients_view(widget):
            if hasattr(widget, '_open_task_card'):
                return widget
            for child in widget.winfo_children():
                result = find_clients_view(child)
                if result:
                    return result
            return None
        
        clients_view = find_clients_view(parent_window)
        if clients_view:
            clients_view._open_task_card(task_id, parent_window)
    
    def refresh(self):
        """Обновляет данные в таблице"""
        self._load_tasks()


class ClientContactsTable:
    """Таблица контактов для конкретного клиента"""
    
    def __init__(self, parent, client_id, contact_persons_mgr, contact_emails_mgr, clients_view):
        self.parent = parent
        self.client_id = client_id
        self.contact_persons_mgr = contact_persons_mgr
        self.contact_emails_mgr = contact_emails_mgr
        self.clients_view = clients_view  # Ссылка на ClientsView для вызова методов
        self.tree = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Создает интерфейс таблицы"""
        # Заголовок
        header_frame = tk.Frame(self.parent, bg='#f8f9fa')
        header_frame.pack(fill=tk.X, padx=15, pady=(20, 10))
        
        tk.Label(
            header_frame,
            text="Контактные лица",
            font=("Arial", 16, "bold"),
            bg='#f8f9fa',
            fg='#333'
        ).pack(side=tk.LEFT)
        
        # Контейнер для элементов справа
        right_container = tk.Frame(header_frame, bg='#f8f9fa')
        right_container.pack(side=tk.RIGHT)
        
        # Сортировка
        tk.Label(
            right_container,
            text="Сортировка:",
            font=("Arial", 10),
            bg='#f8f9fa',
            fg='#666'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.sort_var = tk.StringVar(value="По ФИО (А-Я)")
        sort_options = [
            "По ФИО (А-Я)",
            "По ФИО (Я-А)", 
            "По должности (А-Я)",
            "По должности (Я-А)"
        ]
        
        sort_combo = ttk.Combobox(
            right_container,
            textvariable=self.sort_var,
            values=sort_options,
            state="readonly",
            width=20,
            font=("Arial", 9)
        )
        sort_combo.pack(side=tk.LEFT, padx=(0, 10))
        sort_combo.bind("<<ComboboxSelected>>", self._on_sort_change)
        
        # Кнопка добавления контакта
        add_btn = tk.Button(
            right_container,
            text="+ Добавить контакт",
            command=self._add_contact,
            bg="#28a745",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2"
        )
        add_btn.pack(side=tk.LEFT, padx=10)
        
        # Создаем таблицу
        self._create_table()
        
        # Загружаем данные
        self._load_contacts()
    
    def _create_table(self):
        """Создает Treeview таблицу"""
        # Фрейм для таблицы с прокруткой
        table_frame = tk.Frame(self.parent)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 20))
        
        # Создаем Treeview
        self.tree = ttk.Treeview(
            table_frame,
            columns=("ID", "ФИО", "Должность", "Телефон", "Email"),
            show="headings",
            selectmode="browse"
        )
        
        # Настройка колонок
        self.tree.heading("ID", text="ID")
        self.tree.heading("ФИО", text="ФИО")
        self.tree.heading("Должность", text="Должность")
        self.tree.heading("Телефон", text="Телефон")
        self.tree.heading("Email", text="Email")
        
        # Ширина колонок
        self.tree.column("ID", width=50, minwidth=50)
        self.tree.column("ФИО", width=200, minwidth=150)
        self.tree.column("Должность", width=150, minwidth=120)
        self.tree.column("Телефон", width=120, minwidth=100)
        self.tree.column("Email", width=200, minwidth=150)
        
        # Прокрутка
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Обработчики
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-1>', self._on_single_click)
        
        # Стиль для основного контакта
        self._setup_tag_styles()
    
    def _setup_tag_styles(self):
        """Настраивает стили для разных типов контактов"""
        style = ttk.Style()
        
        # Исправление для tag_configure в Windows
        def fixed_map(option):
            return [elm for elm in style.map('Treeview', query_opt=option) 
                   if elm[:2] != ('!disabled', '!selected')]
        
        style.map('Treeview', foreground=fixed_map('foreground'), 
                  background=fixed_map('background'))
        
        # Выделяем основной контакт зеленым цветом как в таблице клиентов
        self.tree.tag_configure("primary", background="#d4edda")
    
    def _apply_sorting(self, contacts, sort_option):
        """Применяет сортировку к контактам"""
        try:
            if sort_option == "По ФИО (А-Я)":
                contacts = sorted(contacts, key=lambda c: self._get_full_name(c).lower())
            elif sort_option == "По ФИО (Я-А)":
                contacts = sorted(contacts, key=lambda c: self._get_full_name(c).lower(), reverse=True)
            elif sort_option == "По должности (А-Я)":
                contacts = sorted(contacts, key=lambda c: self._get_position(c).lower())
            elif sort_option == "По должности (Я-А)":
                contacts = sorted(contacts, key=lambda c: self._get_position(c).lower(), reverse=True)
            return contacts
        except:
            return contacts
    
    def _get_full_name(self, contact):
        """Получает ФИО контакта"""
        return contact['full_name']
    
    def _get_position(self, contact):
        """Получает должность контакта"""
        return contact['position']
    
    def _on_sort_change(self, event=None):
        """Обработчик изменения сортировки"""
        self._load_contacts()
    
    def _load_contacts(self):
        """Загружает контакты клиента в таблицу"""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.contact_persons_mgr:
            return
        
        try:
            # Получаем контакты клиента
            contacts = self.contact_persons_mgr.get_by_client(self.client_id)
            
            # Применяем сортировку
            sort_option = self.sort_var.get()
            contacts = self._apply_sorting(contacts, sort_option)
            
            for contact in contacts:
                contact_id = contact['id']
                full_name = contact['full_name']
                position = contact['position']
                phone = contact['phone']
                
                # Получаем email для контакта
                email = ""
                if self.contact_emails_mgr:
                    try:
                        emails = self.contact_emails_mgr.get_by_contact(contact_id)
                        if emails:
                            email = emails[0]['email']
                    except Exception as e:
                        print(f"Ошибка загрузки email для контакта {contact_id}: {e}")
                
                # Добавляем в таблицу
                is_primary = contact['is_primary'] if isinstance(contact['is_primary'], bool) else bool(contact['is_primary'])
                tags = ('primary',) if is_primary else ()
                
                self.tree.insert(
                    "", 
                    "end",
                    values=(contact_id, full_name, position, phone, email),
                    tags=tags
                )
        
        except Exception as e:
            print(f"Ошибка при загрузке контактов: {e}")
    
    def _on_double_click(self, event):
        """Обработчик двойного клика - открытие диалога редактирования"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, "values")
            if values:
                contact_id = values[0]
                # Открываем диалог редактирования контакта
                self._edit_contact(contact_id)
    
    def _on_single_click(self, event):
        """Обработчик одинарного клика - ничего не делает"""
        pass
    
    def _add_contact(self):
        """Добавляет новый контакт для клиента"""
        self.clients_view._add_contact_to_client(self.client_id, self.parent)
    
    def _edit_contact(self, contact_id):
        """Открывает диалог редактирования контакта"""
        # Находим родительское окно карточки клиента
        parent_window = self.parent.winfo_toplevel()
        
        # Создаем диалог редактирования контакта
        self.clients_view._edit_contact(contact_id, parent_window)
        
        # Обновляем таблицу контактов после редактирования
        self.refresh()
        
        # Также обновляем вкладку контактов в карточке клиента
        self.clients_view._refresh_contacts_tab()
    
    def refresh(self):
        """Обновляет данные в таблице"""
        self._load_contacts()


class ClientsView(TableViewTemplate):
    """Раздел клиентов с поиском, сортировкой и пагинацией"""

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

    def __init__(self, parent_frame, clients_mgr, contact_persons_mgr, contact_emails_mgr, interactions_mgr, tasks_mgr=None):
        super().__init__(parent_frame, clients_mgr)
        self.clients_mgr = clients_mgr
        self.contact_persons_mgr = contact_persons_mgr
        self.contact_emails_mgr = contact_emails_mgr
        self.interactions_mgr = interactions_mgr
        self.tasks_mgr = tasks_mgr
        
        # Переменные для отслеживания открытых окон
        self.add_client_dialog = None
        self.edit_client_dialogs = {}  # client_id -> dialog
        self.client_card_dialogs = {}  # client_id -> dialog
        self.task_card_dialogs = {}  # task_id -> dialog
        self.add_contact_dialogs = {}  # client_id -> dialog

    def _on_tree_enter(self, event):
        pass

    def _on_tree_leave(self, event):
        pass

    def _on_tree_motion(self, event):
        pass

    def _add_mouse_wheel_support(self, canvas):
        """Добавить поддержку прокрутки колесиком мыши для canvas"""
        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mouse_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    def _create_table(self):
        """Создаёт Treeview таблицу с дополнительной обработкой клика на задачи"""
        # Вызываем родительский метод
        super()._create_table()
        
        # Добавляем обработку одинарного клика на колонку "Задачи"
        self.tree.bind('<Button-1>', self._on_single_click)

    def _on_single_click(self, event):
        """Обрабатывает одинарный клик по таблице"""
        # Определяем колонку и строку
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        if not item or not column:
            return
            
        # Проверяем что кликнули на колонку "Задачи" (седьмая колонка)
        if column == "#7":  # #7 это седьмая колонка (ID, Компания, Контактное лицо, Должность, Телефон, Адрес, Задачи)
            # Получаем ID клиента из первой колонки
            values = self.tree.item(item, 'values')
            if not values:
                return
                
            try:
                client_id = int(values[0])
                self._create_task_for_client(client_id)
            except (ValueError, IndexError):
                pass

    def _get_data(self, page, search, sort_by, sort_order):
        """Загрузка данных с пагинацией и поиском"""
        try:
            # Получаем данные с поиском или без
            if search:
                clients = self.clients_mgr.search(search.lower())
            else:
                clients = self.clients_mgr.get_all()
            
            # Применяем сортировку
            if sort_by:
                clients = self._apply_sort(clients, sort_by, sort_order)
            
            # Эмуляция пагинации
            total = len(clients)
            start_idx = (page - 1) * self.PAGE_SIZE
            end_idx = start_idx + self.PAGE_SIZE
            paginated_clients = clients[start_idx:end_idx]
            
            return paginated_clients, total
            
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            return [], 0

    def _apply_sort(self, clients, sort_by, sort_order):
        """Применяет сортировку к списку клиентов"""
        reverse = sort_order == "DESC"
        
        if sort_by == "company":
            clients.sort(key=lambda x: x.get('company', '').lower(), reverse=reverse)
        elif sort_by == "primary_contact":
            clients.sort(key=lambda x: x.get('primary_contact', '').lower(), reverse=reverse)
        elif sort_by == "created_at":
            clients.sort(key=lambda x: x.get('created_at', ''), reverse=reverse)
            
        return clients

    def _item_to_row_values(self, item):
        """Преобразует клиента в строку таблицы"""
        if not isinstance(item, dict):
            return ("", "", "", "", "", "", "", "")
        
        values = (
            item.get('id', ''),
            item.get('company', '—'),
            item.get('primary_contact', '—'),
            item.get('primary_position', '—'),
            item.get('primary_phone', '—'),
            item.get('address', '—'),
            "➕ Задача"  # Кнопка для создания задачи
        )
        
        return values

    def _open_create_dialog(self):
        """Диалог создания нового клиента"""
        self._show_add_client_dialog()

    def _on_row_double_click(self, client_id):
        """Обработка двойного клика по строке - открытие карточки клиента"""
        self._open_client_card_by_id(client_id)

    def _show_add_client_dialog(self):
        """Диалог добавления клиента с расширенным функционалом"""
        # Проверяем, не открыто ли уже окно добавления клиента
        if self.add_client_dialog and tk.Toplevel.winfo_exists(self.add_client_dialog):
            self.add_client_dialog.lift()
            self.add_client_dialog.focus_force()
            return
        
        # Создаём диалоговое окно
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Добавить клиента")
        dialog.geometry("750x750")
        dialog.configure(bg='white')
        dialog.resizable(False, False)
        
        # Сохраняем ссылку на окно
        self.add_client_dialog = dialog
        
        # Очищаем ссылку при закрытии
        def on_dialog_close():
            self.add_client_dialog = None
            dialog.destroy()
        
        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)

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

            # Кнопка удаления контакта (добавляется после создания contact_widget)
            def remove_contact(widget=contact_widget):
                """Удаляет контактное лицо из формы"""
                contact_box.destroy()
                if widget in contact_widgets:
                    contact_widgets.remove(widget)

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

        # --- СОХРАНЕНИЕ ---
        def save_client():
            """Сохраняет нового клиента с расширенной валидацией"""
            from datetime import date

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
                    email = w['email'].get().strip()
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
                msg = f"Клиент '{company}' успешно добавлен!\n\n" \
                      f"ID: {client_id}\n" \
                      f"Контактов добавлено: {len(saved_contacts)}\n" \
                      f"Основной контакт: {primary_contact_name or 'не указан'}"

                # Используем messagebox для более крупного окна
                messagebox.showinfo("✅ Успех", msg)

                dialog.destroy()

                # Обновление интерфейса
                self._refresh_data()

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

    def _open_client_card(self, client):
        """Открыть карточку клиента"""
        # Проверяем, не открыта ли уже карточка этого клиента
        client_id = client['id']
        if client_id in self.client_card_dialogs:
            existing_dialog = self.client_card_dialogs[client_id]
            if existing_dialog and tk.Toplevel.winfo_exists(existing_dialog):
                existing_dialog.lift()
                existing_dialog.focus_force()
                return
        
        # Создаём новое окно
        card_window = tk.Toplevel(self.parent_frame)
        card_window.title(f"Карточка клиента: {client['company']}")
        card_window.geometry("900x700")
        card_window.configure(bg='white')
        
        # Сохраняем ссылку на окно
        self.client_card_dialogs[client_id] = card_window
        
        # Очищаем ссылку при закрытии
        def on_dialog_close():
            if client_id in self.client_card_dialogs:
                del self.client_card_dialogs[client_id]
            card_window.destroy()
        
        card_window.protocol("WM_DELETE_WINDOW", on_dialog_close)

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
        self._create_tasks_tab(tab_tasks, client['id'], card_window)

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
        """Вкладка 'Контактные лица' (табличное представление)"""
        # Добавляем метку для идентификации вкладки
        parent._is_contacts_tab = True
        parent._client_id = client_id
        
        # Создаем таблицу контактов клиента
        self.contacts_table = ClientContactsTable(parent, client_id, self.contact_persons_mgr, self.contact_emails_mgr, self)
        
        # Сохраняем ссылку на таблицу для обновления
        parent._contacts_table = self.contacts_table

    def _refresh_contacts_tab(self):
        """Обновить вкладку контактов"""
        try:
            # Ищем открытую карточку клиента
            for widget in self.parent_frame.winfo_children():
                if hasattr(widget, '_is_client_card') and widget._is_client_card:
                    # Ищем notebook в карточке клиента
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Notebook):
                            # Ищем вкладку контактов
                            for tab_idx in range(child.index("end")):
                                tab = child.winfo_children()[tab_idx]
                                if hasattr(tab, '_is_contacts_tab') and tab._is_contacts_tab:
                                    # Обновляем таблицу контактов
                                    contacts_table = getattr(tab, '_contacts_table', None)
                                    if contacts_table:
                                        contacts_table.refresh()
                                    return
                            break
                    break
        except Exception as e:
            print(f"Ошибка обновления вкладки контактов: {e}")

    def _create_tasks_tab(self, parent, client_id, card_window):
        """Вкладка 'Задачи'"""
        # Добавляем метку для идентификации вкладки
        parent._is_tasks_tab = True
        parent._client_id = client_id
        parent._card_window = card_window  # Сохраняем ссылку на окно
        
        # Создаем таблицу задач клиента
        self.tasks_table = ClientTasksTable(parent, client_id, self.tasks_mgr, self.clients_mgr)
        
        # Сохраняем ссылку на таблицу для обновления
        parent._tasks_table = self.tasks_table

    def _refresh_tasks_table(self, parent_window):
        """Обновить таблицу задач в карточке клиента"""
        try:
            # Ищем notebook в карточке клиента
            notebook = None
            for widget in parent_window.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    notebook = widget
                    break
            
            if notebook:
                # Ищем вкладку "✅ Задачи"
                for i in range(notebook.index("end")):
                    tab_info = notebook.tab(i)
                    tab_text = tab_info.get("text", "")
                    if "Задачи" in tab_text:
                        # Получаем виджет вкладки правильно
                        tab_frames = notebook.winfo_children()
                        if i < len(tab_frames):
                            tab_frame = tab_frames[i]
                            # Обновляем таблицу
                            tasks_table = getattr(tab_frame, '_tasks_table', None)
                            if tasks_table:
                                tasks_table.refresh()
                            return
        except Exception as e:
            print(f"Ошибка при обновлении таблицы задач: {e}")

    def _open_task_card(self, task_id, parent_window):
        """Открыть карточку задачи с возможностью отметить как выполненную"""
        print(f"_open_task_card вызван с task_id={task_id}, parent_window={parent_window}, тип={type(parent_window)}")
        
        # Проверяем, не открыта ли уже карточка этой задачи
        if task_id in self.task_card_dialogs:
            existing_dialog = self.task_card_dialogs[task_id]
            if existing_dialog and tk.Toplevel.winfo_exists(existing_dialog):
                existing_dialog.lift()
                existing_dialog.focus_force()
                return
        
        try:
            if not self.tasks_mgr:
                from tkinter import messagebox
                messagebox.showerror("Ошибка", "Менеджер задач не инициализирован")
                return

            # Получаем данные задачи
            task_data = self.tasks_mgr.get_by_id(task_id)
            if not task_data:
                from tkinter import messagebox
                messagebox.showerror("Ошибка", f"Задача с ID {task_id} не найдена")
                return

            # Преобразуем данные задачи в словарь для удобной работы
            if hasattr(task_data, '__dict__'):
                # Если это объект с атрибутами
                task_dict = {
                    'id': getattr(task_data, 'id', task_id),
                    'title': getattr(task_data, 'title', 'Без названия'),
                    'status': getattr(task_data, 'status', 'Новая'),
                    'priority': getattr(task_data, 'priority', 'Не указан'),
                    'due_date': getattr(task_data, 'due_date', 'Не указан'),
                    'created_at': getattr(task_data, 'created_at', 'Не указано'),
                    'description': getattr(task_data, 'description', 'Нет описания')
                }
            elif isinstance(task_data, dict):
                # Если это уже словарь
                task_dict = task_data
            else:
                # Пробуем преобразовать в словарь
                try:
                    task_dict = dict(task_data)
                except:
                    task_dict = {
                        'id': task_id,
                        'title': str(task_data) if task_data else 'Без названия',
                        'status': 'Новая',
                        'priority': 'Не указан',
                        'due_date': 'Не указан',
                        'created_at': 'Не указано',
                        'description': 'Нет описания'
                    }

            # Создаем окно карточки задачи
            task_window = tk.Toplevel(self.parent_frame)
            task_window.title(f"Задача: {task_dict['title']}")
            task_window.geometry("600x500")
            task_window.configure(bg='white')
            task_window.resizable(False, False)
            
            # Сохраняем ссылку на окно
            self.task_card_dialogs[task_id] = task_window
            
            # Очищаем ссылку при закрытии
            def on_dialog_close():
                if task_id in self.task_card_dialogs:
                    del self.task_card_dialogs[task_id]
                task_window.destroy()
            
            task_window.protocol("WM_DELETE_WINDOW", on_dialog_close)

            # Заголовок
            header = tk.Frame(task_window, bg='#333333', height=60)
            header.pack(fill=tk.X)
            header.pack_propagate(False)

            tk.Label(
                header,
                text=f"📌 {task_dict['title']}",
                font=("Arial", 18, "bold"),
                fg="white",
                bg='#333333'
            ).pack(side=tk.LEFT, padx=20, pady=15)

            tk.Label(
                header,
                text=f"ID: {task_id}",
                font=("Arial", 12),
                fg="#41a5be",
                bg='#333333'
            ).pack(side=tk.RIGHT, padx=20, pady=15)

            # Основная информация
            info_frame = tk.Frame(task_window, bg='white')
            info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Статус
            current_status = task_dict['status']
            tk.Label(
                info_frame,
                text="Статус:",
                font=("Arial", 12, "bold"),
                bg='white'
            ).grid(row=0, column=0, sticky='w', pady=5)

            status_frame = tk.Frame(info_frame, bg='white')
            status_frame.grid(row=0, column=1, sticky='w', pady=5)

            status_var = tk.StringVar(value=current_status)
            status_options = ["Активная", "Выполнена"]
            
            for option in status_options:
                tk.Radiobutton(
                    status_frame,
                    text=option,
                    variable=status_var,
                    value=option,
                    font=("Arial", 10),
                    bg='white'
                ).pack(side=tk.LEFT, padx=5)

            # Приоритет
            priority = task_dict['priority']
            self._add_info_row(info_frame, "Приоритет:", priority, 1)

            # Срок выполнения
            due_date = task_dict['due_date']
            self._add_info_row(info_frame, "Срок выполнения:", due_date, 2)

            # Дата создания
            created_at = task_dict['created_at']
            self._add_info_row(info_frame, "Дата создания:", created_at, 3)

            # Описание
            tk.Label(
                info_frame,
                text="Описание:",
                font=("Arial", 12, "bold"),
                bg='white'
            ).grid(row=4, column=0, sticky='nw', pady=5)

            desc_text = tk.Text(
                info_frame,
                width=40,
                height=8,
                font=("Arial", 10),
                wrap=tk.WORD
            )
            desc_text.grid(row=4, column=1, sticky='w', pady=5)
            desc_text.insert('1.0', task_dict['description'])
            # Оставляем поле редактируемым

            # Кнопки внизу
            buttons_container = tk.Frame(task_window, bg='#f0f0f0', height=80)
            buttons_container.pack(fill=tk.X, side=tk.BOTTOM)
            buttons_container.pack_propagate(False)

            buttons_frame = tk.Frame(buttons_container, bg='#f0f0f0')
            buttons_frame.pack(pady=15)

            def save_task():
                """Сохранить изменения в задаче"""
                try:
                    print("Начинаем сохранение задачи...")
                    new_status = status_var.get()
                    new_description = desc_text.get('1.0', tk.END).strip()
                    print(f"Новый статус: {new_status}, новое описание: {new_description[:50]}...")
                    
                    # Обновляем статус
                    self.tasks_mgr.update_status(task_id, new_status)
                    print("Статус обновлен в базе данных")
                    
                    # Обновляем описание если оно изменилось
                    if new_description != task_dict['description']:
                        # Проверяем, есть ли метод обновления описания
                        if hasattr(self.tasks_mgr, 'update_description'):
                            self.tasks_mgr.update_description(task_id, new_description)
                        else:
                            # Получаем текущие данные задачи
                            current_task = self.tasks_mgr.get_by_id(task_id)
                            if current_task:
                                # Обновляем через общий метод с обязательными параметрами
                                self.tasks_mgr.update(
                                    task_id,
                                    title=getattr(current_task, 'title', ''),
                                    due_date=getattr(current_task, 'due_date', ''),
                                    client_id=getattr(current_task, 'client_id', ''),
                                    description=new_description
                                )
                        print("Описание обновлено")
                    
                    from tkinter import messagebox
                    messagebox.showinfo("Успех", f"Задача сохранена. Статус: {new_status}")
                    task_window.destroy()
                    
                    # Обновляем таблицу задач в карточке клиента
                    self._refresh_tasks_table(parent_window)
                    
                    # Поднимаем окно карточки клиента на передний план
                    parent_window.lift()
                    parent_window.focus_force()
                    
                except Exception as e:
                    from tkinter import messagebox
                    messagebox.showerror("Ошибка", f"Не удалось сохранить изменения: {e}")
                    print(f"Ошибка при сохранении: {e}")
                    import traceback
                    traceback.print_exc()

            def mark_completed():
                """Отметить задачу как выполненную"""
                status_var.set("Выполнена")
                save_task()

            tk.Button(
                buttons_frame,
                text="💾 Сохранить",
                command=save_task,
                bg="#41a5be",
                fg="white",
                font=("Arial", 12, "bold"),
                relief="flat",
                width=15,
                height=1,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=10)

            tk.Button(
                buttons_frame,
                text="✅ Выполнено",
                command=mark_completed,
                bg="#28a745",
                fg="white",
                font=("Arial", 12, "bold"),
                relief="flat",
                width=15,
                height=1,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=10)

            tk.Button(
                buttons_frame,
                text="Закрыть",
                command=task_window.destroy,
                bg="#6c757d",
                fg="white",
                font=("Arial", 12, "bold"),
                relief="flat",
                width=15,
                height=1,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=10)

        except Exception as e:
            print(f"Ошибка при открытии карточки задачи: {e}")
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Не удалось открыть карточку задачи: {e}")

    def _update_specific_task(self, parent_window, task_id, new_status):
        """Обновить только конкретную задачу в карточке клиента без пересоздания вкладки"""
        try:
            print(f"Ищем задачу {task_id} для обновления статуса на '{new_status}'")
            
            # Ищем notebook в карточке клиента
            notebook = None
            for widget in parent_window.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    notebook = widget
                    print("Найден notebook")
                    break
            
            if notebook:
                # Ищем вкладку "✅ Задачи"
                for i in range(notebook.index("end")):
                    tab_info = notebook.tab(i)
                    tab_text = tab_info.get("text", "")
                    print(f"Вкладка {i}: '{tab_text}'")
                    if "Задачи" in tab_text:
                        # Получаем виджет вкладки правильно
                        tab_frames = notebook.winfo_children()
                        if i < len(tab_frames):
                            tab_frame = tab_frames[i]
                            print(f"Получен фрейм вкладки: {tab_frame}")
                            
                            # Используем сохраненное card_window из вкладки
                            card_window = getattr(tab_frame, '_card_window', None)
                            if card_window:
                                print(f"Используем сохраненное card_window: {card_window}")
                                # Ищем и обновляем задачу
                                self._find_and_update_task(card_window, task_id, new_status)
                            else:
                                print("card_window не найден во вкладке!")
                            return
            print("Не удалось найти задачу для обновления")
        except Exception as e:
            print(f"Ошибка при обновлении конкретной задачи: {e}")
            import traceback
            traceback.print_exc()

    def _find_and_update_task(self, card_window, task_id, new_status):
        """Найти и обновить конкретную задачу в окне"""
        try:
            print(f"Поиск задачи {task_id} в окне {card_window}")
            
            # Ищем notebook в карточке клиента
            notebook = None
            for widget in card_window.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    notebook = widget
                    print("Найден notebook в card_window")
                    break
            
            if notebook:
                # Ищем вкладку "✅ Задачи"
                for i in range(notebook.index("end")):
                    tab_info = notebook.tab(i)
                    tab_text = tab_info.get("text", "")
                    if "Задачи" in tab_text:
                        # Получаем виджет вкладки правильно
                        tab_frames = notebook.winfo_children()
                        if i < len(tab_frames):
                            tab_frame = tab_frames[i]
                            
                            # Ищем canvas в вкладке задач
                            for widget in tab_frame.winfo_children():
                                if isinstance(widget, tk.Canvas):
                                    # Ищем фрейм задачи по ID
                                    for child in widget.winfo_children():
                                        if isinstance(child, tk.Frame) and hasattr(child, '_task_id'):
                                            if getattr(child, '_task_id') == task_id:
                                                print("Найден нужный фрейм задачи!")
                                                # Обновляем статус в виджете
                                                self._update_task_status_in_widget(child, new_status)
                                                print("Статус обновлен успешно!")
                                                return
                        return
            print("Задача не найдена для обновления")
        except Exception as e:
            print(f"Ошибка при поиске и обновлении задачи: {e}")

    def _update_task_status_in_widget(self, task_frame, new_status):
        """Обновить статус в конкретном виджете задачи"""
        try:
            print(f"Обновляем статус в виджете: {new_status}")
            # Ищем метку статуса в фрейме задачи
            for widget in task_frame.winfo_children():
                print(f"Проверяем виджет в фрейме: {widget}, тип: {type(widget)}")
                if isinstance(widget, tk.Frame):
                    print("Найден внутренний фрейм")
                    # Ищем в дочерних элементах
                    for child in widget.winfo_children():
                        print(f"Проверяем дочерний элемент: {child}, тип: {type(child)}, hasattr _is_status_label: {hasattr(child, '_is_status_label')}")
                        if isinstance(child, tk.Label) and hasattr(child, '_is_status_label'):
                            print("Найдена метка статуса!")
                            # Обновляем текст и цвет статуса
                            status_colors = {
                                'Новая': '#17a2b8',
                                'В работе': '#007bff', 
                                'Выполнена': '#28a745',
                                'Отложена': '#6c757d',
                                'Отменена': '#dc3545'
                            }
                            
                            old_text = child.cget("text")
                            old_bg = child.cget("bg")
                            print(f"Старый статус: '{old_text}', старый цвет: {old_bg}")
                            
                            child.config(
                                text=new_status,
                                bg=status_colors.get(new_status, '#6c757d')
                            )
                            
                            new_text = child.cget("text")
                            new_bg = child.cget("bg")
                            print(f"Новый статус: '{new_text}', новый цвет: {new_bg}")
                            return
            print("Метка статуса не найдена во фрейме")
        except Exception as e:
            print(f"Ошибка при обновлении статуса в виджете: {e}")
            import traceback
            traceback.print_exc()

    def _refresh_tasks_tab(self, parent_window=None):
        """Обновить вкладку задач в карточке клиента"""
        try:
            if parent_window is None:
                # Ищем открытую карточку клиента
                for widget in self.parent_frame.winfo_children():
                    if hasattr(widget, '_is_client_card') and widget._is_client_card:
                        parent_window = widget
                        break
            
            if parent_window is None:
                return
                
            # Ищем notebook в карточке клиента
            notebook = None
            for widget in parent_window.winfo_children():
                if isinstance(widget, ttk.Notebook):
                    notebook = widget
                    break
            
            if notebook:
                # Ищем вкладку "✅ Задачи"
                for i in range(notebook.index("end")):
                    tab_info = notebook.tab(i)
                    tab_text = tab_info.get("text", "")
                    if "Задачи" in tab_text:
                        # Получаем tab_id
                        tab_id = notebook.tab(i, "text")
                        # Получаем вкладку
                        tab_frame = notebook.nametowidget(tab_id)
                        # Получаем client_id из метки
                        client_id = getattr(tab_frame, '_client_id', None)
                        if client_id:
                            # Очищаем и пересоздаем вкладку задач
                            for tab_child in tab_frame.winfo_children():
                                tab_child.destroy()
                            self._create_tasks_tab(tab_frame, client_id)
                        return
        except Exception as e:
            print(f"Ошибка при обновлении вкладки задач: {e}")
            import traceback
            traceback.print_exc()

    def _add_contact_to_client(self, client_id, parent_window):
        """Добавить контактное лицо к клиенту в общей стилистике"""
        # Проверяем, не открыто ли уже окно добавления контакта для этого клиента
        if client_id in self.add_contact_dialogs:
            existing_dialog = self.add_contact_dialogs[client_id]
            if existing_dialog and tk.Toplevel.winfo_exists(existing_dialog):
                existing_dialog.lift()
                existing_dialog.focus_force()
                return
        
        from utils.helpers import show_message

        dialog = tk.Toplevel(parent_window)
        dialog.title("Добавить контактное лицо")
        dialog.geometry("500x450")
        dialog.configure(bg='white')
        dialog.resizable(False, False)
        
        # Сохраняем ссылку на окно
        self.add_contact_dialogs[client_id] = dialog
        
        # Очищаем ссылку при закрытии
        def on_dialog_close():
            if client_id in self.add_contact_dialogs:
                del self.add_contact_dialogs[client_id]
            dialog.destroy()
        
        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)

        # Заголовок
        header = tk.Frame(dialog, bg='#333333', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="👤 Добавить контактное лицо",
            font=("Arial", 18, "bold"),
            fg='white',
            bg='#333333'
        ).pack(pady=15)

        # Поля для ввода
        fields_frame = tk.Frame(dialog, bg='white')
        fields_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        tk.Label(fields_frame, text="ФИО *", font=("Arial", 10, "bold"), bg='white').pack(anchor='w')
        name_entry = tk.Entry(
            fields_frame, 
            font=("Arial", 11), 
            width=40,
            relief="solid",
            borderwidth=1
        )
        name_entry.pack(fill=tk.X, pady=(5, 15))

        tk.Label(fields_frame, text="Должность", font=("Arial", 10, "bold"), bg='white').pack(anchor='w')
        position_entry = tk.Entry(
            fields_frame, 
            font=("Arial", 11), 
            width=40,
            relief="solid",
            borderwidth=1
        )
        position_entry.pack(fill=tk.X, pady=(5, 15))

        tk.Label(fields_frame, text="Телефон", font=("Arial", 10, "bold"), bg='white').pack(anchor='w')
        phone_entry = tk.Entry(
            fields_frame, 
            font=("Arial", 11), 
            width=40,
            relief="solid",
            borderwidth=1
        )
        phone_entry.pack(fill=tk.X, pady=(5, 15))

        tk.Label(fields_frame, text="Email", font=("Arial", 10, "bold"), bg='white').pack(anchor='w')
        email_entry = tk.Entry(
            fields_frame, 
            font=("Arial", 11), 
            width=40,
            relief="solid",
            borderwidth=1
        )
        email_entry.pack(fill=tk.X, pady=(5, 15))

        # Кнопки внизу
        buttons_container = tk.Frame(dialog, bg='#f0f0f0', height=80)
        buttons_container.pack(fill=tk.X, side=tk.BOTTOM)
        buttons_container.pack_propagate(False)

        buttons_frame = tk.Frame(buttons_container, bg='#f0f0f0')
        buttons_frame.pack(pady=15)

        def save_contact():
            name = name_entry.get().strip()
            if not name:
                from tkinter import messagebox
                messagebox.showerror("Ошибка", "Введите ФИО контактного лица")
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

                from tkinter import messagebox
                messagebox.showinfo("Успех", "Контактное лицо добавлено")
                dialog.destroy()
                
                # Обновляем вкладку контактов
                self._refresh_contacts_tab()

            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Ошибка", f"Не удалось добавить контакт: {e}")

        tk.Button(
            buttons_frame,
            text="💾 Сохранить",
            command=save_contact,
            bg="#41a5be",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            width=15,
            height=1,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="✖ Отмена",
            command=dialog.destroy,
            bg="#6c757d",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            width=15,
            height=1,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

        name_entry.focus_set()

    def _edit_client_OLD(self, client, parent_window):
        """Редактировать клиента с объединенными email в контактах - СТАРЫЙ МЕТОД"""

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
        
        # Отладочная информация
        print(f"Загрузка контактов для клиента {client['id']}:")
        print(f"client_data: {client_data}")
        print(f"contacts_db: {contacts_db}")
        print(f"Тип contacts_db: {type(contacts_db)}")
        if contacts_db:
            print(f"Количество контактов: {len(contacts_db)}")
            for i, contact in enumerate(contacts_db):
                print(f"Контакт {i}: {contact}, тип: {type(contact)}")

        # Создаем контейнер для контента между заголовком и кнопками
        content_container = tk.Frame(edit_dialog, bg='white')
        content_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas для прокрутки внутри контейнера
        canvas = tk.Canvas(content_container, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(content_container, orient="vertical", command=canvas.yview)
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

        # Добавляем поддержку прокрутки колесиком мыши
        self._add_mouse_wheel_support(canvas)

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
        print("Раздел контактов создан")

        # Переменные для хранения виджетов
        contact_widgets = []
        primary_contact_var = tk.IntVar()
        print("Переменные для контактов инициализированы")

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
            print(f"create_contact_widget вызван с contact_data: {contact_data}")
            
            # Проверяем лимит
            active_widgets = [w for w in contact_widgets if not w.get('deleted', False)]
            if len(active_widgets) >= 4:
                from utils.helpers import show_message
                show_message(edit_dialog, "Лимит", "Максимум 4 контактных лица", "warning")
                return None

            idx = len(active_widgets)
            print(f"Создаем контакт с индексом {idx}")

            # Контейнер для контакта
            contact_box = tk.Frame(contacts_container, bg='#f8f9fa', relief='solid', bd=1)
            contact_box.pack(fill=tk.X, pady=5)
            print("Контейнер для контакта создан и упакован")

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
        loaded_contacts = 0
        if contacts_db:
            print(f"Начинаем загрузку {len(contacts_db)} контактов")
            for contact in contacts_db:
                print(f"Создаем виджет для контакта: {contact}")
                widget = create_contact_widget(contact)
                if widget:
                    loaded_contacts += 1
        else:
            print("Контакты не найдены в базе данных")

        # Всегда создаем хотя бы один пустой виджет для редактирования
        if loaded_contacts == 0:
            print("Создаем пустой виджет для нового контакта")
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
        
        print(f"Раздел контактов завершен. Загружено: {loaded_contacts} контактов")

        # Обновляем scrollregion после создания всех элементов
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        print("Scrollregion обновлен")

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
                self._refresh_data()

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
        
        print("Метод _edit_client завершен")

    def _refresh_client_card(self):
        """Обновить данные в карточке клиента (для перезагрузки вкладок)"""
        # Эта функция может быть использована для обновления данных в открытой карточке
        pass

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
                self._refresh_data()

            except Exception as e:
                show_message(
                    self.parent_frame.master,  # ← ИЗМЕНЕНО!
                    "Ошибка",
                    f"Не удалось удалить клиента:\n{e}",
                    "error"
                )

    def _add_info_row(self, parent, label, value, row):
        """Добавляет строку с информацией"""
        tk.Label(
            parent,
            text=label,
            font=("Arial", 12, "bold"),
            bg='white'
        ).grid(row=row, column=0, sticky='w', pady=5, padx=(0, 10))

        tk.Label(
            parent,
            text=value,
            font=("Arial", 12),
            bg='white',
            fg='#333'
        ).grid(row=row, column=1, sticky='w', pady=5, padx=(0, 10))

    def _edit_client(self, client, parent_window):
        """Диалог редактирования клиента по примеру из раздела эксперты"""
        try:
            client_id = client['id']
            client_data = self.clients_mgr.get_by_id(client_id)
            if not client_data:
                from tkinter import messagebox
                messagebox.showerror("Ошибка", f"Клиент с ID {client_id} не найден")
                return

            dialog, content, buttons_frame = self._create_dialog(
                f"✏️ Редактирование: {client_data.get('company', 'Клиент')}",
                "750x750"
            )

            # Основная информация
            main_fields = self._create_form_section(content, "📋 Основная информация", [
                {
                    'name': 'company',
                    'label': 'Название компании',
                    'type': 'entry',
                    'required': True,
                    'default': client_data.get('company', '')
                },
                {
                    'name': 'address',
                    'label': 'Адрес',
                    'type': 'entry',
                    'required': False,
                    'default': client_data.get('address', '') or ''
                },
                {
                    'name': 'notes',
                    'label': 'Примечания',
                    'type': 'text',
                    'required': False,
                    'height': 3,
                    'default': client_data.get('notes', '') or ''
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
                    from tkinter import messagebox
                    messagebox.showwarning("Лимит", "Максимум 4 контактных лица")
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
            contacts_db = self.contact_persons_mgr.get_by_client(client_id)
            if contacts_db:
                # Загружаем email для каждого контакта
                contacts_with_email = []
                for contact in contacts_db:
                    contact_dict = dict(contact) if hasattr(contact, 'keys') else contact
                    # Загружаем email для контакта
                    if self.contact_emails_mgr:
                        try:
                            emails = self.contact_emails_mgr.get_by_contact(contact_dict['id'])
                            if emails:
                                email_dict = dict(emails[0]) if hasattr(emails[0], 'keys') else emails[0]
                                contact_dict['email'] = email_dict.get('email', '')
                            else:
                                contact_dict['email'] = ''
                        except Exception as e:
                            print(f"Ошибка загрузки email для контакта {contact_dict['id']}: {e}")
                            contact_dict['email'] = ''
                    else:
                        contact_dict['email'] = ''
                    contacts_with_email.append(contact_dict)
                
                for c in contacts_with_email:
                    create_contact_fields(c)
            else:
                create_contact_fields()

            def save():
                try:
                    company = main_fields['company'].get().strip()
                    if not company:
                        from tkinter import messagebox
                        messagebox.showerror("Ошибка", "Укажите название компании")
                        return

                    address = main_fields['address'].get().strip()
                    notes = main_fields['notes'].get('1.0', tk.END).strip()

                    # Обновляем основную информацию клиента
                    self.clients_mgr.update(client_id, company, address, notes)

                    # Обрабатываем контакты
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

                    # Сохраняем контакты
                    for contact_data in contacts_payload:
                        if contact_data['id']:
                            # Обновляем существующий контакт
                            self.contact_persons_mgr.update(
                                contact_data['id'],
                                contact_data['full_name'],
                                contact_data['position'],
                                contact_data['phone'],
                                contact_data['is_primary']
                            )
                            # Обновляем email
                            if self.contact_emails_mgr:
                                try:
                                    existing_emails = self.contact_emails_mgr.get_by_contact(contact_data['id'])
                                    if existing_emails and contact_data['email']:
                                        # Обновляем существующий email
                                        email_id = dict(existing_emails[0])['id'] if hasattr(existing_emails[0], 'keys') else existing_emails[0]['id']
                                        self.contact_emails_mgr.update(email_id, contact_data['email'], True)
                                    elif contact_data['email']:
                                        # Создаем новый email
                                        self.contact_emails_mgr.add(contact_data['id'], contact_data['email'], True)
                                except Exception as e:
                                    print(f"Ошибка сохранения email: {e}")
                        else:
                            # Создаем новый контакт
                            new_contact_id = self.contact_persons_mgr.add(
                                client_id=client_id,
                                full_name=contact_data['full_name'],
                                position=contact_data['position'],
                                phone=contact_data['phone'],
                                is_primary=contact_data['is_primary']
                            )
                            # Добавляем email если есть
                            if contact_data['email'] and self.contact_emails_mgr:
                                try:
                                    self.contact_emails_mgr.add(new_contact_id, contact_data['email'], True)
                                except Exception as e:
                                    print(f"Ошибка сохранения email: {e}")

                    # Удаляем контакты помеченные как удаленные
                    for w in contact_widgets:
                        if w.get('deleted', False) and w.get('id'):
                            try:
                                self.contact_persons_mgr.delete(w['id'])
                            except Exception as e:
                                print(f"Ошибка удаления контакта: {e}")

                    from tkinter import messagebox
                    dialog.destroy()
                    self._refresh_data()
                    self._refresh_contacts_tab()

                except Exception as e:
                    from tkinter import messagebox
                    messagebox.showerror("Ошибка", str(e))

            self._create_dialog_buttons(buttons_frame, save)

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")

    def _delete_client_from_card(self, client, card_window):
        """Удалить клиента из карточки"""
        confirm = show_confirmation(
            card_window,
            "Удаление клиента",
            f"Вы уверены, что хотите удалить клиента '{client.get('company', '')}'?\n\nЭто действие нельзя отменить!"
        )

        if confirm:
            try:
                self.clients_mgr.delete(client.get('id'))
                messagebox.showinfo("Успех", "Клиент удален!")
                card_window.destroy()
                self._refresh_data()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить клиента: {e}")
