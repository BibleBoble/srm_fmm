# 🔧 План рефакторинга ООП структуры

## 📁 Файлы для создания/изменения

### Новые файлы
```
✨ services/
   ├── __init__.py
   ├── client_service.py          (200-300 строк)
   └── task_service.py             (150-200 строк)

✨ utils/
   ├── formatters.py              (80-100 строк)
   ├── dto.py                     (120-150 строк)
   └── parsers.py                 (100-120 строк)
```

### Файлы для обновления
```
📝 utils/constants.py             (+30 строк: классы Icons, StatusColors)
📝 models/client.py               (+20 строк: методы валидации)
📝 models/task.py                 (+15 строк: методы валидации)
📝 models/contact_person.py       (+20 строк: методы валидации)
📝 managers/tasks_manager.py      (+50 строк: методы сортировки/фильтрации)
📝 managers/contact_persons_manager.py (+40 строк: методы сортировки)
📝 views/clients_view.py          (-300 строк: удаление дублированной логики)
```

---

## 🎯 Конкретные примеры кода

### 1️⃣ Создание `utils/formatters.py`

```python
# -*- coding: utf-8 -*-
"""
Форматеры для представления данных в UI
"""
from datetime import datetime, date
from typing import Optional


class DateFormatter:
    """Форматер дат"""
    
    DEFAULT_FORMAT = "%d.%m.%Y"
    DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"
    
    @staticmethod
    def format_date(date_obj, format_str: str = DEFAULT_FORMAT) -> str:
        """Форматирует дату в нужный вид"""
        if not date_obj:
            return ""
        
        if isinstance(date_obj, str):
            # Если уже строка и в нужном формате — возвращаем
            if all(c in "0123456789.-/" for c in date_obj):
                return date_obj
            # Иначе пробуем распарсить
            from utils.parsers import DateParser
            parsed = DateParser.parse_date(date_obj)
            if parsed:
                return parsed.strftime(format_str)
            return date_obj
        
        elif isinstance(date_obj, (datetime, date)):
            return date_obj.strftime(format_str)
        
        return str(date_obj) if date_obj else ""


class PriorityFormatter:
    """Форматер приоритета"""
    
    ICONS = {
        'Высокий': '🔴',
        'Средний': '🟡',
        'Низкий': '🟢'
    }
    
    @staticmethod
    def format(priority: str, with_icon: bool = True) -> str:
        """Форматирует приоритет с иконкой"""
        if not priority:
            return ""
        
        icon = PriorityFormatter.ICONS.get(priority, "")
        if with_icon and icon:
            return f"{icon} {priority}"
        return priority


class StatusFormatter:
    """Форматер статуса"""
    
    ICONS = {
        'Активная': '⏳',
        'Выполнена': '✅',
        'Новая': '📝',
        'В работе': '🔄',
        'Отложена': '⏸',
        'Отменена': '❌'
    }
    
    @staticmethod
    def format(status: str, with_icon: bool = True) -> str:
        """Форматирует статус с иконкой"""
        if not status:
            return "Новая"
        
        icon = StatusFormatter.ICONS.get(status, "")
        if with_icon and icon:
            return f"{icon} {status}"
        return status
    
    @staticmethod
    def normalize(status: str) -> str:
        """Нормализует статус (Новая/В работе/Отложена → Активная)"""
        if status in ['Новая', 'В работе', 'Отложена']:
            return 'Активная'
        return status
```

---

### 2️⃣ Создание `utils/dto.py`

```python
# -*- coding: utf-8 -*-
"""
Data Transfer Objects для UI представления
"""
from dataclasses import dataclass
from typing import Optional, List, Tuple


@dataclass
class ClientTableRowDTO:
    """DTO для отображения клиента в таблице"""
    id: int
    company: str
    primary_contact: str = "—"
    primary_position: str = "—"
    primary_phone: str = "—"
    address: str = "—"
    action: str = "➕"
    
    def to_tuple(self) -> Tuple:
        """Преобразовать в кортеж для Treeview"""
        return (
            self.id,
            self.company,
            self.primary_contact,
            self.primary_position,
            self.primary_phone,
            self.address,
            self.action
        )


@dataclass
class TaskTableRowDTO:
    """DTO для отображения задачи в таблице"""
    id: int
    status: str
    title: str
    priority: str
    due_date: str
    
    def to_tuple(self) -> Tuple:
        return (self.id, self.status, self.title, self.priority, self.due_date)


@dataclass
class ContactTableRowDTO:
    """DTO для отображения контакта в таблице"""
    id: int
    full_name: str
    position: str = "—"
    phone: str = "—"
    email: str = "—"
    
    def to_tuple(self) -> Tuple:
        return (self.id, self.full_name, self.position, self.phone, self.email)


# === КОНВЕРТЕРЫ ===

def client_dict_to_row_dto(client: dict) -> ClientTableRowDTO:
    """Преобразовать словарь клиента в DTO для таблицы"""
    return ClientTableRowDTO(
        id=client.get('id', ''),
        company=client.get('company', '—'),
        primary_contact=client.get('primary_contact', '—'),
        primary_position=client.get('primary_position', '—'),
        primary_phone=client.get('primary_phone', '—'),
        address=client.get('address', '—')
    )


def task_to_row_dto(task, formatters) -> TaskTableRowDTO:
    """
    Преобразовать задачу в DTO для таблицы
    
    Args:
        task: Task объект или dict
        formatters: объект с методами format_status(), format_priority(), format_date()
    """
    from utils.parsers import safe_get
    
    task_id = safe_get(task, 'id')
    status = safe_get(task, 'status', 'Новая')
    title = safe_get(task, 'title', '')
    priority = safe_get(task, 'priority', '')
    due_date = safe_get(task, 'due_date')
    
    return TaskTableRowDTO(
        id=task_id,
        status=formatters.format_status(status),
        title=title,
        priority=formatters.format_priority(priority),
        due_date=formatters.format_date(due_date)
    )


def contact_dict_to_row_dto(contact: dict) -> ContactTableRowDTO:
    """Преобразовать словарь контакта в DTO для таблицы"""
    return ContactTableRowDTO(
        id=contact.get('id', ''),
        full_name=contact.get('full_name', '—'),
        position=contact.get('position', '—'),
        phone=contact.get('phone', '—'),
        email=contact.get('email', '—')
    )
```

---

### 3️⃣ Создание `utils/parsers.py`

```python
# -*- coding: utf-8 -*-
"""
Парсеры для преобразования данных
"""
from datetime import datetime, date
from typing import Any, Optional, List, Union


class DateParser:
    """Парсер дат из разных форматов"""
    
    COMMON_FORMATS = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y"
    ]
    
    @staticmethod
    def parse_date(
        date_str: Union[str, date, datetime],
        formats: List[str] = None
    ) -> Optional[date]:
        """
        Распарсить дату из строки в date объект
        
        Args:
            date_str: строка, date или datetime
            formats: список форматов для попытки парсинга
        
        Returns:
            date объект или None
        """
        if not date_str:
            return None
        
        if isinstance(date_str, date):
            return date_str
        
        if isinstance(date_str, datetime):
            return date_str.date()
        
        if not isinstance(date_str, str):
            return None
        
        formats = formats or DateParser.COMMON_FORMATS
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.date()
            except (ValueError, AttributeError):
                continue
        
        return None


def safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """
    Безопасно получить поле из dict или object
    
    Args:
        obj: dict или объект с атрибутами
        key: ключ/имя атрибута
        default: значение по умолчанию
    
    Returns:
        значение поля или default
    """
    if obj is None:
        return default
    
    if isinstance(obj, dict):
        return obj.get(key, default)
    
    try:
        return getattr(obj, key, default)
    except AttributeError:
        return default


def normalize_boolean(value: Any) -> bool:
    """Преобразовать значение в булев тип"""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on', 'да')
    return bool(value)


def normalize_string(value: Any, strip: bool = True) -> str:
    """Преобразовать значение в строку"""
    if value is None:
        return ""
    s = str(value)
    return s.strip() if strip else s
```

---

### 4️⃣ Создание `services/client_service.py`

```python
# -*- coding: utf-8 -*-
"""
Бизнес-сервис для операций с клиентами
"""
from datetime import date
from typing import Dict, Any, List, Optional


class ClientService:
    """
    Сервис для операций с клиентами
    Инкапсулирует бизнес-логику, независимую от UI
    """
    
    def __init__(self, clients_mgr, contact_persons_mgr, 
                 contact_emails_mgr, interactions_mgr):
        self.clients_mgr = clients_mgr
        self.contact_persons_mgr = contact_persons_mgr
        self.contact_emails_mgr = contact_emails_mgr
        self.interactions_mgr = interactions_mgr
    
    def create_client_with_contacts(self, client_data: Dict[str, Any]) -> int:
        """
        Создать клиента с контактными лицами
        
        Args:
            client_data: {
                'company': str (обязательно),
                'address': str,
                'notes': str,
                'contacts': [
                    {
                        'full_name': str (обязательно),
                        'position': str,
                        'phone': str,
                        'email': str,
                        'is_primary': bool
                    },
                    ...
                ]
            }
        
        Returns:
            client_id: int
        
        Raises:
            ValueError: если валидация не пройдена
        """
        # 1. Валидация
        company = client_data.get('company', '').strip()
        if not company:
            raise ValueError("Название компании обязательно")
        if len(company) < 2:
            raise ValueError("Название должно содержать минимум 2 символа")
        
        contacts = client_data.get('contacts', [])
        if not contacts or not any(c.get('full_name', '').strip() for c in contacts):
            raise ValueError("Нужен хотя бы один контакт")
        
        # 2. Создаём клиента
        client_id = self.clients_mgr.add(
            company=company,
            address=client_data.get('address', '').strip(),
            notes=client_data.get('notes', '').strip()
        )
        
        if not client_id:
            raise RuntimeError("Не удалось создать клиента в БД")
        
        # 3. Добавляем контакты
        for contact in contacts:
            full_name = contact.get('full_name', '').strip()
            if not full_name:
                continue  # Пропускаем пустые контакты
            
            contact_id = self.contact_persons_mgr.add(
                client_id=client_id,
                full_name=full_name,
                position=contact.get('position', '').strip(),
                phone=contact.get('phone', '').strip(),
                is_primary=bool(contact.get('is_primary', False))
            )
            
            # 4. Добавляем email если есть
            email = contact.get('email', '').strip()
            if email and contact_id:
                try:
                    self.contact_emails_mgr.add(
                        contact_person_id=contact_id,
                        email=email,
                        is_primary=bool(contact.get('is_primary', False))
                    )
                except Exception as e:
                    print(f"Предупреждение: не удалось добавить email '{email}': {e}")
        
        # 5. Записываем в историю
        try:
            self.interactions_mgr.add(
                client_id=client_id,
                date=date.today(),
                type_interaction="Создание",
                description=f"Клиент добавлен. Контактов: {len(contacts)}"
            )
        except Exception as e:
            print(f"Предупреждение: не удалось записать в историю: {e}")
        
        return client_id
    
    def update_client_with_contacts(
        self,
        client_id: int,
        client_data: Dict[str, Any]
    ) -> bool:
        """
        Обновить клиента и его контакты
        
        Args:
            client_id: ID клиента
            client_data: данные клиента (аналогично create_client_with_contacts)
        
        Returns:
            True если успешно
        
        Raises:
            ValueError: если валидация не пройдена
        """
        # Валидация
        company = client_data.get('company', '').strip()
        if not company:
            raise ValueError("Название компании обязательно")
        
        # Обновляем основные данные
        self.clients_mgr.update(
            client_id,
            company=company,
            address=client_data.get('address', '').strip(),
            notes=client_data.get('notes', '').strip()
        )
        
        # Обновляем контакты (если нужно)
        # ...дополнительная логика...
        
        return True
    
    def delete_client(self, client_id: int) -> bool:
        """Удалить клиента (каскадное удаление благодаря ON DELETE CASCADE)"""
        try:
            self.clients_mgr.delete(client_id)
            return True
        except Exception as e:
            raise RuntimeError(f"Не удалось удалить клиента: {e}")
```

---

### 5️⃣ Обновление `models/client.py`

```python
# Добавить методы валидации в класс Client:

class Client:
    # ...existing code...
    
    def validate_company_name(self, name: str) -> tuple:
        """
        Валидация названия компании
        
        Returns:
            (is_valid: bool, error_message: str)
        """
        name = name.strip() if isinstance(name, str) else ""
        
        if not name:
            return False, "Название компании обязательно"
        if len(name) < 2:
            return False, "Название должно содержать минимум 2 символа"
        if len(name) > 255:
            return False, "Название слишком длинное (макс 255 символов)"
        
        return True, ""
    
    def is_valid_for_save(self) -> bool:
        """Полная валидация перед сохранением"""
        is_ok, _ = self.validate_company_name(self.company)
        return is_ok
```

---

### 6️⃣ Обновление `managers/tasks_manager.py`

```python
# Добавить методы в класс TasksManager:

def get_sorted_by_priority(self, reverse: bool = False):
    """Получить задачи отсортированные по приоритету"""
    priority_order = {'Высокий': 1, 'Средний': 2, 'Низкий': 3}
    tasks = self.get_all()
    return sorted(
        tasks,
        key=lambda t: priority_order.get(getattr(t, 'priority', 'Средний'), 4),
        reverse=reverse
    )

def get_sorted_by_due_date(self, reverse: bool = False):
    """Получить задачи отсортированные по сроку выполнения"""
    from datetime import datetime
    tasks = self.get_all()
    return sorted(
        tasks,
        key=lambda t: getattr(t, 'due_date') or (datetime.min if not reverse else datetime.max),
        reverse=reverse
    )

def get_filtered_by_status(self, status: str):
    """Получить задачи по статусу ('Активная', 'Выполнена')"""
    from utils.formatters import StatusFormatter
    tasks = self.get_all()
    normalized = StatusFormatter.normalize(status)
    
    return [
        t for t in tasks
        if StatusFormatter.normalize(getattr(t, 'status', 'Новая')) == normalized
    ]

def get_filtered_by_client(self, client_id: int, status: str = None):
    """Получить задачи клиента, опционально по статусу"""
    tasks = self.get_by_client(client_id)
    if status:
        from utils.formatters import StatusFormatter
        normalized = StatusFormatter.normalize(status)
        return [
            t for t in tasks
            if StatusFormatter.normalize(getattr(t, 'status', 'Новая')) == normalized
        ]
    return tasks
```

---

## ✅ Чеклист внедрения (Фаза 1)

- [ ] Создать `utils/formatters.py`
- [ ] Создать `utils/dto.py`
- [ ] Создать `utils/parsers.py`
- [ ] Обновить `utils/constants.py` — добавить классы Icons, StatusColors
- [ ] Обновить `models/client.py` — добавить методы валидации
- [ ] Обновить `models/task.py` — добавить методы валидации
- [ ] Обновить `models/contact_person.py` — добавить методы валидации
- [ ] Запустить тесты — проверить что ничего не сломалось
- [ ] Создать `services/__init__.py`
- [ ] Создать `services/client_service.py`
- [ ] Обновить одну view-функцию (_show_add_client_dialog) использовать ClientService
- [ ] Удалить 300+ строк дублированной логики из views/clients_view.py


