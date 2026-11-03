# -*- coding: utf-8 -*-
"""
Тесты для карточки клиента
Проверка CRUD операций для таблиц: клиенты, контакты, задачи
"""
import unittest
import tkinter as tk
from tkinter import ttk
import sys
import os
import tempfile

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from managers.database import Database
from managers.clients_manager import ClientsManager
from managers.contact_persons_manager import ContactPersonsManager
from managers.contact_emails_manager import ContactEmailsManager
from managers.tasks_manager import TasksManager
from managers.interactions_manager import InteractionsManager
from services.client_service import ClientService
from services.task_service import TaskService


class TestClientCardCRUD(unittest.TestCase):
    """Тесты CRUD операций для карточки клиента"""
    
    @classmethod
    def setUpClass(cls):
        """Настройка тестовой базы данных"""
        # Создаём временную БД
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix='.db')
        
        # Инициализируем Database с тестовой БД
        Database._instance = None
        cls.db = Database(cls.db_path)
        cls._create_tables()
    
    @classmethod
    def tearDownClass(cls):
        """Очистка после тестов"""
        # Закрываем соединение с БД перед удалением файла
        if hasattr(cls.db, '_connection') and cls.db._connection:
            try:
                cls.db._connection.close()
            except:
                pass
        
        # Сбрасываем singleton
        cls.db._instance = None
        cls.db._connection = None
        Database._instance = None
        Database._connection = None
        
        os.close(cls.db_fd)
        
        # Удаляем файл (может не сработать на Windows, если файл занят)
        try:
            os.unlink(cls.db_path)
        except PermissionError:
            pass  # Файл может быть занят другим процессом
    
    @classmethod
    def _create_tables(cls):
        """Создание таблиц для тестов"""
        cursor = cls.db._connection.cursor()
        
        # Таблица клиентов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                address TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица контактных лиц
        cursor.execute('''
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
        ''')
        
        # Таблица email
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_person_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                is_primary INTEGER DEFAULT 0,
                FOREIGN KEY (contact_person_id) REFERENCES contact_persons(id) ON DELETE CASCADE
            )
        ''')
        
        # Таблица задач
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                completed INTEGER DEFAULT 0,
                priority TEXT DEFAULT 'Средний',
                client_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        ''')
        
        # Таблица взаимодействий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                date DATE NOT NULL,
                type_interaction TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        ''')
        
        cls.db._connection.commit()
    
    def setUp(self):
        """Подготовка перед каждым тестом"""
        # Очищаем таблицы
        cursor = self.db._connection.cursor()
        cursor.execute("DELETE FROM interaction_history")
        cursor.execute("DELETE FROM contact_emails")
        cursor.execute("DELETE FROM contact_persons")
        cursor.execute("DELETE FROM tasks")
        cursor.execute("DELETE FROM clients")
        self.db._connection.commit()
        
        # Создаём менеджеры
        self.clients_mgr = ClientsManager()
        self.contact_persons_mgr = ContactPersonsManager()
        self.contact_emails_mgr = ContactEmailsManager()
        self.tasks_mgr = TasksManager()
        self.interactions_mgr = InteractionsManager()
        
        # Создаём сервисы
        self.client_service = ClientService(
            self.clients_mgr,
            self.contact_persons_mgr,
            self.contact_emails_mgr,
            self.interactions_mgr
        )
        self.task_service = TaskService(self.tasks_mgr, self.clients_mgr)
    
    # ==================== ТЕСТЫ КЛИЕНТОВ ====================
    
    def test_create_client(self):
        """Тест создания клиента"""
        client_data = {
            'company': 'ООО "Тест"',
            'address': 'г. Москва, ул. Тестовая, 1',
            'notes': 'Тестовые заметки',
            'contacts': [
                {
                    'full_name': 'Тестовый Контакт',
                    'position': 'Менеджер',
                    'phone': '+7 (999) 000-00-00',
                    'email': 'test@test.com',
                    'is_primary': True
                }
            ]
        }
        
        client_id = self.client_service.create_client_with_contacts(client_data)
        
        self.assertIsNotNone(client_id)
        self.assertIsInstance(client_id, int)
        
        # Проверяем, что клиент создан
        client = self.clients_mgr.get_by_id(client_id)
        self.assertIsNotNone(client)
        self.assertEqual(client['company'], 'ООО "Тест"')
        self.assertEqual(client['address'], 'г. Москва, ул. Тестовая, 1')
    
    def test_create_client_with_contacts(self):
        """Тест создания клиента с контактами"""
        client_data = {
            'company': 'ООО "Тест с контактами"',
            'address': 'г. Москва',
            'notes': '',
            'contacts': [
                {
                    'full_name': 'Иванов Иван Иванович',
                    'position': 'Директор',
                    'phone': '+7 (999) 123-45-67',
                    'email': 'ivanov@test.com',
                    'is_primary': True
                },
                {
                    'full_name': 'Петров Петр Петрович',
                    'position': 'Менеджер',
                    'phone': '+7 (999) 987-65-43',
                    'email': 'petrov@test.com',
                    'is_primary': False
                }
            ]
        }
        
        client_id = self.client_service.create_client_with_contacts(client_data)
        
        # Проверяем клиента
        client = self.clients_mgr.get_by_id(client_id)
        self.assertIsNotNone(client)
        
        # Проверяем контакты
        contacts = self.contact_persons_mgr.get_by_client(client_id)
        self.assertEqual(len(contacts), 2)
        
        # Проверяем основной контакт
        primary = self.contact_persons_mgr.get_primary(client_id)
        self.assertIsNotNone(primary)
        self.assertEqual(primary['full_name'], 'Иванов Иван Иванович')
    
    def test_read_client(self):
        """Тест чтения данных клиента"""
        # Создаём клиента
        client_id = self.clients_mgr.add(
            company='ООО "Чтение"',
            address='г. СПб',
            notes='Тест чтения'
        )
        
        # Читаем
        client = self.clients_mgr.get_by_id(client_id)
        
        self.assertIsNotNone(client)
        self.assertEqual(client['company'], 'ООО "Чтение"')
        self.assertEqual(client['address'], 'г. СПб')
    
    def test_update_client(self):
        """Тест обновления клиента"""
        # Создаём клиента
        client_id = self.clients_mgr.add(
            company='ООО "Старое название"',
            address='г. Москва',
            notes=''
        )
        
        # Обновляем
        self.clients_mgr.update(
            client_id,
            company='ООО "Новое название"',
            address='г. Казань',
            notes='Обновлённые заметки'
        )
        
        # Проверяем
        client = self.clients_mgr.get_by_id(client_id)
        self.assertEqual(client['company'], 'ООО "Новое название"')
        self.assertEqual(client['address'], 'г. Казань')
    
    def test_delete_client(self):
        """Тест удаления клиента (каскадное)"""
        # Создаём клиента с контактами и задачами
        client_data = {
            'company': 'ООО "На удаление"',
            'address': '',
            'notes': '',
            'contacts': [
                {
                    'full_name': 'Удаляемый Контакт',
                    'position': '',
                    'phone': '',
                    'email': 'delete@test.com',
                    'is_primary': True
                }
            ]
        }
        
        client_id = self.client_service.create_client_with_contacts(client_data)
        
        # Добавляем задачу
        self.tasks_mgr.add(
            title='Задача для удаления',
            client_id=client_id
        )
        
        # Удаляем клиента
        self.clients_mgr.delete(client_id)
        
        # Проверяем, что всё удалено
        self.assertIsNone(self.clients_mgr.get_by_id(client_id))
        contacts = self.contact_persons_mgr.get_by_client(client_id)
        self.assertEqual(len(contacts), 0)
    
    # ==================== ТЕСТЫ КОНТАКТОВ ====================
    
    def test_create_contact(self):
        """Тест создания контактного лица"""
        # Создаём клиента
        client_id = self.clients_mgr.add(company='Тестовый клиент')
        
        # Создаём контакт
        contact_id = self.contact_persons_mgr.add(
            client_id=client_id,
            full_name='Сидоров Сидор Сидорович',
            position='Бухгалтер',
            phone='+7 (111) 222-33-44',
            is_primary=True
        )
        
        self.assertIsNotNone(contact_id)
        
        # Проверяем
        contact = self.contact_persons_mgr.get_by_id(contact_id)
        self.assertEqual(contact['full_name'], 'Сидоров Сидор Сидорович')
        self.assertEqual(contact['position'], 'Бухгалтер')
    
    def test_update_contact(self):
        """Тест обновления контакта"""
        client_id = self.clients_mgr.add(company='Клиент')
        contact_id = self.contact_persons_mgr.add(
            client_id=client_id,
            full_name='Старое Имя',
            position='Старая должность',
            phone='',
            is_primary=False
        )
        
        # Обновляем
        self.contact_persons_mgr.update(
            contact_id,
            full_name='Новое Имя',
            position='Новая должность',
            phone='+7 (999) 000-00-00',
            is_primary=True
        )
        
        # Проверяем
        contact = self.contact_persons_mgr.get_by_id(contact_id)
        self.assertEqual(contact['full_name'], 'Новое Имя')
        self.assertEqual(contact['is_primary'], 1)
    
    def test_delete_contact(self):
        """Тест удаления контакта"""
        client_id = self.clients_mgr.add(company='Клиент')
        contact_id = self.contact_persons_mgr.add(
            client_id=client_id,
            full_name='Удаляемый',
            position='',
            phone='',
            is_primary=False
        )
        
        # Удаляем
        self.contact_persons_mgr.delete(contact_id)
        
        # Проверяем
        self.assertIsNone(self.contact_persons_mgr.get_by_id(contact_id))
    
    def test_contact_email_crud(self):
        """Тест CRUD email контакта"""
        client_id = self.clients_mgr.add(company='Клиент')
        contact_id = self.contact_persons_mgr.add(
            client_id=client_id,
            full_name='Контакт с email',
            position='',
            phone='',
            is_primary=False
        )
        
        # Создание
        email_id = self.contact_emails_mgr.add(
            contact_person_id=contact_id,
            email='test@example.com',
            is_primary=True
        )
        self.assertIsNotNone(email_id)
        
        # Чтение
        emails = self.contact_emails_mgr.get_by_contact(contact_id)
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0]['email'], 'test@example.com')
        
        # Обновление
        self.contact_emails_mgr.update(email_id, 'new@example.com', is_primary=True)
        emails = self.contact_emails_mgr.get_by_contact(contact_id)
        self.assertEqual(emails[0]['email'], 'new@example.com')
        
        # Удаление
        self.contact_emails_mgr.delete(email_id)
        emails = self.contact_emails_mgr.get_by_contact(contact_id)
        self.assertEqual(len(emails), 0)
    
    # ==================== ТЕСТЫ ЗАДАЧ ====================
    
    def test_create_task(self):
        """Тест создания задачи"""
        client_id = self.clients_mgr.add(company='Клиент с задачей')
        
        task_data = {
            'title': 'Тестовая задача',
            'description': 'Описание задачи',
            'client_id': client_id,
            'priority': 'Высокий',
            'due_date': '25.12.2025'
        }
        
        task_id = self.task_service.create_task(task_data)
        
        self.assertIsNotNone(task_id)
        
        # Проверяем
        task = self.tasks_mgr.get_by_id(task_id)
        self.assertEqual(task.title, 'Тестовая задача')
        self.assertEqual(task.priority, 'Высокий')
    
    def test_read_task(self):
        """Тест чтения задачи"""
        client_id = self.clients_mgr.add(company='Клиент')
        
        task_id = self.tasks_mgr.add(
            title='Задача для чтения',
            description='Описание',
            due_date='01.01.2025',
            client_id=client_id,
            priority='Средний'
        )
        
        task = self.tasks_mgr.get_by_id(task_id)
        
        self.assertIsNotNone(task)
        self.assertEqual(task.title, 'Задача для чтения')
    
    def test_update_task(self):
        """Тест обновления задачи"""
        client_id = self.clients_mgr.add(company='Клиент')
        
        task_id = self.tasks_mgr.add(
            title='Старое название',
            description='Старое описание',
            due_date='01.01.2025',
            client_id=client_id,
            priority='Низкий'
        )
        
        # Обновляем через сервис
        task_data = {
            'title': 'Новое название',
            'description': 'Новое описание',
            'status': 'Выполнена',
            'priority': 'Высокий',
            'due_date': '31.12.2025',
            'client_id': client_id
        }
        
        self.task_service.update_task(task_id, task_data)
        
        # Проверяем
        task = self.tasks_mgr.get_by_id(task_id)
        self.assertEqual(task.title, 'Новое название')
        self.assertEqual(task.priority, 'Высокий')
    
    def test_delete_task(self):
        """Тест удаления задачи"""
        client_id = self.clients_mgr.add(company='Клиент')
        
        task_id = self.tasks_mgr.add(
            title='Задача на удаление',
            client_id=client_id
        )
        
        # Удаляем
        self.tasks_mgr.delete(task_id)
        
        # Проверяем
        self.assertIsNone(self.tasks_mgr.get_by_id(task_id))
    
    def test_task_status_toggle(self):
        """Тест переключения статуса задачи"""
        client_id = self.clients_mgr.add(company='Клиент')
        
        task_id = self.tasks_mgr.add(
            title='Задача со статусом',
            client_id=client_id
        )
        
        # Переключаем статус
        new_status = self.task_service.toggle_task_status(task_id)
        
        self.assertEqual(new_status, 'Выполнена')
        
        # Проверяем в БД
        task = self.tasks_mgr.get_by_id(task_id)
        self.assertTrue(task.completed)
        
        # Переключаем обратно
        new_status = self.task_service.toggle_task_status(task_id)
        self.assertEqual(new_status, 'Активная')
    
    def test_get_tasks_for_client(self):
        """Тест получения задач клиента"""
        client_id = self.clients_mgr.add(company='Клиент с задачами')
        
        # Создаём несколько задач
        for i in range(3):
            self.tasks_mgr.add(
                title=f'Задача {i+1}',
                client_id=client_id
            )
        
        # Получаем задачи
        tasks = self.task_service.get_tasks_for_client(client_id)
        
        self.assertEqual(len(tasks), 3)
    
    # ==================== ИНТЕГРАЦИОННЫЕ ТЕСТЫ ====================
    
    def test_full_client_workflow(self):
        """Полный workflow: создание клиента → контакты → задачи → удаление"""
        # 1. Создаём клиента с контактами
        client_data = {
            'company': 'ООО "Полный цикл"',
            'address': 'г. Москва, Кремль',
            'notes': 'Важный клиент',
            'contacts': [
                {
                    'full_name': 'Генеральный Директор',
                    'position': 'CEO',
                    'phone': '+7 (999) 000-00-01',
                    'email': 'ceo@fullcycle.com',
                    'is_primary': True
                }
            ]
        }
        
        client_id = self.client_service.create_client_with_contacts(client_data)
        self.assertIsNotNone(client_id)
        
        # 2. Добавляем задачи
        for i in range(2):
            self.task_service.create_task({
                'title': f'Задача {i+1} для клиента',
                'description': f'Описание задачи {i+1}',
                'client_id': client_id,
                'priority': 'Высокий' if i == 0 else 'Средний',
                'due_date': f'0{i+1}.01.2025'
            })
        
        # 3. Проверяем, что всё создано
        self.assertIsNotNone(self.clients_mgr.get_by_id(client_id))
        self.assertEqual(len(self.contact_persons_mgr.get_by_client(client_id)), 1)
        self.assertEqual(len(self.task_service.get_tasks_for_client(client_id)), 2)
        
        # 4. Обновляем клиента
        self.client_service.update_client_with_contacts(client_id, {
            'company': 'ООО "Полный цикл (обновлённое)"',
            'address': 'г. СПб',
            'notes': 'Обновлённые заметки'
        })
        
        # 5. Проверяем обновление
        client = self.clients_mgr.get_by_id(client_id)
        self.assertEqual(client['company'], 'ООО "Полный цикл (обновлённое)"')
        
        # 6. Удаляем клиента
        self.clients_mgr.delete(client_id)
        
        # 7. Проверяем каскадное удаление
        self.assertIsNone(self.clients_mgr.get_by_id(client_id))
        self.assertEqual(len(self.contact_persons_mgr.get_by_client(client_id)), 0)
        self.assertEqual(len(self.task_service.get_tasks_for_client(client_id)), 0)
    
    def test_client_validation(self):
        """Тест валидации данных клиента"""
        # Пустое название компании
        with self.assertRaises(ValueError):
            self.client_service.create_client_with_contacts({
                'company': '',
                'contacts': []
            })
        
        # Нет контактов
        with self.assertRaises(ValueError):
            self.client_service.create_client_with_contacts({
                'company': 'Компания без контактов',
                'contacts': []
            })
    
    def test_task_validation(self):
        """Тест валидации задач"""
        # Пустое название
        with self.assertRaises(ValueError):
            self.task_service.create_task({
                'title': '',
                'client_id': 1
            })
        
        # Слишком короткое название
        with self.assertRaises(ValueError):
            self.task_service.create_task({
                'title': 'AB',
                'client_id': 1
            })


class TestClientCardUI(unittest.TestCase):
    """Тесты UI компонентов карточки клиента"""
    
    @classmethod
    def setUpClass(cls):
        """Создание тестового окна"""
        cls.root = tk.Tk()
        cls.root.withdraw()  # Скрываем окно
    
    @classmethod
    def tearDownClass(cls):
        """Закрытие тестового окна"""
        cls.root.destroy()
    
    def test_notebook_creation(self):
        """Тест создания вкладок"""
        notebook = ttk.Notebook(self.root)
        
        # Создаём вкладки
        tab1 = tk.Frame(notebook)
        tab2 = tk.Frame(notebook)
        tab3 = tk.Frame(notebook)
        
        notebook.add(tab1, text="📋 Инфо")
        notebook.add(tab2, text="👥 Контакты")
        notebook.add(tab3, text="✅ Задачи")
        
        self.assertEqual(notebook.index("end"), 3)
    
    def test_form_field_creation(self):
        """Тест создания полей формы"""
        frame = tk.Frame(self.root)
        
        # Метка
        label = tk.Label(frame, text="Компания:")
        label.pack()
        
        # Поле ввода
        var = tk.StringVar(value="Тестовое значение")
        entry = tk.Entry(frame, textvariable=var)
        entry.pack()
        
        self.assertEqual(var.get(), "Тестовое значение")
    
    def test_button_states(self):
        """Тест состояний кнопок"""
        btn = tk.Button(self.root, text="Сохранить", state="disabled")
        
        self.assertEqual(btn.cget("state"), "disabled")
        
        btn.config(state="normal")
        self.assertEqual(btn.cget("state"), "normal")


def run_tests():
    """Запуск всех тестов"""
    # Создаём test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestClientCardCRUD))
    suite.addTests(loader.loadTestsFromTestCase(TestClientCardUI))
    
    # Запускаем
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
