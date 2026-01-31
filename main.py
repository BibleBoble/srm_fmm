"""
Точка входа в приложение SRM FMM
Система управления отношениями с клиентами для ФММ
"""
import tkinter as tk
from app import App


def main():
    print("=" * 50)
    print("Запуск приложения SRM FMM (Classic Mode)")
    print("=" * 50)

    # Возвращаем стандартный Tk
    root = tk.Tk()

    # Устанавливаем размер, который был удобен
    root.geometry("1200x800")

    app = App(root)
    root.mainloop()

    print("\nПриложение закрыто")


if __name__ == "__main__":
    main()