"""
Представление договоров
"""
import tkinter as tk
from views.base_view import BaseView


class ContractsView(BaseView):
    """Класс для отображения договоров"""

    def show(self):
        """Отображает раздел 'Договора'"""
        self.clear()

        tk.Label(
            self.parent_frame,
            text="Раздел: Договора",
            font=("Arial", 24),
            fg="#333",
            bg='white'
        ).pack(pady=50)

        tk.Label(
            self.parent_frame,
            text="Здесь будет список договоров...",
            font=("Arial", 14),
            fg="gray",
            bg='white'
        ).pack()