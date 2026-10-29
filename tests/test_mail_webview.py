import unittest
from unittest.mock import Mock, call, patch

from views.mail_webview import (
    MAIL_URL,
    _create_mail_window,
    _prepare_embedded_window,
    _refresh_embedded_window,
    _set_embedded_window_size,
    _show_embedded_window
)


class MailWebViewWindowTests(unittest.TestCase):
    def test_mail_window_starts_hidden_until_embedded(self):
        webview = Mock()
        expected_window = object()
        webview.create_window.return_value = expected_window

        result = _create_mail_window(webview, 1280, 720)

        self.assertIs(result, expected_window)
        webview.create_window.assert_called_once_with(
            "Яндекс.Почта",
            MAIL_URL,
            width=1280,
            height=720,
            min_size=(400, 300),
            frameless=True,
            hidden=True,
            focus=False
        )

    def test_mail_window_dimensions_are_positive(self):
        webview = Mock()

        _create_mail_window(webview, 0, -1)

        self.assertEqual(webview.create_window.call_args.kwargs["width"], 1)
        self.assertEqual(webview.create_window.call_args.kwargs["height"], 1)

    def test_child_window_is_sized_before_it_is_shown(self):
        order = Mock()
        user32 = Mock()
        user32.SetWindowPos.side_effect = lambda *args: order.size()
        window = Mock()
        window.show.side_effect = order.show

        _show_embedded_window(window, user32, 123, 1280, 720)

        user32.SetWindowPos.assert_called_once()
        window.show.assert_called_once_with()
        self.assertEqual(order.mock_calls, [call.size(), call.show()])

    def test_resize_does_not_force_window_visible(self):
        user32 = Mock()
        user32.SetWindowPos.return_value = 1

        _set_embedded_window_size(user32, 123, 800, 600)

        flags = user32.SetWindowPos.call_args.args[-1]
        self.assertEqual(flags & 0x0040, 0)

    def test_refresh_repaints_embedded_window_and_child_controls(self):
        user32 = Mock()
        user32.RedrawWindow.return_value = 1

        _refresh_embedded_window(user32, 123)

        redraw_flags = user32.RedrawWindow.call_args.args[-1]
        self.assertEqual(redraw_flags & 0x0080, 0x0080)
        self.assertEqual(redraw_flags & 0x0100, 0x0100)
        self.assertEqual(user32.RedrawWindow.call_args.args[0].value, 123)

    def test_embedding_is_ready_only_after_native_form_is_processed(self):
        window = Mock()
        ready = Mock()
        errors = Mock()

        with (
            patch("views.mail_webview._attach_navigation_diagnostics") as diagnostics,
            patch("views.mail_webview._embed_window") as embed,
        ):
            _prepare_embedded_window(window, 44, 800, 600, ready, errors)

        diagnostics.assert_called_once_with(window)
        embed.assert_called_once_with(window, 44, 800, 600)
        ready.set.assert_called_once_with()
        errors.put.assert_not_called()

    def test_embedding_failure_is_reported_and_unblocks_startup(self):
        window = Mock()
        ready = Mock()
        errors = Mock()

        with patch(
            "views.mail_webview._attach_navigation_diagnostics",
            side_effect=RuntimeError("Native form is not initialized")
        ):
            _prepare_embedded_window(window, 44, 800, 600, ready, errors)

        errors.put.assert_called_once_with("Native form is not initialized")
        ready.set.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
