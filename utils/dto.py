# -*- coding: utf-8 -*-
"""
Data Transfer Objects для UI представления
"""
from dataclasses import dataclass
from typing import Tuple


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


