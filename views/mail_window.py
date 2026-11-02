# -*- coding: utf-8 -*-
"""
Управление встроенным браузером Яндекс.Почты через tkwebview2.WebView2.
Браузер создаётся лениво — только при первом открытии раздела «Почта».
При переключении в другой раздел фрейм скрывается через pack_forget(),
а не удаляется, поэтому при возврате сайт открывается мгновенно.
"""
import tkinter as tk
from tkwebview2.tkwebview2 import WebView2
from tkinter import messagebox


MAIL_URL = "https://mail.yandex.ru"


class MailWindowController:
    """Управляет встроенным WebView2 браузером в разделе «Почта»."""

    def __init__(self, parent_frame):
        """
        Args:
            parent_frame: tk.Frame — контейнер, в который встраивается браузер
        """
        self.parent_frame = parent_frame
        self.browser = None
        self._created = False

    def show(self):
        """Показывает раздел с почтой. Создаёт браузер при первом вызове."""
        if self.browser is None:
            self._create_browser()
        self.parent_frame.pack(fill="both", expand=True)

    def hide(self):
        """Скрывает раздел с почтой (не удаляет браузер)."""
        self.parent_frame.pack_forget()

    def _create_browser(self):
        """Создаёт WebView2 и загружает Яндекс.Почту."""
        self.parent_frame.update_idletasks()
        width = max(self.parent_frame.winfo_width(), 800)
        height = max(self.parent_frame.winfo_height(), 600)

        self.browser = WebView2(self.parent_frame, width, height)
        self.browser.pack(fill="both", expand=True)
        self.browser.load_url(MAIL_URL)
        self._created = True

    def close(self):
        """Закрывает браузер и освобождает ресурсы."""
        if self.browser is not None:
            try:
                self.browser.destroy_window()
            except Exception:
                pass
            self.browser = None
        self._created = False