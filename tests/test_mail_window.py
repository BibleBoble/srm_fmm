import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from views.mail_window import MailWindowController


class MailWindowStartupTests(unittest.TestCase):
    def setUp(self):
        self.pending_callbacks = []
        self.root = Mock()
        self.root.after.side_effect = (
            lambda delay, callback: self.pending_callbacks.append(callback)
            or len(self.pending_callbacks)
        )
        self.host_frame = Mock()
        self.host_frame.winfo_width.return_value = 1
        self.host_frame.winfo_height.return_value = 1
        self.controller = MailWindowController(self.root, self.host_frame)

    def test_startup_waits_for_layout_size(self):
        with patch.object(self.controller, "_start_process") as start_process:
            self.controller.start_background()

            start_process.assert_not_called()
            self.assertEqual(len(self.pending_callbacks), 1)

            self.host_frame.winfo_width.return_value = 1200
            self.host_frame.winfo_height.return_value = 800
            self.pending_callbacks.pop()()

            start_process.assert_called_once_with()

    def test_resize_starts_browser_once_container_has_size(self):
        with patch.object(self.controller, "_start_process") as start_process:
            self.controller.start_background()
            self.host_frame.winfo_width.return_value = 1200
            self.host_frame.winfo_height.return_value = 800

            self.controller._on_host_resize(
                Mock(width=1200, height=800)
            )

            start_process.assert_called_once_with()
            self.root.after_cancel.assert_called_once()
            self.assertIsNone(self.controller._start_job)

    def test_process_receives_current_container_dimensions(self):
        self.host_frame.winfo_width.return_value = 1200
        self.host_frame.winfo_height.return_value = 800
        process = Mock(stdout=None)

        with (
            patch("views.mail_window.subprocess.Popen", return_value=process) as popen,
            patch("views.mail_window.threading.Thread") as thread,
        ):
            self.controller._start_process()

        command = popen.call_args.args[0]
        self.assertEqual(command[-2:], ["1200", "800"])
        thread.return_value.start.assert_called_once_with()

    def test_background_start_does_not_show_browser(self):
        self.host_frame.winfo_width.return_value = 1200
        self.host_frame.winfo_height.return_value = 800

        with (
            patch.object(self.controller, "_start_process") as start_process,
            patch.object(self.controller, "_send_command") as send_command,
        ):
            self.controller.start_background()

        start_process.assert_called_once_with()
        send_command.assert_not_called()

    def test_show_requests_embedded_browser_visibility(self):
        self.controller.process = Mock()
        self.controller.process.poll.return_value = None
        self.host_frame.winfo_width.return_value = 1200
        self.host_frame.winfo_height.return_value = 800

        with patch.object(self.controller, "_send_command") as send_command:
            self.controller.show()
            self.root.after_idle.call_args.args[0]()

        self.assertEqual(
            send_command.call_args_list,
            [call("resize 1200 800"), call("show")]
        )

    def test_navigation_failure_is_reported_to_user(self):
        self.controller._startup_complete = True
        self.controller.process = Mock()
        self.controller.process.poll.return_value = None
        self.controller._output_queue.put(
            "NAVIGATION_FAILED: mail.yandex.ru; статус ConnectionAborted"
        )

        with patch("views.mail_window.messagebox.showerror") as showerror:
            self.controller._drain_process_output()

        showerror.assert_called_once()
        self.assertIn("не загрузилась", showerror.call_args.args[1])
        self.assertIn("ConnectionAborted", showerror.call_args.args[1])
        self.assertTrue(self.controller._page_loaded)

    def test_switching_sections_hides_native_webview(self):
        self.controller._visible = True
        self.controller.process = Mock()
        self.controller.process.poll.return_value = None

        with patch.object(self.controller, "_send_command") as send_command:
            self.controller.hide()

        self.assertFalse(self.controller._visible)
        send_command.assert_called_once_with("hide")
        self.host_frame.grid_remove.assert_called_once_with()
        self.assertFalse(self.controller._host_mapped)

    def test_returning_to_mail_restores_host_before_showing_webview(self):
        self.controller._host_mapped = False
        self.controller.process = Mock()
        self.controller.process.poll.return_value = None
        self.host_frame.winfo_width.return_value = 1200
        self.host_frame.winfo_height.return_value = 800

        with patch.object(self.controller, "_send_command") as send_command:
            self.controller.show()
            self.root.after_idle.call_args.args[0]()

        self.host_frame.grid.assert_called_once_with()
        self.host_frame.tkraise.assert_called_once_with()
        self.assertTrue(self.controller._host_mapped)
        self.assertEqual(
            send_command.call_args_list,
            [call("resize 1200 800"), call("show")]
        )

    def test_restoring_application_requests_webview_repaint(self):
        self.controller._visible = True
        self.controller.process = Mock()
        self.controller.process.poll.return_value = None
        self.host_frame.winfo_width.return_value = 1200
        self.host_frame.winfo_height.return_value = 800

        with patch.object(self.controller, "_send_command") as send_command:
            self.controller._on_root_mapped(
                SimpleNamespace(widget=self.root)
            )
            self.root.after_idle.call_args.args[0]()

        self.assertEqual(
            send_command.call_args_list,
            [call("resize 1200 800"), call("show")]
        )
        self.assertEqual(self.pending_callbacks, [])


if __name__ == "__main__":
    unittest.main()
