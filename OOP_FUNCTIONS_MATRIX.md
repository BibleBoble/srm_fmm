# 📊 МАТРИЦА функций и их правильного размещения

## Полная справочная таблица

Эта таблица показывает **ВСЕ функции/методы** из `views/clients_view.py` и указывает, где они **должны быть**

| №  | Функция/Метод | Текущее место | Правильное место | Тип проблемы | Сложность правки |
|:---:|:---|:---:|:---:|:---|:---:|
| **ЛОГИКА СОРТИРОВКИ И ФИЛЬТРАЦИИ** | | | | | |
| 1  | `_apply_sorting()` (ClientTasksTable) | ClientTasksTable | TasksManager.get_sorted() | 🔴 Дублирование | 🟠 MEDIUM |
| 2  | `_apply_sorting()` (ClientContactsTable) | ClientContactsTable | ContactPersonsManager.get_sorted() | 🔴 Дублирование | 🟠 MEDIUM |
| 3  | Условия фильтрации "Активные/Выполненные" | ClientTasksTable | TasksManager.get_filtered() | 🔴 Дублирование | 🟠 MEDIUM |
| **ПАРСИНГ И ПОЛУЧЕНИЕ ПОЛЕЙ** | | | | | |
| 4  | `_get_title(task)` | ClientTasksTable | utils/parsers.safe_get() | 🟡 Код боли | 🟢 EASY |
| 5  | `_get_status(task)` | ClientTasksTable | models/task.py или utils/formatters | 🟡 Логика | 🟢 EASY |
| 6  | `_get_priority(task)` | ClientTasksTable | utils/parsers.safe_get() | 🟡 Код боли | 🟢 EASY |
| 7  | `_get_due_date(task)` | ClientTasksTable | utils/parsers.DateParser | 🔴 Парсинг | 🟢 EASY |
| 8  | `_get_full_name(contact)` | ClientContactsTable | utils/parsers.safe_get() | 🟡 Код боли | 🟢 EASY |
| 9  | `_get_position(contact)` | ClientContactsTable | utils/parsers.safe_get() | 🟡 Код боли | 🟢 EASY |
| **ФОРМАТИРОВАНИЕ И ПРЕОБРАЗОВАНИЕ** | | | | | |
| 10 | Иконки приоритета `{'Высокий': '🔴', ...}` | Хардкод в _load_tasks | utils/constants.Icons | 🟡 Константа | 🟢 EASY |
| 11 | Форматирование дат `strftime("%d.%m.%Y")` | _load_tasks x2 места | utils/formatters.DateFormatter | 🔴 Дублирование | 🟢 EASY |
| 12 | Преобразование строки в дату | _get_due_date, Task.from_dict | utils/parsers.DateParser | 🔴 Дублирование | 🟢 EASY |
| 13 | `_item_to_row_values(client)` | ClientsView | utils/dto.client_to_row_dto() | 🟡 Трансформация | 🟢 EASY |
| 14 | Преобразование task в row | _load_tasks | utils/dto.task_to_row_dto() | 🟡 Трансформация | 🟢 EASY |
| 15 | Преобразование contact в row | _load_contacts | utils/dto.contact_to_row_dto() | 🟡 Трансформация | 🟢 EASY |
| **ВАЛИДАЦИЯ ДАННЫХ** | | | | | |
| 16 | Проверка "company != '' и len > 2" | _show_add_client_dialog | Client.validate_company_name() | 🔴 Бизнес-логика | 🟢 EASY |
| 17 | Проверка "full_name не пусто" | _show_add_client_dialog | ContactPerson.validate_full_name() | 🔴 Бизнес-логика | 🟢 EASY |
| 18 | Проверка "email формат" | _show_add_client_dialog | ContactEmail.validate_email() | 🟠 Есть в utils | 🟢 EASY |
| 19 | Проверка "title не пусто" | _create_task_for_client | Task.validate_title() | 🔴 Бизнес-логика | 🟢 EASY |
| **СОЗДАНИЕ И РЕДАКТИРОВАНИЕ (СЛОЖНЫЕ ОПЕРАЦИИ)** | | | | | |
| 20 | Создание клиента + контакты + email + история | _show_add_client_dialog | ClientService.create_client_with_contacts() | 🔴 500+ строк | 🔴 HARD |
| 21 | Редактирование клиента | _edit_client | ClientService.update_client_with_contacts() | 🔴 200+ строк | 🔴 HARD |
| 22 | Удаление клиента | _delete_client_from_card | ClientService.delete_client() | 🟠 Простое | 🟢 EASY |
| 23 | Создание задачи | _create_task_for_client | TaskService.create_task() | 🟠 100+ строк | 🔴 HARD |
| 24 | Редактирование задачи | _edit_task | TaskService.update_task() | 🟠 150+ строк | 🔴 HARD |
| 25 | Создание контакта | _add_contact | ContactService.create_contact() | 🟡 Небольшое | 🟠 MEDIUM |
| 26 | Редактирование контакта | _edit_contact | ContactService.update_contact() | 🟡 Небольшое | 🟠 MEDIUM |
| **СОБЫТИЯ И ОБРАБОТЧИКИ (ОСТАЮТСЯ В VIEW)** | | | | | |
| 27 | `_on_double_click(event)` | ClientTasksTable | ✅ ОСТАЁТСЯ в View | 🟢 UI-событие | 🟢 EASY |
| 28 | `_on_single_click(event)` | ClientContactsTable | ✅ ОСТАЁТСЯ в View | 🟢 UI-событие | 🟢 EASY |
| 29 | `_on_sort_change(event)` | ClientTasksTable | ✅ ОСТАЁТСЯ в View | 🟢 UI-событие | 🟢 EASY |
| 30 | `_toggle_status(item, task_id)` | ClientTasksTable | Может остаться в View (простая операция) | 🟡 Переиспользуемо | 🟠 MEDIUM |
| **ОБНОВЛЕНИЕ И REFRESH (ОСТАЮТСЯ В VIEW)** | | | | | |
| 31 | `_load_tasks()` | ClientTasksTable | ✅ ОСТАЁТСЯ в View (渲染 таблицы) | 🟢 UI-логика | 🟢 EASY |
| 32 | `_load_contacts()` | ClientContactsTable | ✅ ОСТАЁТСЯ в View (渲染 таблицы) | 🟢 UI-логика | 🟢 EASY |
| 33 | `_refresh_data()` | ClientsView | ✅ ОСТАЁТСЯ в View (обновление UI) | 🟢 UI-логика | 🟢 EASY |
| 34 | `_refresh_contacts_tab()` | ClientsView | ✅ ОСТАЁТСЯ в View (обновление UI) | 🟢 UI-логика | 🟢 EASY |
| **UI-СПЕЦИФИЧНЫЕ (ОСТАЮТСЯ В VIEW)** | | | | | |
| 35 | `_create_table()` (Treeview) | ClientTasksTable | ✅ ОСТАЁТСЯ в View | 🟢 UI-строение | 🟢 EASY |
| 36 | `_create_ui()` (фреймы, кнопки) | ClientTasksTable | ✅ ОСТАЁТСЯ в View | 🟢 UI-строение | 🟢 EASY |
| 37 | `_setup_tag_styles()` | ClientContactsTable | ✅ ОСТАЁТСЯ в View | 🟢 UI-стили | 🟢 EASY |
| 38 | `_add_mouse_wheel_support()` | ClientsView | ✅ ОСТАЁТСЯ в View | 🟢 UI-интерактивность | 🟢 EASY |
| 39 | `_create_form_section()` | ClientsView | ✅ ОСТАЁТСЯ в View (UI-помощник) | 🟡 Можно в utils | 🟢 EASY |
| 40 | `_add_info_row()` | ClientsView | ✅ ОСТАЁТСЯ в View (UI-помощник) | 🟡 Можно в utils | 🟢 EASY |

---

## 📈 Статистика

### Что переносить

| Категория | Кол-во | Сложность | Приоритет |
|---|:---:|:---:|:---:|
| 🔴 Дублирование логики | 3 | HARD | HIGH |
| 🔴 Парсинг и преобразование | 5 | EASY | HIGH |
| 🔴 Форматирование и константы | 5 | EASY | HIGH |
| 🔴 Валидация | 4 | EASY | HIGH |
| 🔴 Сложные операции (Service) | 7 | HARD | MEDIUM |
| **ИТОГО ПЕРЕНОСИТЬ** | **24** | **MIXED** | **HIGH** |

### Что оставлять в View

| Категория | Кол-во | Сложность | Причина |
|---|:---:|:---:|:---|
| ✅ События и обработчики | 4 | EASY | UI-реакции |
| ✅ Отображение данных | 3 | EASY | Рендеринг Treeview |
| ✅ Создание виджетов | 5 | EASY | UI-строение |
| ✅ Стили и интерактивность | 4 | EASY | UI-оформление |
| **ИТОГО ОСТАВЛЯТЬ** | **16** | **EASY** | **ВСЕГДА В VIEW** |

---

## 🎯 Приоритизация работы

### Очередь исправлений (рекомендуемый порядок)

#### НЕДЕЛЯ 1: Быстрые правки (EASY) — 8 часов
```
Day 1:
  ✅ Создать utils/formatters.py (1ч)
  ✅ Создать utils/dto.py (1ч)
  ✅ Создать utils/parsers.py (1ч)
  ✅ Обновить utils/constants.py (+Icons, +StatusColors) (0.5ч)
  Total: 3.5 часов

Day 2:
  ✅ Обновить models/client.py (+validate_company_name) (0.5ч)
  ✅ Обновить models/task.py (+validate_title) (0.5ч)
  ✅ Обновить models/contact_person.py (+validate_full_name) (0.5ч)
  ✅ Обновить views/clients_view.py:
     - Заменить иконки на utils.constants.Icons (0.5ч)
     - Заменить format_date на utils.formatters (0.5ч)
     - Заменить _get_* на utils.parsers.safe_get (1ч)
  Total: 4 часов

Total Week 1: 7.5 часов (+ тестирование)
```

#### НЕДЕЛЯ 2: Менеджеры (MEDIUM) — 6 часов
```
Day 1:
  ✅ Обновить managers/tasks_manager.py:
     - Добавить get_sorted() (1ч)
     - Добавить get_filtered() (0.5ч)
  ✅ Обновить managers/contact_persons_manager.py:
     - Добавить get_sorted() (0.5ч)
  Total: 2 часов

Day 2:
  ✅ Обновить views/clients_view.py:
     - ClientTasksTable._apply_sorting → TasksManager.get_sorted() (1ч)
     - ClientContactsTable._apply_sorting → ContactPersonsManager.get_sorted() (0.5ч)
  ✅ Тестирование (1ч)
  Total: 2.5 часов

Total Week 2: 4.5 часов (+ тестирование)
```

#### НЕДЕЛЯ 3: Сервисы (HARD) — 10 часов
```
Day 1-2:
  ✅ Создать services/__init__.py (0.1ч)
  ✅ Создать services/client_service.py (3ч)
  ✅ Создать services/task_service.py (2ч)
  Total: 5.1 часов

Day 3:
  ✅ Рефакторить views/clients_view.py:
     - _show_add_client_dialog → ClientService.create_client_with_contacts() (2ч)
     - _edit_client → ClientService.update_client_with_contacts() (2ч)
  ✅ Тестирование (1ч)
  Total: 5 часов

Total Week 3: 10.1 часов (+ тестирование)
```

#### ИТОГО: 3 недели, 22 часа работы

---

## ✅ Контрольный список выполнения

### Этап 1: Utils (Day 1-2)
- [ ] Создан `utils/formatters.py`
- [ ] Создан `utils/dto.py`
- [ ] Создан `utils/parsers.py`
- [ ] Обновлён `utils/constants.py` (Icons, StatusColors)
- [ ] Тесты: импорт из utils работает
- [ ] Тесты: formatters форматируют правильно

### Этап 2: Models (Day 2-3)
- [ ] Обновлены `models/client.py`, `task.py`, `contact_person.py`
- [ ] Добавлены методы `validate_*()` в каждой модели
- [ ] Тесты: валидация работает

### Этап 3: Managers (День 1-2)
- [ ] Обновлён `managers/tasks_manager.py`
  - [ ] Добавлен `get_sorted(sort_by, reverse)`
  - [ ] Добавлен `get_filtered(filter_by)`
- [ ] Обновлён `managers/contact_persons_manager.py`
  - [ ] Добавлен `get_sorted(sort_by, reverse)`
- [ ] Тесты: менеджеры могут сортировать и фильтровать

### Этап 4: Views/Formatters (Day 1-2)
- [ ] Заменены иконки на `utils.constants.Icons`
- [ ] Заменено форматирование дат на `utils.formatters`
- [ ] Заменены `_get_*()` на `utils.parsers.safe_get()`
- [ ] Тесты: view по-прежнему корректно отображает данные

### Этап 5: Views/Sorting (День 2)
- [ ] ClientTasksTable использует `TasksManager.get_sorted()`
- [ ] ClientContactsTable использует `ContactPersonsManager.get_sorted()`
- [ ] Удалены методы `_apply_sorting()` из view
- [ ] Тесты: сортировка работает как раньше

### Этап 6: Services (День 1-3)
- [ ] Создан `services/client_service.py`
- [ ] Создан `services/task_service.py`
- [ ] Тесты: сервисы создают объекты без UI

### Этап 7: Views/Dialogs (День 3)
- [ ] `_show_add_client_dialog()` использует `ClientService.create_client_with_contacts()`
- [ ] `_edit_client()` использует `ClientService.update_client_with_contacts()`
- [ ] Удалены 300+ строк дублированной логики
- [ ] Тесты: диалоги работают как раньше

### Финальная проверка
- [ ] Приложение запускается без ошибок
- [ ] Все CRUD операции работают
- [ ] Сортировка/фильтрация работают
- [ ] Форматирование дат/приоритетов работает
- [ ] Валидация работает
- [ ] UI выглядит как раньше

---

## 📝 Дополнительные файлы для чтения

1. **`oop_analysis.md`** — полный анализ с примерами проблем
2. **`OOP_REFACTORING_PLAN.md`** — конкретные примеры кода (copy-paste ready)
3. **Этот файл** — матрица функций и контрольный список


