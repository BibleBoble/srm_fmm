# -*- coding: utf-8 -*-
"""
Представление раздела "Клиенты" - РЕФАКТОРИНГ
Разделено на 3 класса для соблюдения SRP:
- ClientListView: список клиентов с таблицей
- ClientCardView: карточка клиента с вкладками  
- ClientFormDialog: форма создания/редактирования
"""
import tkinter as tk
from tkinter import messagebox
from views.client_list_view import ClientListView
from views.client_card_view import ClientCardView
from views.client_form_dialog import ClientFormDialog
from services.client_service import ClientService


class ClientsView:
    """
    Главный класс раздела "Клиенты" (Facade + Controller)
    
    Координирует работу 3 специализированных классов:
    - ClientListView: отображает таблицу клиентов
    - ClientCardView: отображает карточку клиента
    - ClientFormDialog: форма создания/редактирования
    
    Usage:
        view = ClientsView(parent_frame, managers...)
        view.show()
    """
    
    def __init__(self, parent_frame, clients_mgr, contact_persons_mgr, 
                 contact_emails_mgr, interactions_mgr, tasks_mgr=None):
        """
        Args:
            parent_frame: родительский фрейм для размещения
            clients_mgr: менеджер клиентов
            contact_persons_mgr: менеджер контактов
            contact_emails_mgr: менеджер email
            interactions_mgr: менеджер взаимодействий
            tasks_mgr: менеджер задач (опционально)
        """
        self.parent_frame = parent_frame
        self.clients_mgr = clients_mgr
        self.contact_persons_mgr = contact_persons_mgr
        self.contact_emails_mgr = contact_emails_mgr
        self.interactions_mgr = interactions_mgr
        self.tasks_mgr = tasks_mgr
        
        # Сервис для операций с клиентами
        self.client_service = ClientService(
            clients_mgr, contact_persons_mgr, 
            contact_emails_mgr, interactions_mgr
        )
        
        # Подпредставления (ленивая инициализация)
        self._list_view = None
        self._current_card = None
        
    def show(self):
        """Показать раздел клиентов"""
        self._show_list_view()
        
    def _show_list_view(self):
        """Показать список клиентов"""
        # Очищаем фрейм
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
            
        # Создаем список клиентов
        self._list_view = ClientListView(
            self.parent_frame,
            self.clients_mgr,
            self.tasks_mgr,
            on_client_click=self._on_client_selected,
            on_add_client=self._on_add_client,
            on_create_task=self._on_create_task
        )
        self._list_view.show()
        
    def _on_client_selected(self, client_id):
        """Обработчик выбора клиента из списка"""
        self._open_client_card(client_id)
        
    def _on_add_client(self):
        """Обработчик добавления нового клиента"""
        dialog = ClientFormDialog(
            self.parent_frame,
            self.client_service,
            on_save=self._on_client_saved
        )
        dialog.show()
        # Ожидаем закрытия диалога и обновляем таблицу
        self.parent_frame.wait_window(dialog.dialog)
        # Если клиент был сохранён, обновляем таблицу
        if dialog.saved_client_id:
            self._on_client_saved(dialog.saved_client_id)
        
    def _on_create_task(self, client_id):
        """Обработчик создания задачи для клиента"""
        # Открываем карточку клиента с активной вкладкой задач
        self._open_client_card(client_id)
        # После открытия карточки можно активировать вкладку задач
        if self._current_card:
            # Активируем вкладку задач (индекс 2)
            try:
                # Находим Notebook в карточке и выбираем вкладку задач
                for widget in self._current_card.card_window.winfo_children():
                    if isinstance(widget, tk.ttk.Notebook):
                        widget.select(2)  # Вкладка задач
                        break
            except Exception:
                pass
        
    def _on_client_saved(self, client_id):
        """Обработчик сохранения клиента"""
        # Обновляем список
        if self._list_view:
            self._list_view.refresh()
            
    def _open_client_card(self, client_id):
        """Открыть карточку клиента"""
        # Проверяем, не открыта ли уже
        if self._current_card and self._current_card.card_window:
            try:
                if self._current_card.card_window.winfo_exists():
                    self._current_card.card_window.lift()
                    return
            except:
                pass
                
        # Создаем новую карточку
        self._current_card = ClientCardView(
            self.parent_frame,
            client_id,
            self.clients_mgr,
            self.contact_persons_mgr,
            self.contact_emails_mgr,
            self.tasks_mgr,
            on_edit=self._on_edit_client,
            on_delete=self._on_delete_client,
            on_close=lambda: setattr(self, '_current_card', None)
        )
        self._current_card.show()
        
    def _on_edit_client(self, client_data, parent_window):
        """Обработчик редактирования клиента"""
        dialog = ClientFormDialog(
            parent_window,
            self.client_service,
            on_save=lambda cid: self._on_client_updated(cid, parent_window),
            client_data=client_data
        )
        dialog.show()
        # Ожидаем закрытия диалога
        parent_window.wait_window(dialog.dialog)
        # Если клиент был сохранён, обновляем
        if dialog.saved_client_id:
            self._on_client_updated(dialog.saved_client_id, parent_window)
        
    def _on_client_updated(self, client_id, parent_window):
        """Обработчик обновления клиента"""
        # Закрываем старую карточку
        parent_window.destroy()
        # Обновляем список клиентов
        if self._list_view:
            self._list_view.refresh()
        # Открываем обновленную карточку
        self._open_client_card(client_id)
        
    def _on_delete_client(self, client_id):
        """Обработчик удаления клиента"""
        # Обновляем список
        if self._list_view:
            self._list_view.refresh()
        self._current_card = None
        
    def refresh(self):
        """Обновить данные"""
        if self._list_view:
            self._list_view.refresh()


# Для обратной совместимости - старый интерфейс
class ClientsViewLegacy:
    """
    Legacy-обертка для обратной совместимости
    Перенаправляет вызовы в новый ClientsView
    """
    
    def __init__(self, parent_frame, clients_mgr, contact_persons_mgr,
                 contact_emails_mgr, interactions_mgr, tasks_mgr=None):
        self._new_view = ClientsView(
            parent_frame, clients_mgr, contact_persons_mgr,
            contact_emails_mgr, interactions_mgr, tasks_mgr
        )
        
    def show(self):
        self._new_view.show()
