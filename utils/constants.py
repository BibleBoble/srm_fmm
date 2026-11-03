# -*- coding: utf-8 -*-
"""
Константы приложения SRM FMM
"""
# ============================================
# ЦВЕТА UI
# ============================================

class Colors:
    """Цветовая схема интерфейса"""

    # Основные цвета
    PRIMARY = "#0f766e"
    PRIMARY_HOVER = "#115e59"
    DARK = "#172b4d"
    LIGHT = "#f3f6fa"
    WHITE = "#ffffff"
    TEXT = "#243247"
    MUTED = "#64748b"
    BORDER = "#dbe3ec"
    SURFACE = "#ffffff"
    NAV_BG = "#172b4d"
    NAV_BUTTON_BG = "#243b5e"
    NAV_ACTIVE_BG = "#ffffff"
    NAV_ACTIVE_FG = "#172b4d"

    # Цвета состояний
    SUCCESS = "#15803d"
    DANGER = "#b42318"
    DANGER_HOVER = "#912018"
    WARNING = "#c2410c"
    INFO = "#2563eb"

    # Дополнительные
    GRAY = "#64748b"
    GRAY_LIGHT = "#f8fafc"
    GRAY_BORDER = "#dbe3ec"

    # Специальные
    OVERDUE = "#fee2e2"
    HOVER = "#e6f4f1"
    COMPLETED_BG = "#ecfdf3"
    COMPLETED_FG = "#166534"
    OVERDUE_FG = "#991b1b"
    TASK_COMPLETED_BG = "#eaf6ed"
    TASK_OVERDUE_BG = "#ffdfb8"
    TASK_CURRENT_BG = "#eaf4fb"
    TASK_ROW_BORDER = "#b8c5d3"
    TASK_TEXT = "#000000"
    PRIORITY_HIGH_BG = "#fff7ed"
    PRIORITY_HIGH_FG = "#9a3412"
    PRIORITY_MEDIUM_BG = "#fffbeb"
    PRIORITY_MEDIUM_FG = "#92400e"
    PRIORITY_LOW_BG = "#eff6ff"
    PRIORITY_LOW_FG = "#1d4ed8"


# ============================================
# ШРИФТЫ
# ============================================

class Fonts:
    """Шрифты интерфейса"""

    # Семейство шрифтов
    FAMILY = "Arial"

    # Размеры и стили
    HEADER_LARGE = (FAMILY, 24, "bold")  # Большие заголовки
    HEADER = (FAMILY, 18, "bold")  # Заголовки диалогов
    SUBHEADER = (FAMILY, 14, "bold")  # Подзаголовки
    NORMAL = (FAMILY, 11)  # Обычный текст
    NORMAL_BOLD = (FAMILY, 11, "bold")  # Обычный жирный
    SMALL = (FAMILY, 10)  # Мелкий текст
    SMALL_ITALIC = (FAMILY, 9, "italic")  # Мелкий курсив
    BUTTON = (FAMILY, 12, "bold")  # Кнопки
    MENU = (FAMILY, 11)  # Меню
    MENU_ACTIVE = (FAMILY, 11, "bold")  # Активное меню


# ============================================
# РАЗМЕРЫ UI
# ============================================

class Sizes:
    """Размеры элементов интерфейса"""

    # Окна
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800

    # Диалоги
    DIALOG_SMALL_WIDTH = 450
    DIALOG_SMALL_HEIGHT = 300
    DIALOG_MEDIUM_WIDTH = 600
    DIALOG_MEDIUM_HEIGHT = 400
    DIALOG_LARGE_WIDTH = 750
    DIALOG_LARGE_HEIGHT = 750

    # Элементы
    HEADER_HEIGHT = 60
    MENU_HEIGHT = 56
    BUTTON_PANEL_HEIGHT = 80
    ENTRY_WIDTH = 50
    TEXT_HEIGHT = 4

    # Отступы
    PADDING_SMALL = 5
    PADDING_MEDIUM = 10
    PADDING_MEDIUMRARE = 15
    PADDING_LARGE = 20
    PADDING_XLARGE = 30

    # Таблицы
    TABLE_ROW_HEIGHT = 42
    TABLE_MAX_ROWS = 25
    TABLE_VISIBLE_ROWS = 25  # Высота Treeview в строках

    # Верхняя панель разделов (поиск, кнопки)
    TOP_PANEL_HEIGHT = 80
    TOP_PANEL_PADDING_X = 20
    TOP_PANEL_PADDING_Y = 15

    # Панель пагинации
    PAGINATION_HEIGHT = 80
    PAGINATION_BUTTON_WIDTH = 80

    # Поле поиска
    SEARCH_ENTRY_WIDTH = 50


# ============================================
# ТАБЛИЧНЫЕ ПРЕДСТАВЛЕНИЯ (TableViewTemplate)
# ============================================

class TableView:
    """Константы для шаблона табличных представлений (клиенты, эксперты и т.д.)"""

    # Цвета
    TOP_PANEL_BG = Colors.LIGHT
    TABLE_BG = Colors.SURFACE
    ROW_EVEN = "#f8fafc"
    ROW_ODD = Colors.SURFACE
    ROW_HOVER = Colors.HOVER
    HEADING_BG = Colors.DARK
    HEADING_FG = Colors.WHITE
    HEADING_ACTIVE = "#243b5e"
    BUTTON_BG = Colors.PRIMARY
    BUTTON_ACTIVE_BG = Colors.PRIMARY_HOVER
    BUTTON_FG = Colors.WHITE
    LABEL_FG = Colors.TEXT
    HINT_FG = Colors.MUTED
    PAGINATION_BG = Colors.LIGHT
    PAGINATION_BUTTON_BG = Colors.PRIMARY
    PAGINATION_BUTTON_DISABLED = Colors.BORDER

    # Шрифты
    INFO_FONT = (Fonts.FAMILY, 11, "bold")
    LABEL_FONT = (Fonts.FAMILY, 10)
    SEARCH_FONT = (Fonts.FAMILY, 12)
    BUTTON_FONT = (Fonts.FAMILY, 11, "bold")
    TABLE_FONT = (Fonts.FAMILY, 10)
    HEADING_FONT = (Fonts.FAMILY, 10, "bold")
    PAGINATION_FONT = (Fonts.FAMILY, 10)

    # Ширины колонок по умолчанию
    COLUMN_ID_WIDTH = 50
    COLUMN_DEFAULT_WIDTH = 150
    COLUMN_WIDE_WIDTH = 250


# ============================================
# ЛИМИТЫ ДАННЫХ
# ============================================

class Limits:
    """Ограничения на данные"""

    # Контакты и email
    MAX_CONTACTS_PER_CLIENT = 4
    MAX_EMAILS_PER_CONTACT = 4
    MAX_CONTACTS_PER_EXPERT = 4

    # Длины строк
    MAX_COMPANY_NAME_LENGTH = 200
    MAX_EMAIL_LENGTH = 100
    MAX_PHONE_LENGTH = 20
    MAX_NOTES_LENGTH = 1000

    # Пагинация
    ITEMS_PER_PAGE = 50
    MAX_ITEMS_PER_PAGE = 100


# ============================================
# НАСТРОЙКИ UI
# ============================================

class UISettings:
    """Настройки поведения UI"""

    # Поиск
    SEARCH_DEBOUNCE_MS = 400  # Задержка перед поиском (мс)

    # Анимации
    HOVER_DELAY_MS = 100  # Задержка hover эффекта

    # Сообщения
    SUCCESS_MESSAGE_DURATION = 2000  # Длительность показа успешного сообщения (мс)
    ERROR_MESSAGE_DURATION = 5000  # Длительность показа ошибки (мс)


# ============================================
# ПРИОРИТЕТЫ ЗАДАЧ
# ============================================

class TaskPriorities:
    """Приоритеты задач"""

    HIGH = "Высокий"
    MEDIUM = "Средний"
    LOW = "Низкий"

    ALL = [HIGH, MEDIUM, LOW]

    # Иконки для приоритетов
    ICONS = {
        HIGH: "🔥",
        MEDIUM: "⚡",
        LOW: "❄"
    }

    # Цвета для приоритетов
    COLORS = {
        HIGH: Colors.DANGER,
        MEDIUM: Colors.WARNING,
        LOW: Colors.INFO
    }


# ============================================
# ВАЛИДАЦИЯ
# ============================================

class Validation:
    """Регулярные выражения для валидации"""

    # Email
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Телефон (международный формат)
    PHONE_PATTERN = r'^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}$'

    # Номер договора
    CONTRACT_NUMBER_PATTERN = r'^[A-Za-z0-9\-\/]+$'


def get_priority_icon(priority: str) -> str:
    """
    Получить иконку для приоритета

    Args:
        priority: Приоритет

    Returns:
        Иконка (emoji) или пустую строку
    """
    return TaskPriorities.ICONS.get(priority, "")


# ============================================
# ИКОНКИ UI
# ============================================

class Icons:
    """Иконки для UI элементов"""

    PRIORITY = {
        'Высокий': '🔴',
        'Средний': '🟡',
        'Низкий': '🟢'
    }

    STATUS = {
        'Активная': '⏳',
        'Выполнена': '✅',
        'Новая': '📝',
        'В работе': '🔄',
        'Отложена': '⏸',
        'Отменена': '❌'
    }


# ============================================
# ЦВЕТА СТАТУСОВ
# ============================================

class StatusColors:
    """Цвета для разных статусов"""

    COLORS = {
        'Активная': '#17a2b8',
        'Выполнена': '#28a745',
        'Новая': '#007bff',
        'В работе': '#17a2b8',
        'Отложена': '#6c757d',
        'Отменена': '#dc3545'
    }


# ============================================
# ЭКСПОРТ
# ============================================

__all__ = [
    'Colors',
    'Fonts',
    'Sizes',
    'TableView',
    'Limits',
    'UISettings',
    'TaskPriorities',
    'Validation',
    'Icons',
    'StatusColors',
    'get_priority_icon',
]
