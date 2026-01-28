"""
Базовый класс для всех представлений (разделов приложения)
"""
import tkinter as tk
from utils.helpers import clear_frame


class BaseView:
    """
    Базовый класс для представлений.
    Все разделы приложения наследуют этот класс.
    """

    def __init__(self, parent_frame):
        """
        Args:
            parent_frame: tk.Frame - контейнер, куда будет отрисовано представление
        """
        self.parent_frame = parent_frame

    def clear(self):
        """Очищает родительский фрейм"""
        clear_frame(self.parent_frame)

    def show(self):
        """
        Отображает представление.
        ОБЯЗАТЕЛЬНО переопределяется в дочерних классах.
        """
        raise NotImplementedError(
            f"Метод show() должен быть переопределён в классе {self.__class__.__name__}"
        )