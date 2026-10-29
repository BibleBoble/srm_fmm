# managers/experts_manager.py

from managers.database import Database


class ExpertsManager:
    def __init__(self):
        self.db = Database()

    # Эксперты (основная запись)
    def add_expert(self, expert_data: dict) -> int:
        """Добавляет нового эксперта с полной информацией"""
        try:
            # Добавляем основную запись
            name = expert_data.get('name', '').strip()
            if not name:
                raise ValueError("Имя эксперта обязательно")
            
            query = "INSERT INTO experts (name, notes) VALUES (?, ?)"
            expert_id = self.db.execute(query, (name, expert_data.get('notes', '').strip()))
            
            # Добавляем основной контакт если есть
            if expert_data.get('primary_contact') or expert_data.get('primary_phone') or expert_data.get('primary_email'):
                self.add_contact(
                    expert_id,
                    expert_data.get('primary_contact', ''),
                    phone=expert_data.get('primary_phone', ''),
                    email=expert_data.get('primary_email', ''),
                    is_primary=True
                )
            
            # Добавляем специализации
            if expert_data.get('specializations'):
                specs = [s.strip() for s in expert_data['specializations'].split(',') if s.strip()]
                for spec in specs:
                    self.add_specialization(expert_id, spec)
            
            return expert_id
        except Exception as e:
            print(f"Ошибка при добавлении эксперта: {e}")
            return None

    def add_expert_with_contacts(self, expert_data: dict) -> int:
        """Добавляет нового эксперта с несколькими контактными лицами"""
        try:
            # Добавляем основную запись
            name = expert_data.get('name', '').strip()
            if not name:
                raise ValueError("Название компании обязательно")
            
            query = "INSERT INTO experts (name, notes) VALUES (?, ?)"
            expert_id = self.db.execute(query, (name, expert_data.get('notes', '').strip()))
            
            if not expert_id:
                print("❌ Не удалось создать эксперта - expert_id is None")
                return None
            
            print(f"✓ Эксперт создан с ID: {expert_id}")
            
            # Добавляем контактные лица
            if expert_data.get('contacts'):
                for i, contact in enumerate(expert_data['contacts']):
                    print(f"🔄 Добавление контакта {i+1}: {contact.get('full_name', 'N/A')}")
                    
                    contact_id = self.add_contact(
                        expert_id,
                        contact.get('full_name', ''),
                        position=contact.get('position', ''),
                        phone=contact.get('phone', ''),
                        email=contact.get('email', ''),
                        is_primary=contact.get('is_primary', False)
                    )
                    
                    if contact_id:
                        print(f"✓ Контакт {i+1} добавлен с ID: {contact_id}")
                    else:
                        print(f"❌ Не удалось добавить контакт {i+1}")

            # Добавляем специализации (виды работ)
            specializations = expert_data.get('specializations')
            if specializations:
                if isinstance(specializations, str):
                    specs = [s.strip() for s in specializations.split(',') if s.strip()]
                else:
                    specs = [str(s).strip() for s in specializations if str(s).strip()]
                for spec in specs:
                    self.add_specialization(expert_id, spec)
            
            return expert_id
        except Exception as e:
            print(f"❌ Ошибка при добавлении эксперта: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_expert_by_id(self, expert_id: int) -> dict | None:
        expert = self.db.fetch_one("SELECT * FROM experts WHERE id = ?", (expert_id,))
        if not expert:
            return None

        expert_dict = dict(expert)
        expert_dict['contacts'] = self.get_contacts(expert_id)
        expert_dict['specializations'] = self.get_specializations(expert_id)
        return expert_dict

    def update_expert(self, expert_id: int, expert_data: dict) -> bool:
        """Обновляет данные эксперта"""
        try:
            # Обновляем основную информацию
            name = expert_data.get('name', '').strip()
            if not name:
                raise ValueError("Имя эксперта обязательно")
            
            query = "UPDATE experts SET name = ?, notes = ? WHERE id = ?"
            self.db.execute(query, (name, expert_data.get('notes', '').strip(), expert_id))
            
            # Обновляем основной контакт
            existing_contacts = self.get_contacts(expert_id)
            primary_contact = None
            
            # Ищем существующий основной контакт
            for contact in existing_contacts:
                if contact.get('is_primary'):
                    primary_contact = contact
                    break
            
            if expert_data.get('primary_contact') or expert_data.get('primary_phone') or expert_data.get('primary_email'):
                if primary_contact:
                    # Обновляем существующий контакт
                    self.update_contact(
                        primary_contact['id'],
                        expert_data.get('primary_contact', ''),
                        phone=expert_data.get('primary_phone', ''),
                        email=expert_data.get('primary_email', ''),
                        is_primary=True
                    )
                else:
                    # Создаем новый контакт
                    self.add_contact(
                        expert_id,
                        expert_data.get('primary_contact', ''),
                        phone=expert_data.get('primary_phone', ''),
                        email=expert_data.get('primary_email', ''),
                        is_primary=True
                    )
            
            # Обновляем специализации
            # Сначала удаляем все существующие
            self.db.execute("DELETE FROM expert_specializations WHERE expert_id = ?", (expert_id,))
            
            # Добавляем новые
            if expert_data.get('specializations'):
                specs = [s.strip() for s in expert_data['specializations'].split(',') if s.strip()]
                for spec in specs:
                    self.add_specialization(expert_id, spec)
            
            return True
        except Exception as e:
            print(f"Ошибка при обновлении эксперта: {e}")
            return False

    def update_expert_with_contacts(self, expert_id: int, expert_data: dict) -> bool:
        """Обновляет эксперта и список его контактных лиц (до 4)

        expert_data ожидает:
        - name: str
        - notes: str
        - contacts: list[dict] где dict может содержать:
            id (optional), full_name, position, phone, email, is_primary
        """
        try:
            name = (expert_data.get('name') or '').strip()
            if not name:
                raise ValueError("Название компании обязательно")

            notes = (expert_data.get('notes') or '').strip()
            self.db.execute(
                "UPDATE experts SET name = ?, notes = ? WHERE id = ?",
                (name, notes, expert_id)
            )

            incoming = expert_data.get('contacts') or []
            if not isinstance(incoming, list):
                incoming = []

            # Ограничение 4 контакта
            incoming = incoming[:4]

            existing = self.get_contacts(expert_id)
            existing_ids = {c.get('id') for c in existing if c.get('id') is not None}
            incoming_ids = {c.get('id') for c in incoming if c.get('id') is not None}

            # Удаляем контакты, которых больше нет
            for contact_id in (existing_ids - incoming_ids):
                self.delete_contact(contact_id)

            # Сбрасываем primary, затем выставим заново
            self.db.execute("UPDATE expert_contacts SET is_primary = 0 WHERE expert_id = ?", (expert_id,))

            # Upsert контактов
            for c in incoming:
                contact_id = c.get('id')
                full_name = (c.get('full_name') or '').strip()
                if not full_name:
                    continue

                position = (c.get('position') or '').strip()
                phone = (c.get('phone') or '').strip()
                email = (c.get('email') or '').strip()
                is_primary = bool(c.get('is_primary'))

                if contact_id:
                    self.update_contact(
                        contact_id,
                        full_name,
                        position=position,
                        phone=phone,
                        email=email,
                        is_primary=is_primary
                    )
                else:
                    self.add_contact(
                        expert_id,
                        full_name,
                        position=position,
                        phone=phone,
                        email=email,
                        is_primary=is_primary
                    )

            # Обновляем специализации
            self.db.execute("DELETE FROM expert_specializations WHERE expert_id = ?", (expert_id,))
            specializations = expert_data.get('specializations')
            if specializations:
                if isinstance(specializations, str):
                    specs = [s.strip() for s in specializations.split(',') if s.strip()]
                else:
                    specs = [str(s).strip() for s in specializations if str(s).strip()]
                for spec in specs:
                    self.add_specialization(expert_id, spec)

            return True

        except Exception as e:
            print(f"Ошибка при обновлении эксперта с контактами: {e}")
            return False

    def delete_expert(self, expert_id: int):
        self.db.execute("DELETE FROM experts WHERE id = ?", (expert_id,))

    # Контактные лица (до 4)
    def add_contact(self, expert_id: int, full_name: str, position: str = "", phone: str = "", email: str = "", is_primary: bool = False) -> int | None:
        if self.get_contact_count(expert_id) >= 4:
            return None  # Лимит достигнут

        if is_primary:
            self.db.execute("UPDATE expert_contacts SET is_primary = 0 WHERE expert_id = ?", (expert_id,))

        query = """
            INSERT INTO expert_contacts (expert_id, full_name, position, phone, email, is_primary)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        params = (expert_id, full_name.strip(), position.strip(), phone.strip(), email.strip(), int(is_primary))
        return self.db.execute(query, params)

    def get_contacts(self, expert_id: int) -> list[dict]:
        query = """
            SELECT * FROM expert_contacts
            WHERE expert_id = ?
            ORDER BY is_primary DESC, full_name ASC
        """
        rows = self.db.fetch_all(query, (expert_id,))
        return [dict(row) for row in rows]

    def get_contact_count(self, expert_id: int) -> int:
        row = self.db.fetch_one("SELECT COUNT(*) as cnt FROM expert_contacts WHERE expert_id = ?", (expert_id,))
        return row["cnt"] if row else 0

    def update_contact(self, contact_id: int, full_name: str, position: str = "", phone: str = "", email: str = "", is_primary: bool = False):
        contact = self.db.fetch_one("SELECT expert_id FROM expert_contacts WHERE id = ?", (contact_id,))
        if not contact:
            return

        if is_primary:
            self.db.execute("UPDATE expert_contacts SET is_primary = 0 WHERE expert_id = ? AND id != ?", (contact['expert_id'], contact_id))

        query = """
            UPDATE expert_contacts
            SET full_name = ?, position = ?, phone = ?, email = ?, is_primary = ?
            WHERE id = ?
        """
        self.db.execute(query, (full_name.strip(), position.strip(), phone.strip(), email.strip(), int(is_primary), contact_id))

    def delete_contact(self, contact_id: int):
        self.db.execute("DELETE FROM expert_contacts WHERE id = ?", (contact_id,))

    # Специализации (неограниченно)
    def add_specialization(self, expert_id: int, specialization: str) -> int | None:
        spec = specialization.strip()
        if not spec or self.db.fetch_one(
            "SELECT 1 FROM expert_specializations WHERE expert_id = ? AND LOWER(specialization) = LOWER(?)",
            (expert_id, spec)
        ):
            return None  # Пусто или дубликат

        query = "INSERT INTO expert_specializations (expert_id, specialization) VALUES (?, ?)"
        return self.db.execute(query, (expert_id, spec))

    def get_specializations(self, expert_id: int) -> list[str]:
        rows = self.db.fetch_all(
            "SELECT specialization FROM expert_specializations WHERE expert_id = ? ORDER BY specialization",
            (expert_id,)
        )
        return [row["specialization"] for row in rows]

    def delete_specialization(self, expert_id: int, specialization: str):
        self.db.execute(
            "DELETE FROM expert_specializations WHERE expert_id = ? AND specialization = ?",
            (expert_id, specialization.strip())
        )

    # Пагинация + поиск
    def get_paginated(self, page: int = 1, per_page: int = 30, search: str = None, sort_by: str = None, sort_order: str = "ASC"):
        offset = (page - 1) * per_page
        params = []
        where = []

        if search:
            tokens = [
                token.casefold()
                for token in str(search).split()
                if token.strip()
            ]
            for token in tokens:
                where.append("""
                    (
                        FUZZY_CONTAINS(e.name, ?) = 1 OR
                        EXISTS (
                            SELECT 1 FROM expert_contacts ec
                            WHERE ec.expert_id = e.id AND (
                                FUZZY_CONTAINS(ec.full_name, ?) = 1 OR
                                FUZZY_CONTAINS(ec.phone, ?) = 1 OR
                                FUZZY_CONTAINS(ec.email, ?) = 1
                            )
                        ) OR
                        EXISTS (
                            SELECT 1 FROM expert_specializations es
                            WHERE es.expert_id = e.id
                              AND FUZZY_CONTAINS(es.specialization, ?) = 1
                        )
                    )
                """)
                params.extend([token] * 5)

        where_sql = "WHERE " + " AND ".join(where) if where else ""
        params_for_count = params.copy()

        order_by = "ORDER BY e.name ASC"
        if sort_by == "name":
            order_by = f"ORDER BY e.name {sort_order}"

        # Запрос с агрегацией
        query = f"""
            SELECT e.*,
                   (SELECT full_name FROM expert_contacts WHERE expert_id = e.id AND is_primary = 1 LIMIT 1) AS primary_contact,
                   (SELECT phone FROM expert_contacts WHERE expert_id = e.id AND is_primary = 1 LIMIT 1) AS primary_phone,
                   (SELECT email FROM expert_contacts WHERE expert_id = e.id AND is_primary = 1 LIMIT 1) AS primary_email,
                   GROUP_CONCAT(es.specialization, ', ') AS specializations_str
            FROM experts e
            LEFT JOIN expert_specializations es ON es.expert_id = e.id
            {where_sql}
            GROUP BY e.id
            {order_by}
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])

        rows = self.db.fetch_all(query, tuple(params))
        items = [dict(row) for row in rows]

        count_query = f"SELECT COUNT(DISTINCT e.id) as cnt FROM experts e {where_sql}"
        count_row = self.db.fetch_one(count_query, tuple(params_for_count))
        total = count_row["cnt"] if count_row else 0

        return items, total

    def get_count(self) -> int:
        """Возвращает общее количество экспертов"""
        row = self.db.fetch_one("SELECT COUNT(*) as cnt FROM experts")
        return row["cnt"] if row else 0

    def get_all(self) -> list[dict]:
        """Возвращает всех экспертов без пагинации"""
        query = """
            SELECT e.*,
                   (SELECT full_name FROM expert_contacts WHERE expert_id = e.id AND is_primary = 1 LIMIT 1) AS primary_contact,
                   (SELECT phone FROM expert_contacts WHERE expert_id = e.id AND is_primary = 1 LIMIT 1) AS primary_phone,
                   (SELECT email FROM expert_contacts WHERE expert_id = e.id AND is_primary = 1 LIMIT 1) AS primary_email,
                   GROUP_CONCAT(es.specialization, ', ') AS specializations_str
            FROM experts e
            LEFT JOIN expert_specializations es ON es.expert_id = e.id
            GROUP BY e.id
            ORDER BY e.name ASC
        """
        rows = self.db.fetch_all(query)
        return [dict(row) for row in rows] if rows else []
