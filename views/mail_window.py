# -*- coding: utf-8 -*-
"""
Управление встроенным окном Яндекс.Почты в отдельном Toplevel.
Браузер запускается отдельным процессом при старте приложения.
При переключении разделов окно скрывается (не закрывается), поэтому
при возврате на «Почту» отображается мгновенно.
"""
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox


class MailWindowController:
    """Запускает отдельный Qt WebEngine в своём окне Toplevel."""

    MIN_HOST_WIDTH = 100
    MIN_HOST_HEIGHT = 100
    STARTUP_TIMEOUT = 45
    NAVIGATION_TIMEOUT = 60

    def __init__(self, root, toplevel):
        self.root = root
        self.toplevel = toplevel
        self.process = None
        self._closing = False
        self._visible = False
        self._output_queue = queue.Queue()
        self._startup_deadline = None
        self._navigation_deadline = None
        self._startup_complete = False
        self._page_loaded = False
        self._error_reported = False
        self._poll_job = None
        self._start_job = None
        self._show_job = None
        self._start_deadline = None
        self.toplevel.bind("<Configure>", self._on_host_resize, add="+")
        self.root.bind("<Map>", self._on_root_mapped, add="+")

    def show(self):
        """Показывает встроенный браузер либо запускает его."""
        if self._closing:
            return

        self._visible = True
        self.toplevel.deiconify()
        self.toplevel.lift()
        self.toplevel.update_idletasks()

        if self._is_running():
            return
        self._start_when_sized()

    def _start_when_sized(self):
        if self._closing or self._start_job is not None:
            return

        width, height = self._host_size()
        if width >= self.MIN_HOST_WIDTH and height >= self.MIN_HOST_HEIGHT:
            self._start_deadline = None
            self._start_process()
            return

        if self._start_deadline is None:
            self._start_deadline = time.monotonic() + 10
        if time.monotonic() >= self._start_deadline:
            self._start_deadline = None
            self._show_error(
                "Не удалось определить размер окна почты. "
                "Переключитесь на вкладку «Почта» и попробуйте снова."
            )
            return

        self._start_job = self.root.after(100, self._retry_start_when_sized)

    def _retry_start_when_sized(self):
        self._start_job = None
        self._start_when_sized()

    def _start_process(self):
        if self._closing or self._is_running():
            return

        while True:
            try:
                self._output_queue.get_nowait()
            except queue.Empty:
                break

        project_root = Path(__file__).resolve().parent.parent
        project_interpreter = project_root / ".venv" / "Scripts" / "python.exe"
        interpreter = (
            str(project_interpreter)
            if project_interpreter.is_file()
            else sys.executable
        )

        width, height = self._host_size()
        parent_handle = self.toplevel.winfo_id()

        command = [
            interpreter,
            "-X", "utf8",
            str(Path(__file__).parent / "mail_webview.py"),
            str(parent_handle),
            str(width),
            str(height),
        ]

        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW
                if sys.platform == "win32" else 0,
            )
        except Exception as error:
            self._show_error(f"Не удалось запустить процесс почты: {error}")
            return

        threading.Thread(
            target=self._read_process_output,
            args=(self.process,),
            daemon=True,
        ).start()
        self._poll_job = self.root.after(250, self._drain_process_output)

    def _is_running(self):
        return self.process is not None and self.process.poll() is None

    def _host_size(self):
        return (
            max(self.toplevel.winfo_width(), 1),
            max(self.toplevel.winfo_height(), 1),
        )

    def _on_host_resize(self, event):
        if not self._is_running():
            return
        width, height = event.width, event.height
        if width < 1 or height < 1:
            return
        self._send_command(f"resize {width} {height}")

    def _on_root_mapped(self, event):
        if event.widget is self.root and self._visible:
            self.root.after_idle(self._refresh_after_restore)

    def _refresh_after_restore(self):
        if not self._visible or not self._is_running():
            return
        self.toplevel.deiconify()
        self.toplevel.lift()
        self.toplevel.update_idletasks()

    def _send_command(self, command: str):
        if self.process is None or self.process.stdin is None:
            return
        try:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    def _read_process_output(self, process):
        if process.stdout is None:
            return
        for line in process.stdout:
            message = line.strip()
            if message == "READY" or message.startswith(
                ("ERROR:", "NAVIGATION_COMPLETED:", "NAVIGATION_FAILED:")
            ):
                self._output_queue.put(message)

    def _drain_process_output(self):
        self._poll_job = None
        if self._closing:
            return

        while True:
            try:
                message = self._output_queue.get_nowait()
            except queue.Empty:
                break

            if message.startswith("ERROR:"):
                self._error_reported = True
                self._startup_complete = True
                self._page_loaded = True
                self._show_error(
                    "Не удалось запустить встроенную Яндекс.Почту.\n\n"
                    f"{message.removeprefix('ERROR:').strip()}"
                )
                self._send_command("quit")
            elif message == "READY":
                self._startup_complete = True
                self._startup_deadline = None
            elif message.startswith("NAVIGATION_COMPLETED:"):
                self._page_loaded = True
                self._navigation_deadline = None
            elif message.startswith("NAVIGATION_FAILED:"):
                self._page_loaded = True
                self._navigation_deadline = None
                self._show_error(
                    "Яндекс.Почта не загрузилась.\n\n"
                    f"{message.removeprefix('NAVIGATION_FAILED:').strip()}"
                )

        if self._is_running() and not self._startup_complete:
            if (
                self._startup_deadline is not None
                and time.monotonic() >= self._startup_deadline
                and not self._error_reported
            ):
                self._error_reputed = True
                self._show_error(
                    "Qt WebEngine не запустился за отведённое время. "
                    "Проверьте установку зависимостей проекта."
                )
                self._send_command("quit")
            self._poll_job = self.root.after(250, self._drain_process_output)
            return

        if self._is_running() and not self._page_loaded:
            if not self._visible:
                self._poll_job = self.root.after(
                    1000, self._drain_process_output
                )
                return
            if self._navigation_deadline is None:
                self._navigation_deadline = (
                    time.monotonic() + self.NAVIGATION_TIMEOUT
                )
            elif (
                time.monotonic() >= self._navigation_deadline
                and not self._error_reputed
            ):
                self._error_reputed = True
                self._page_loaded = True
                self._show_error(
                    "Яндекс.Почта не завершила загрузку. "
                    "Проверьте подключение к Интернету."
                )
            self._poll_job = self.root.after(1000, self._drain_process_output)
            return

        if not self._is_running() and not self._error_reputed:
            self._error_reputed = True
            self._show_error(
                "Процесс встроенной почты завершился. "
                "Перезапустите приложение и попробуйте снова."
            )

    def _show_error(self, message):
        if not self._closing:
            messagebox.showerror("Почта", message, parent=self.root)

    def close(self):
        """Корректно завершает почтовый процесс перед закрытием приложения."""
        self._closing = True
        for job in (
            self._poll_job,
            self._start_job,
            self._show_job
        ):
            if job is not None:
                self.root.after_cancel(job)
        self._poll_job = None
        self._start_job = None
        self._show_job = None

        process = self.process
        if process is None or process.poll() is not None:
            return

        try:
            if process.stdin is not None:
                process.stdin.write("quit\n")
                process.stdin.flush()
            process.wait(timeout=5)
        except (BrokenPipeError, OSError, subprocess.TimeoutExpired) as error:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            if not isinstance(error, BrokenPipeError):
                print(f"Не удалось штатно закрыть окно почты: {error}")