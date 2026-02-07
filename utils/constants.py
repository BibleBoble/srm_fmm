# -*- coding: utf-8 -*-
"""
Константы приложения SRM FMM
"""
from pathlib import Path


# ============================================
# ПУТИ
# ============================================

class Paths:
    """Пути к файлам и директориям"""

    BASE_DIR = Path(__file__).parent
    DB_PATH = BASE_DIR / "database.db"
    LOGS_DIR = BASE_DIR / "logs"
    BACKUPS_DIR = BASE_DIR / "backups"

    # Создаем директории если их нет
    LOGS_DIR.mkdir(exist_ok=True)
    BACKUPS_DIR.mkdir(exist_ok=True)

    @classmethod
    def get_db_path(cls) -> str:
        """Получить путь к БД в виде строки"""
        return str(cls.DB_PATH)


# ============================================
# ЦВЕТА UI
# ============================================

class Colors:
    """Цветовая схема интерфейса"""

    # Основные цвета
    PRIMARY = "#41a5be"  # Бирюзовый (кнопки, акценты)
    DARK = "#333333"  # Темный (заголовки, меню)
    LIGHT = "#f0f0f0"  # Светлый фон
    WHITE = "#ffffff"  # Белый

    # Цвета состояний
    SUCCESS = "#4CAF50"  # Зеленый (успех)
    DANGER = "#d9534f"  # Красный (опасность, удаление)
    WARNING = "#FF9800"  # Оранжевый (предупреждение)
    INFO = "#2196F3"  # Синий (информация)

    # Дополнительные
    GRAY = "#6c757d"  # Серый (отмена, неактивные элементы)
    GRAY_LIGHT = "#f8f9fa"  # Светло-серый (фон карточек)
    GRAY_BORDER = "#ccc"  # Серый для границ

    # Специальные
    OVERDUE = "#fee2e2"  # Фон для просроченных задач
    HOVER = "#e8f4f8"  # Фон при наведении


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
    MENU_HEIGHT = 50
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
    TABLE_ROW_HEIGHT = 40
    TABLE_MAX_ROWS = 25
    TABLE_VISIBLE_ROWS = 25  # Высота Treeview в строках

    # Верхняя панель разделов (поиск, кнопки)
    TOP_PANEL_HEIGHT = 70
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
    TOP_PANEL_BG = "#f0f0f0"
    TABLE_BG = "#ffffff"
    ROW_EVEN = "#f8f9fa"
    ROW_ODD = "#ffffff"
    ROW_HOVER = "#e8f4f8"
    HEADING_BG = "#333333"
    HEADING_FG = "#ffffff"
    HEADING_ACTIVE = "#444444"
    BUTTON_BG = "#41a5be"
    BUTTON_FG = "black"
    LABEL_FG = "#333"
    HINT_FG = "#666"
    PAGINATION_BG = "#f0f0f0"
    PAGINATION_BUTTON_BG = "#41a5be"
    PAGINATION_BUTTON_DISABLED = "#cccccc"

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
# НАСТРОЙКИ БД
# ============================================

class DBSettings:
    """Настройки базы данных"""

    # Подключение
    CHECK_SAME_THREAD = False  # ⚠️ ОСТОРОЖНО с многопоточностью!
    TIMEOUT = 10.0  # Таймаут блокировки (сек)

    # Оптимизация
    JOURNAL_MODE = "WAL"  # Write-Ahead Logging
    SYNCHRONOUS = "NORMAL"  # Уровень синхронизации

    # Резервное копирование
    AUTO_BACKUP = True  # Автоматическое резервное копирование
    BACKUP_FREQUENCY_DAYS = 7  # Частота создания бэкапов (дни)
    MAX_BACKUPS = 5  # Максимальное количество хранимых бэкапов


# ============================================
# ТИПЫ ВЗАИМОДЕЙСТВИЙ
# ============================================

class InteractionTypes:
    """Типы взаимодействий с клиентами"""

    CALL = "Звонок"
    KP_SENT = "Отправлено КП"
    WORK_STARTED = "Запуск работы"
    WORK_COMPLETED = "Работа выполнена"
    MEETING = "Встреча"
    EMAIL = "Email"

    ALL = [CALL, KP_SENT, WORK_STARTED, WORK_COMPLETED, MEETING, EMAIL]

    # Иконки для типов
    ICONS = {
        CALL: "📞",
        KP_SENT: "📄",
        WORK_STARTED: "🚀",
        WORK_COMPLETED: "✅",
        MEETING: "🤝",
        EMAIL: "📧"
    }


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
# СТАТУСЫ ДОГОВОРОВ
# ============================================

class ContractStatuses:
    """Статусы договоров"""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    ALL = [ACTIVE, COMPLETED, CANCELLED]

    # Русские названия
    LABELS = {
        ACTIVE: "Активный",
        COMPLETED: "Завершен",
        CANCELLED: "Отменен"
    }


# ============================================
# СООБЩЕНИЯ
# ============================================

class Messages:
    """Стандартные сообщения приложения"""

    # Успех
    SUCCESS_SAVED = "Данные успешно сохранены"
    SUCCESS_DELETED = "Запись удалена"
    SUCCESS_UPDATED = "Данные обновлены"

    # Ошибки
    ERROR_REQUIRED_FIELD = "Заполните обязательные поля"
    ERROR_INVALID_EMAIL = "Некорректный формат email"
    ERROR_INVALID_PHONE = "Некорректный формат телефона"
    ERROR_DATABASE = "Ошибка базы данных"
    ERROR_NOT_FOUND = "Запись не найдена"

    # Предупреждения
    WARNING_LIMIT_REACHED = "Достигнут лимит записей"
    WARNING_DUPLICATE = "Такая запись уже существует"

    # Подтверждения
    CONFIRM_DELETE = "Вы действительно хотите удалить?"
    CONFIRM_EXIT = "Вы действительно хотите выйти?"


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


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def get_interaction_icon(interaction_type: str) -> str:
    """
    Получить иконку для типа взаимодействия

    Args:
        interaction_type: Тип взаимодействия

    Returns:
        Иконка (emoji) или пустую строку
    """
    return InteractionTypes.ICONS.get(interaction_type, "📌")


def get_priority_icon(priority: str) -> str:
    """
    Получить иконку для приоритета

    Args:
        priority: Приоритет

    Returns:
        Иконка (emoji) или пустую строку
    """
    return TaskPriorities.ICONS.get(priority, "")


def get_priority_color(priority: str) -> str:
    """
    Получить цвет для приоритета

    Args:
        priority: Приоритет

    Returns:
        Цвет в формате hex
    """
    return TaskPriorities.COLORS.get(priority, Colors.PRIMARY)


# ============================================
# ЭКСПОРТ
# ============================================

__all__ = [
    'Paths',
    'Colors',
    'Fonts',
    'Sizes',
    'TableView',
    'Limits',
    'UISettings',
    'DBSettings',
    'InteractionTypes',
    'TaskPriorities',
    'ContractStatuses',
    'Messages',
    'Validation',
    'get_interaction_icon',
    'get_priority_icon',
    'get_priority_color'
]

# ============================================
# ТЕСТИРОВАНИЕ
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("КОНСТАНТЫ ПРИЛОЖЕНИЯ SRM FMM")
    print("=" * 50)

    print(f"\n📁 Пути:")
    print(f"  • База данных: {Paths.get_db_path()}")
    print(f"  • Логи: {Paths.LOGS_DIR}")
    print(f"  • Бэкапы: {Paths.BACKUPS_DIR}")

    print(f"\n🎨 Цвета:")
    print(f"  • Основной: {Colors.PRIMARY}")
    print(f"  • Успех: {Colors.SUCCESS}")
    print(f"  • Опасность: {Colors.DANGER}")

    print(f"\n📏 Размеры:")
    print(f"  • Окно: {Sizes.WINDOW_WIDTH}x{Sizes.WINDOW_HEIGHT}")
    print(f"  • Диалог: {Sizes.DIALOG_MEDIUM_WIDTH}x{Sizes.DIALOG_MEDIUM_HEIGHT}")

    print(f"\n🔢 Лимиты:")
    print(f"  • Контактов на клиента: {Limits.MAX_CONTACTS_PER_CLIENT}")
    print(f"  • Email на контакт: {Limits.MAX_EMAILS_PER_CONTACT}")

    print(f"\n✅ Типы взаимодействий:")
    for itype in InteractionTypes.ALL:
        icon = get_interaction_icon(itype)
        print(f"  • {icon} {itype}")

    print(f"\n⚡ Приоритеты:")
    for priority in TaskPriorities.ALL:
        icon = get_priority_icon(priority)
        color = get_priority_color(priority)
        print(f"  • {icon} {priority} ({color})")

    print("\n" + "=" * 50)