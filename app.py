"""
Главный класс приложения SRM FMM
"""
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from utils.constants import Colors, Fonts, Sizes
from utils.ui_helpers import install_clipboard_bindings

# Импортируем менеджеры
from managers.clients_manager import ClientsManager
from managers.tasks_manager import TasksManager
from managers.experts_manager import ExpertsManager

# Импортируем представления
from views.clients_view import ClientsView
from views.experts_view import ExpertsView
from views.tasks_view import TasksView
from views.reports_view import ReportsView
from views.mail_window import MailView
from services.document_service import DocumentService


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
        install_clipboard_bindings(self.root)

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

        # Фоновое формирование PDF: DOCX создаётся сразу, PDF — в процессе.
        self.document_service = DocumentService(self.root)

        # Представления (создадим после создания content_frame)
        self.clients_view = None
        self.tasks_view = None
        self.reports_view = None
        self.mail_view = None

        # Настройка окна
        self._setup_window()

        # Создание интерфейса
        self._create_menu()
        self._create_content_area()
        self._create_views()

        # Встроенная Яндекс.Почта: процесс стартует сразу и остаётся
        # загруженным, поэтому раздел открывается мгновенно.
        self.mail_view = MailView(self.root, self.mail_frame, self.content_frame)
        self.root.after(300, self.mail_view.preload)

        # Открываем основной рабочий раздел при запуске.
        self.show_tasks()

    def _setup_window(self):
        """Настройка главного окна в классическом стиле"""
        self.root.title("SRM FMM")
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)

        # Кроссплатформенное развертывание окна
        try:
            self.root.state('zoomed')
        except:
            self.root.attributes('-zoomed', True)

        # Используем светлый фон интерфейса.
        self.root.configure(bg=Colors.LIGHT)

    def _create_menu(self):
        """Создаёт верхнее меню"""
        self.top_bar = tk.Frame(self.root, bg=Colors.NAV_BG, height=Sizes.MENU_HEIGHT)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # Список кнопок меню
        self.menu_buttons = {}
        buttons_data = [
            ("Задачи", self.show_tasks),
            ("Клиенты", self.show_clients),
            ("Эксперты", self.show_experts),
            ("Отчеты", self.show_reports),
            ("Почта", self.show_mail)
        ]

        for text, command in buttons_data:
            btn = tk.Button(
                self.top_bar,
                text=text,
                command=command,
                bg=Colors.NAV_BUTTON_BG,
                fg=Colors.WHITE,
                font=Fonts.MENU,
                relief="flat",
                padx=17,
                pady=9,
                cursor="hand2",
                activebackground=Colors.PRIMARY_HOVER,
                activeforeground=Colors.WHITE,
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
            bg=Colors.DANGER,
            fg=Colors.WHITE,
            font=Fonts.MENU,
            relief="flat",
            padx=15,
            cursor="hand2",
            activebackground=Colors.DANGER_HOVER,
            activeforeground=Colors.WHITE,
            highlightthickness=0,
            bd=0
        ).pack(side=tk.RIGHT, padx=10, pady=10)

        tk.Button(
            self.top_bar,
            text="Документы",
            command=self._open_client_documents,
            bg=Colors.NAV_BUTTON_BG,
            fg=Colors.WHITE,
            font=Fonts.MENU,
            relief="flat",
            padx=15,
            cursor="hand2",
            activebackground=Colors.PRIMARY_HOVER,
            activeforeground=Colors.WHITE,
            highlightthickness=0,
            bd=0
        ).pack(side=tk.RIGHT, padx=(0, 5), pady=10)

    def _open_client_documents(self):
        """Открывает общую папку документов клиентов в Проводнике."""
        documents_dir = Path(r"D:\diplom_srm\clients_files")
        if not documents_dir.is_dir():
            messagebox.showerror(
                "Документы",
                f"Папка документов клиентов не найдена:\n{documents_dir}",
                parent=self.root
            )
            return

        try:
            os.startfile(str(documents_dir))
        except OSError as error:
            messagebox.showerror(
                "Документы",
                f"Не удалось открыть папку документов:\n{error}",
                parent=self.root
            )

    def _set_active_menu(self, menu_name):
        """Установить активный раздел в меню"""
        for name, btn in self.menu_buttons.items():
            if name == menu_name:
                # Активная кнопка - БЕЛЫЙ фон
                btn.config(
                    bg=Colors.NAV_ACTIVE_BG,
                    fg=Colors.NAV_ACTIVE_FG,
                    font=Fonts.MENU_ACTIVE,
                    activebackground=Colors.NAV_ACTIVE_BG,
                    activeforeground=Colors.NAV_ACTIVE_FG
                )
            else:
                # Неактивные кнопки остаются на фоне навигационной панели.
                btn.config(
                    bg=Colors.NAV_BUTTON_BG,
                    fg=Colors.WHITE,
                    font=Fonts.MENU,
                    activebackground=Colors.PRIMARY_HOVER,
                    activeforeground=Colors.WHITE
                )

    def _create_content_area(self):
        """Создаёт область контента: обычные разделы и встроенную почту."""
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.content_frame = tk.Frame(self.root, bg=Colors.LIGHT)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Контейнер обычных разделов: клиенты, задачи, эксперты, отчёты.
        self.views_frame = tk.Frame(self.content_frame, bg=Colors.LIGHT)
        self.views_frame.grid(row=0, column=0, sticky="nsew")

        # Контейнер встроенного окна Яндекс.Почты. Окно браузера живёт
        # в отдельном процессе и прикрепляется к этому фрейму.
        self.mail_frame = tk.Frame(self.content_frame, bg=Colors.LIGHT)
        self.mail_frame.grid(row=0, column=0, sticky="nsew")

        self.views_frame.tkraise()

    def _create_views(self):
        """Создаёт все представления (но не отображает их)"""
        self.clients_view = ClientsView(
            self.views_frame,
            self.clients_mgr,
            self.contact_persons_mgr,
            self.contact_emails_mgr,
            self.interactions_mgr,
            self.tasks_mgr,
            document_service=self.document_service
        )

        self.experts_view = ExpertsView(self.views_frame, self.experts_mgr)
        self.tasks_view = TasksView(self.views_frame, self.tasks_mgr, self.clients_mgr)
        self.tasks_view.open_client_callback = self.clients_view._open_client_card_by_id
        self.reports_view = ReportsView(
            self.views_frame,
            self.clients_mgr,
            self.tasks_mgr,
            self.interactions_mgr
        )

    def _on_exit(self):
        """Обработчик выхода: окно скрывается сразу, почта гасится в фоне."""
        from tkinter import messagebox
        if not messagebox.askyesno("Выход", "Вы действительно хотите выйти?"):
            return

        # Мгновенно убираем окно — приложение не «зависает» на закрытии.
        self.root.withdraw()

        def finish():
            # Закрываем соединение с БД и приложение.
            from managers.database import Database
            if self.document_service is not None:
                self.document_service.close()
            Database().close()
            self.root.destroy()

        if self.mail_view is not None:
            self.mail_view.request_shutdown(on_done=finish)
        else:
            finish()

    # --- МЕТОДЫ НАВИГАЦИИ ---

    def show_clients(self):
        """Показывает раздел 'Клиенты'"""
        print("-> Переход на: Клиенты")
        self._show_standard_content()
        self._set_active_menu("Клиенты")
        self.clients_view.show()

    def show_experts(self):
        """Показывает раздел 'Эксперты'"""
        print("-> Переход на: Эксперты")
        self._show_standard_content()
        self._set_active_menu("Эксперты")
        self.experts_view.show()

    def show_tasks(self):
        """Показывает раздел 'Задачи'"""
        print("-> Переход на: Задачи")
        self._show_standard_content()
        self._set_active_menu("Задачи")
        self.tasks_view.show()

    def show_reports(self):
        """Показывает раздел 'Отчеты'"""
        print("-> Переход на: Отчеты")
        self._show_standard_content()
        self._set_active_menu("Отчеты")
        self.reports_view.show()

    def show_mail(self):
        """Показывает встроенную Яндекс.Почту в основном окне."""
        self._set_active_menu("Почта")
        self.mail_frame.tkraise()
        self.mail_view.show()

    def _show_standard_content(self):
        """Переключается на контейнер стандартных разделов."""
        self.views_frame.tkraise()
        if self.mail_view is not None:
            self.mail_view.hide()