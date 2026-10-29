# -*- coding: utf-8 -*-
"""
SearchableCombobox widget — перенос из views/tasks_view.py
"""
import tkinter as tk


class SearchableCombobox:
    """Комбобокс с поиском и автодополнением"""

    def __init__(self, parent, values=None, font=("Arial", 11), **kwargs):
        self.parent = parent
        self.values = values or []
        self.filtered_values = self.values.copy()
        self.listbox_visible = False

        # Создаем frame для entry
        self.frame = tk.Frame(parent, bg='white')

        # Entry для ввода с поиском
        self.var = tk.StringVar()
        self.entry = tk.Entry(
            self.frame,
            textvariable=self.var,
            font=font,
            relief="solid",
            borderwidth=1,
            **kwargs
        )
        self.entry.pack(fill=tk.X, expand=True)  # type: ignore[arg-type]

        # Listbox для отображения результатов (создается в родительском окне)
        self.listbox_frame = tk.Toplevel(parent)
        self.listbox_frame.withdraw()  # Изначально скрыт
        self.listbox_frame.overrideredirect(True)  # Убираем рамку окна

        self.listbox = tk.Listbox(
            self.listbox_frame,
            font=font,
            bg='white',
            selectbackground='#41a5be',
            selectforeground='white',
            height=6,
            relief="solid",
            borderwidth=1,
            highlightthickness=0
        )

        # Scrollbar для списка
        scrollbar = tk.Scrollbar(self.listbox_frame, orient="vertical")
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)  # type: ignore[arg-type]
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)  # type: ignore[arg-type]

        # Привязываем события
        self.var.trace('w', self._on_type)
        self.entry.bind('<FocusIn>', self._on_focus_in)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<KeyRelease>', self._on_key_release)
        self.entry.bind('<Return>', self._on_select)
        self.entry.bind('<Escape>', self._hide_list)
        self.entry.bind('<Down>', self._on_down)
        self.entry.bind('<Up>', self._on_up)
        # Используем ButtonRelease чтобы корректно получать кликнутый индекс
        self.listbox.bind('<ButtonRelease-1>', self._on_listbox_click)
        self.listbox.bind('<Return>', self._on_select)
        self.listbox.bind('<Escape>', self._hide_list)

        # Глобальная привязка для скрытия при клике вне
        self.listbox_frame.bind('<FocusOut>', self._on_focus_out)

    def _on_type(self, *args):
        """Фильтрация при вводе текста"""
        text = self.var.get().lower()

        if not text:
            self.filtered_values = self.values.copy()
        else:
            self.filtered_values = [
                val for val in self.values
                if text in val.lower()
            ]

        self._update_listbox()
        if self.filtered_values:
            self._show_list()
        else:
            self._hide_list()

    def _update_listbox(self):
        """Обновление содержимого listbox"""
        self.listbox.delete(0, tk.END)
        for value in self.filtered_values:
            self.listbox.insert(tk.END, value)

    def _show_list(self):
        """Показать список"""
        if not self.filtered_values:
            return

        # Позиционируем список под entry
        try:
            x = self.entry.winfo_rootx()
            y = self.entry.winfo_rooty() + self.entry.winfo_height()
            width = self.entry.winfo_width()

            self.listbox_frame.geometry(f"{width}x{min(150, len(self.filtered_values) * 25)}+{x}+{y}")
            self.listbox_frame.deiconify()
            self.listbox_frame.lift()
            self.listbox_visible = True
        except:
            pass

    def _hide_list(self, event=None):
        """Скрыть список"""
        try:
            self.listbox_frame.withdraw()
            self.listbox_visible = False
        except:
            pass

    def _on_focus_in(self, event=None):
        """При получении фокуса"""
        if self.var.get():
            self._show_list()

    def _on_focus_out(self, event=None):
        """При потере фокуса"""
        # Задержка чтобы успеть кликнуть на список
        self.parent.after(150, self._hide_list)

    def _on_key_release(self, event):
        """При отпускании клавиши"""
        if event.keysym in ('Up', 'Down', 'Return', 'Escape'):
            return
        self._on_type()

    def _on_down(self, event):
        """Стрелка вниз"""
        if not self.listbox_visible:
            self._show_list()
        else:
            current = self.listbox.curselection()
            if current:
                next_index = (current[0] + 1) % len(self.filtered_values)
            else:
                next_index = 0
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(next_index)
            self.listbox.see(next_index)
        return "break"

    def _on_up(self, event):
        """Стрелка вверх"""
        if self.listbox_visible:
            current = self.listbox.curselection()
            if current:
                prev_index = (current[0] - 1) % len(self.filtered_values)
            else:
                prev_index = len(self.filtered_values) - 1
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(prev_index)
            self.listbox.see(prev_index)
        return "break"

    def _on_select(self, event=None):
        """Выбор элемента"""
        selection = self.listbox.curselection()
        if selection:
            selected_value = self.listbox.get(selection[0])
            self.var.set(selected_value)
        self._hide_list()

    def _on_listbox_click(self, event=None):
        """Клик по элементу списка: выбираем элемент по координате и вставляем в entry"""
        try:
            # nearest возвращает индекс ближайшего элемента к координате y
            idx = self.listbox.nearest(event.y)
            if idx is not None:
                selected_value = self.listbox.get(idx)
                self.var.set(selected_value)
        except Exception:
            # fallback на стандартное поведение
            self._on_select()
        finally:
            self._hide_list()

    def get(self):
        """Получить текущее значение"""
        return self.var.get()

    def set(self, value):
        """Установить значение"""
        self.var.set(value)

    def pack(self, **kwargs):
        """Упаковка основного frame"""
        self.frame.pack(**kwargs)  # type: ignore[arg-type]

    def pack_side(self, side=tk.LEFT, **kwargs):
        """Упаковка на стороне"""
        self.frame.pack(side=side, **kwargs)  # type: ignore[arg-type]
