import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from views.mail_window import MailView


class MailViewTests(unittest.TestCase):
    def setUp(self):
        self.pending_callbacks = []

        def schedule(delay, callback, *args):
            self.pending_callbacks.append(lambda: callback(*args))
            return len(self.pending_callbacks)

        self.root = Mock()
        self.root.after.side_effect = schedule

        self.host_frame = Mock()
        self.host_frame.winfo_width.return_value = 1
        self.host_frame.winfo_height.return_value = 1
        self.host_frame.winfo_id.return_value = 4242

        self.size_source = Mock()
        self.size_source.winfo_width.return_value = 1
        self.size_source.winfo_height.return_value = 1

        with patch("views.mail_window._create_kill_job", return_value=None):
            self.view = MailView(self.root, self.host_frame, self.size_source)

    def give_host_size(self, width=1200, height=800):
        self.host_frame.winfo_width.return_value = width
        self.host_frame.winfo_height.return_value = height

    def mark_process_running(self):
        self.view.process = Mock()
        self.view.process.poll.return_value = None

    def test_preload_waits_for_layout_size(self):
        with patch.object(self.view, "_start_process") as start_process:
            self.view.preload()

            start_process.assert_not_called()
            self.assertEqual(len(self.pending_callbacks), 1)

            self.give_host_size()
            self.pending_callbacks.pop()()

            start_process.assert_called_once_with()

    def test_preload_uses_container_size_before_first_show(self):
        self.size_source.winfo_width.return_value = 1200
        self.size_source.winfo_height.return_value = 800

        with patch.object(self.view, "_start_process") as start_process:
            self.view.preload()

        start_process.assert_called_once_with()

    def test_process_receives_container_handle_and_dimensions(self):
        self.give_host_size()
        process = Mock(stdout=None)

        with (
            patch("views.mail_window.subprocess.Popen", return_value=process) as popen,
            patch("views.mail_window.threading.Thread") as thread,
        ):
            self.view._start_process()

        command = popen.call_args.args[0]
        self.assertEqual(command[-3:], ["4242", "1200", "800"])
        thread.return_value.start.assert_called_once_with()

    def test_preload_does_not_show_browser(self):
        self.give_host_size()

        with (
            patch.object(self.view, "_start_process"),
            patch.object(self.view, "_send_command") as send_command,
        ):
            self.view.preload()

        send_command.assert_not_called()

    def test_show_requests_visibility_with_current_size(self):
        self.give_host_size()
        self.mark_process_running()

        with patch.object(self.view, "_send_command") as send_command:
            self.view.show()

        send_command.assert_called_once_with("show 1200 800")

    def test_hide_keeps_process_alive(self):
        self.view._visible = True
        self.mark_process_running()

        with patch.object(self.view, "_send_command") as send_command:
            self.view.hide()

        self.assertFalse(self.view._visible)
        send_command.assert_called_once_with("hide")
        self.assertTrue(self.view._is_running())

    def test_show_before_ready_is_applied_on_ready(self):
        self.give_host_size()

        with patch.object(self.view, "_start_process"):
            self.view.show()

        self.assertTrue(self.view._pending_show)

        self.mark_process_running()
        self.view._output_queue.put("READY")

        with patch.object(self.view, "_send_command") as send_command:
            self.view._drain_process_output()

        send_command.assert_called_once_with("show 1200 800")
        self.assertFalse(self.view._pending_show)

    def test_navigation_failure_is_reported_to_user(self):
        self.view._startup_complete = True
        self.mark_process_running()
        self.view._output_queue.put(
            "NAVIGATION_FAILED: mail.yandex.ru; статус ConnectionAborted"
        )

        with patch("views.mail_window.messagebox.showerror") as showerror:
            self.view._drain_process_output()

        showerror.assert_called_once()
        self.assertIn("не загрузилась", showerror.call_args.args[1])
        self.assertIn("ConnectionAborted", showerror.call_args.args[1])
        self.assertTrue(self.view._page_loaded)

    def test_resize_is_ignored_while_section_is_hidden(self):
        self.mark_process_running()

        with patch.object(self.view, "_send_command") as send_command:
            self.view._on_host_resize(Mock(width=1200, height=800))

        send_command.assert_not_called()

    def test_resize_is_forwarded_while_section_is_visible(self):
        self.view._visible = True
        self.mark_process_running()

        with patch.object(self.view, "_send_command") as send_command:
            self.view._on_host_resize(Mock(width=1280, height=720))

        send_command.assert_called_once_with("resize 1280 720")

    def test_restoring_application_requests_webview_repaint(self):
        self.view._visible = True
        self.mark_process_running()

        with patch.object(self.view, "_send_command") as send_command:
            self.view._on_root_mapped(SimpleNamespace(widget=self.root))
            self.root.after_idle.call_args.args[0]()

        send_command.assert_called_once_with("refresh")

    def test_request_shutdown_sends_quit_without_waiting(self):
        self.mark_process_running()

        with patch.object(self.view, "_send_command") as send_command:
            self.view.request_shutdown(on_done=None)

        send_command.assert_called_once_with("quit")
        self.view.process.wait.assert_not_called()
        self.assertEqual(len(self.pending_callbacks), 1)

    def test_shutdown_finishes_process_tree_after_grace_period(self):
        self.mark_process_running()
        done = Mock()

        with patch.object(self.view, "_send_command"):
            self.view.request_shutdown(on_done=done)

        self.pending_callbacks[-1]()

        self.view.process.kill.assert_called_once()
        done.assert_called_once()
        self.assertIsNone(self.view._job)

    def test_shutdown_without_process_finishes_immediately(self):
        done = Mock()

        self.view.request_shutdown(on_done=done)

        done.assert_called_once()
        self.assertEqual(self.pending_callbacks, [])


if __name__ == "__main__":
    unittest.main()
