"""
Главный класс приложения SRM FMM
"""
import tkinter as tk
from datetime import date

# Импортируем менеджеры
from managers.clients_manager import ClientsManager
from managers.contracts_manager import ContractsManager
from managers.tasks_manager import TasksManager

# Импортируем представления
from views.calendar_view import CalendarView
from views.clients_view import ClientsView
from views.contracts_view import ContractsView
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

        # Данные приложения
        self.selected_date = None  # выбранная дата в календаре

        # Создаём менеджеры БД
        self.clients_mgr = ClientsManager()
        self.contracts_mgr = ContractsManager()
        self.tasks_mgr = TasksManager()

        from managers.contact_persons_manager import ContactPersonsManager
        from managers.emails_manager import EmailsManager
        from managers.interactions_manager import InteractionsManager

        self.contact_persons_mgr = ContactPersonsManager()
        self.emails_mgr = EmailsManager()
        self.interactions_mgr = InteractionsManager()

        # Представления (создадим после создания content_frame)
        self.calendar_view = None
        self.clients_view = None
        self.contracts_view = None
        self.experts_view = None
        self.tasks_view = None
        self.reports_view = None

        # Настройка окна
        self._setup_window()

        # Создание интерфейса
        self._create_menu()
        self._create_content_area()
        self._create_views()

        # Показываем главную страницу
        self.show_main()

    def _setup_window(self):
        """Настройка главного окна"""
        self.root.title("SRM FMM")
        try:
            self.root.iconbitmap(default="obosrashka.ico")
        except:
            pass  # Если иконки нет
        self.root.state('zoomed')
        self.root.configure(bg='white')

    def _create_menu(self):
        """Создаёт верхнее меню"""
        self.top_bar = tk.Frame(self.root, bg="#333333", height=50)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)

        # Список кнопок меню
        self.menu_buttons = {}
        buttons_data = [
            ("Главная", self.show_main),
            ("Клиенты", self.show_clients),
            ("Договора", self.show_contracts),
            ("Эксперты", self.show_experts),
            ("Задачи", self.show_tasks),
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
        self.calendar_view = CalendarView(
            self.content_frame,
            on_date_click_callback=self.on_date_click
        )

        # Передаём ВСЕ менеджеры в ClientsView
        self.clients_view = ClientsView(
            self.content_frame,
            self.clients_mgr,
            self.contact_persons_mgr,
            self.emails_mgr,
            self.interactions_mgr
        )

        self.contracts_view = ContractsView(self.content_frame)
        self.experts_view = ExpertsView(self.content_frame)
        self.tasks_view = TasksView(self.content_frame, self.tasks_mgr, self.clients_mgr)
        self.reports_view = ReportsView(self.content_frame)

    # --- ОБРАБОТЧИКИ СОБЫТИЙ ---

    def on_date_click(self, day, month, year):
        """
        Вызывается при клике на дату в календаре

        Args:
            day, month, year: int - компоненты даты
        """
        self.selected_date = date(year, month, day)
        print(f"App: выбрана дата {self.selected_date.strftime('%d.%m.%Y (%A)')}")

        # Здесь можно добавить дополнительную логику:
        # - показать окно создания задачи
        # - загрузить события на эту дату
        # - и т.д.

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

    def show_main(self):
        """Показывает главную страницу (календарь)"""
        print("→ Переход на: Главная")
        self._set_active_menu("Главная")
        self.calendar_view.show()

    def show_clients(self):
        """Показывает раздел 'Клиенты'"""
        print("→ Переход на: Клиенты")
        self._set_active_menu("Клиенты")
        self.clients_view.show()

    def show_contracts(self):
        """Показывает раздел 'Договора'"""
        print("→ Переход на: Договора")
        self._set_active_menu("Договора")
        self.contracts_view.show()

    def show_experts(self):
        """Показывает раздел 'Эксперты'"""
        print("→ Переход на: Эксперты")
        self._set_active_menu("Эксперты")
        self.experts_view.show()

    def show_tasks(self):
        """Показывает раздел 'Задачи'"""
        print("→ Переход на: Задачи")
        self._set_active_menu("Задачи")
        self.tasks_view.show()

    def show_reports(self):
        """Показывает раздел 'Отчеты'"""
        print("→ Переход на: Отчеты")
        self._set_active_menu("Отчеты")
        self.reports_view.show()