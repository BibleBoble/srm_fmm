# -*- coding: utf-8 -*-
"""
Singleton класс для работы с базой данных
Версия: 2.0 (исправлены критические ошибки)
"""
import sqlite3
import logging
from pathlib import Path
from threading import Lock
from typing import Optional, List, Dict, Any, Tuple


class DatabaseError(Exception):
    """Базовое исключение для ошибок БД"""
    pass


class Database:
    """
    Единственный экземпляр для работы с SQLite БД.
    Автоматически создаёт таблицы при первом запуске.
    
    Improvements:
    - Исправлено дублирование таблицы experts
    - Добавлен thread-safety через Lock
    - Добавлено логирование
    - Типизация методов
    - Централизованная обработка ошибок
    """

    _instance: Optional['Database'] = None
    _connection: Optional[sqlite3.Connection] = None
    _lock = Lock()  # Для thread-safety

    def __new__(cls, db_path: str = "database.db") -> 'Database':
        """Реализация паттерна Singleton с thread-safety"""
        if cls._instance is None:
            with cls._lock:
                # Двойная проверка для thread-safety
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.db_path = db_path
                    cls._instance.logger = cls._setup_logger()
                    cls._instance._connect()
        return cls._instance

    @staticmethod
    def _setup_logger() -> logging.Logger:
        """Настройка логгера для БД"""
        logger = logging.getLogger('SRM.Database')
        logger.setLevel(logging.INFO)
        
        # Создаем директорию для логов если её нет
        Path('logs').mkdir(exist_ok=True)
        
        # Файловый handler
        fh = logging.FileHandler('logs/database.log', encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # Консольный handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        
        # Форматирование
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger

    def _connect(self) -> None:
        """Подключение к базе данных"""
        try:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # ВНИМАНИЕ: используйте Lock при многопоточности!
                timeout=10.0  # Таймаут ожидания блокировки БД
            )
            
            # Включаем доступ к столбцам по именам
            self._connection.row_factory = sqlite3.Row
            
            # Включаем внешние ключи (для связей между таблицами)
            self._connection.execute("PRAGMA foreign_keys = ON")
            
            # Оптимизация производительности
            self._connection.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
            self._connection.execute("PRAGMA synchronous = NORMAL")
            
            self.logger.info(f"Подключение к БД '{self.db_path}' установлено")
            print(f"✓ Подключение к БД '{self.db_path}' установлено")
            
            # Создаём таблицы, если их нет
            self._create_tables()
            
        except sqlite3.Error as e:
            error_msg = f"Ошибка подключения к БД: {e}"
            self.logger.error(error_msg)
            print(f"✗ {error_msg}")
            raise DatabaseError(error_msg) from e

    def _create_tables(self) -> None:
        """Создание всех таблиц"""
        cursor = self._connection.cursor()
        
        try:
            # ============================================
            # ТАБЛИЦА 1: КЛИЕНТЫ (компании)
            # ============================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    address TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # ============================================
            # ТАБЛИЦА 2: КОНТАКТНЫЕ ЛИЦА КЛИЕНТОВ
            # ============================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contact_persons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    full_name TEXT NOT NULL,
                    position TEXT,
                    phone TEXT,
                    is_primary INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                )
            """)
            
            # ============================================
            # ТАБЛИЦА 3: EMAIL КОНТАКТНЫХ ЛИЦ
            # (Изменена структура: email привязаны к контактам, а не к клиентам)
            # ============================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contact_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_person_id INTEGER NOT NULL,
                    email TEXT NOT NULL,
                    is_primary INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contact_person_id) REFERENCES contact_persons(id) ON DELETE CASCADE
                )
            """)
            
            # ============================================
            # ТАБЛИЦА 4: ИСТОРИЯ ВЗАИМОДЕЙСТВИЙ С КЛИЕНТАМИ
            # ============================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interaction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                )
            """)
            
            # ============================================
            # ТАБЛИЦА 5: ДОГОВОРА
            # ============================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    number TEXT NOT NULL UNIQUE,
                    date DATE NOT NULL,
                    amount REAL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
                )
            """)
            
            # ============================================
            # ТАБЛИЦА 6: ЗАДАЧИ
            # ============================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date DATE,
                    completed INTEGER DEFAULT 0,
                    priority TEXT DEFAULT 'Средний',
                    client_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
                )
            """)
            
            # ============================================
            # ТАБЛИЦА 7: ЭКСПЕРТЫ
            # (ИСПРАВЛЕНО: убрано дублирование!)
            # ============================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # ============================================
            # ТАБЛИЦА 8: КОНТАКТНЫЕ ЛИЦА ЭКСПЕРТОВ
            # ============================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expert_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expert_id INTEGER NOT NULL,
                    full_name TEXT NOT NULL,
                    position TEXT,
                    phone TEXT,
                    email TEXT,
                    is_primary INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (expert_id) REFERENCES experts(id) ON DELETE CASCADE
                )
            """)
            
            # ============================================
            # ТАБЛИЦА 9: СПЕЦИАЛИЗАЦИИ ЭКСПЕРТОВ
            # ============================================
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expert_specializations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expert_id INTEGER NOT NULL,
                    specialization TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (expert_id) REFERENCES experts(id) ON DELETE CASCADE,
                    UNIQUE(expert_id, specialization)
                )
            """)
            
            # ============================================
            # ИНДЕКСЫ ДЛЯ УСКОРЕНИЯ ПОИСКА
            # ============================================
            
            # Индексы для клиентов
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_company ON clients(company)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_search ON clients(company, address)")
            
            # Индексы для задач
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_client ON tasks(client_id)")
            
            # Индексы для договоров
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_client ON contracts(client_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_date ON contracts(date)")
            
            # Индексы для контактных лиц
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contact_persons_client ON contact_persons(client_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contact_persons_primary ON contact_persons(client_id, is_primary)")
            
            # Индексы для email
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contact_emails_person ON contact_emails(contact_person_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_contact_emails_primary ON contact_emails(contact_person_id, is_primary)")
            
            # Индексы для истории взаимодействий
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_client ON interaction_history(client_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_date ON interaction_history(date)")
            
            # Индексы для экспертов
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_experts_name ON experts(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expert_contacts_expert ON expert_contacts(expert_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expert_contacts_primary ON expert_contacts(expert_id, is_primary)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expert_specializations_expert ON expert_specializations(expert_id)")
            
            self._connection.commit()
            self.logger.info("Таблицы и индексы созданы/проверены")
            print("✓ Таблицы созданы/проверены")
            
        except sqlite3.Error as e:
            error_msg = f"Ошибка создания таблиц: {e}"
            self.logger.error(error_msg)
            print(f"✗ {error_msg}")
            raise DatabaseError(error_msg) from e

    def execute(self, query: str, params: Tuple = ()) -> Optional[int]:
        """
        Выполняет запрос на изменение (INSERT, UPDATE, DELETE)
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            
        Returns:
            ID последней вставленной строки или None при ошибке
        """
        with self._lock:  # Thread-safety
            try:
                cursor = self._connection.cursor()
                cursor.execute(query, params)
                self._connection.commit()
                
                # Логируем только важные операции
                if query.strip().upper().startswith(('INSERT', 'DELETE')):
                    self.logger.info(f"Выполнен запрос: {query[:50]}...")
                
                return cursor.lastrowid
                
            except sqlite3.Error as e:
                error_msg = f"ОШИБКА SQL: {e}\nЗапрос: {query}\nПараметры: {params}"
                self.logger.error(error_msg)
                print(f"❌ {error_msg}")
                
                self._connection.rollback()
                return None

    def fetch_all(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """
        Получить все записи
        
        Args:
            query: SQL запрос SELECT
            params: Параметры запроса
            
        Returns:
            Список записей (sqlite3.Row)
        """
        with self._lock:  # Thread-safety
            try:
                cursor = self._connection.cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                self.logger.debug(f"Получено {len(results)} записей")
                return results
                
            except sqlite3.Error as e:
                error_msg = f"Ошибка получения данных: {e}\nЗапрос: {query}"
                self.logger.error(error_msg)
                print(f"✗ {error_msg}")
                return []

    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """
        Получить одну запись
        
        Args:
            query: SQL запрос SELECT
            params: Параметры запроса
            
        Returns:
            sqlite3.Row или None
        """
        with self._lock:  # Thread-safety
            try:
                cursor = self._connection.cursor()
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                self.logger.debug(f"Получена запись: {bool(result)}")
                return result
                
            except sqlite3.Error as e:
                error_msg = f"Ошибка получения данных: {e}\nЗапрос: {query}"
                self.logger.error(error_msg)
                print(f"✗ {error_msg}")
                return None

    def execute_many(self, query: str, params_list: List[Tuple]) -> bool:
        """
        Выполнить множественную вставку (batch insert)
        
        Args:
            query: SQL запрос
            params_list: Список кортежей с параметрами
            
        Returns:
            True если успешно, False при ошибке
        """
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.executemany(query, params_list)
                self._connection.commit()
                
                self.logger.info(f"Batch insert: {len(params_list)} записей")
                return True
                
            except sqlite3.Error as e:
                error_msg = f"Ошибка batch insert: {e}"
                self.logger.error(error_msg)
                print(f"❌ {error_msg}")
                
                self._connection.rollback()
                return False

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Получить информацию о структуре таблицы
        
        Args:
            table_name: Название таблицы
            
        Returns:
            Список словарей с информацией о колонках
        """
        query = f"PRAGMA table_info({table_name})"
        rows = self.fetch_all(query)
        
        return [
            {
                'cid': row['cid'],
                'name': row['name'],
                'type': row['type'],
                'notnull': bool(row['notnull']),
                'default_value': row['dflt_value'],
                'primary_key': bool(row['pk'])
            }
            for row in rows
        ]

    def get_all_tables(self) -> List[str]:
        """
        Получить список всех таблиц в БД
        
        Returns:
            Список названий таблиц
        """
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        rows = self.fetch_all(query)
        return [row['name'] for row in rows]

    def vacuum(self) -> bool:
        """
        Оптимизация БД (очистка неиспользуемого пространства)
        
        Returns:
            True если успешно
        """
        with self._lock:
            try:
                self._connection.execute("VACUUM")
                self.logger.info("БД оптимизирована (VACUUM)")
                print("✓ БД оптимизирована")
                return True
            except sqlite3.Error as e:
                error_msg = f"Ошибка VACUUM: {e}"
                self.logger.error(error_msg)
                print(f"✗ {error_msg}")
                return False

    def backup(self, backup_path: str) -> bool:
        """
        Создать резервную копию БД
        
        Args:
            backup_path: Путь к файлу резервной копии
            
        Returns:
            True если успешно
        """
        with self._lock:
            try:
                backup_conn = sqlite3.connect(backup_path)
                self._connection.backup(backup_conn)
                backup_conn.close()
                
                self.logger.info(f"Создана резервная копия: {backup_path}")
                print(f"✓ Создана резервная копия: {backup_path}")
                return True
                
            except sqlite3.Error as e:
                error_msg = f"Ошибка создания резервной копии: {e}"
                self.logger.error(error_msg)
                print(f"✗ {error_msg}")
                return False

    def close(self) -> None:
        """Закрыть соединение с БД"""
        if self._connection:
            self._connection.close()
            self.logger.info("Соединение с БД закрыто")
            print("✓ Соединение с БД закрыто")
            
            # Сбрасываем singleton для возможности переподключения
            Database._instance = None
            Database._connection = None

    def __enter__(self):
        """Поддержка context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие при выходе из context manager"""
        if exc_type is not None:
            self.logger.error(f"Ошибка в context manager: {exc_val}")
            self._connection.rollback()
        self.close()

    def __repr__(self) -> str:
        """Строковое представление объекта"""
        return f"Database(path='{self.db_path}', connected={self._connection is not None})"


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def get_db_stats(db: Database) -> Dict[str, Any]:
    """
    Получить статистику БД
    
    Args:
        db: Экземпляр Database
        
    Returns:
        Словарь со статистикой
    """
    stats = {
        'tables': {},
        'total_records': 0
    }
    
    tables = db.get_all_tables()
    for table in tables:
        count_query = f"SELECT COUNT(*) as count FROM {table}"
        result = db.fetch_one(count_query)
        count = result['count'] if result else 0
        
        stats['tables'][table] = count
        stats['total_records'] += count
    
    return stats


def print_db_info(db: Database) -> None:
    """
    Вывести информацию о БД в консоль
    
    Args:
        db: Экземпляр Database
    """
    print("\n" + "=" * 50)
    print("ИНФОРМАЦИЯ О БАЗЕ ДАННЫХ")
    print("=" * 50)
    print(f"Путь: {db.db_path}")
    print(f"Подключение: {'✓ Активно' if db._connection else '✗ Не подключено'}")
    
    stats = get_db_stats(db)
    print(f"\nВсего записей: {stats['total_records']}")
    print("\nТаблицы:")
    
    for table, count in sorted(stats['tables'].items()):
        print(f"  • {table:30} {count:>6} записей")
    
    print("=" * 50 + "\n")


# ============================================
# ТЕСТИРОВАНИЕ (если запущен напрямую)
# ============================================

if __name__ == "__main__":
    # Тестирование Database
    print("Тестирование Database...")
    
    # Создаем тестовую БД
    db = Database("test_database.db")
    
    # Выводим информацию
    print_db_info(db)
    
    # Тестируем вставку
    client_id = db.execute(
        "INSERT INTO clients (company, address) VALUES (?, ?)",
        ("Тестовая компания", "Тестовый адрес")
    )
    print(f"✓ Добавлен клиент с ID: {client_id}")
    
    # Тестируем выборку
    clients = db.fetch_all("SELECT * FROM clients")
    print(f"✓ Найдено клиентов: {len(clients)}")
    
    # Тестируем информацию о таблице
    table_info = db.get_table_info('clients')
    print(f"✓ Структура таблицы clients: {len(table_info)} колонок")
    
    # Создаем резервную копию
    db.backup("test_backup.db")
    
    # Закрываем
    db.close()
    
    print("\n✓ Все тесты пройдены!")