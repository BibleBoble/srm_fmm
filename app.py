"""
Главный класс приложения SRM FMM
"""
import tkinter as tk

# Импортируем менеджеры
from managers.clients_manager import ClientsManager
from managers.tasks_manager import TasksManager
from managers.experts_manager import ExpertsManager

# Импортируем представления
from views.clients_view import ClientsView
from views.experts_view import ExpertsView
from views.tasks_view import TasksView
from views.reports_view import ReportsView


class App:
    """
    Главный класс приложения SRM FMM
    """

    def __init__(self, root):
        """
        Args:
            root: tk.Tk - корневое окно приложения
        """
        self.root = root

        # Создаём менеджеры БД
        self.clients_mgr = ClientsManager()
        self.tasks_mgr = TasksManager()
        self.experts_mgr = ExpertsManager()  # <-- Уже есть здесь

        from managers.contact_persons_manager import ContactPersonsManager
        from managers.contact_emails_manager import ContactEmailsManager
        from managers.interactions_manager import InteractionsManager

        self.contact_persons_mgr = ContactPersonsManager()
        self.contact_emails_mgr = ContactEmailsManager()
        self.interactions_mgr = InteractionsManager()

        # Представления (создадим после создания content_frame)
        self.clients_view = None
        self.tasks_view = None
        self.reports_view = None

        # Настройка окна
        self._setup_window()

        # Создание интерфейса
        self._create_menu()
        self._create_content_area()
        self._create_views()

        # Открываем основной рабочий раздел при запуске.
        self.show_tasks()

    def _setup_window(self):
        """Настройка главного окна в классическом стиле"""
        self.root.title("SRM FMM")

        # Кроссплатформенное развертывание окна
        try:
            self.root.state('zoomed')
        except:
            self.root.attributes('-zoomed', True)

        # Возвращаем принудительный белый фон
        self.root.configure(bg='white')

    def _create_menu(self):
        """Создаёт верхнее меню"""
        self.top_bar = tk.Frame(self.root, bg="#333333", height=50)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)

        # Список кнопок меню
        self.menu_buttons = {}
        buttons_data = [
            ("Задачи", self.show_tasks),
            ("Клиенты", self.show_clients),
            ("Эксперты", self.show_experts),
            ("Отчеты", self.show_reports)
        ]

        for text, command in buttons_data:
            btn = tk.Button(
                self.top_bar,
                text=text,
                command=command,
                bg="#41a5be",
                fg="black",
                font=("Arial", 11),
                relief="flat",
                padx=15,
                cursor="hand2",
                activebackground="#41a5be",
                activeforeground="black",
                highlightthickness=0,
                bd=0
            )
            btn.pack(side=tk.LEFT, padx=5, pady=10)
            self.menu_buttons[text] = btn

        # Кнопка выхода
        tk.Button(
            self.top_bar,
            text="Выход",
            command=self._on_exit,
            bg="#d9534f",
            fg="white",
            font=("Arial", 11),
            relief="flat",
            padx=15,
            cursor="hand2",
            activebackground="#d9534f",
            activeforeground="white",
            highlightthickness=0,
            bd=0
        ).pack(side=tk.RIGHT, padx=10, pady=10)

    def _set_active_menu(self, menu_name):
        """Установить активный раздел в меню"""
        for name, btn in self.menu_buttons.items():
            if name == menu_name:
                # Активная кнопка - БЕЛЫЙ фон
                btn.config(
                    bg="white",
                    fg="black",
                    font=("Arial", 11, "bold"),
                    activebackground="white",
                    activeforeground="black"
                )
            else:
                # Неактивные кнопки - бирюзовый фон
                btn.config(
                    bg="#41a5be",
                    fg="black",
                    font=("Arial", 11),
                    activebackground="#41a5be",
                    activeforeground="black"
                )

    def _create_content_area(self):
        """Создаёт область для контента"""
        self.content_frame = tk.Frame(self.root, bg="white")
        self.content_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def _create_views(self):
        """Создаёт все представления (но не отображает их)"""
        self.clients_view = ClientsView(
            self.content_frame,
            self.clients_mgr,
            self.contact_persons_mgr,
            self.contact_emails_mgr,
            self.interactions_mgr,
            self.tasks_mgr
        )

        self.experts_view = ExpertsView(self.content_frame, self.experts_mgr)
        self.tasks_view = TasksView(self.content_frame, self.tasks_mgr, self.clients_mgr)
        self.reports_view = ReportsView(self.content_frame)

    def _on_exit(self):
        """Обработчик выхода из приложения"""
        from tkinter import messagebox
        if messagebox.askyesno("Выход", "Вы действительно хотите выйти?"):
            # Закрываем соединение с БД
            from managers.database import Database
            db = Database()
            db.close()
            # Закрываем приложение
            self.root.quit()

    # --- МЕТОДЫ НАВИГАЦИИ ---

    def show_clients(self):
        """Показывает раздел 'Клиенты'"""
        print("-> Переход на: Клиенты")
        self._set_active_menu("Клиенты")
        self.clients_view.show()

    def show_experts(self):
        """Показывает раздел 'Эксперты'"""
        print("-> Переход на: Эксперты")
        self._set_active_menu("Эксперты")
        self.experts_view.show()

    def show_tasks(self):
        """Показывает раздел 'Задачи'"""
        print("-> Переход на: Задачи")
        self._set_active_menu("Задачи")
        self.tasks_view.show()

    def show_reports(self):
        """Показывает раздел 'Отчеты'"""
        print("-> Переход на: Отчеты")
        self._set_active_menu("Отчеты")
        self.reports_view.show()