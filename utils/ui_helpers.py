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


def confirm_close_on_focus_loss(window: tk.Toplevel, on_close=None) -> None:
    """Asks before closing a window when focus moves outside its owned dialogs."""
    state = {"pending": False}

    def handle_focus_loss(event=None):
        if state["pending"]:
            return
        state["pending"] = True

        def confirm_if_focus_left():
            if not window.winfo_exists():
                state["pending"] = False
                return

            focused = window.focus_get()
            focused_top = focused.winfo_toplevel() if focused else None
            current = focused_top
            while current is not None:
                if current == window:
                    state["pending"] = False
                    return
                try:
                    owner_path = current.transient()
                    current = window.nametowidget(owner_path) if owner_path else None
                except (KeyError, tk.TclError):
                    current = None

            should_close = messagebox.askyesno(
                "Закрыть окно?",
                "Окно потеряло фокус. Закрыть его?",
                parent=window
            )
            state["pending"] = False
            if should_close:
                if on_close:
                    on_close()
                elif window.winfo_exists():
                    window.destroy()
            elif window.winfo_exists():
                window.deiconify()
                window.lift()
                window.focus_force()

        try:
            window.after_idle(confirm_if_focus_left)
        except tk.TclError:
            state["pending"] = False

    window.bind("<FocusOut>", handle_focus_loss, add="+")


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