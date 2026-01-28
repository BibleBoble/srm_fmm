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

    # ... (код класса CalendarView остается выше) ...

    class CalendarDialog(tk.Toplevel):
        """
        Всплывающее окно выбора даты (без сторонних библиотек).
        """

        def __init__(self, parent, on_select):
            super().__init__(parent)
            self.on_select = on_select
            self.title("Выберите дату")
            self.geometry("300x300")
            self.configure(bg='white')
            self.resizable(False, False)

            # Центрируем
            try:
                x = parent.winfo_rootx() + 50
                y = parent.winfo_rooty() + 50
                self.geometry(f"+{x}+{y}")
            except:
                pass

            self.current_date = date.today()
            self.year = self.current_date.year
            self.month = self.current_date.month

            self._setup_ui()
            self._update_calendar()

        def _setup_ui(self):
            header = tk.Frame(self, bg='#333333', height=40)
            header.pack(fill=tk.X)

            tk.Button(header, text="<", command=self._prev, bg='#333333', fg='white', relief='flat').pack(side=tk.LEFT,
                                                                                                          padx=10)
            self.lbl_month = tk.Label(header, text="", font=("Arial", 12, "bold"), bg='#333333', fg='white')
            self.lbl_month.pack(side=tk.LEFT, expand=True)
            tk.Button(header, text=">", command=self._next, bg='#333333', fg='white', relief='flat').pack(side=tk.RIGHT,
                                                                                                          padx=10)

            self.grid_frame = tk.Frame(self, bg='white')
            self.grid_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        def _update_calendar(self):
            for w in self.grid_frame.winfo_children(): w.destroy()

            self.lbl_month.config(text=f"{calendar.month_name[self.month]} {self.year}")
            days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

            for i, d in enumerate(days):
                tk.Label(self.grid_frame, text=d, font=("Arial", 9, "bold"), bg='white',
                         fg='red' if i >= 5 else 'black').grid(row=0, column=i, sticky='nsew')

            cal = calendar.monthcalendar(self.year, self.month)
            for r, week in enumerate(cal):
                for c, day in enumerate(week):
                    if day != 0:
                        bg = "#4CAF50" if (
                                    day == date.today().day and self.month == date.today().month and self.year == date.today().year) else "white"
                        fg = "white" if bg == "#4CAF50" else ("red" if c >= 5 else "black")
                        tk.Button(self.grid_frame, text=str(day), bg=bg, fg=fg, relief='flat',
                                  command=lambda d=day: self._select(d)).grid(row=r + 1, column=c, sticky='nsew',
                                                                              padx=1, pady=1)

            for i in range(7): self.grid_frame.columnconfigure(i, weight=1)

        def _prev(self):
            self.month -= 1
            if self.month < 1: self.month, self.year = 12, self.year - 1
            self._update_calendar()

        def _next(self):
            self.month += 1
            if self.month > 12: self.month, self.year = 1, self.year + 1
            self._update_calendar()

        def _select(self, day):
            selected = date(self.year, self.month, day)
            self.on_select(selected.isoformat())
            self.destroy()


# ... (здесь должен быть ваш старый код класса CalendarView) ...

# --- ДОБАВИТЬ ОТСЮДА ---
class CalendarDialog(tk.Toplevel):
    """
    Всплывающее окно выбора даты.
    Стиль управления аналогичен главной странице (Spinbox).
    """

    def __init__(self, parent, on_select):
        super().__init__(parent)
        self.on_select = on_select
        self.title("Выберите дату")
        self.geometry("350x320")  # Чуть шире, чтобы поместились спинбоксы
        self.configure(bg='white')
        self.resizable(False, False)

        # Центрируем относительно родителя
        try:
            x = parent.winfo_rootx() + 50
            y = parent.winfo_rooty() + 50
            self.geometry(f"+{x}+{y}")
        except:
            pass

        self.current_date = date.today()

        self._setup_ui()
        self._update_calendar()

    def _setup_ui(self):
        # --- ШАПКА (Управление) ---
        header = tk.Frame(self, bg='white', pady=10)
        header.pack(fill=tk.X)

        # Функция-обертка для bind (принимает событие, но игнорирует его)
        def auto_update(*args):
            self._update_calendar()

        # Месяц
        tk.Label(header, text="Месяц:", bg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=(15, 5))

        self.month_var = tk.StringVar(value=self.current_date.month)
        self.month_var.trace("w", auto_update)  # Отслеживаем изменение переменной

        self.spin_month = tk.Spinbox(
            header,
            from_=1, to=12,
            width=3,
            font=("Arial", 10),
            textvariable=self.month_var,
            command=auto_update  # Вызывается при клике на стрелочки
        )
        self.spin_month.pack(side=tk.LEFT)

        # Привязываем нажатие Enter
        self.spin_month.bind('<Return>', auto_update)

        # Год
        tk.Label(header, text="Год:", bg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=(15, 5))

        self.year_var = tk.StringVar(value=self.current_date.year)
        self.year_var.trace("w", auto_update)

        self.spin_year = tk.Spinbox(
            header,
            from_=1900, to=2100,
            width=5,
            font=("Arial", 10),
            textvariable=self.year_var,
            command=auto_update
        )
        self.spin_year.pack(side=tk.LEFT)

        self.spin_year.bind('<Return>', auto_update)

        # --- СЕТКА КАЛЕНДАРЯ ---
        self.grid_frame = tk.Frame(self, bg='white')
        self.grid_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

    def _update_calendar(self):
        # Очистка старой сетки
        for w in self.grid_frame.winfo_children():
            w.destroy()

        try:
            m = int(self.spin_month.get())
            y = int(self.spin_year.get())
        except ValueError:
            return  # Если ввели ерунду, просто не обновляем

        # Дни недели
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for i, d in enumerate(days):
            color = 'red' if i >= 5 else 'black'
            tk.Label(
                self.grid_frame,
                text=d,
                font=("Arial", 9, "bold"),
                bg='white',
                fg=color
            ).grid(row=0, column=i, sticky='nsew', pady=(0, 5))

        # Числа
        cal = calendar.monthcalendar(y, m)
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day != 0:
                    # Проверка на сегодня
                    is_today = (day == date.today().day and m == date.today().month and y == date.today().year)

                    bg_color = "#4CAF50" if is_today else "white"
                    fg_color = "white" if is_today else ("red" if c >= 5 else "black")

                    btn = tk.Button(
                        self.grid_frame,
                        text=str(day),
                        bg=bg_color,
                        fg=fg_color,
                        relief='flat',
                        command=lambda d=day, month=m, year=y: self._select(d, month, year)
                    )
                    btn.grid(row=r + 1, column=c, sticky='nsew', padx=1, pady=1)

        # Растягивание сетки
        for i in range(7):
            self.grid_frame.columnconfigure(i, weight=1)

    def _select(self, day, month, year):
        """Возврат выбранной даты"""
        try:
            selected = date(year, month, day)
            self.on_select(selected.isoformat())
            self.destroy()
        except ValueError:
            pass  # Некорректная дата (например 31 февраля)