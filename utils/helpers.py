"""
Вспомогательные функции общего назначения
"""


def clear_frame(frame):
    """
    Удаляет все дочерние виджеты из фрейма.

    Args:
        frame: tk.Frame - контейнер для очистки
    """
    for widget in frame.winfo_children():
        widget.destroy()


def show_message(parent, title, message, msg_type="info"):
    """
    Показать сообщение без системного звука

    Args:
        parent: родительское окно
        title: str - заголовок окна
        message: str - текст сообщения
        msg_type: str - тип сообщения ("info", "success", "warning", "error")
    """
    import tkinter as tk

    # Цвета в зависимости от типа
    colors = {
        "info": {"bg": "#2196F3", "icon": "ℹ"},
        "success": {"bg": "#4CAF50", "icon": "✓"},
        "warning": {"bg": "#FF9800", "icon": "⚠"},
        "error": {"bg": "#f44336", "icon": "✗"}
    }

    color_data = colors.get(msg_type, colors["info"])

    # Создаём независимое окно
    dialog = tk.Tk()
    dialog.title(title)
    dialog.geometry("450x250")
    dialog.resizable(False, False)
    dialog.configure(bg='white')
    dialog.attributes('-topmost', True)

    # Заголовок
    header = tk.Frame(dialog, bg=color_data["bg"], height=70)
    header.pack(side=tk.TOP, fill=tk.X)
    header.pack_propagate(False)

    tk.Label(
        header,
        text=f"{color_data['icon']} {title}",
        font=("Arial", 18, "bold"),
        fg='white',
        bg=color_data["bg"]
    ).place(relx=0.5, rely=0.5, anchor='center')

    # Текст сообщения
    message_frame = tk.Frame(dialog, bg='white')
    message_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=30, pady=20)

    tk.Label(
        message_frame,
        text=message,
        font=("Arial", 12),
        fg='#333',
        bg='white',
        wraplength=380,
        justify='center'
    ).pack(expand=True)

    # Кнопка
    button_frame = tk.Frame(dialog, bg='white', height=70)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)
    button_frame.pack_propagate(False)

    def close_dialog():
        dialog.quit()
        dialog.destroy()

    btn = tk.Button(
        button_frame,
        text="ОК",
        command=close_dialog,
        bg=color_data["bg"],
        fg="white",
        font=("Arial", 12, "bold"),
        width=20,
        height=2,
        relief="solid",
        bd=2,
        cursor="hand2"
    )
    btn.place(relx=0.5, rely=0.5, anchor='center')

    # Привязки
    dialog.bind('<Return>', lambda e: close_dialog())
    dialog.bind('<Escape>', lambda e: close_dialog())

    # Центрируем
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() - 450) // 2
    y = (dialog.winfo_screenheight() - 250) // 2
    dialog.geometry(f"450x250+{x}+{y}")

    btn.focus_set()

    dialog.mainloop()


def show_confirmation(parent, title, message):
    """
    Показать диалог подтверждения без звука

    Args:
        parent: родительское окно
        title: str - заголовок
        message: str - текст вопроса

    Returns:
        bool - True если нажато "Да", False если "Нет"
    """
    import tkinter as tk

    result = [False]

    # Создаём НЕЗАВИСИМОЕ окно (не Toplevel)
    dialog = tk.Tk()
    dialog.title(title)

    # Фиксированный размер
    dialog.geometry("600x400")
    dialog.resizable(False, False)
    dialog.configure(bg='white')

    # Поверх всех окон
    dialog.attributes('-topmost', True)

    # Убираем стандартные кнопки окна (чтобы нельзя было закрыть крестиком)
    dialog.protocol("WM_DELETE_WINDOW", lambda: None)

    # ============================================
    # ЗАГОЛОВОК
    # ============================================
    header = tk.Frame(dialog, bg='#FF6B6B', height=80)
    header.pack(side=tk.TOP, fill=tk.X)
    header.pack_propagate(False)

    tk.Label(
        header,
        text=f"⚠ {title}",
        font=("Arial", 20, "bold"),
        fg='white',
        bg='#FF6B6B'
    ).place(relx=0.5, rely=0.5, anchor='center')

    # ============================================
    # ТЕКСТ СООБЩЕНИЯ
    # ============================================
    message_frame = tk.Frame(dialog, bg='white')
    message_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=30, pady=20)

    tk.Label(
        message_frame,
        text=message,
        font=("Arial", 12),
        fg='#333',
        bg='white',
        wraplength=530,
        justify='left'
    ).pack(anchor='w')

    # ============================================
    # КНОПКИ (ФИКСИРОВАНЫ ВНИЗУ)
    # ============================================
    buttons_bg = tk.Frame(dialog, bg='#f0f0f0', height=100)
    buttons_bg.pack(side=tk.BOTTOM, fill=tk.X)
    buttons_bg.pack_propagate(False)

    # Контейнер для центрирования кнопок
    buttons_container = tk.Frame(buttons_bg, bg='#f0f0f0')
    buttons_container.place(relx=0.5, rely=0.5, anchor='center')

    def on_yes():
        result[0] = True
        dialog.quit()
        dialog.destroy()

    def on_no():
        result[0] = False
        dialog.quit()
        dialog.destroy()

    # Кнопка "ДА, УДАЛИТЬ"
    yes_btn = tk.Button(
        buttons_container,
        text="ДА, УДАЛИТЬ",
        command=on_yes,
        bg="#DC3545",
        fg="white",
        font=("Arial", 13, "bold"),
        width=18,
        height=2,
        relief="solid",
        bd=2,
        cursor="hand2",
        activebackground="#C82333",
        activeforeground="white"
    )
    yes_btn.grid(row=0, column=0, padx=15)

    # Кнопка "ОТМЕНА"
    no_btn = tk.Button(
        buttons_container,
        text="ОТМЕНА",
        command=on_no,
        bg="#6C757D",
        fg="white",
        font=("Arial", 13, "bold"),
        width=18,
        height=2,
        relief="solid",
        bd=2,
        cursor="hand2",
        activebackground="#5A6268",
        activeforeground="white"
    )
    no_btn.grid(row=0, column=1, padx=15)

    # Привязки клавиш
    dialog.bind('<Escape>', lambda e: on_no())

    # Центрируем окно на экране
    dialog.update_idletasks()
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    x = (screen_width - 600) // 2
    y = (screen_height - 400) // 2
    dialog.geometry(f"600x400+{x}+{y}")

    # Фокус на кнопку "Отмена"
    no_btn.focus_set()

    # Запускаем главный цикл для этого окна
    dialog.mainloop()

    return result[0]