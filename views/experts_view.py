# views/experts_view.py

import tkinter as tk  # <-- Добавьте эту строку
from views.table_view_template import TableViewTemplate
from utils.ui_helpers import show_message

class ExpertsView(TableViewTemplate):
    # Настройки раздела
    TITLE = "Эксперты"
    ADD_BUTTON_TEXT = "+ Добавить эксперта"
    SEARCH_HINT = "Поиск по компании или контактному лицу"
    SEARCH_FIELDS_TEXT = "компании, контактному лицу, виду работ"

    # Настройки таблицы
    COLUMNS = ("Название", "Контактное лицо", "Телефон", "Email", "Виды работ")
    COLUMN_WIDTHS = {
        "Название": 240,
        "Контактное лицо": 190,
        "Телефон": 150,
        "Email": 220,
        "Виды работ": 260
    }
    STRETCH_COLUMNS = ["Название", "Виды работ"]

    # Пагинация
    USE_PAGINATION = True
    PAGE_SIZE = 30  # Совпадает с per_page по умолчанию в менеджере
    SHOW_PAGE_INFO = True

    def __init__(self, parent_frame, experts_mgr):
        super().__init__(parent_frame, experts_mgr)
        self.experts_mgr = experts_mgr

    def _get_paginated_data(self, page=1, per_page=50, search=None):
        """Использует встроенный метод менеджера для пагинации"""
        try:
            # Ваш менеджер уже имеет get_paginated!
            items, total = self.manager.get_paginated(
                page=page,
                per_page=per_page,
                search=search,
                sort_by=self.sort_by,
                sort_order=self.sort_order
            )
            return items, total
        except Exception as e:
            print(f"Ошибка получения пагинированных данных экспертов: {e}")
            # Резервный вариант
            try:
                all_items = self.manager.get_all()
                total = len(all_items)
                start = (page - 1) * per_page
                end = start + per_page
                return all_items[start:end], total
            except:
                return [], 0

    def _item_to_row_values(self, item):
        """Преобразует эксперта в строку таблицы"""
        if not isinstance(item, dict):
            try:
                item = dict(item)
            except:
                item = {}

        # Получаем данные из словаря
        name = item.get('name', '—')

        # Контактные данные
        primary_contact = item.get('primary_contact', '—')
        primary_phone = item.get('primary_phone', '—')
        primary_email = item.get('primary_email', '—')

        # Виды работ
        specializations = item.get('specializations_str', '')
        if not specializations and 'specializations' in item:
            specs = item['specializations']
            if isinstance(specs, list):
                specializations = ", ".join(specs)
            elif isinstance(specs, str):
                specializations = specs

        return (
            name,
            primary_contact or '—',
            primary_phone or '—',
            primary_email or '—',
            specializations or '—'
        )

    def _open_create_dialog(self):
        """Открыть диалог создания эксперта"""
        show_message(self.parent_frame, "В разработке",
                     "Создание эксперта пока не реализовано", "info")

    def _open_detail_dialog(self, expert_id):
        """Открыть карточку эксперта"""
        try:
            expert = self.experts_mgr.get_expert_by_id(expert_id)
            if expert:
                self._show_expert_detail(expert)
            else:
                show_message(self.parent_frame, "Ошибка",
                             f"Эксперт с ID {expert_id} не найден", "error")
        except Exception as e:
            show_message(self.parent_frame, "Ошибка",
                         f"Не удалось загрузить данные эксперта: {str(e)}", "error")

    def _show_expert_detail(self, expert):
        """Показать детали эксперта (упрощенная версия)"""
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title(f"Эксперт: {expert.get('name', '')}")
        dialog.geometry("600x500")
        dialog.configure(bg='white')

        # Заголовок
        header = tk.Frame(dialog, bg='#333333', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"👨‍💼 {expert.get('name', 'Эксперт')}",
            font=("Arial", 16, "bold"),
            fg="white",
            bg='#333333'
        ).pack(side=tk.LEFT, padx=20, pady=15)

        # Основная информация
        main_frame = tk.Frame(dialog, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Название
        tk.Label(main_frame, text="Название:", font=("Arial", 11, "bold"),
                 bg='white').pack(anchor='w', pady=5)
        tk.Label(main_frame, text=expert.get('name', '—'), font=("Arial", 11),
                 bg='white').pack(anchor='w', pady=(0, 15))

        # Контактные лица
        contacts = expert.get('contacts', [])
        if contacts:
            tk.Label(main_frame, text="Контактные лица:", font=("Arial", 11, "bold"),
                     bg='white').pack(anchor='w', pady=5)

            for contact in contacts:
                contact_text = f"• {contact.get('full_name', '—')}"
                if contact.get('position'):
                    contact_text += f" ({contact.get('position')})"
                if contact.get('phone'):
                    contact_text += f" 📞 {contact.get('phone')}"
                if contact.get('email'):
                    contact_text += f" ✉ {contact.get('email')}"
                if contact.get('is_primary'):
                    contact_text += " ⭐"

                tk.Label(main_frame, text=contact_text, font=("Arial", 10),
                         bg='white').pack(anchor='w', pady=2)

        # Специализации
        specializations = expert.get('specializations', [])
        if specializations:
            tk.Label(main_frame, text="Виды работ:", font=("Arial", 11, "bold"),
                     bg='white').pack(anchor='w', pady=(15, 5))

            for spec in specializations:
                tk.Label(main_frame, text=f"• {spec}", font=("Arial", 10),
                         bg='white').pack(anchor='w', pady=2)

        # Кнопки
        btn_frame = tk.Frame(dialog, bg='#f0f0f0', height=60)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        btn_frame.pack_propagate(False)

        tk.Button(
            btn_frame,
            text="Закрыть",
            command=dialog.destroy,
            bg="#6c757d",
            fg="white",
            font=("Arial", 11),
            relief="flat",
            padx=20,
            pady=10
        ).pack(pady=10)

    def _handle_column_click(self, obj_id, column_name):
        """Обработка клика по колонке 'Виды работ'"""
        if column_name == "Виды работ" and obj_id:
            try:
                expert = self.experts_mgr.get_expert_by_id(obj_id)
                if expert and expert.get('specializations'):
                    specs = expert['specializations']
                    if isinstance(specs, list):
                        spec_text = "\n".join([f"• {s}" for s in specs])
                        show_message(self.parent_frame, "Виды работ",
                                     spec_text, "info")
            except:
                pass