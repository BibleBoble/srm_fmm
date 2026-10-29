#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки ФАЗЫ 1 (День 1-2)
"""

def test_phase1():
    """Тестирование всех компонентов ФАЗЫ 1"""

    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ФАЗЫ 1: Utils & Constants & Models")
    print("="*60)

    # 1. Тестирование formatters.py
    print("\n1️⃣  ТЕСТИРОВАНИЕ utils/formatters.py")
    print("-" * 60)
    try:
        from utils.formatters import DateFormatter, PriorityFormatter, StatusFormatter
        from datetime import date

        # Тест DateFormatter
        test_date = date(2026, 2, 24)
        formatted = DateFormatter.format_date(test_date)
        print(f"  ✅ DateFormatter.format_date({test_date}) = {formatted}")
        assert formatted == "24.02.2026", f"Ошибка формата даты: {formatted}"

        # Тест PriorityFormatter
        priority_str = PriorityFormatter.format('Высокий')
        print(f"  ✅ PriorityFormatter.format('Высокий') = {priority_str}")
        assert '🔴' in priority_str, "Иконка приоритета отсутствует"

        # Тест StatusFormatter
        status_str = StatusFormatter.format('Выполнена')
        print(f"  ✅ StatusFormatter.format('Выполнена') = {status_str}")
        assert '✅' in status_str, "Иконка статуса отсутствует"

        # Тест normalize
        normalized = StatusFormatter.normalize('Новая')
        print(f"  ✅ StatusFormatter.normalize('Новая') = {normalized}")
        assert normalized == 'Активная', "Нормализация статуса не работает"

        print("  ✅ utils/formatters.py РАБОТАЕТ КОРРЕКТНО")
    except Exception as e:
        print(f"  ❌ ОШИБКА в formatters.py: {e}")
        return False

    # 2. Тестирование dto.py
    print("\n2️⃣  ТЕСТИРОВАНИЕ utils/dto.py")
    print("-" * 60)
    try:
        from utils.dto import ClientTableRowDTO, TaskTableRowDTO, ContactTableRowDTO
        from utils.dto import client_dict_to_row_dto, task_to_row_dto, contact_dict_to_row_dto

        # Тест ClientTableRowDTO
        client_data = {
            'id': 1,
            'company': 'ООО Тест',
            'primary_contact': 'Иван Петров',
            'primary_position': 'Директор',
            'primary_phone': '+79991234567',
            'address': 'ул. Тестовая 123'
        }
        client_dto = client_dict_to_row_dto(client_data)
        print(f"  ✅ client_dict_to_row_dto() создан: {client_dto.company}")
        row_tuple = client_dto.to_tuple()
        assert len(row_tuple) == 7, "Неверное количество полей в DTO"

        # Тест ContactTableRowDTO
        contact_data = {
            'id': 1,
            'full_name': 'Мария Сидорова',
            'position': 'Менеджер',
            'phone': '+79991234567',
            'email': 'maria@test.com'
        }
        contact_dto = contact_dict_to_row_dto(contact_data)
        print(f"  ✅ contact_dict_to_row_dto() создан: {contact_dto.full_name}")

        print("  ✅ utils/dto.py РАБОТАЕТ КОРРЕКТНО")
    except Exception as e:
        print(f"  ❌ ОШИБКА в dto.py: {e}")
        return False

    # 3. Тестирование parsers.py
    print("\n3️⃣  ТЕСТИРОВАНИЕ utils/parsers.py")
    print("-" * 60)
    try:
        from utils.parsers import DateParser, safe_get, normalize_boolean, normalize_string

        # Тест DateParser
        parsed = DateParser.parse_date("24.02.2026")
        print(f"  ✅ DateParser.parse_date('24.02.2026') = {parsed}")
        assert parsed is not None, "Парсинг даты не работает"
        assert str(parsed) == "2026-02-24", f"Неверный формат даты: {parsed}"

        # Тест safe_get
        test_dict = {'name': 'Тест', 'value': 42}
        result = safe_get(test_dict, 'name')
        print(f"  ✅ safe_get(dict, 'name') = {result}")
        assert result == 'Тест', "safe_get не работает для dict"

        # Тест safe_get с объектом
        class TestObj:
            name = "Объект"
        obj = TestObj()
        result = safe_get(obj, 'name')
        print(f"  ✅ safe_get(obj, 'name') = {result}")
        assert result == 'Объект', "safe_get не работает для объектов"

        # Тест normalize_boolean
        assert normalize_boolean(True) == True, "normalize_boolean для True не работает"
        assert normalize_boolean(1) == True, "normalize_boolean для 1 не работает"
        assert normalize_boolean('yes') == True, "normalize_boolean для 'yes' не работает"
        print(f"  ✅ normalize_boolean() работает")

        # Тест normalize_string
        result = normalize_string("  тест  ")
        assert result == "тест", "normalize_string не работает"
        print(f"  ✅ normalize_string() работает")

        print("  ✅ utils/parsers.py РАБОТАЕТ КОРРЕКТНО")
    except Exception as e:
        print(f"  ❌ ОШИБКА в parsers.py: {e}")
        return False

    # 4. Тестирование constants.py
    print("\n4️⃣  ТЕСТИРОВАНИЕ utils/constants.py (Icons, StatusColors)")
    print("-" * 60)
    try:
        from utils.constants import Icons, StatusColors

        # Тест Icons.PRIORITY
        priority_icon = Icons.PRIORITY.get('Высокий')
        print(f"  ✅ Icons.PRIORITY['Высокий'] = {priority_icon}")
        assert priority_icon == '🔴', "Иконка приоритета неверна"

        # Тест Icons.STATUS
        status_icon = Icons.STATUS.get('Выполнена')
        print(f"  ✅ Icons.STATUS['Выполнена'] = {status_icon}")
        assert status_icon == '✅', "Иконка статуса неверна"

        # Тест StatusColors
        color = StatusColors.COLORS.get('Активная')
        print(f"  ✅ StatusColors.COLORS['Активная'] = {color}")
        assert color == '#17a2b8', "Цвет статуса неверен"

        print("  ✅ utils/constants.py (Icons, StatusColors) РАБОТАЕТ КОРРЕКТНО")
    except Exception as e:
        print(f"  ❌ ОШИБКА в constants.py: {e}")
        return False

    # 5. Тестирование models с валидацией
    print("\n5️⃣  ТЕСТИРОВАНИЕ models (Client, Task, ContactPerson)")
    print("-" * 60)
    try:
        from models.client import Client
        from models.task import Task
        from models.contact_person import ContactPerson

        # Тест Client.validate_company_name
        client = Client(company="ООО Тест")
        is_valid, msg = client.validate_company_name("ООО Тест")
        print(f"  ✅ Client.validate_company_name('ООО Тест') = {is_valid}")
        assert is_valid == True, f"Валидация клиента не работает: {msg}"

        is_valid, msg = client.validate_company_name("")
        assert is_valid == False, "Валидация пустого имени не работает"
        print(f"  ✅ Client.validate_company_name('') вернул ошибку: {msg}")

        # Тест Task.validate_title
        task = Task(title="Тестовая задача")
        is_valid, msg = task.validate_title("Тестовая задача")
        print(f"  ✅ Task.validate_title('Тестовая задача') = {is_valid}")
        assert is_valid == True, f"Валидация задачи не работает: {msg}"

        # Тест ContactPerson.validate_full_name
        contact = ContactPerson(full_name="Иван Петров")
        is_valid, msg = contact.validate_full_name("Иван Петров")
        print(f"  ✅ ContactPerson.validate_full_name('Иван Петров') = {is_valid}")
        assert is_valid == True, f"Валидация контакта не работает: {msg}"

        # Тест is_valid_for_save
        assert client.is_valid_for_save() == True, "Client.is_valid_for_save() не работает"
        print(f"  ✅ Client.is_valid_for_save() = True")

        assert task.is_valid_for_save() == True, "Task.is_valid_for_save() не работает"
        print(f"  ✅ Task.is_valid_for_save() = True")

        assert contact.is_valid_for_save() == True, "ContactPerson.is_valid_for_save() не работает"
        print(f"  ✅ ContactPerson.is_valid_for_save() = True")

        print("  ✅ models (валидация) РАБОТАЕТ КОРРЕКТНО")
    except Exception as e:
        print(f"  ❌ ОШИБКА в models: {e}")
        return False

    # Финальный результат
    print("\n" + "="*60)
    print("✅ ФАЗА 1 (День 1-2) ПОЛНОСТЬЮ УСПЕШНА!")
    print("="*60)
    print("\n📊 Результаты:")
    print("  ✅ utils/formatters.py — создан и работает")
    print("  ✅ utils/dto.py — создан и работает")
    print("  ✅ utils/parsers.py — создан и работает")
    print("  ✅ utils/constants.py — обновлён (Icons, StatusColors)")
    print("  ✅ models/client.py — обновлена (валидация)")
    print("  ✅ models/task.py — обновлена (валидация)")
    print("  ✅ models/contact_person.py — обновлена (валидация)")
    print("\n🎯 Следующий шаг: ФАЗА 2 (День 3-5)")
    print("   Добавить методы сортировки в managers/\n")

    return True

if __name__ == "__main__":
    success = test_phase1()
    exit(0 if success else 1)

