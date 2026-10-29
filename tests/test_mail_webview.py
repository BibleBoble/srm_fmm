import io
import queue
import unittest
from unittest.mock import Mock, patch

from views.mail_webview import (
    MAIL_URL,
    SWP_NOACTIVATE,
    SWP_NOZORDER,
    SWP_SHOWWINDOW,
    _page_host,
    _read_commands,
    _resize_window,
    _show_window
)


class MailWebViewTests(unittest.TestCase):
    def test_mail_url_uses_yandex_mail(self):
        self.assertEqual(MAIL_URL, "https://mail.yandex.ru")

    def test_page_host_omits_query_and_path(self):
        self.assertEqual(
            _page_host("https://mail.yandex.ru/inbox?uid=private"),
            "mail.yandex.ru"
        )

    def test_command_reader_queues_supported_commands(self):
        commands = queue.Queue()
        command_input = io.StringIO(
            "resize 1280 720\nshow\nhide\nrefresh\nquit\n"
        )

        with patch("views.mail_webview.sys.stdin", command_input):
            _read_commands(commands)

        self.assertEqual(
            [commands.get_nowait() for _ in range(commands.qsize())],
            [
                ("resize", 1280, 720),
                ("show",),
                ("hide",),
                ("refresh",),
                ("quit",)
            ]
        )

    def test_resize_keeps_child_window_in_place(self):
        user32 = Mock()
        user32.SetWindowPos.return_value = 1

        _resize_window(user32, 123, 800, 600)

        arguments = user32.SetWindowPos.call_args.args
        self.assertEqual(arguments[-1] & SWP_NOZORDER, SWP_NOZORDER)
        self.assertEqual(arguments[-1] & SWP_NOACTIVATE, SWP_NOACTIVATE)

    def test_show_uses_host_size_without_activating_window(self):
        user32 = Mock()
        user32.SetWindowPos.return_value = 1

        _show_window(user32, 123, 800, 600)

        arguments = user32.SetWindowPos.call_args.args
        self.assertEqual(arguments[4:6], (800, 600))
        self.assertEqual(arguments[-1] & SWP_NOACTIVATE, SWP_NOACTIVATE)
        self.assertEqual(arguments[-1] & SWP_SHOWWINDOW, SWP_SHOWWINDOW)


if __name__ == "__main__":
    unittest.main()
