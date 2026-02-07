"""
Представление календаря
"""
import tkinter as tk
from tkinter import messagebox
import calendar
from datetime import date
import locale
from views.base_view import BaseView

# Блок руссификации вывода
try:
    locale.setlocale(locale.LC_TIME, "Russian_Russia.1251")
except:
    try:
        locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
    except:
        pass


class CalendarView(BaseView):
    """
    Класс для отображения календаря
    """

    def __init__(self, parent_frame, on_date_click_callback=None):
        """
        Args:
            parent_frame: tk.Frame - контейнер для календаря
            on_date_click_callback: функция(day, month, year) - вызывается при клике по дате
        """
        super().__init__(parent_frame)
        self.on_date_click_callback = on_date_click_callback

        # Виджеты (создадим их в show())
        self.calendar_wrapper = None
        self.grid_frame = None
        self.spin_month = None
        self.spin_year = None

    def show(self):
        """Отображает календарь"""
        self.clear()
        self._create_widgets()
        self._generate_grid()

    def _create_widgets(self):
        """Создаёт все виджеты календаря"""
        current_month_name = date.today().strftime("%B")

        # Контейнер для календаря
        self.calendar_wrapper = tk.Frame(self.parent_frame, bg="white")
        self.calendar_wrapper.pack(side=tk.RIGHT, anchor="ne", padx=10, pady=10)

        # Заголовок
        tk.Label(
            self.calendar_wrapper,
            text=current_month_name,
            font=("Arial", 18, "bold"),
            fg="#333",
            bg="white"
        ).pack(pady=(0, 5))

        # Панель управления
        controls_frame = tk.Frame(self.calendar_wrapper, bg="white")
        controls_frame.pack(pady=5)

        # Месяц
        tk.Label(controls_frame, text="Месяц:", bg="white").pack(side=tk.LEFT, padx=2)
        self.spin_month = tk.Spinbox(
            controls_frame,
            from_=1, to=12,
            width=3,
            font=("Arial", 10)
        )
        self.spin_month.delete(0, "end")
        self.spin_month.insert(0, date.today().month)
        self.spin_month.pack(side=tk.LEFT)

        # Год
        tk.Label(controls_frame, text="Год:", bg="white").pack(side=tk.LEFT, padx=2)
        self.spin_year = tk.Spinbox(
            controls_frame,
            from_=1900, to=2100,
            width=4,
            font=("Arial", 10)
        )
        self.spin_year.delete(0, "end")
        self.spin_year.insert(0, date.today().year)
        self.spin_year.pack(side=tk.LEFT)

        # Кнопка обновления
        tk.Button(
            self.calendar_wrapper,
            text="ОК",
            command=self._generate_grid,
            bg="#0078d7",
            fg="white",
            font=("Arial", 9)
        ).pack(pady=5)

        # Рамка для сетки календаря
        self.grid_frame = tk.Frame(self.calendar_wrapper, bg="white", bd=5, relief="ridge")
        self.grid_frame.pack()

    def _generate_grid(self):
        """Генерирует сетку календаря"""
        # Удаляем старые цифры
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        try:
            m = int(self.spin_month.get())
            y = int(self.spin_year.get())
            today = date.today()

            cal_matrix = calendar.monthcalendar(y, m)
            days_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

            # 1. Заголовки дней недели
            for i, day_name in enumerate(days_names):
                c_color = "red" if i >= 5 else "black"
                lbl = tk.Label(
                    self.grid_frame,
                    text=day_name,
                    font=("Arial", 9, "bold"),
                    fg=c_color,
                    bg="white",
                    width=2,
                    height=1,
                    anchor="center"
                )
                lbl.grid(row=0, column=i, padx=2, pady=2)

            # 2. Сами числа
            for row_idx, week in enumerate(cal_matrix):
                for col_idx, day_num in enumerate(week):
                    if day_num != 0:
                        # Определяем цвета
                        if day_num == today.day and m == today.month and y == today.year:
                            num_color = "white"
                            bcg_color = "green"
                        elif col_idx >= 5:
                            num_color = "red"
                            bcg_color = "white"
                        else:
                            num_color = "black"
                            bcg_color = "white"

                        btn = tk.Button(
                            self.grid_frame,
                            text=str(day_num),
                            font=("Arial", 9),
                            fg=num_color,
                            bg=bcg_color,
                            width=2,
                            height=1,
                            bd=1,
                            relief="solid",
                            activebackground="#dddddd",
                            command=lambda d=day_num: self._on_date_click(d, m, y)
                        )
                        btn.grid(row=row_idx + 1, column=col_idx, padx=0, pady=0)

        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный год или месяц!")

    def _on_date_click(self, day, month, year):
        """Обработчик клика по дате"""
        print(f"CalendarView: клик по дате {day:02d}.{month:02d}.{year}")

        # Вызываем внешний callback, если он задан
        if self.on_date_click_callback:
            self.on_date_click_callback(day, month, year)


class CalendarDialog(tk.Toplevel):
    """
    Улучшенный всплывающий диалог выбора даты.
    Современный дизайн с навигацией и автоматическим обновлением.
    """

    def __init__(self, parent, title="Выберите дату"):
        super().__init__(parent)
        self.title(title)
        self.geometry("350x320")
        self.configure(bg='white')
        self.resizable(False, False)
        
        # Результат выбора
        self.selected_date = None
        
        # Центрируем относительно родителя
        try:
            x = parent.winfo_rootx() + 50
            y = parent.winfo_rooty() + 50
            self.geometry(f"+{x}+{y}")
        except:
            pass

        self.current_date = date.today()
        self.result = None

        self._setup_ui()
        self._update_calendar()

    def _setup_ui(self):
        """Создание интерфейса"""
        # Шапка с навигацией
        header = tk.Frame(self, bg='#f0f0f0', height=50)
        header.pack(fill=tk.X, padx=10, pady=10)
        header.pack_propagate(False)

        # Навигация по месяцам
        nav_frame = tk.Frame(header, bg='#f0f0f0')
        nav_frame.pack(expand=True)

        # Кнопки навигации
        tk.Button(
            nav_frame, 
            text="◀", 
            command=self._prev_month,
            bg="#41a5be", 
            fg="white", 
            font=("Arial", 10, "bold"),
            width=3,
            relief="flat"
        ).pack(side=tk.LEFT, padx=5)

        # Метка месяца и года
        self.month_label = tk.Label(
            nav_frame, 
            text="", 
            font=("Arial", 12, "bold"), 
            bg='#f0f0f0', 
            fg='#333'
        )
        self.month_label.pack(side=tk.LEFT, expand=True)

        tk.Button(
            nav_frame, 
            text="▶", 
            command=self._next_month,
            bg="#41a5be", 
            fg="white", 
            font=("Arial", 10, "bold"),
            width=3,
            relief="flat"
        ).pack(side=tk.RIGHT, padx=5)

        # Быстрый выбор через спинбоксы
        spin_frame = tk.Frame(self, bg='white')
        spin_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Месяц
        tk.Label(spin_frame, text="Месяц:", bg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.month_var = tk.StringVar(value=self.current_date.month)
        self.spin_month = tk.Spinbox(
            spin_frame,
            from_=1, to=12,
            width=3,
            font=("Arial", 10),
            textvariable=self.month_var,
            command=self._update_calendar
        )
        self.spin_month.pack(side=tk.LEFT, padx=(0, 15))
        self.spin_month.bind('<Return>', lambda e: self._update_calendar())

        # Год
        tk.Label(spin_frame, text="Год:", bg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.year_var = tk.StringVar(value=self.current_date.year)
        self.spin_year = tk.Spinbox(
            spin_frame,
            from_=1900, to=2100,
            width=5,
            font=("Arial", 10),
            textvariable=self.year_var,
            command=self._update_calendar
        )
        self.spin_year.pack(side=tk.LEFT)
        self.spin_year.bind('<Return>', lambda e: self._update_calendar())

        # Сетка календаря
        self.grid_frame = tk.Frame(self, bg='white')
        self.grid_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=(0, 10))

        # Кнопки управления
        btn_frame = tk.Frame(self, bg='#f0f0f0')
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

        tk.Button(
            btn_frame,
            text="OK",
            command=self._on_ok,
            bg="#28a745",
            fg="white",
            font=("Arial", 11, "bold"),
            width=10
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_frame,
            text="Отмена",
            command=self.destroy,
            bg="#6c757d",
            fg="white",
            font=("Arial", 11, "bold"),
            width=10
        ).pack(side=tk.RIGHT, padx=5)

    def _update_calendar(self):
        """Обновление сетки календаря"""
        # Очистка старой сетки
        for w in self.grid_frame.winfo_children():
            w.destroy()

        try:
            m = int(self.month_var.get())
            y = int(self.year_var.get())
        except ValueError:
            return  # Если ввели некорректные данные, просто не обновляем

        # Обновляем заголовок
        self.month_label.config(text=f"{calendar.month_name[m]} {y}")

        # Дни недели
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for i, d in enumerate(days):
            color = '#dc3545' if i >= 5 else '#333'  # Красный для выходных
            tk.Label(
                self.grid_frame,
                text=d,
                font=("Arial", 10, "bold"),
                bg='white',
                fg=color,
                width=4,
                height=2
            ).grid(row=0, column=i, sticky='nsew', pady=(0, 5))

        # Числа месяца
        cal = calendar.monthcalendar(y, m)
        today = date.today()
        
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day != 0:
                    # Проверка на сегодня
                    is_today = (day == today.day and m == today.month and y == today.year)
                    # Проверка на выбранную дату
                    is_selected = (self.selected_date and 
                                 day == self.selected_date.day and 
                                 m == self.selected_date.month and 
                                 y == self.selected_date.year)

                    # Цветовая схема
                    if is_selected:
                        bg_color = "#28a745"  # Зеленый для выбранной
                        fg_color = "white"
                        font_style = ("Arial", 10, "bold")
                    elif is_today:
                        bg_color = "#41a5be"
                        fg_color = "white"
                        font_style = ("Arial", 10, "bold")
                    elif c >= 5:  # Выходные
                        bg_color = "#f8f9fa"
                        fg_color = "#dc3545"
                        font_style = ("Arial", 10)
                    else:  # Будни
                        bg_color = "white"
                        fg_color = "#333"
                        font_style = ("Arial", 10)

                    btn = tk.Button(
                        self.grid_frame,
                        text=str(day),
                        bg=bg_color,
                        fg=fg_color,
                        font=font_style,
                        relief="flat",
                        activebackground="#e8f4f8",
                        command=lambda d=day, month=m, year=y: self._select_date(d, month, year)
                    )
                    btn.grid(row=r + 1, column=c, sticky='nsew', padx=1, pady=1)

        # Растягивание колонок
        for i in range(7):
            self.grid_frame.columnconfigure(i, weight=1)

    def _prev_month(self):
        """Предыдущий месяц"""
        month = int(self.month_var.get())
        year = int(self.year_var.get())
        
        month -= 1
        if month < 1:
            month = 12
            year -= 1
            
        self.month_var.set(month)
        self.year_var.set(year)
        self._update_calendar()

    def _next_month(self):
        """Следующий месяц"""
        month = int(self.month_var.get())
        year = int(self.year_var.get())
        
        month += 1
        if month > 12:
            month = 1
            year += 1
            
        self.month_var.set(month)
        self.year_var.set(year)
        self._update_calendar()

    def _select_date(self, day, month, year):
        """Выбор даты"""
        try:
            self.selected_date = date(year, month, day)
            # Подсветка выбранной даты
            self._update_calendar()
            # Автоматически закрываем диалог после выбора даты
            self.result = self.selected_date
            self.destroy()
        except ValueError:
            pass

    def _on_ok(self):
        """Подтверждение выбора"""
        if self.selected_date:
            self.result = self.selected_date
        else:
            # Если дата не выбрана, используем текущую
            self.result = date(int(self.year_var.get()), int(self.month_var.get()), date.today().day)
        self.destroy()

    def show(self):
        """Показать диалог и вернуть результат"""
        self.grab_set()
        self.wait_window()
        return self.result
