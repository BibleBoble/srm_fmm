# -*- coding: utf-8 -*-
"""Тест встраивания почты (views/mail_webview.py) в том же процессе.

Запуск из папки проекта:
    .venv\\Scripts\\python.exe test_embed_mail.py

Откроется окно Tk с белым фреймом — в него будет встроен WebView2
с Яндекс.Почтой. Все ошибки/Traceback видны прямо в консоли.
Закрытие окна браузера завершает скрипт.
"""
import sys
import tkinter as tk

root = tk.Tk()
root.title("Тест встраивания почты")
root.geometry("1100x750")
frame = tk.Frame(root, bg="white")
frame.pack(fill="both", expand=True)
root.update()
root.update_idletasks()

hwnd = frame.winfo_id()
width = frame.winfo_width()
height = frame.winfo_height()
print("HWND контейнера:", hwnd)
print("Размер контейнера:", width, "x", height)
if width < 100 or height < 100:
    print("ВНИМАНИЕ: контейнер слишком мал — окно может не встроиться.")

sys.argv = ["mail_webview", str(hwnd), str(width), str(height)]

try:
    from views.mail_webview import main as mail_main
    mail_main()
except Exception:
    import traceback
    traceback.print_exc()
    input("\nОшибка — нажмите Enter...")

print("Тест завершён.")
