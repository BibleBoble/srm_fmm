# table_view_template.py
# Замените весь метод _create_ui на этот:

import tkinter as tk
from tkinter import ttk  # <-- Добавьте эту строку
from views.base_view import BaseView
from utils.ui_helpers import create_search_frame, center_toplevel, show_message


# ... остальной код ...

def _create_ui(self):
    """Создает UI в стиле clients_view с пагинацией"""
    # Верхняя панель
    top_panel = tk.Frame(
        self.parent_frame,
        bg=self.COLORS['top_panel_bg'],
        height=self.SIZES['top_panel_height']
    )
    top_panel.pack(fill=tk.X)
    top_panel.pack_propagate(False)

    # Контейнер поиска
    search_container = tk.Frame(top_panel, bg=self.COLORS['top_panel_bg'])
    search_container.pack(side=tk.LEFT, expand=True, padx=20, pady=15)

    # Счетчик элементов
    try:
        count = self._get_item_count()
    except Exception as e:
        print(f"Ошибка получения количества: {e}")
        count = 0

    self.info_label = tk.Label(
        search_container,
        text=f"{self.TITLE}: {count}",
        font=self.FONTS['info'],
        bg=self.COLORS['top_panel_bg'],
        fg='#333',
        width=15
    )
    self.info_label.pack(side=tk.LEFT, padx=(0, 0))

    # Кнопка добавления (правая часть)
    add_btn_container = tk.Frame(top_panel, bg=self.COLORS['top_panel_bg'])
    add_btn_container.pack(side=tk.RIGHT, padx=20, pady=15)

    tk.Button(
        add_btn_container,
        text=self.ADD_BUTTON_TEXT,
        command=self._open_create_dialog,
        bg=self.COLORS['button_bg'],
        fg=self.COLORS['button_fg'],
        font=self.FONTS['button'],
        relief="flat",
        padx=20,
        pady=8,
        cursor="hand2"
    ).pack(side=tk.RIGHT)

    # Панель поиска
    search_frame = tk.Frame(top_panel, bg=self.COLORS['top_panel_bg'])
    search_frame.pack(side=tk.LEFT, padx=10, pady=15)

    tk.Label(
        search_frame,
        text=f"Поиск по {self.SEARCH_FIELDS_TEXT}:",
        font=self.FONTS['label'],
        bg=self.COLORS['top_panel_bg'],
        fg='#666'
    ).pack(side=tk.LEFT, padx=(0, 10))

    search_entry = tk.Entry(
        search_frame,
        textvariable=self.search_var,
        width=40,
        font=self.FONTS['label'],
        relief="solid",
        bd=1
    )
    search_entry.pack(side=tk.LEFT)
    search_entry.insert(0, self.SEARCH_HINT)

    # Событие при изменении поиска
    self.search_var.trace_add('write', self._on_search_change)

    # Контейнер для таблицы
    self.table_container = tk.Frame(self.parent_frame, bg='white')
    self.table_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    # Создание таблицы (Treeview)
    self._create_table()

    # Панель пагинации (если включена)
    if self.USE_PAGINATION:
        self.pagination_frame = tk.Frame(
            self.parent_frame,
            bg='white',
            height=self.SIZES['pagination_height']
        )
        self.pagination_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.pagination_frame.pack_propagate(False)


def _create_table(self):
    """Создает Treeview таблицу"""
    # Фрейм для таблицы с прокруткой
    table_frame = tk.Frame(self.table_container, bg='white')
    table_frame.pack(fill=tk.BOTH, expand=True)

    # Вертикальная прокрутка
    vsb = tk.Scrollbar(table_frame, orient="vertical")
    vsb.pack(side=tk.RIGHT, fill=tk.Y)

    # Горизонтальная прокрутка
    hsb = tk.Scrollbar(table_frame, orient="horizontal")
    hsb.pack(side=tk.BOTTOM, fill=tk.X)

    # Создаем Treeview
    self.tree = ttk.Treeview(
        table_frame,
        columns=self.COLUMNS,
        show='headings',
        height=self.TABLE_HEIGHT,
        yscrollcommand=vsb.set,
        xscrollcommand=hsb.set,
        selectmode='browse'
    )

    # Настраиваем прокрутки
    vsb.config(command=self.tree.yview)
    hsb.config(command=self.tree.xview)

    # Настраиваем колонки
    for col in self.COLUMNS:
        self.tree.heading(col, text=col, anchor='w')
        width = self.COLUMN_WIDTHS.get(col, 150)
        stretch = True if col in self.STRETCH_COLUMNS else False
        self.tree.column(col, width=width, anchor='w', stretch=stretch)

    # Упаковываем таблицу
    self.tree.pack(fill=tk.BOTH, expand=True)

    # Настраиваем теги для чередования строк
    self.tree.tag_configure('evenrow', background=self.COLORS['row_even'])
    self.tree.tag_configure('oddrow', background=self.COLORS['row_odd'])
    self.tree.tag_configure('selected', background=self.COLORS['row_hover'])

    # События
    self.tree.bind('<Double-1>', self._on_double_click)
    self.tree.bind('<ButtonRelease-1>', self._on_single_click)
    self.tree.bind('<Enter>', self._on_tree_enter)
    self.tree.bind('<Leave>', self._on_tree_leave)
    self.tree.bind('<Motion>', self._on_tree_motion)

    # Ресайз колонок
    self.tree.bind('<Configure>', self._configure_columns)