"""Ручная проверка встраивания Яндекс.Почты в Tkinter-контейнер."""
import tkinter as tk

from views.mail_window import MailWindowController


root = tk.Tk()
root.title("Проверка встроенной почты")
root.geometry("1100x750")

toolbar = tk.Frame(root)
toolbar.pack(fill=tk.X)

content = tk.Frame(root, bg="#eeeeee")
content.place(x=0, y=40, relwidth=1, relheight=1)
mail_host = tk.Frame(root, bg="white", bd=0, highlightthickness=0)
mail_host.place(x=0, y=40, relwidth=1, relheight=1)
controller = MailWindowController(mail_host)
content.tkraise()


def show_mail():
    content.place_forget()
    mail_host.place(x=0, y=40, relwidth=1, relheight=1)
    controller.show()


def cover_mail():
    controller.hide()
    content.place(x=0, y=40, relwidth=1, relheight=1)


tk.Button(toolbar, text="Показать почту", command=show_mail).pack(side=tk.LEFT)
tk.Button(toolbar, text="Другой раздел", command=cover_mail).pack(
    side=tk.LEFT
)
root.protocol("WM_DELETE_WINDOW", lambda: (controller.close(), root.destroy()))
root.mainloop()
