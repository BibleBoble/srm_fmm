"""
Singleton класс для работы с базой данных
"""
import sqlite3
import os


class Database:
    """
    Единственный экземпляр для работы с SQLite БД.
    Автоматически создаёт таблицы при первом запуске.
    """

    _instance = None
    _connection = None

    def __new__(cls, db_path="database.db"):
        """Реализация паттерна Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db_path = db_path
            cls._instance._connect()
        return cls._instance

    def _connect(self):
        """Подключение к базе данных"""
        try:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False  # для работы в многопоточности
            )
            # Включаем доступ к столбцам по именам
            self._connection.row_factory = sqlite3.Row

            # Включаем внешние ключи (для связей между таблицами)
            self._connection.execute("PRAGMA foreign_keys = ON")

            print(f"✓ Подключение к БД '{self.db_path}' установлено")

            # Создаём таблицы, если их нет
            self._create_tables()

        except sqlite3.Error as e:
            print(f"✗ Ошибка подключения к БД: {e}")
            raise

    def _create_tables(self):
        """Создание всех таблиц"""
        cursor = self._connection.cursor()

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
        # ТАБЛИЦА 2: КОНТАКТНЫЕ ЛИЦА
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
        # ТАБЛИЦА 3: EMAIL КЛИЕНТОВ
        # ============================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                is_primary INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        """)

        # ============================================
        # ТАБЛИЦА 4: ИСТОРИЯ ВЗАИМОДЕЙСТВИЙ
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
        # ОСТАЛЬНЫЕ ТАБЛИЦЫ (договора, задачи, эксперты)
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date DATE,
                completed INTEGER DEFAULT 0,
                client_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT,
                phone TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'Средний'")
            print("✓ Добавлена колонка 'priority' в таблицу tasks")
        except:
            pass  # Колонка уже существует, всё в порядке
        # ---------------------

        self._connection.commit()
        print("✓ Таблицы созданы/проверены")

    def execute(self, query, params=()):
        """
        Выполнить SQL-запрос (INSERT, UPDATE, DELETE).

        Args:
            query: str - SQL запрос
            params: tuple - параметры запроса

        Returns:
            int - ID последней вставленной записи (для INSERT)
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, params)
            self._connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"✗ Ошибка выполнения запроса: {e}")
            self._connection.rollback()
            raise

    def fetch_all(self, query, params=()):
        """
        Получить все записи.

        Args:
            query: str - SQL запрос SELECT
            params: tuple - параметры запроса

        Returns:
            list - список записей (sqlite3.Row)
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"✗ Ошибка получения данных: {e}")
            return []

    def fetch_one(self, query, params=()):
        """
        Получить одну запись.

        Args:
            query: str - SQL запрос SELECT
            params: tuple - параметры запроса

        Returns:
            sqlite3.Row или None
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"✗ Ошибка получения данных: {e}")
            return None

    def close(self):
        """Закрыть соединение с БД"""
        if self._connection:
            self._connection.close()
            print("✓ Соединение с БД закрыто")