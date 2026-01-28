"""
Представление отчётов
"""
import tkinter as tk
from views.base_view import BaseView


class ReportsView(BaseView):
    """Класс для отображения отчётов"""

    def show(self):
        """Отображает раздел 'Отчеты'"""
        self.clear()

        tk.Label(
            self.parent_frame,
            text="Раздел: Отчеты",
            font=("Arial", 24),
            fg="#333",
            bg='white'
        ).pack(pady=50)

        tk.Label(
            self.parent_frame,
            text="Здесь будут отчёты...",
            font=("Arial", 14),
            fg="gray",
            bg='white'
        ).pack()