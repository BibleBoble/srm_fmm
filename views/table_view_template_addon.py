# -*- coding: utf-8 -*-
"""
Дополнительные методы для TableViewTemplate - диалоги редактирования
"""

def _open_edit_dialog(self, item_id, item_data, fields_config, save_callback, title="Редактирование", geometry="750x650"):
    """Универсальный диалог редактирования записи
    
    Args:
        item_id: ID записи
        item_data: данные записи (dict)
        fields_config: конфигурация полей (как в _create_form_section)
        save_callback: функция сохранения (принимает item_id и данные)
        title: заголовок диалога
        geometry: размеры диалога
    """
    from utils.helpers import show_message
    import tkinter as tk
    
    dialog, content, buttons_frame = self._create_dialog(title, geometry)
    
    # Создаем поля формы
    all_widgets = {}
    
    for section_title, section_fields in fields_config.items():
        # Устанавливаем значения по умолчанию из item_data
        for field in section_fields:
            field_name = field['name']
            if field_name in item_data:
                field['default'] = item_data[field_name]
        
        section_widgets = self._create_form_section(content, section_title, section_fields)
        all_widgets.update(section_widgets)
    
    def save_changes():
        """Сохранение изменений"""
        try:
            # Сбор данных из полей
            updated_data = {}
            
            for field_name, widget in all_widgets.items():
                if isinstance(widget, tk.Text):
                    updated_data[field_name] = widget.get('1.0', tk.END).strip()
                elif hasattr(widget, 'get'):  # Entry и Combobox
                    updated_data[field_name] = widget.get().strip()
                else:
                    updated_data[field_name] = str(widget).strip()
            
            # Вызов callback для сохранения
            if save_callback(item_id, updated_data, dialog):
                dialog.destroy()
                self._refresh_data()
                
        except Exception as e:
            show_message(dialog, "Ошибка", f"Произошла ошибка: {str(e)}", "error")
    
    self._create_dialog_buttons(buttons_frame, save_changes)

# Добавляем метод в класс TableViewTemplate
from views.table_view_template import TableViewTemplate
TableViewTemplate._open_edit_dialog = _open_edit_dialog
