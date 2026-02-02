# -*- coding: utf-8 -*-
"""
Скрипт миграции базы данных
Переход с client_emails на contact_emails
"""
import sqlite3
from pathlib import Path
from datetime import datetime


class Migration:
    """Класс для миграции БД"""

    def __init__(self, db_path: str = "database.db"):
        self.db_path = db_path
        self.backup_path = None

    def create_backup(self) -> bool:
        """Создать резервную копию перед миграцией"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_path = f"database_backup_{timestamp}.db"

            # Копируем БД
            conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(self.backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
            conn.close()

            print(f"✓ Резервная копия создана: {self.backup_path}")
            return True

        except Exception as e:
            print(f"✗ Ошибка создания резервной копии: {e}")
            return False

    def check_old_schema(self) -> bool:
        """Проверить, существует ли старая схема client_emails"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Проверяем наличие старой таблицы
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='client_emails'
            """)

            old_table_exists = cursor.fetchone() is not None
            conn.close()

            return old_table_exists

        except Exception as e:
            print(f"✗ Ошибка проверки схемы: {e}")
            return False

    def migrate_emails(self) -> bool:
        """
        Миграция email с client_emails на contact_emails

        Логика:
        1. Получаем все старые email
        2. Для каждого email находим основное контактное лицо клиента
        3. Переносим email на это контактное лицо
        4. Удаляем старую таблицу
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            print("\n→ Начинаем миграцию email...")

            # Получаем все старые email
            cursor.execute("SELECT * FROM client_emails")
            old_emails = cursor.fetchall()

            print(f"  Найдено старых email: {len(old_emails)}")

            migrated = 0
            skipped = 0

            for email in old_emails:
                # Преобразуем Row в dict для удобства
                email_dict = dict(email)

                # Находим основное контактное лицо клиента
                cursor.execute("""
                    SELECT id FROM contact_persons 
                    WHERE client_id = ? AND is_primary = 1
                    LIMIT 1
                """, (email_dict['client_id'],))

                contact = cursor.fetchone()

                if contact:
                    contact_dict = dict(contact)

                    # Проверяем, не существует ли уже такой email у этого контакта
                    cursor.execute("""
                        SELECT id FROM contact_emails
                        WHERE contact_person_id = ? AND email = ?
                    """, (contact_dict['id'], email_dict['email']))

                    existing = cursor.fetchone()

                    if not existing:
                        # Переносим email на основной контакт
                        cursor.execute("""
                            INSERT INTO contact_emails 
                            (contact_person_id, email, is_primary, created_at)
                            VALUES (?, ?, ?, ?)
                        """, (
                            contact_dict['id'],
                            email_dict['email'],
                            email_dict['is_primary'],
                            email_dict.get('created_at', datetime.now().isoformat())
                        ))
                        migrated += 1
                    else:
                        print(f"  ⚠ Email {email_dict['email']} уже существует у контакта {contact_dict['id']}")
                        skipped += 1
                else:
                    print(
                        f"  ⚠ Не найден основной контакт для клиента {email_dict['client_id']}, email '{email_dict['email']}' пропущен")
                    skipped += 1

            conn.commit()

            # Удаляем старую таблицу
            cursor.execute("DROP TABLE IF EXISTS client_emails")
            conn.commit()

            conn.close()

            print(f"\n✓ Миграция завершена:")
            print(f"  • Перенесено: {migrated} email")
            print(f"  • Пропущено: {skipped} email")
            print(f"  • Старая таблица удалена")

            return True

        except Exception as e:
            print(f"\n✗ Ошибка миграции: {e}")
            print(f"  Резервная копия сохранена: {self.backup_path}")
            return False

    def migrate_experts_table(self) -> bool:
        """
        Миграция таблицы experts
        Удаляет старую структуру с полями specialization, phone, email
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            print("\n→ Проверяем структуру таблицы experts...")

            # Получаем информацию о колонках
            cursor.execute("PRAGMA table_info(experts)")
            columns = cursor.fetchall()
            column_names = [col['name'] for col in columns]

            # Проверяем, есть ли старые колонки
            old_columns = ['specialization', 'phone', 'email']
            has_old_structure = any(col in column_names for col in old_columns)

            if not has_old_structure:
                print("  ✓ Таблица experts уже имеет новую структуру")
                conn.close()
                return True

            print("  → Найдена старая структура, начинаем миграцию...")

            # Получаем все старые данные
            cursor.execute("SELECT * FROM experts")
            old_experts = cursor.fetchall()

            print(f"  Найдено экспертов: {len(old_experts)}")

            # Создаем временную таблицу с новой структурой
            cursor.execute("""
                CREATE TABLE experts_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Переносим данные
            migrated_experts = 0
            migrated_contacts = 0
            migrated_specs = 0

            for expert in old_experts:
                # Преобразуем Row в dict
                expert_dict = dict(expert)

                # Вставляем эксперта
                cursor.execute("""
                    INSERT INTO experts_new (id, name, created_at)
                    VALUES (?, ?, ?)
                """, (
                    expert_dict['id'],
                    expert_dict['name'],
                    expert_dict.get('created_at', datetime.now().isoformat())
                ))
                migrated_experts += 1

                # Создаем контакт, если есть phone или email
                phone = expert_dict.get('phone', '')
                email = expert_dict.get('email', '')

                if phone or email:
                    cursor.execute("""
                        INSERT INTO expert_contacts 
                        (expert_id, full_name, phone, email, is_primary)
                        VALUES (?, ?, ?, ?, 1)
                    """, (
                        expert_dict['id'],
                        expert_dict['name'],  # Используем имя эксперта
                        phone,
                        email
                    ))
                    migrated_contacts += 1

                # Создаем специализацию, если есть
                specialization = expert_dict.get('specialization', '')
                if specialization:
                    cursor.execute("""
                        INSERT INTO expert_specializations
                        (expert_id, specialization)
                        VALUES (?, ?)
                    """, (expert_dict['id'], specialization))
                    migrated_specs += 1

            # Удаляем старую таблицу и переименовываем новую
            cursor.execute("DROP TABLE experts")
            cursor.execute("ALTER TABLE experts_new RENAME TO experts")

            conn.commit()
            conn.close()

            print(f"\n✓ Миграция таблицы experts завершена:")
            print(f"  • Перенесено экспертов: {migrated_experts}")
            print(f"  • Создано контактов: {migrated_contacts}")
            print(f"  • Создано специализаций: {migrated_specs}")

            return True

        except Exception as e:
            print(f"\n✗ Ошибка миграции таблицы experts: {e}")
            return False

    def run(self) -> bool:
        """Запустить полную миграцию"""
        print("\n" + "=" * 50)
        print("МИГРАЦИЯ БАЗЫ ДАННЫХ")
        print("=" * 50)

        # Шаг 1: Создаем резервную копию
        print("\n[1/4] Создание резервной копии...")
        if not self.create_backup():
            print("\n✗ Миграция отменена из-за ошибки создания резервной копии")
            return False

        # Шаг 2: Проверяем необходимость миграции email
        print("\n[2/4] Проверка схемы email...")
        if self.check_old_schema():
            print("  → Найдена старая схема client_emails")
            if not self.migrate_emails():
                print("\n✗ Миграция email не удалась")
                return False
        else:
            print("  ✓ Старая схема не найдена, миграция email не требуется")

        # Шаг 3: Миграция таблицы experts
        print("\n[3/4] Миграция таблицы experts...")
        if not self.migrate_experts_table():
            print("\n✗ Миграция таблицы experts не удалась")
            return False

        # Шаг 4: Оптимизация БД
        print("\n[4/4] Оптимизация БД...")
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()
            print("  ✓ БД оптимизирована")
        except Exception as e:
            print(f"  ⚠ Ошибка оптимизации: {e}")

        print("\n" + "=" * 50)
        print("✓ МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
        print("=" * 50)
        print(f"\nРезервная копия сохранена: {self.backup_path}")
        print("Вы можете безопасно удалить её после проверки работы приложения.\n")

        return True


def main():
    """Главная функция"""
    import sys

    # Проверяем наличие файла БД
    db_path = "database.db"

    if not Path(db_path).exists():
        print(f"✗ Файл {db_path} не найден!")
        print("  Миграция не требуется для новой БД.")
        sys.exit(1)

    # Запрашиваем подтверждение
    print("\n⚠ ВНИМАНИЕ!")
    print("Сейчас будет произведена миграция базы данных.")
    print("Будет создана резервная копия, но на всякий случай")
    print("рекомендуется сделать ручную копию файла database.db")

    response = input("\nПродолжить миграцию? (yes/no): ").lower().strip()

    if response not in ['yes', 'y', 'да', 'д']:
        print("\n✗ Миграция отменена пользователем")
        sys.exit(0)

    # Запускаем миграцию
    migration = Migration(db_path)
    success = migration.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()