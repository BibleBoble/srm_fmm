"""
Точка входа в приложение SRM FMM
Система управления отношениями с клиентами для ФММ
"""
import tkinter as tk
from app import App


def main():
    """Запуск приложения"""
    print("=" * 50)
    print("Запуск приложения SRM FMM")
    print("=" * 50)

    root = tk.Tk()
    app = App(root)
    root.mainloop()

    print("\nПриложение закрыто")


if __name__ == "__main__":
    main()