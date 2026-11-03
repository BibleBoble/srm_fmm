# utils/ui_helpers.py

import tkinter as tk
from tkinter import messagebox


def install_clipboard_bindings(root: tk.Misc) -> None:
    """Устанавливает единые сочетания clipboard для Tk и ttk полей ввода."""
    def selection_text(widget):
        if isinstance(widget, tk.Text):
            if not widget.tag_ranges("sel"):
                return None
            return widget.get("sel.first", "sel.last")
        if not widget.selection_present():
            return None
        start = int(widget.index("sel.first"))
        end = int(widget.index("sel.last"))
        return widget.tk.call("string", "range", widget.get(), start, end - 1)

    def copy_selection(event):
        widget = event.widget
        try:
            selected = selection_text(widget)
            if selected is None:
                return "break"
            widget.clipboard_clear()
            widget.clipboard_append(selected)
            widget.update_idletasks()
        except (tk.TclError, AttributeError):
            return "break"
        return "break"

    def paste_clipboard(event):
        widget = event.widget
        if str(widget.cget("state")) in {"disabled", "readonly"}:
            return "break"
        try:
            value = widget.clipboard_get()
            if isinstance(widget, tk.Text):
                if widget.tag_ranges("sel"):
                    insert_at = widget.index("sel.first")
                    widget.delete("sel.first", "sel.last")
                else:
                    insert_at = widget.index("insert")
                widget.insert(insert_at, value)
                widget.mark_set("insert", f"{insert_at}+{len(value)}c")
            else:
                if widget.selection_present():
                    insert_at = widget.index("sel.first")
                    widget.delete("sel.first", "sel.last")
                    widget.insert(insert_at, value)
                    widget.icursor(insert_at + len(value))
                else:
                    widget.insert("insert", value)
        except (tk.TclError, AttributeError):
            return "break"
        return "break"

    def cut_selection(event):
        widget = event.widget
        if str(widget.cget("state")) in {"disabled", "readonly"}:
            return "break"
        try:
            selected = selection_text(widget)
            if selected is None:
                return "break"
            widget.clipboard_clear()
            widget.clipboard_append(selected)
            widget.update_idletasks()
            widget.delete("sel.first", "sel.last")
        except (tk.TclError, AttributeError):
            return "break"
        return "break"

    def handle_control_key(event):
        """Распознаёт клавиши по Windows keycode при русской раскладке."""
        keycode_actions = {
            65: select_all,
            67: copy_selection,
            86: paste_clipboard,
            88: cut_selection,
            45: copy_selection
        }
        action = keycode_actions.get(event.keycode)
        if action is not None:
            return action(event)

        key_actions = {
            "a": select_all,
            "c": copy_selection,
            "v": paste_clipboard,
            "x": cut_selection,
            "insert": copy_selection
        }
        action = key_actions.get(event.keysym.lower())
        if action is not None:
            return action(event)
        return None

    def select_all(event):
        widget = event.widget
        if isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")
        elif hasattr(widget, "selection_range"):
            widget.selection_range(0, tk.END)
        return "break"

    shortcuts = {
        "<Control-c>": copy_selection,
        "<Control-C>": copy_selection,
        "<Control-v>": paste_clipboard,
        "<Control-V>": paste_clipboard,
        "<Control-x>": cut_selection,
        "<Control-X>": cut_selection,
        "<Control-a>": select_all,
        "<Control-A>": select_all,
        "<Control-Insert>": copy_selection,
        "<Shift-Insert>": paste_clipboard,
        "<Control-KeyPress>": handle_control_key
    }
    for class_name in ("Entry", "Text", "TEntry", "TCombobox"):
        for sequence, callback in shortcuts.items():
            root.bind_class(class_name, sequence, callback)


def center_toplevel(window: tk.Toplevel) -> None:
    """Центрирует Toplevel окно на экране"""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    if width <= 1:
        width = window.winfo_reqwidth()
    if height <= 1:
        height = window.winfo_reqheight()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


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