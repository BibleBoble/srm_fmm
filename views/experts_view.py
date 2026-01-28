"""
Представление экспертов
"""
import tkinter as tk
from views.base_view import BaseView


class ExpertsView(BaseView):
    """Класс для отображения экспертов"""

    def show(self):
        """Отображает раздел 'Эксперты'"""
        self.clear()

        tk.Label(
            self.parent_frame,
            text="Раздел: Эксперты",
            font=("Arial", 24),
            fg="#333",
            bg='white'
        ).pack(pady=50)

        tk.Label(
            self.parent_frame,
            text="Здесь будет список экспертов...",
            font=("Arial", 14),
            fg="gray",
            bg='white'
        ).pack()