from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import tkinter as tk
from tkinter import messagebox, ttk

from utils.ui_helpers import center_toplevel


def show_document_input_dialog(
    parent,
    title,
    fields,
    include_line_items=False,
    open_client_folder=None,
    initial_values=None,
    initial_line_items=None
):
    """Собирает реквизиты и строки услуг перед предпросмотром документа.

    initial_values / initial_line_items позволяют открыть форму повторно
    с уже введёнными данными, если при проверке нашлась ошибка.
    """
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry("720x700")
    dialog.minsize(600, 500)
    dialog.transient(parent)

    container = ttk.Frame(dialog)
    container.pack(fill=tk.BOTH, expand=True)
    canvas = tk.Canvas(container, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
    content = ttk.Frame(canvas, padding=14)
    content_id = canvas.create_window((0, 0), window=content, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    content.bind(
        "<Configure>",
        lambda event: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.bind(
        "<Configure>",
        lambda event: canvas.itemconfigure(content_id, width=event.width)
    )
    content.columnconfigure(1, weight=1)

    field_widgets = {}
    initial_values = initial_values or {}
    for row_index, field in enumerate(fields):
        label = f"{field['label']}{' *' if field.get('required') else ''}"
        ttk.Label(content, text=label).grid(
            row=row_index,
            column=0,
            sticky="nw",
            padx=(0, 12),
            pady=6
        )
        value = initial_values.get(field["key"], field.get("value", ""))
        if field.get("choices"):
            widget = ttk.Combobox(
                content,
                values=field["choices"],
                state="readonly"
            )
            widget.set(value)
        elif field.get("multiline"):
            widget = tk.Text(content, height=3, wrap=tk.WORD)
            widget.insert("1.0", value)
        else:
            widget = ttk.Entry(content)
            widget.insert(0, value)
        widget.grid(row=row_index, column=1, sticky="ew", pady=6)
        field_widgets[field["key"]] = widget

    line_rows = []
    if include_line_items:
        line_frame = ttk.LabelFrame(content, text="Услуги", padding=8)
        line_frame.grid(
            row=len(fields),
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(12, 4)
        )
        for column, heading in enumerate(("Наименование", "Срок", "Сумма, руб.")):
            ttk.Label(line_frame, text=heading).grid(
                row=0,
                column=column,
                sticky="w",
                padx=3,
                pady=(0, 5)
            )
        line_frame.columnconfigure(0, weight=3)
        line_frame.columnconfigure(1, weight=2)
        line_frame.columnconfigure(2, weight=2)

        def add_line(initial=None):
            row_number = len(line_rows) + 1
            name = tk.Text(line_frame, width=30, height=5, wrap=tk.WORD)
            name.grid(row=row_number, column=0, sticky="ew", padx=3, pady=3)
            term = ttk.Entry(line_frame, width=18)
            term.grid(row=row_number, column=1, sticky="ew", padx=3, pady=3)
            amount = ttk.Entry(line_frame, width=16)
            amount.grid(row=row_number, column=2, sticky="ew", padx=3, pady=3)
            if initial is not None:
                name.insert("1.0", str(initial.get("name", "")))
                term.insert(0, str(initial.get("term", "")))
                amount.insert(0, str(initial.get("amount", "")))
            widgets = [name, term, amount]
            remove_button = ttk.Button(
                line_frame,
                text="Удалить",
                command=lambda row=widgets: remove_line(row)
            )
            remove_button.grid(row=row_number, column=3, padx=3, pady=3)
            line_rows.append((widgets, remove_button))

        def remove_line(widgets):
            if len(line_rows) <= 1:
                widgets[0].delete("1.0", tk.END)
                for widget in widgets[1:]:
                    widget.delete(0, tk.END)
                return
            for row_index, (row_widgets, button) in enumerate(line_rows):
                if row_widgets is widgets:
                    for widget in row_widgets:
                        widget.destroy()
                    button.destroy()
                    line_rows.pop(row_index)
                    break
            for row_index, (row_widgets, button) in enumerate(line_rows, start=1):
                for column, widget in enumerate(row_widgets):
                    widget.grid_configure(row=row_index, column=column)
                button.grid_configure(row=row_index, column=3)

        ttk.Button(
            content,
            text="Добавить услугу",
            command=add_line
        ).grid(
            row=len(fields) + 1,
            column=1,
            sticky="w",
            pady=(0, 8)
        )
        if initial_line_items:
            for item in initial_line_items:
                add_line(item)
        else:
            add_line()

    result = {"value": None}

    def read_field(field):
        widget = field_widgets[field["key"]]
        if field.get("multiline"):
            return widget.get("1.0", "end-1c").strip()
        if field.get("choices"):
            return widget.get().strip()
        return widget.get().strip()

    def submit():
        values = {}
        for field in fields:
            value = read_field(field)
            if field.get("required") and not value:
                messagebox.showerror(
                    "Не заполнено поле",
                    f"Заполните поле «{field['label']}».",
                    parent=dialog
                )
                field_widgets[field["key"]].focus_set()
                return
            values[field["key"]] = value

        items = []
        if include_line_items:
            for row_number, (widgets, _) in enumerate(line_rows, start=1):
                name = widgets[0].get("1.0", "end-1c").strip()
                term, amount_text = (widget.get().strip() for widget in widgets[1:])
                if not any((name, term, amount_text)):
                    continue
                if not name or not term or not amount_text:
                    messagebox.showerror(
                        "Неполная услуга",
                        f"Заполните наименование, срок и сумму услуги №{row_number}.",
                        parent=dialog
                    )
                    return
                try:
                    amount = Decimal(amount_text.replace(" ", "").replace(",", "."))
                except InvalidOperation:
                    messagebox.showerror(
                        "Неверная сумма",
                        f"Укажите числовую сумму для услуги №{row_number}.",
                        parent=dialog
                    )
                    widgets[2].focus_set()
                    return
                if not amount.is_finite() or amount < 0:
                    messagebox.showerror(
                        "Неверная сумма",
                        f"Сумма услуги №{row_number} должна быть неотрицательной.",
                        parent=dialog
                    )
                    widgets[2].focus_set()
                    return
                try:
                    normalized_amount = amount.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    )
                except InvalidOperation:
                    messagebox.showerror(
                        "Слишком большая сумма",
                        f"Сумма услуги №{row_number} вне допустимого диапазона.",
                        parent=dialog
                    )
                    widgets[2].focus_set()
                    return
                items.append({
                    "name": name,
                    "term": term,
                    "amount": normalized_amount,
                })

            if not items:
                messagebox.showerror(
                    "Нет услуг",
                    "Добавьте хотя бы одну услугу.",
                    parent=dialog
                )
                return

        result["value"] = {"values": values, "line_items": items}
        dialog.destroy()

    buttons = ttk.Frame(dialog, padding=(12, 8))
    buttons.pack(fill=tk.X)
    if open_client_folder is not None:
        ttk.Button(
            buttons,
            text="Открыть папку клиента",
            command=open_client_folder
        ).pack(side=tk.LEFT)
    ttk.Button(buttons, text="Отмена", command=dialog.destroy).pack(side=tk.RIGHT)
    ttk.Button(buttons, text="Продолжить", command=submit).pack(
        side=tk.RIGHT,
        padx=(0, 8)
    )
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    center_toplevel(dialog)
    dialog.grab_set()
    parent.wait_window(dialog)
    return result["value"]
