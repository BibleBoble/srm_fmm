# -*- coding: utf-8 -*-
"""
Шаблон табличного представления для разделов приложения.
Основан на структуре раздела "Клиенты".
"""
import tkinter as tk
from tkinter import ttk, messagebox
from views.base_view import BaseView
from utils.constants import Colors, TableView, Sizes, Limits, UISettings
from utils.helpers import show_message, show_confirmation
from utils.ui_helpers import center_toplevel


class TableViewTemplate(BaseView):
    """
    Базовый класс для табличных представлений с поиском, сортировкой и пагинацией.
    
    Наследник должен определить:
    - TITLE: str - название раздела
    - COLUMNS: tuple - заголовки колонок таблицы
    - ADD_BUTTON_TEXT: str - текст кнопки добавления
    - SEARCH_FIELDS_TEXT: str - подсказка по полям поиска
    - COLUMN_WIDTHS: dict - ширина колонок {название: ширина}
    - STRETCH_COLUMNS: list - колонки, растягиваемые по ширине
    - ID_COLUMN: str - название колонки с ID (для двойного клика)
    
    И реализовать:
    - _get_data(page, search, sort_by, sort_order) -> (items, total)
    - _item_to_row_values(item) -> tuple
    - _open_create_dialog()
    - _on_row_double_click(item_id)
    """

    # Настройки по умолчанию (переопределяются в наследниках)
    TITLE = "Раздел"
    COLUMNS = ("ID", "Название")
    ADD_BUTTON_TEXT = "+ Добавить"
    SEARCH_FIELDS_TEXT = "названию"
    COLUMN_WIDTHS = {}
    STRETCH_COLUMNS = []
    ID_COLUMN = "ID"
    SORT_OPTIONS = []  # [(value, label), ...] или пусто - без сортировки
    PAGE_SIZE = Limits.ITEMS_PER_PAGE

    def __init__(self, parent_frame, manager):
        super().__init__(parent_frame)
        self.manager = manager
        # Восстановлено оригинальное поведение — публичный атрибут parent
        self.parent = parent_frame

        self.search_var = tk.StringVar()
        self.search_job = None
        self._search_trace_id = self.search_var.trace_add(
            "write",
            self._on_search_change
        )
        self.current_page = 1
        self.total_items = 0
        self.sort_var = tk.StringVar(value="")
        if self.SORT_OPTIONS:
            self.sort_var.set(self.SORT_OPTIONS[0][0])

    def show(self):
        """Отображает раздел"""
        self.clear()
        self._create_ui()
        self._refresh_data()

    def _create_ui(self):
        """Создаёт весь интерфейс: шапка, таблица, пагинация"""
        # 1. Верхняя панель
        top_panel = tk.Frame(
            self.parent_frame,
            bg=TableView.TOP_PANEL_BG,
            height=Sizes.TOP_PANEL_HEIGHT
        )
        top_panel.grid(row=0, column=0, sticky="ew")
        top_panel.grid_propagate(False)

        # Счётчик и поиск
        search_container = tk.Frame(top_panel, bg=TableView.TOP_PANEL_BG)
        search_container.pack(side=tk.LEFT, expand=True, padx=Sizes.TOP_PANEL_PADDING_X, pady=Sizes.TOP_PANEL_PADDING_Y)

        self.info_label = tk.Label(
            search_container,
            text="",
            font=TableView.INFO_FONT,
            bg=TableView.TOP_PANEL_BG,
            fg=TableView.LABEL_FG,
            width=25
        )
        self.info_label.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(
            search_container,
            text="Поиск:",
            font=TableView.LABEL_FONT,
            bg=TableView.TOP_PANEL_BG,
            fg=TableView.LABEL_FG
        ).pack(side=tk.LEFT, padx=(0, 5))

        search_entry = tk.Entry(
            search_container,
            textvariable=self.search_var,
            font=TableView.SEARCH_FONT,
            width=min(40, Sizes.SEARCH_ENTRY_WIDTH),
            relief="solid",
            borderwidth=1,
            bg=TableView.TABLE_BG,
            fg=TableView.LABEL_FG,
            insertbackground=TableView.LABEL_FG,
            highlightthickness=1,
            highlightbackground=TableView.ROW_HOVER,
            highlightcolor=TableView.BUTTON_BG
        )
        search_entry.pack(side=tk.LEFT, padx=5, ipady=6)

        tk.Label(
            search_container,
            text=f"По полям: {self.SEARCH_FIELDS_TEXT}",
            font=TableView.LABEL_FONT,
            bg=TableView.TOP_PANEL_BG,
            fg=TableView.HINT_FG
        ).pack(side=tk.LEFT, padx=10)

        # Сортировка (если задана)
        if self.SORT_OPTIONS:
            tk.Label(
                top_panel,
                text="Сортировка:",
                font=TableView.LABEL_FONT,
                bg=TableView.TOP_PANEL_BG,
                fg=TableView.LABEL_FG
            ).pack(side=tk.LEFT, padx=(10, 5), pady=Sizes.TOP_PANEL_PADDING_Y)

            sort_combo = ttk.Combobox(
                top_panel,
                textvariable=self.sort_var,
                values=[opt[1] for opt in self.SORT_OPTIONS],
                state="readonly",
                width=15,
                font=TableView.LABEL_FONT
            )
            sort_combo.pack(side=tk.LEFT, padx=5)
            sort_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_data())

        # Кнопка добавления
        self.add_button = tk.Button(
            top_panel,
            text=self.ADD_BUTTON_TEXT,
            command=self._open_create_dialog,
            bg=TableView.BUTTON_BG,
            fg=TableView.BUTTON_FG,
            font=TableView.BUTTON_FONT,
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground=TableView.BUTTON_ACTIVE_BG,
            activeforeground=TableView.BUTTON_FG
        )
        self.add_button.pack(side=tk.RIGHT, padx=Sizes.TOP_PANEL_PADDING_X, pady=Sizes.TOP_PANEL_PADDING_Y)

        # 2. Используем grid для точного контроля расположения
        self.parent_frame.grid_rowconfigure(1, weight=1)  # Таблица растягивается
        self.parent_frame.grid_rowconfigure(2, weight=0)   # Пагинация фиксирована
        self.parent_frame.grid_columnconfigure(0, weight=1)
        
        # 2.1. Таблица
        self.table_container = tk.Frame(self.parent_frame, bg=TableView.TABLE_BG)
        self.table_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self._create_table()

        # 2.2. Панель пагинации
        self.pagination_frame = tk.Frame(
            self.parent_frame,
            bg=TableView.PAGINATION_BG,
            height=Sizes.PAGINATION_HEIGHT
        )
        self.pagination_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        self.pagination_frame.grid_propagate(False)

        self._create_pagination_widgets()

    def _create_table(self):
        """Создаёт Treeview таблицу"""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=TableView.TABLE_BG,
            foreground=TableView.LABEL_FG,
            rowheight=Sizes.TABLE_ROW_HEIGHT,
            fieldbackground=TableView.TABLE_BG,
            borderwidth=0,
            relief="flat",
            font=TableView.TABLE_FONT
        )
        style.map(
            "Treeview",
            background=[("selected", TableView.ROW_HOVER)],
            foreground=[("selected", TableView.LABEL_FG)]
        )
        style.configure(
            "Treeview.Heading",
            background=TableView.HEADING_BG,
            foreground=TableView.HEADING_FG,
            font=TableView.HEADING_FONT,
            padding=(12, 10),
            borderwidth=0,
            relief="flat"
        )
        style.map("Treeview.Heading", background=[("active", TableView.HEADING_ACTIVE)])
        style.configure(
            "TCombobox",
            padding=(8, 5),
            fieldbackground=TableView.TABLE_BG,
            foreground=TableView.LABEL_FG
        )

        self.tree = ttk.Treeview(
            self.table_container,
            columns=self.COLUMNS,
            show="headings",
            height=30,  # Фиксированная высота 30 строк
            selectmode="browse"
        )

        for col in self.COLUMNS:
            self.tree.heading(col, text=col)
            width = self.COLUMN_WIDTHS.get(col, TableView.COLUMN_DEFAULT_WIDTH)
            stretch = col in self.STRETCH_COLUMNS
            self.tree.column(col, width=width, anchor='w' if col != self.ID_COLUMN else 'center', stretch=stretch)

        self.tree.tag_configure('evenrow', background=TableView.ROW_EVEN)
        self.tree.tag_configure('oddrow', background=TableView.ROW_ODD)
        self.tree.tag_configure('selected', background=TableView.ROW_HOVER)

        # Добавляем тег для основного (primary) — светло-зелёный фон
        self.tree.tag_configure(
            'primary',
            background=Colors.COMPLETED_BG,
            foreground=Colors.COMPLETED_FG
        )

        scrollbar = ttk.Scrollbar(self.table_container, orient="vertical", command=self.tree.yview)
        self.scrollbar = scrollbar
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Configure>', self._configure_columns)
        self.tree.bind('<Enter>', self._on_tree_enter)
        self.tree.bind('<Leave>', self._on_tree_leave)
        self.tree.bind('<Motion>', self._on_tree_motion)

    def _create_pagination_widgets(self):
        """Создаёт кнопки пагинации"""
        for w in self.pagination_frame.winfo_children():
            w.destroy()

        total_pages = max(1, (self.total_items + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        page_info = f"Стр. {self.current_page} из {total_pages} (всего: {self.total_items})"

        btn_frame = tk.Frame(self.pagination_frame, bg=TableView.PAGINATION_BG)
        btn_frame.pack(expand=True, pady=10)

        tk.Button(
            btn_frame,
            text="<< Первая",
            command=lambda: self._go_to_page(1),
            state="normal" if self.current_page > 1 else "disabled",
            bg=TableView.PAGINATION_BUTTON_BG,
            fg=Colors.WHITE,
            disabledforeground=Colors.WHITE,
            font=TableView.PAGINATION_FONT,
            width=10,
            relief="flat",
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="< Назад",
            command=lambda: self._go_to_page(self.current_page - 1),
            state="normal" if self.current_page > 1 else "disabled",
            bg=TableView.PAGINATION_BUTTON_BG,
            fg=Colors.WHITE,
            disabledforeground=Colors.WHITE,
            font=TableView.PAGINATION_FONT,
            width=10,
            relief="flat",
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(
            btn_frame,
            text=page_info,
            font=TableView.PAGINATION_FONT,
            bg=TableView.PAGINATION_BG,
            fg=TableView.LABEL_FG
        ).pack(side=tk.LEFT, padx=15)

        tk.Button(
            btn_frame,
            text="Вперёд >",
            command=lambda: self._go_to_page(self.current_page + 1),
            state="normal" if self.current_page < total_pages else "disabled",
            bg=TableView.PAGINATION_BUTTON_BG,
            fg=Colors.WHITE,
            disabledforeground=Colors.WHITE,
            font=TableView.PAGINATION_FONT,
            width=10,
            relief="flat",
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Последняя >>",
            command=lambda: self._go_to_page(total_pages),
            state="normal" if self.current_page < total_pages else "disabled",
            bg=TableView.PAGINATION_BUTTON_BG,
            fg=Colors.WHITE,
            disabledforeground=Colors.WHITE,
            font=TableView.PAGINATION_FONT,
            width=10,
            relief="flat",
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

    def _go_to_page(self, page):
        """Переход на страницу"""
        self.current_page = max(1, page)
        self._refresh_data()

    def _on_search_change(self, *args):
        """Debounce для поиска"""
        if self.search_job:
            self.parent_frame.after_cancel(self.search_job)
        self.search_job = self.parent_frame.after(
            UISettings.SEARCH_DEBOUNCE_MS,
            self._perform_search
        )

    def _perform_search(self):
        """Выполняет поиск и сбрасыет на первую страницу"""
        self.search_job = None
        self.current_page = 1
        self._refresh_data()

    def _refresh_data(self):
        """Загружает данные и обновляет таблицу"""
        search = self.search_var.get().strip() if self.search_var else ""
        sort_by, sort_order = self._get_sort_params()

        try:
            items, total = self._get_data(self.current_page, search, sort_by, sort_order)
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            items, total = [], 0

        self.total_items = total

        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Заполнение
        for idx, item in enumerate(items):
            # Используем хук _get_row_tags для получения кортежа тегов (наследники могут добавить 'primary' и т.д.)
            try:
                tags = tuple(self._get_row_tags(item, idx))
                if not tags:
                    tags = ('evenrow',)  # fallback
            except Exception:
                tags = ('evenrow',) if idx % 2 == 0 else ('oddrow',)
            values = self._item_to_row_values(item)
            self.tree.insert("", tk.END, values=values, tags=tags)

        # Обновление UI
        total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        start = (self.current_page - 1) * self.PAGE_SIZE + 1 if items else 0
        end = min(self.current_page * self.PAGE_SIZE, total) if items else 0

        self.info_label.config(
            text=f"{self.TITLE}: {total} | Стр. {start}-{end}"
            if total > 0 else f"{self.TITLE}: 0"
        )
        self._create_pagination_widgets()

    def _get_sort_params(self):
        """Возвращает (sort_by, sort_order) из sort_var"""
        if not self.SORT_OPTIONS:
            return None, "ASC"
        val = self.sort_var.get()
        for opt_val, opt_label in self.SORT_OPTIONS:
            if opt_label == val:
                # Формат может быть "name" или "name:DESC"
                if ":" in str(opt_val):
                    parts = str(opt_val).split(":")
                    return parts[0], parts[1]
                return opt_val, "ASC"
        return None, "ASC"

    def _configure_columns(self, event=None):
        """Динамическая настройка ширины колонок при ресайзе"""
        if not hasattr(self, 'tree') or not self.tree.winfo_exists():
            return
        width = self.tree.winfo_width()
        fixed_total = sum(
            self.COLUMN_WIDTHS.get(c, TableView.COLUMN_DEFAULT_WIDTH)
            for c in self.COLUMNS if c not in self.STRETCH_COLUMNS
        )
        stretch_cols = [c for c in self.COLUMNS if c in self.STRETCH_COLUMNS]
        if stretch_cols and width > fixed_total:
            col_width = max(100, (width - fixed_total) // len(stretch_cols))
            for col in stretch_cols:
                self.tree.column(col, width=col_width, stretch=True)

    def _on_double_click(self, event):
        """Обработчик двойного клика - извлекает ID и вызывает _on_row_double_click"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, 'values')
        if not values:
            return
        # ID - первая колонка или колонка с именем ID_COLUMN
        try:
            idx = self.COLUMNS.index(self.ID_COLUMN) if self.ID_COLUMN in self.COLUMNS else 0
            item_id = int(values[idx])
            self._on_row_double_click(item_id)
        except (ValueError, IndexError):
            pass

    def _on_tree_enter(self, event):
        self._hover_row = None

    def _on_tree_leave(self, event):
        # корректно удаляем только тег 'selected', не затирая другие теги
        if hasattr(self, '_hover_row') and self._hover_row:
            try:
                tags = list(self.tree.item(self._hover_row).get('tags', ()))
                if 'selected' in tags:
                    tags.remove('selected')
                self.tree.item(self._hover_row, tags=tuple(tags))
            except Exception:
                pass
            self._hover_row = None

    def _on_tree_motion(self, event):
        item = self.tree.identify_row(event.y)
        # Убираем 'selected' с предыдущей строки корректно
        if hasattr(self, '_hover_row') and self._hover_row and self._hover_row != item:
            try:
                prev_tags = list(self.tree.item(self._hover_row).get('tags', ()))
                if 'selected' in prev_tags:
                    prev_tags.remove('selected')
                self.tree.item(self._hover_row, tags=tuple(prev_tags))
            except Exception:
                pass

        if item:
            self._hover_row = item
            try:
                cur_tags = list(self.tree.item(item).get('tags', ()))
                if 'selected' not in cur_tags:
                    # добавляем selected, сохраняя существующие теги (например 'primary')
                    cur_tags.append('selected')
                    self.tree.item(item, tags=tuple(cur_tags))
            except Exception:
                # fallback: просто ставим selected
                self.tree.item(item, tags=('selected',))

    # --- Абстрактные методы для переопределения ---

    def _get_data(self, page, search, sort_by, sort_order):
        """
        Загружает данные для страницы.
        Returns: (list of items, total_count)
        """
        raise NotImplementedError

    def _item_to_row_values(self, item):
        """Преобразует элемент в кортеж значений для строки таблицы"""
        raise NotImplementedError

    def _open_create_dialog(self):
        """Открывает диалог создания записи"""
        raise NotImplementedError

    def _on_row_double_click(self, item_id):
        """Обработчик двойного клика по строке (открытие карточки)"""
        pass

    def _get_row_tags(self, item, idx):
        """
        Хук: вернуть последовательность тегов для строки.
        По умолчанию — простое чередование 'evenrow'/'oddrow'.
        Наследники (например ClientsView) могут переопределить и добавить 'primary'.
        """
        base = 'evenrow' if idx % 2 == 0 else 'oddrow'
        return (base,)

    # --- Универсальные методы для диалогов ---
    
    def _create_dialog(self, title, geometry="750x600"):
        """Создает базовое диалоговое окно"""
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title(title)
        dialog.geometry(geometry)
        dialog.configure(bg=Colors.LIGHT)
        dialog.resizable(False, False)
        center_toplevel(dialog)
        
        # Заголовок
        header = tk.Frame(dialog, bg=Colors.DARK, height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=title,
            font=("Arial", 18, "bold"),
            fg=Colors.WHITE,
            bg=Colors.DARK
        ).pack(pady=15)
        
        # Кнопки внизу
        buttons_container = tk.Frame(dialog, bg=Colors.SURFACE, height=80)
        buttons_container.pack(fill=tk.X, side=tk.BOTTOM)
        buttons_container.pack_propagate(False)
        
        buttons_frame = tk.Frame(buttons_container, bg=Colors.SURFACE)
        buttons_frame.pack(pady=15)
        
        # Canvas для прокрутки контента
        canvas_container = tk.Frame(dialog, bg=Colors.LIGHT)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_container, bg=Colors.SURFACE, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        
        scrollable_content = tk.Frame(canvas, bg=Colors.SURFACE)
        
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

        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mouse_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        return dialog, scrollable_content, buttons_frame
    
    def _create_form_section(self, parent, title, fields_config):
        """Создает секцию формы с полями
        
        Args:
            parent: родительский виджет
            title: заголовок секции
            fields_config: список конфигураций полей
                [
                    {
                        'label': 'Название поля',
                        'type': 'entry'|'text'|'combobox',
                        'required': bool,
                        'options': [] (для combobox),
                        'default': ''
                    }
                ]
        
        Returns:
            dict: словарь с виджетами полей
        """
        # Заголовок секции
        tk.Label(
            parent, 
            text=title, 
            font=("Arial", 14, "bold"), 
            bg='white',
            fg='#333'
        ).pack(anchor='w', padx=20, pady=(15, 10))
        
        # Контейнер полей
        frame = tk.Frame(parent, bg='white')
        frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        widgets = {}
        
        for field_config in fields_config:
            label_text = field_config['label']
            if field_config.get('required'):
                label_text += " *"
            
            # Метка поля
            tk.Label(
                frame, 
                text=label_text, 
                font=("Arial", 10), 
                bg='white', 
                fg='#333'
            ).pack(anchor='w')
            
            field_name = field_config['name']
            field_type = field_config['type']
            
            if field_type == 'entry':
                widget = tk.Entry(
                    frame, 
                    font=("Arial", 11), 
                    relief="solid", 
                    borderwidth=1
                )
                widget.pack(fill=tk.X, pady=(5, 15), ipady=5)
                
            elif field_type == 'text':
                widget = tk.Text(
                    frame, 
                    font=("Arial", 10), 
                    height=field_config.get('height', 3), 
                    relief="solid", 
                    borderwidth=1, 
                    wrap=tk.WORD
                )
                widget.pack(fill=tk.X, pady=(5, 0))
                
            elif field_type == 'combobox':
                widget = ttk.Combobox(
                    frame,
                    values=field_config.get('options', []),
                    state="readonly",
                    font=("Arial", 11)
                )
                widget.pack(fill=tk.X, pady=(5, 15), ipady=3)
            
            # Установка значения по умолчанию
            if 'default' in field_config:
                default_value = field_config['default']
                
                # Преобразуем в строку и убираем None
                if default_value is None:
                    default_value = ''
                else:
                    default_value = str(default_value)
                
                if field_type == 'text':
                    if default_value.strip():  # Проверяем что значение не пустое после очистки от пробелов
                        widget.insert('1.0', default_value)
                elif field_type == 'combobox':
                    widget.set(default_value)
                else:  # entry
                    widget.delete(0, tk.END)
                    widget.insert(0, default_value)
            
            widgets[field_name] = widget
        
        return widgets
    
    def _create_dialog_buttons(self, parent, save_callback, cancel_callback=None):
        """Создает кнопки сохранения и отмены"""
        if cancel_callback is None:
            cancel_callback = lambda: parent.winfo_toplevel().destroy()
        
        # Кнопка сохранения
        tk.Button(
            parent,
            text="💾 Сохранить",
            command=save_callback,
            bg=Colors.PRIMARY,
            fg=Colors.WHITE,
            font=("Arial", 12, "bold"),
            cursor="hand2",
            padx=20,
            pady=10,
            relief="flat",
            activebackground=Colors.PRIMARY_HOVER,
            activeforeground=Colors.WHITE
        ).pack(side=tk.LEFT, padx=10)
        
        # Кнопка отмены
        tk.Button(
            parent,
            text="✖ Отмена",
            command=cancel_callback,
            bg=Colors.LIGHT,
            fg=Colors.TEXT,
            font=("Arial", 12, "bold"),
            cursor="hand2",
            padx=20,
            pady=10,
            relief="flat",
            activebackground=Colors.BORDER,
            activeforeground=Colors.TEXT
        ).pack(side=tk.LEFT, padx=10)
