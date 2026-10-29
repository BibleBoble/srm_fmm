# 📅 ПЛАН РЕАЛИЗАЦИИ: Рефакторинг ООП структуры

## 🎯 Общая информация

**Цель**: Переместить 800+ строк бизнес-логики из views в правильные слои (managers, models, services, utils)

**Объём работы**: 22-30 часов  
**Длительность**: 3-4 недели (с учётом тестирования)  
**Риск**: НИЗКИЙ (изменения не влияют на функциональность)  
**Приоритет**: ВЫСОКИЙ (улучшит архитектуру и поддерживаемость)

---

## 📊 Структура плана

```
ФАЗА 1: Utils & Constants (Неделя 1, дни 1-2)    — 8 часов
ФАЗА 2: Models & Managers (Неделя 1-2, дни 3-5)  — 6 часов
ФАЗА 3: Services (Неделя 2, дни 6-8)             — 10 часов
ФАЗА 4: Views Рефакторинг (Неделя 3, дни 9-10)   — 8 часов
─────────────────────────────────────────────────────────
РЕЗЕРВ: Тестирование и доп. правки              — 5 часов
ИТОГО: 37 часов работы
```

---

# 🚀 ФАЗА 1: UTILS И CONSTANTS (Неделя 1, дни 1-2)

## 📋 Цель фазы
Создать вспомогательные модули для форматирования, парсинга и преобразования данных.

### ✅ День 1 (Понедельник): 4 часа

#### 1.1 Создать `utils/formatters.py` (1.5 часа)
```
⏱️ Время: 1.5 часа
📋 Задача:
  • Скопировать код из OOP_REFACTORING_PLAN.md
  • Классы: DateFormatter, PriorityFormatter, StatusFormatter
  • Проверить импорты (datetime, date, typing)
  • Тест: python -c "from utils.formatters import DateFormatter; print('OK')"
```

**Действия:**
- [ ] Создать файл `utils/formatters.py`
- [ ] Вставить код из плана
- [ ] Проверить синтаксис
- [ ] Запустить быстрый тест импорта

---

#### 1.2 Создать `utils/dto.py` (1.5 часа)
```
⏱️ Время: 1.5 часа
📋 Задача:
  • Скопировать код из OOP_REFACTORING_PLAN.md
  • Dataclasses: ClientTableRowDTO, TaskTableRowDTO, ContactTableRowDTO
  • Конвертеры: client_dict_to_row_dto(), task_to_row_dto(), contact_dict_to_row_dto()
  • Тест: python -c "from utils.dto import ClientTableRowDTO; print('OK')"
```

**Действия:**
- [ ] Создать файл `utils/dto.py`
- [ ] Вставить код из плана
- [ ] Проверить синтаксис
- [ ] Запустить быстрый тест импорта

---

#### 1.3 Создать `utils/parsers.py` (1 час)
```
⏱️ Время: 1 час
📋 Задача:
  • Скопировать код из OOP_REFACTORING_PLAN.md
  • Класс DateParser с COMMON_FORMATS
  • Функции: safe_get(), normalize_boolean(), normalize_string()
  • Тест: python -c "from utils.parsers import DateParser, safe_get; print('OK')"
```

**Действия:**
- [ ] Создать файл `utils/parsers.py`
- [ ] Вставить код из плана
- [ ] Проверить синтаксис
- [ ] Запустить быстрый тест импорта

---

### ✅ День 2 (Вторник): 4 часа

#### 2.1 Обновить `utils/constants.py` (1.5 часа)
```
⏱️ Время: 1.5 часа
📋 Задача:
  • Добавить класс Icons с иконками приоритета/статуса
  • Добавить класс StatusColors с цветами
  • Не удалять существующие классы (Colors, Fonts, Sizes, Paths)
  • Тест: python -c "from utils.constants import Icons; print(Icons.PRIORITY)"
```

**Действия:**
- [ ] Открыть `utils/constants.py`
- [ ] Добавить после существующих классов:
  ```python
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
  ```
- [ ] Запустить тест импорта
- [ ] Проверить что существующий код не сломался

---

#### 2.2 Обновить модели с валидацией (2.5 часа)

**2.2a: `models/client.py`** (0.8 часа)
```
⏱️ Время: 0.8 часа
📋 Задача: Добавить методы валидации в класс Client
```

- [ ] Открыть `models/client.py`
- [ ] Добавить методы (из плана):
  ```python
  def validate_company_name(self, name: str) -> tuple:
      """Валидация названия компании"""
      # ... (из OOP_REFACTORING_PLAN.md)
  
  def is_valid_for_save(self) -> bool:
      """Полная валидация перед сохранением"""
  ```
- [ ] Проверить синтаксис
- [ ] Тест: быстрый импорт

---

**2.2b: `models/task.py`** (0.8 часа)
```
⏱️ Время: 0.8 часа
📋 Задача: Добавить методы валидации в класс Task
```

- [ ] Открыть `models/task.py`
- [ ] Добавить методы:
  ```python
  def validate_title(self, title: str) -> tuple:
      """Валидация названия задачи"""
      # ... должны быть созданы
  
  def is_valid_for_save(self) -> bool:
      """Полная валидация"""
  ```

---

**2.2c: `models/contact_person.py`** (0.9 часа)
```
⏱️ Время: 0.9 часа
📋 Задача: Добавить методы валидации в класс ContactPerson
```

- [ ] Открыть `models/contact_person.py`
- [ ] Добавить методы:
  ```python
  def validate_full_name(self, name: str) -> tuple:
      """Валидация ФИО"""
  
  def is_valid_for_save(self) -> bool:
      """Полная валидация"""
  ```

---

#### 2.3 Проверка и тестирование (0.5 часа)
```
⏱️ Время: 0.5 часа
📋 Задача: Убедиться что всё работает
```

- [ ] Запустить тесты импорта всех новых модулей
- [ ] Проверить что старый код не сломался
- [ ] Запустить приложение (должно стартовать без ошибок)

---

**✅ ИТОГО ФАЗА 1: 8 часов**

---

# 📊 ФАЗА 2: MANAGERS И СОРТИРОВКА (Неделя 2, дни 3-5)

## 📋 Цель фазы
Добавить методы сортировки и фильтрации в менеджеры. Это основа для переиспользования логики.

### ✅ День 3 (Среда): 3 часа

#### 3.1 Обновить `managers/tasks_manager.py` (2 часа)
```
⏱️ Время: 2 часа
📋 Задача: Добавить методы get_sorted(), get_filtered()
```

**Действия:**
- [ ] Открыть `managers/tasks_manager.py`
- [ ] Добавить методы из плана:
  ```python
  def get_sorted_by_priority(self, reverse: bool = False):
      """Получить задачи отсортированные по приоритету"""
  
  def get_sorted_by_due_date(self, reverse: bool = False):
      """Получить задачи отсортированные по сроку выполнения"""
  
  def get_filtered_by_status(self, status: str):
      """Получить задачи по статусу ('Активная', 'Выполнена')"""
  
  def get_filtered_by_client(self, client_id: int, status: str = None):
      """Получить задачи клиента, опционально по статусу"""
  ```
- [ ] Проверить что методы используют `from utils.formatters import StatusFormatter`
- [ ] Протестировать импорт и вызов методов

---

#### 3.2 Обновить `managers/contact_persons_manager.py` (1 час)
```
⏱️ Время: 1 час
📋 Задача: Добавить методы сортировки контактов
```

**Действия:**
- [ ] Открыть `managers/contact_persons_manager.py`
- [ ] Добавить методы:
  ```python
  def get_sorted_by_name(self, reverse: bool = False):
      """Получить контакты отсортированные по ФИО"""
  
  def get_sorted_by_position(self, reverse: bool = False):
      """Получить контакты отсортированные по должности"""
  
  def get_filtered_by_client(self, client_id: int, is_primary: bool = None):
      """Получить контакты клиента, опционально основные"""
  ```

---

### ✅ День 4 (Четверг): 2 часа

#### 4.1 Обновить `managers/clients_manager.py` (1 час)
```
⏱️ Время: 1 час
📋 Задача: Добавить методы сортировки клиентов (опционально)
```

**Действия:**
- [ ] Открыть `managers/clients_manager.py`
- [ ] Добавить методы:
  ```python
  def get_sorted_by_company(self, reverse: bool = False):
      """Получить клиентов отсортированные по названию компании"""
  
  def get_sorted_by_contact(self, reverse: bool = False):
      """Получить клиентов отсортированные по контакту"""
  ```

---

#### 4.2 Проверка и интеграция (1 час)
```
⏱️ Время: 1 час
📋 Задача: Убедиться что менеджеры работают правильно
```

- [ ] Запустить тесты импорта менеджеров
- [ ] Проверить что методы доступны и работают
- [ ] Запустить приложение

---

### ✅ День 5 (Пятница): 1 час

#### 5.1 Завершение и документирование (1 час)
```
⏱️ Время: 1 час
📋 Задача: Убедиться что всё готово к следующей фазе
```

- [ ] Создать временный тестовый скрипт для проверки всех методов
- [ ] Документировать какие методы добавлены
- [ ] Подготовить список методов для использования в views

---

**✅ ИТОГО ФАЗА 2: 6 часов**

---

# 🎯 ФАЗА 3: SERVICES (Неделя 2, дни 6-8)

## 📋 Цель фазы
Создать сервисные классы, которые инкапсулируют сложные операции.

### ✅ День 6 (Понедельник Неделя 2): 4 часа

#### 6.1 Создать `services/__init__.py` (0.2 часа)
```
⏱️ Время: 0.2 часа
📋 Задача: Инициализировать пакет services
```

- [ ] Создать файл `services/__init__.py`
- [ ] Добавить:
  ```python
  # -*- coding: utf-8 -*-
  """
  Сервисные классы для бизнес-операций
  """
  from services.client_service import ClientService
  
  __all__ = ['ClientService']
  ```

---

#### 6.2 Создать `services/client_service.py` (3.8 часа)
```
⏱️ Время: 3.8 часа
📋 Задача: Скопировать ClientService из плана
```

**Действия:**
- [ ] Создать файл `services/client_service.py`
- [ ] Вставить код из `OOP_REFACTORING_PLAN.md` (200+ строк)
- [ ] Проверить все импорты (date, Dict, Any, List, Optional)
- [ ] Проверить методы:
  - [ ] `__init__()` — инициализация менеджеров
  - [ ] `create_client_with_contacts()` — создание клиента
  - [ ] `update_client_with_contacts()` — обновление клиента
  - [ ] `delete_client()` — удаление клиента
- [ ] Тест импорта: `from services.client_service import ClientService`
- [ ] Быстрый функциональный тест (создать тестовые данные, вызвать методы)

---

### ✅ День 7 (Вторник): 3 часа

#### 7.1 Создать `services/task_service.py` (2.5 часа)
```
⏱️ Время: 2.5 часа
📋 Задача: Создать сервис для операций с задачами
```

**Действия:**
- [ ] Создать файл `services/task_service.py`
- [ ] Создать класс TaskService с методами:
  ```python
  class TaskService:
      def __init__(self, tasks_mgr, clients_mgr, interactions_mgr):
          self.tasks_mgr = tasks_mgr
          self.clients_mgr = clients_mgr
          self.interactions_mgr = interactions_mgr
      
      def create_task(self, task_data: Dict[str, Any]) -> int:
          """Создать задачу с валидацией"""
          # Валидация
          # Создание задачи
          # Запись в историю
          return task_id
      
      def update_task(self, task_id: int, task_data: Dict[str, Any]) -> bool:
          """Обновить задачу"""
      
      def delete_task(self, task_id: int) -> bool:
          """Удалить задачу"""
  ```
- [ ] Проверить синтаксис
- [ ] Тест импорта

---

#### 7.2 Обновить `services/__init__.py` (0.3 часа)
```
⏱️ Время: 0.3 часа
```

- [ ] Добавить в импорт TaskService:
  ```python
  from services.client_service import ClientService
  from services.task_service import TaskService
  
  __all__ = ['ClientService', 'TaskService']
  ```

---

#### 7.3 Проверка services (0.2 часа)
```
⏱️ Время: 0.2 часа
```

- [ ] Тесты импорта обоих сервисов
- [ ] Проверка что менеджеры передаются правильно

---

### ✅ День 8 (Среда): 3 часа

#### 8.1 Интеграция services с views (2 часа)
```
⏱️ Время: 2 часа
📋 Задача: Обновить views использовать services
```

**Действия:**
- [ ] Открыть `views/clients_view.py`
- [ ] Найти метод `_show_add_client_dialog()`
- [ ] Заменить логику создания клиента на вызов сервиса:
  ```python
  from services.client_service import ClientService
  
  service = ClientService(
      self.clients_mgr,
      self.contact_persons_mgr,
      self.contact_emails_mgr,
      self.interactions_mgr
  )
  
  try:
      client_id = service.create_client_with_contacts(form_data)
      messagebox.showinfo("Успех", f"Клиент #{client_id} создан")
      self._refresh_data()
  except ValueError as e:
      messagebox.showerror("Ошибка", str(e))
  ```
- [ ] Удалить старую логику (500+ строк дублирования)
- [ ] Тестирование: попробовать создать клиента через UI

---

#### 8.2 Обновить другие диалоги редактирования (1 час)
```
⏱️ Время: 1 час
📋 Задача: Аналогично обновить _edit_client, _edit_contact
```

- [ ] Заменить логику в `_edit_client()`
- [ ] Заменить логику в `_edit_contact()`
- [ ] Заменить логику в `_create_task_for_client()`

---

**✅ ИТОГО ФАЗА 3: 10 часов**

---

# 🔧 ФАЗА 4: РЕФАКТОРИНГ VIEWS (Неделя 3, дни 9-10)

## 📋 Цель фазы
Очистить views от дублированной логики, использовать новые utils и formatters.

### ✅ День 9 (Четверг): 4 часа

#### 9.1 Заменить форматирование в ClientTasksTable (1.5 часа)
```
⏱️ Время: 1.5 часа
📋 Задача: Использовать utils/formatters вместо хардкода
```

**Действия:**
- [ ] Открыть `views/clients_view.py`
- [ ] Найти класс `ClientTasksTable._load_tasks()`
- [ ] Заменить дату форматирование:
  ```python
  # БЫЛО:
  due_date_str = due_date.strftime("%d.%m.%Y")
  
  # СТАЛО:
  from utils.formatters import DateFormatter
  due_date_str = DateFormatter.format_date(task.due_date)
  ```
- [ ] Заменить иконки приоритета:
  ```python
  # БЫЛО:
  priority_icons = {'Высокий': '🔴', 'Средний': '🟡', 'Низкий': '🟢'}
  
  # СТАЛО:
  from utils.constants import Icons
  from utils.formatters import PriorityFormatter
  priority_str = PriorityFormatter.format(priority)
  ```
- [ ] Заменить статусы:
  ```python
  # БЫЛО:
  status = "Активная" if not completed else "Выполнена"
  
  # СТАЛО:
  from utils.formatters import StatusFormatter
  status_str = StatusFormatter.format(status)
  ```

---

#### 9.2 Удалить дублированные методы получения полей (1.5 часа)
```
⏱️ Время: 1.5 часа
📋 Задача: Удалить _get_title(), _get_status(), _get_priority(), _get_due_date()
```

**Действия:**
- [ ] Найти все `_get_*()` методы в ClientTasksTable
- [ ] Заменить на `utils.parsers.safe_get()`:
  ```python
  # БЫЛО:
  def _get_title(self, task):
      return task.title if hasattr(task, 'title') else task.get('title', '')
  
  # СТАЛО:
  from utils.parsers import safe_get
  title = safe_get(task, 'title', '')
  ```
- [ ] Удалить эти методы целиком из класса
- [ ] Проверить что всё ещё работает

---

#### 9.3 Обновить ClientContactsTable аналогично (1 час)
```
⏱️ Время: 1 час
```

- [ ] Заменить форматирование в `_load_contacts()`
- [ ] Удалить `_get_*()` методы
- [ ] Проверить что работает

---

### ✅ День 10 (Пятница): 4 часа

#### 10.1 Финальное тестирование и документирование (2 часа)
```
⏱️ Время: 2 часа
📋 Задача: Убедиться что всё работает корректно
```

**Действия:**
- [ ] Запустить приложение
- [ ] Пройти все основные сценарии:
  - [ ] Создать клиента
  - [ ] Редактировать клиента
  - [ ] Удалить клиента
  - [ ] Создать контакт
  - [ ] Отредактировать контакт
  - [ ] Создать задачу
  - [ ] Сортировка и фильтрация
- [ ] Проверить логи на ошибки
- [ ] Проверить что нет рандомных исключений

---

#### 10.2 Удалить устаревший код и очистить (1 час)
```
⏱️ Время: 1 час
📋 Задача: Убрать всё лишнее
```

- [ ] Удалить неиспользуемые импорты из views
- [ ] Удалить закомментированный код
- [ ] Проверить что views содержит только UI-логику
- [ ] Убедиться что views НЕ содержат:
  - ❌ Логику сортировки
  - ❌ Валидацию данных
  - ❌ Парсинг типов
  - ❌ Форматирование

---

#### 10.3 Обновить документацию (1 час)
```
⏱️ Время: 1 час
📋 Задача: Документировать изменения
```

- [ ] Обновить docstrings в новых файлах
- [ ] Создать REFACTORING_COMPLETE.md с описанием изменений
- [ ] Обновить комментарии в коде

---

**✅ ИТОГО ФАЗА 4: 8 часов**

---

# 📝 РЕЗЕРВ: ТЕСТИРОВАНИЕ И ДОПОЛНЕНИЯ (5 часов)

```
Этот блок используется для:
• Исправления ошибок, которые обнаружатся при тестировании
• Написания простых unit-тестов для сервисов
• Создания скрипта миграции/восстановления БД если нужно
• Документирования в README как использовать новые сервисы
```

---

# 📊 ВРЕМЕННАЯ ШКАЛА

```
НЕДЕЛЯ 1:
  ПН (День 1):  ФАЗА 1.1 — formatters.py, dto.py, parsers.py        [4 часа]
  ВТ (День 2):  ФАЗА 1.2 — constants.py + Models                    [4 часа]
  СР (День 3):  ФАЗА 2.1 — managers.py (methods)                    [3 часа]
  ЧТ (День 4):  ФАЗА 2.2 — managers (finish) + tests                [2 часа]
  ПТ (День 5):  ФАЗА 2.3 — dokumenting + prepare                    [1 час]

НЕДЕЛЯ 2:
  ПН (День 6):  ФАЗА 3.1 — services/__init__.py + ClientService     [4 часа]
  ВТ (День 7):  ФАЗА 3.2 — TaskService + integration                [3 часа]
  СР (День 8):  ФАЗА 3.3 — Views integration + testing              [3 часа]

НЕДЕЛЯ 3:
  ЧТ (День 9):  ФАЗА 4.1 — formatters in views, remove duplication  [4 часа]
  ПТ (День 10): ФАЗА 4.2 — final testing + documentation            [4 часа]

РЕЗЕРВ:         Тестирование + фиксы                                 [5 часов]

─────────────────────────────────────────────────────────────────
ВСЕГО: 37 часов = ~1 неделя full-time или 3-4 недели part-time
```

---

# ✅ КОНТРОЛЬНЫЙ СПИСОК ВЫПОЛНЕНИЯ

## ФАЗА 1: Utils & Constants
- [ ] `utils/formatters.py` создан и работает
- [ ] `utils/dto.py` создан и работает
- [ ] `utils/parsers.py` создан и работает
- [ ] `utils/constants.py` обновлён (Icons, StatusColors)
- [ ] `models/client.py` обновлена (validate_company_name)
- [ ] `models/task.py` обновлена (validate_title)
- [ ] `models/contact_person.py` обновлена (validate_full_name)
- [ ] Все импорты работают
- [ ] Приложение стартует без ошибок

## ФАЗА 2: Managers
- [ ] `managers/tasks_manager.py` содержит методы сортировки/фильтрации
- [ ] `managers/contact_persons_manager.py` обновлен
- [ ] `managers/clients_manager.py` обновлен
- [ ] Все методы доступны и работают
- [ ] Тестовый скрипт проверяет все методы

## ФАЗА 3: Services
- [ ] `services/__init__.py` создан
- [ ] `services/client_service.py` создан (200+ строк)
- [ ] `services/task_service.py` создан
- [ ] `views/clients_view.py` использует ClientService
- [ ] `_show_add_client_dialog()` переписана
- [ ] `_edit_client()` переписана
- [ ] `_edit_contact()` переписана
- [ ] Создание/редактирование клиентов работает через сервисы
- [ ] Тестирование: создать/отредактировать/удалить клиента

## ФАЗА 4: Views Cleanup
- [ ] ClientTasksTable использует `utils.formatters`
- [ ] ClientContactsTable использует `utils.formatters`
- [ ] Все `_get_*()` методы удалены из views
- [ ] Иконки берутся из `utils.constants.Icons`
- [ ] Форматирование дат централизовано
- [ ] views содержит только UI-логику
- [ ] Тестирование: все UI операции работают

## Финальная проверка
- [ ] Приложение запускается без ошибок
- [ ] Все основные операции работают
- [ ] Логи чистые (нет ошибок)
- [ ] Code review: views содержат только UI
- [ ] Code review: business logic в правильных местах
- [ ] Документация обновлена

---

# 🚨 КРИТИЧЕСКИЕ ТОЧКИ (Watch Out!)

```
⚠️  День 1-2: При создании utils убедитесь что импорты правильные
⚠️  День 3: При добавлении методов в managers НЕ меняйте существующие
⚠️  День 6-7: Services должны быть полностью функциональны
⚠️  День 8: Views должны использовать services БЕЗ дублирования
⚠️  День 9-10: Удаляемый код должен быть переиспользован в utils/managers
```

---

# 📞 КАК РЕШИТЬ ПРОБЛЕМЫ

| Проблема | Решение |
|---|---|
| ImportError при импорте новых модулей | Убедитесь что файлы созданы в правильных местах, проверьте пути |
| Методы в managers не работают | Проверьте что используются правильные парамеры и типы из utils |
| Старые вызовы в views не работают | Замените на новые вызовы сервисов/utils/formatters |
| UI не отображает данные правильно | Проверьте что DTO преобразует данные правильно |
| Ошибки при тестировании | Используйте контрольный список выполнения для каждой фазы |

---

# 📚 ССЫЛКИ НА ДОКУМЕНТЫ

- **OOP_REFACTORING_PLAN.md** — полный код всех новых файлов
- **oop_analysis.md** — подробный анализ проблем
- **OOP_FUNCTIONS_MATRIX.md** — матрица функций для переноса

---

**Готово!** Этот план готов к исполнению. Начните с Фазы 1, День 1! 🚀

