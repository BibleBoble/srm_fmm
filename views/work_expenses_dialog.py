# -*- coding: utf-8 -*-
"""Диалог расходов по работе (карточка клиента и карточка задачи)."""
import re
import tkinter as tk
from datetime import date
from decimal import Decimal
from tkinter import ttk, messagebox

from managers.experts_manager import ExpertsManager
from managers.works_manager import WorksManager
from utils.date_utils import parse_ddmmyyyy
from utils.ui_helpers import center_toplevel


def _format_iso_date(value):
    """Показать дату ISO (2026-11-03) в формате ДД.ММ.ГГГГ."""
    if not value:
        return "—"
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(value))
    if match:
        return f"{match.group(3)}.{match.group(2)}.{match.group(1)}"
    return str(value)


class _SuggestionList:
    """Список подсказок под полем — не забирает фокус у ввода."""

    def __init__(self, parent, combo, on_select):
        self.parent = parent
        self.combo = combo
        self.on_select = on_select
        self.frame = tk.Frame(parent, bd=1, relief="solid", bg="white")
        self.listbox = tk.Listbox(
            self.frame,
            activestyle="none",
            exportselection=False,
            takefocus=0,
            height=1
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind("<ButtonRelease-1>", self._on_click)
        self.visible = False

    def show(self, values):
        if not values or not self.frame.winfo_exists():
            self.hide()
            return
        self.listbox.delete(0, tk.END)
        for value in values:
            self.listbox.insert(tk.END, value)
        self.listbox.selection_clear(0, tk.END)

        width = max(self.combo.winfo_width(), 240)
        height = min(len(values), 8) * 20 + 4
        x = self.combo.winfo_rootx() - self.parent.winfo_rootx()
        y = (
            self.combo.winfo_rooty() - self.parent.winfo_rooty()
            + self.combo.winfo_height()
        )
        self.frame.place(x=x, y=y, width=width, height=height)
        self.frame.lift()
        self.visible = True

    def hide(self):
        try:
            self.frame.place_forget()
        except tk.TclError:
            pass
        self.visible = False

    def _on_click(self, event=None):
        selection = self.listbox.curselection()
        if not selection:
            return "break"
        value = self.listbox.get(selection[0])
        self.hide()
        self.on_select(value)
        self.combo.focus_set()
        return "break"


def show_work_expenses_dialog(parent, work, works_mgr=None, experts_mgr=None):
    """Открыть окно «Расходы по работе» для указанной работы."""
    works_mgr = works_mgr or WorksManager()
    experts_mgr = experts_mgr or ExpertsManager()

    dialog = tk.Toplevel(parent)
    dialog.title("Расходы по работе")
    dialog.geometry("820x560")
    dialog.transient(parent.winfo_toplevel())
    dialog.grab_set()

    ttk.Label(
        dialog,
        text=f"Работа: {work['title'][:100]}",
        font=("Arial", 10, "bold")
    ).pack(anchor="w", padx=16, pady=(12, 8))

    table_frame = tk.Frame(dialog)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=16)
    tree = ttk.Treeview(
        table_frame,
        columns=("date", "category", "amount", "counterparty", "comment"),
        show="headings",
        height=8
    )
    for column, heading, width, anchor in (
        ("date", "Дата", 90, "center"),
        ("category", "Категория", 140, "w"),
        ("amount", "Сумма, руб.", 110, "e"),
        ("counterparty", "Контрагент", 180, "w"),
        ("comment", "Комментарий", 240, "w"),
    ):
        tree.heading(column, text=heading)
        tree.column(column, width=width, anchor=anchor, stretch=True)
    scrollbar = ttk.Scrollbar(
        table_frame, orient="vertical", command=tree.yview
    )
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh():
        for item in tree.get_children():
            tree.delete(item)
        for row in works_mgr.list_expenses(work["id"]):
            tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    _format_iso_date(row.get("date")),
                    row.get("category") or "",
                    f"{float(row.get('amount') or 0):.2f}".replace(".", ","),
                    row.get("counterparty") or "",
                    row.get("comment") or ""
                )
            )

    form = ttk.Frame(dialog)
    form.pack(fill=tk.X, padx=16, pady=10)
    for column in range(10):
        form.columnconfigure(column, weight=1 if column % 2 else 0)

    try:
        experts = experts_mgr.get_all()
    except Exception:  # noqa: BLE001 - список экспертов не критичен
        experts = []
    expert_by_name = {
        str(expert["name"]): expert["id"] for expert in experts
    }
    expert_names = list(expert_by_name)

    ttk.Label(form, text="Дата:").grid(row=0, column=0, sticky="w")
    date_var = tk.StringVar(value=date.today().strftime("%d.%m.%Y"))
    ttk.Entry(form, textvariable=date_var, width=12).grid(
        row=1, column=0, sticky="ew", padx=(0, 8)
    )

    ttk.Label(form, text="Категория:").grid(row=0, column=1, sticky="w")
    category_var = tk.StringVar(value="Другое")
    category_combo = ttk.Combobox(
        form,
        textvariable=category_var,
        values=(
            "Налог", "Оплата исполнителю",
            "Курьерская служба", "Другое"
        ),
        state="readonly",
        width=20
    )
    category_combo.grid(row=1, column=1, sticky="ew", padx=(0, 8))

    ttk.Label(form, text="Сумма:").grid(row=0, column=2, sticky="w")
    amount_var = tk.StringVar()
    ttk.Entry(form, textvariable=amount_var, width=12).grid(
        row=1, column=2, sticky="ew", padx=(0, 8)
    )

    ttk.Label(form, text="Контрагент:").grid(row=0, column=3, sticky="w")
    counterparty_var = tk.StringVar()
    counterparty_combo = ttk.Combobox(
        form, textvariable=counterparty_var, width=18
    )
    counterparty_combo.grid(
        row=1, column=3, sticky="ew", padx=(0, 8)
    )

    edit_state = {"expense_id": None}
    suppress = {"value": False}

    def apply_category(event=None):
        category = category_var.get()
        if category == "Оплата исполнителю":
            counterparty_combo.configure(values=expert_names)
        else:
            counterparty_combo.configure(values=())
            suggestion.hide()
        if category == "Налог" and event is not None:
            tax = float(work.get("amount") or 0) * 0.06
            amount_var.set(f"{tax:.2f}".replace(".", ","))

    def on_expert_selected(value):
        suppress["value"] = True
        counterparty_var.set(value)
        suppress["value"] = False
        suggestion.hide()
        counterparty_combo.focus_set()

    suggestion = _SuggestionList(dialog, counterparty_combo, on_expert_selected)

    def filter_experts(*_args):
        if category_var.get() != "Оплата исполнителю":
            suggestion.hide()
            return
        query = counterparty_var.get().strip().casefold()
        if not query:
            matches = expert_names
        else:
            matches = [
                name for name in expert_names if query in name.casefold()
            ]
        counterparty_combo.configure(values=matches)
        if suppress["value"]:
            return
        suggestion.show(matches)

    def schedule_hide(event=None):
        dialog.after(150, hide_if_unfocused)

    def hide_if_unfocused():
        try:
            focus = dialog.focus_get()
        except (KeyError, tk.TclError):
            focus = None
        if focus is not counterparty_combo and focus is not suggestion.listbox:
            suggestion.hide()

    def move_selection(step):
        if not suggestion.visible:
            filter_experts()
        if not suggestion.visible:
            return "break"
        size = suggestion.listbox.size()
        if not size:
            return "break"
        current = suggestion.listbox.curselection()
        if current:
            index = max(0, min(size - 1, current[0] + step))
        else:
            index = 0 if step > 0 else size - 1
        suggestion.listbox.selection_clear(0, tk.END)
        suggestion.listbox.selection_set(index)
        suggestion.listbox.see(index)
        return "break"

    def choose_suggestion(event=None):
        if not suggestion.visible:
            return None
        selection = suggestion.listbox.curselection()
        if selection:
            on_expert_selected(suggestion.listbox.get(selection[0]))
            return "break"
        return None

    def hide_suggestion(event=None):
        suggestion.hide()
        return "break"

    category_combo.bind("<<ComboboxSelected>>", apply_category)
    counterparty_var.trace_add("write", filter_experts)
    counterparty_combo.bind("<FocusIn>", lambda event: filter_experts(), add="+")
    counterparty_combo.bind("<FocusOut>", schedule_hide, add="+")
    counterparty_combo.bind(
        "<Down>", lambda event: move_selection(1), add="+"
    )
    counterparty_combo.bind(
        "<Up>", lambda event: move_selection(-1), add="+"
    )
    counterparty_combo.bind("<Return>", choose_suggestion, add="+")
    counterparty_combo.bind("<Escape>", hide_suggestion, add="+")
    dialog.protocol("WM_DELETE_WINDOW", lambda: (suggestion.hide(), dialog.destroy()))
    apply_category()

    ttk.Label(form, text="Комментарий:").grid(row=0, column=4, sticky="w")
    comment_var = tk.StringVar()
    ttk.Entry(form, textvariable=comment_var, width=20).grid(
        row=1, column=4, sticky="ew"
    )

    def reset_form():
        edit_state["expense_id"] = None
        add_button.config(text="Добавить")
        amount_var.set("")
        counterparty_var.set("")
        comment_var.set("")

    def add_expense():
        try:
            amount = Decimal(
                amount_var.get().replace(" ", "").replace(",", ".")
            )
        except Exception:  # noqa: BLE001 - проверка ввода
            messagebox.showerror(
                "Расходы", "Некорректная сумма.", parent=dialog
            )
            return
        expense_date = parse_ddmmyyyy(date_var.get())
        if expense_date is None:
            messagebox.showerror(
                "Расходы",
                "Введите дату в формате ДД.ММ.ГГГГ.",
                parent=dialog
            )
            return

        category = category_var.get() or "Другое"
        counterparty = counterparty_var.get().strip()
        if category == "Оплата исполнителю" and counterparty:
            expert_id = expert_by_name.get(counterparty)
            if expert_id is None:
                expert_id = next(
                    (
                        value for name, value in expert_by_name.items()
                        if name.casefold() == counterparty.casefold()
                    ),
                    None
                )
            if expert_id is not None:
                works_mgr.set_expert(work["id"], expert_id)

        expense_values = (
            expense_date.isoformat(),
            category,
            amount,
            counterparty,
            comment_var.get().strip()
        )
        if edit_state["expense_id"] is not None:
            works_mgr.update_expense(
                edit_state["expense_id"], *expense_values
            )
        else:
            works_mgr.add_expense(work["id"], *expense_values)
        reset_form()
        refresh()

    def edit_expense():
        selection = tree.selection()
        if not selection:
            return
        expense_id = int(selection[0])
        expense = next(
            (
                row for row in works_mgr.list_expenses(work["id"])
                if row["id"] == expense_id
            ),
            None
        )
        if expense is None:
            return
        edit_state["expense_id"] = expense_id
        date_var.set(
            _format_iso_date(expense.get("date"))
            if expense.get("date")
            else date.today().strftime("%d.%m.%Y")
        )
        category_var.set(expense.get("category") or "Другое")
        apply_category()
        amount_var.set(
            f"{float(expense.get('amount') or 0):.2f}".replace(".", ",")
        )
        counterparty_var.set(expense.get("counterparty") or "")
        comment_var.set(expense.get("comment") or "")
        add_button.config(text="Сохранить изменения")

    def delete_expense():
        selection = tree.selection()
        if not selection:
            return
        works_mgr.delete_expense(int(selection[0]))
        refresh()

    buttons = ttk.Frame(dialog)
    buttons.pack(fill=tk.X, padx=16, pady=(0, 12))
    add_button = ttk.Button(
        buttons, text="Добавить", command=add_expense
    )
    add_button.pack(side=tk.LEFT)
    ttk.Button(
        buttons, text="✏ Редактировать", command=edit_expense
    ).pack(side=tk.LEFT, padx=8)
    ttk.Button(buttons, text="Удалить", command=delete_expense).pack(
        side=tk.LEFT
    )
    ttk.Button(
        buttons, text="Закрыть", command=dialog.destroy
    ).pack(side=tk.RIGHT)

    refresh()
    center_toplevel(dialog)
    return dialog
