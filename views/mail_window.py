"""Управление встроенным окном Яндекс.Почты."""
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from tkinter import messagebox


class MailWindowController:
    """Встраивает отдельный процесс WebView2 в постоянный Tk-контейнер."""

    MIN_HOST_WIDTH = 100
    MIN_HOST_HEIGHT = 100

    def __init__(self, root, host_frame):
        self.root = root
        self.host_frame = host_frame
        self.process = None
        self._closing = False
        self._output_queue = queue.Queue()
        self._reader_done = threading.Event()
        self._startup_complete = False
        self._page_loaded = False
        self._visible = False
        self._navigation_deadline = None
        self._poll_job = None
        self._resize_job = None
        self._start_job = None
        self._start_deadline = None
        self.host_frame.bind("<Configure>", self._on_host_resize, add="+")
        self.root.bind("<Map>", self._on_root_mapped, add="+")

    def show(self):
        """Запускает WebView2 либо возвращает в область раздела готовое окно."""
        if self._closing:
            return

        self._visible = True
        self.host_frame.update_idletasks()
        if self.process is not None and self.process.poll() is None:
            self._send_command("show")
            return

        self._start_when_sized()

    def start_background(self):
        """Запускает почтовый WebView при старте приложения, не выбирая раздел."""
        if self._closing:
            return
        if self.process is not None and self.process.poll() is None:
            return
        self.host_frame.update_idletasks()
        self._start_when_sized()

    def hide(self):
        """Оставляет WebView2 под другим разделом, сохраняя его поверхность."""
        # Tk перекрывает mail_host другим разделом; прятать HWND WebView нельзя,
        # иначе WebView2 может потерять поверхность при следующем отображении.
        self._visible = False

    def _start_process(self):
        if self._closing:
            return
        if self.process is not None and self.process.poll() is None:
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
        width = max(self.host_frame.winfo_width(), 1)
        height = max(self.host_frame.winfo_height(), 1)
        command = [
            interpreter,
            "-X",
            "utf8",
            "-m",
            "views.mail_webview",
            str(self.host_frame.winfo_id()),
            str(width),
            str(height)
        ]
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            self.process = subprocess.Popen(
                command,
                cwd=str(project_root),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=creation_flags
            )
        except OSError as error:
            self._show_error(f"Не удалось запустить окно почты:\n{error}")
            return

        self._reader_done = threading.Event()
        self._startup_complete = False
        self._page_loaded = False
        self._navigation_deadline = None
        threading.Thread(
            target=self._read_process_output,
            args=(self.process, self._reader_done),
            daemon=True
        ).start()
        self._poll_job = self.root.after(100, self._drain_process_output)
        if self._visible:
            self._send_command("show")

    def _on_root_mapped(self, event):
        if event.widget is self.root and self._visible:
            self.root.after_idle(self._refresh_after_restore)

    def _refresh_after_restore(self):
        if (
            self._visible
            and self.process is not None
            and self.process.poll() is None
        ):
            self._send_command("refresh")

    def _start_when_sized(self):
        """Waits for Tk to lay out the host before creating the native browser."""
        if self._closing:
            return
        if self._start_job is not None:
            return

        self.host_frame.update_idletasks()
        width = self.host_frame.winfo_width()
        height = self.host_frame.winfo_height()
        if width >= self.MIN_HOST_WIDTH and height >= self.MIN_HOST_HEIGHT:
            self._start_deadline = None
            self._start_process()
            return

        if self._start_deadline is None:
            self._start_deadline = time.monotonic() + 10
        if time.monotonic() >= self._start_deadline:
            self._start_deadline = None
            self._show_error(
                "Не удалось определить размер области почты. "
                "Переключитесь на вкладку «Почта» и попробуйте снова."
            )
            return

        self._start_job = self.root.after(100, self._retry_start_when_sized)

    def _retry_start_when_sized(self):
        self._start_job = None
        self._start_when_sized()

    def _send_command(self, command):
        process = self.process
        if process is None or process.poll() is not None or process.stdin is None:
            return
        try:
            process.stdin.write(f"{command}\n")
            process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            print(f"Не удалось передать команду окну почты: {error}")

    def _on_host_resize(self, event):
        if (
            event.width < self.MIN_HOST_WIDTH
            or event.height < self.MIN_HOST_HEIGHT
        ):
            return
        if self.process is None or self.process.poll() is not None:
            if self._start_job is not None:
                self.root.after_cancel(self._start_job)
                self._start_job = None
            self._start_deadline = None
            self._start_process()
            return
        if self._resize_job is not None:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(
            75,
            lambda width=event.width, height=event.height: self._resize_host(
                width,
                height
            )
        )

    def _resize_host(self, width, height):
        self._resize_job = None
        self._send_command(f"resize {width} {height}")

    def _read_process_output(self, process, reader_done):
        try:
            if process.stdout is not None:
                for line in process.stdout:
                    message = line.strip()
                    if message in {"READY", "PYWEBVIEW_READY"} or message.startswith(
                        ("ERROR:", "NAVIGATION_COMPLETED:", "NAVIGATION_FAILED:")
                    ) or "WebView2 initialization failed" in message:
                        self._output_queue.put(message)
        finally:
            reader_done.set()

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
                detail = message.removeprefix("ERROR:").strip()
                self._show_error(
                    "Не удалось встроить Яндекс.Почту.\n\n"
                    f"{detail}\n\n"
                    "Проверьте установку pywebview и Microsoft Edge WebView2 Runtime."
                )
                self._send_command("quit")
            elif message in {"READY", "PYWEBVIEW_READY"}:
                self._startup_complete = True
            elif message.startswith("NAVIGATION_COMPLETED:"):
                self._page_loaded = True
            elif message.startswith("NAVIGATION_FAILED:"):
                self._page_loaded = True
                self._show_error(
                    "Яндекс.Почта не загрузилась в WebView2.\n\n"
                    f"{message.removeprefix('NAVIGATION_FAILED:').strip()}"
                )
            elif "WebView2 initialization failed" in message:
                self._show_error(
                    "Microsoft Edge WebView2 не смог загрузить почту.\n\n"
                    f"{message}"
                )

        process_is_running = self.process is not None and self.process.poll() is None
        if not self._startup_complete and (
            process_is_running or not self._reader_done.is_set()
        ):
            self._poll_job = self.root.after(100, self._drain_process_output)
        elif process_is_running and not self._page_loaded:
            if self._navigation_deadline is None:
                self._navigation_deadline = time.monotonic() + 45
            if time.monotonic() >= self._navigation_deadline:
                self._page_loaded = True
                self._show_error(
                    "WebView2 создан, но сайт почты не сообщил о завершении загрузки. "
                    "Проверьте доступ к Интернету, прокси и Edge WebView2 Runtime."
                )
            else:
                self._poll_job = self.root.after(1000, self._drain_process_output)

    def _show_error(self, message):
        if not self._closing:
            messagebox.showerror("Почта", message, parent=self.root)

    def close(self):
        """Завершает процесс WebView2 перед закрытием приложения."""
        self._closing = True
        for job in (self._poll_job, self._resize_job, self._start_job):
            if job is not None:
                self.root.after_cancel(job)
        self._poll_job = None
        self._resize_job = None
        self._start_job = None

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