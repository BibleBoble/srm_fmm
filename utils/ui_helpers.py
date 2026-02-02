# utils/ui_helpers.py

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


def center_toplevel(window: tk.Toplevel) -> None:
    """Центрирует Toplevel окно на экране"""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def create_labeled_entry(
    parent,
    label_text: str,
    row: int,
    width: int = 50,  # как в clients (шире для ввода)
    required: bool = False
) -> tk.Entry:
    """Создаёт метку + однострочное поле ввода — стиль как в clients"""
    tk.Label(parent, text=label_text + (" *" if required else ""),
             bg="white", fg="#333", font=("Arial", 10)).grid(
        row=row, column=0, padx=15, pady=8, sticky="e"  # больше padx/pady как в диалогах clients
    )
    entry = tk.Entry(parent, width=width, font=("Arial", 10), relief="flat", bd=1, highlightthickness=1, highlightcolor="#ccc")
    entry.grid(row=row, column=1, padx=15, pady=8, sticky="ew")
    return entry


def create_labeled_text(
    parent,
    label_text: str,
    row: int,
    height: int = 4,  # как в clients для notes
    width: int = 60,
    required: bool = False
) -> tk.Text:
    """Создаёт метку + многострочное поле — стиль как в clients"""
    tk.Label(parent, text=label_text + (" *" if required else ""),
             bg="white", fg="#333", font=("Arial", 10)).grid(
        row=row, column=0, padx=15, pady=8, sticky="ne"
    )
    text = tk.Text(parent, height=height, width=width, font=("Arial", 10), wrap="word",
                   relief="flat", bd=1, highlightthickness=1, highlightcolor="#ccc")
    text.grid(row=row, column=1, padx=15, pady=8, sticky="ew")
    return text


def create_search_frame(
    parent,
    search_var: tk.StringVar,
    on_search_changed,
    search_fields: str | list[str] | None = None,
    delay_ms: int = 400
) -> None:
    """
    Создаёт строку поиска + пояснение по полям поиска — стиль как в clients
    """
    frame = tk.Frame(parent, bg="white")
    frame.pack(fill="x", padx=15, pady=(15, 5))  # pady как в clients

    tk.Label(frame, text="Поиск:", bg="white", fg="#333", font=("Arial", 10)).pack(side="left", padx=(0, 10))

    entry = tk.Entry(frame, textvariable=search_var, width=60, font=("Arial", 10), relief="flat", bd=1, highlightthickness=1, highlightcolor="#ccc")
    entry.pack(side="left", fill="x", expand=True)

    # Формируем текст пояснения
    if search_fields:
        if isinstance(search_fields, list):
            fields_text = ", ".join(search_fields)
        else:
            fields_text = str(search_fields).strip()

        if fields_text:
            label = tk.Label(
                frame,
                text=f"Поиск по: {fields_text}",
                bg="white",
                fg="#666",
                font=("Arial", 9, "italic")
            )
            label.pack(side="left", padx=15)

    # debounce
    job = [None]

    def on_change(*args):
        if job[0]:
            parent.after_cancel(job[0])
        job[0] = parent.after(delay_ms, lambda: on_search_changed(search_var.get().strip()))

    search_var.trace("w", on_change)


def show_message(parent, title: str, message: str, icon: str = "info"):
    """Удобная обёртка над messagebox — стиль сообщений как в clients"""
    if icon == "info":
        messagebox.showinfo(title, message, parent=parent)
    elif icon == "warning":
        messagebox.showwarning(title, message, parent=parent)
    elif icon == "error":
        messagebox.showerror(title, message, parent=parent)
    else:
        messagebox.showinfo(title, message, parent=parent)

def show_confirmation(parent, title: str, message: str) -> bool:
    """Показывает диалог подтверждения (Да/Нет) и возвращает True/False"""
    from tkinter import messagebox
    return messagebox.askyesno(title, message, parent=parent)