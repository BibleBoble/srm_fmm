# -*- coding: utf-8 -*-
"""
Встроенная Яндекс.Почта.

Браузер работает в отдельном процессе Qt WebEngine: его окно прикрепляется
к фрейму внутри главного окна приложения, поэтому почта выглядит частью
интерфейса, а не отдельным окном.

Процесс запускается при старте приложения (preload) и остаётся загруженным:
переключение разделов только скрывает и показывает готовое окно, поэтому
раздел «Почта» открывается мгновенно и не теряет сессию входа.
"""
import ctypes
import ctypes.wintypes
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox


_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_PROCESS_TERMINATE = 0x0001
_PROCESS_SET_QUOTA = 0x0100


class _JobBasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", ctypes.wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.wintypes.DWORD),
        ("SchedulingClass", ctypes.wintypes.DWORD),
    ]


class _JobIoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
    ]


class _JobExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JobBasicLimitInformation),
        ("IoInfo", _JobIoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def _create_kill_job():
    """Создаёт job-объект, который убивает всё дерево процессов при закрытии."""
    if sys.platform != "win32":
        return None

    kernel32 = ctypes.windll.kernel32
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        return None

    info = _JobExtendedLimitInformation()
    info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    kernel32.SetInformationJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint32,
    ]
    configured = kernel32.SetInformationJobObject(
        job,
        _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
        ctypes.byref(info),
        ctypes.sizeof(info),
    )
    if not configured:
        _close_job_handle(job)
        return None
    return job


def _close_job_handle(job):
    kernel32 = ctypes.windll.kernel32
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle(job)


def _assign_process_to_job(job, pid):
    """Привязывает процесс почты (и его потомков) к job-объекту."""
    if not job or sys.platform != "win32":
        return False

    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.OpenProcess.argtypes = [
        ctypes.wintypes.DWORD,
        ctypes.wintypes.BOOL,
        ctypes.wintypes.DWORD,
    ]
    kernel32.AssignProcessToJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]

    handle = kernel32.OpenProcess(
        _PROCESS_SET_QUOTA | _PROCESS_TERMINATE,
        False,
        pid,
    )
    if not handle:
        return False
    try:
        return bool(kernel32.AssignProcessToJobObject(job, handle))
    finally:
        kernel32.CloseHandle(handle)


def _terminate_job(job):
    kernel32 = ctypes.windll.kernel32
    kernel32.TerminateJobObject.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    kernel32.TerminateJobObject.restype = ctypes.wintypes.BOOL
    kernel32.TerminateJobObject(job, 1)


class MailView:
    """Управляет окном Яндекс.Почты, встроенным в tk-фрейм."""

    MIN_HOST_WIDTH = 100
    MIN_HOST_HEIGHT = 100
    STARTUP_TIMEOUT = 45
    NAVIGATION_TIMEOUT = 60
    SHUTDOWN_GRACE_MS = 700

    def __init__(self, root, host_frame, size_source):
        """
        Args:
            root: tk.Tk - корневое окно приложения.
            host_frame: tk.Frame - фрейм, внутрь которого встраивается браузер.
            size_source: tk.Widget - контейнер, по размеру которого считается
                геометрия до первого показа раздела.
        """
        self.root = root
        self.host_frame = host_frame
        self.size_source = size_source
        self.process = None
        self.last_navigation = ""
        self._closing = False
        self._visible = False
        self._pending_show = False
        self._startup_complete = False
        self._page_loaded = False
        self._error_reported = False
        self._output_queue = queue.Queue()
        self._poll_job = None
        self._start_job = None
        self._pending_show_job = None
        self._shutdown_job = None
        self._startup_deadline = None
        self._navigation_deadline = None
        self._job = _create_kill_job()

        self.host_frame.bind("<Configure>", self._on_host_resize, add="+")
        self.root.bind("<Map>", self._on_root_mapped, add="+")

    # --- публичный интерфейс ---

    def preload(self):
        """Запускает браузер заранее, не показывая его пользователю."""
        if self._closing or self._is_running():
            return
        self._start_when_sized()

    def show(self):
        """Показывает заранее загруженную почту."""
        if self._closing:
            return
        self._visible = True
        self._pending_show = True
        if self._is_running():
            self._apply_pending_show()
        else:
            self._start_when_sized()

    def hide(self):
        """Скрывает почту, не выгружая страницу и не теряя сессию."""
        self._visible = False
        self._pending_show = False
        self._cancel_pending_show()
        if self._is_running():
            self._send_command("hide")

    def request_shutdown(self, on_done=None):
        """Запускает остановку почты, не блокируя интерфейс.

        Процессу отправляется quit, после короткой паузы всё дерево процессов
        добивается принудительно. Управление возвращается сразу, а ``on_done``
        вызывается, когда почта уже остановлена.
        """
        if self._closing:
            return
        self._closing = True

        for job in (self._poll_job, self._start_job, self._pending_show_job):
            if job is not None:
                self.root.after_cancel(job)
        self._poll_job = None
        self._start_job = None
        self._pending_show_job = None

        if not self._is_running():
            self._release_job()
            if on_done is not None:
                on_done()
            return

        self._send_command("quit")
        self._shutdown_job = self.root.after(
            self.SHUTDOWN_GRACE_MS,
            self._finalize_shutdown,
            on_done,
        )

    def _finalize_shutdown(self, on_done=None):
        self._shutdown_job = None
        process = self.process
        if process is not None and process.poll() is None:
            self._terminate_process_tree(process)
        self._close_pipes(process)
        self._release_job()
        if on_done is not None:
            on_done()

    def _terminate_process_tree(self, process):
        """Гасит процесс почты вместе со всеми дочерними процессами Qt."""
        if self._job:
            _terminate_job(self._job)
            return
        try:
            process.kill()
        except OSError:
            pass

    @staticmethod
    def _close_pipes(process):
        if process is None:
            return
        for stream in (process.stdin, process.stdout):
            try:
                if stream is not None:
                    stream.close()
            except OSError:
                pass

    def _release_job(self):
        if self._job:
            _close_job_handle(self._job)
            self._job = None

    def close(self):
        """Совместимость: останавливает почту без ожидания в UI-потоке."""
        self.request_shutdown()

    # --- запуск процесса ---

    def _start_when_sized(self):
        if self._closing or self._start_job is not None:
            return

        width, height = self._host_size()
        if width >= self.MIN_HOST_WIDTH and height >= self.MIN_HOST_HEIGHT:
            self._startup_deadline = None
            self._start_process()
            return

        if self._startup_deadline is None:
            self._startup_deadline = time.monotonic() + 10
        if time.monotonic() >= self._startup_deadline:
            self._startup_deadline = None
            self._show_error(
                "Не удалось определить размер области почты. "
                "Откройте раздел «Почта» ещё раз."
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
        self.host_frame.update_idletasks()
        parent_handle = self.host_frame.winfo_id()

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

        # Привязываем процесс к job-объекту: при аварийном или обычном
        # завершении приложения всё дерево процессов Qt будет уничтожено.
        _assign_process_to_job(self._job, self.process.pid)

        threading.Thread(
            target=self._read_process_output,
            args=(self.process,),
            daemon=True,
        ).start()
        self._poll_job = self.root.after(250, self._drain_process_output)

    def _is_running(self):
        return self.process is not None and self.process.poll() is None

    # --- геометрия и показ ---

    def _host_size(self):
        """Возвращает размер области под почту в пикселях Tk."""
        for widget in (self.host_frame, self.size_source):
            try:
                width = widget.winfo_width()
                height = widget.winfo_height()
            except tk.TclError:
                continue
            if width >= self.MIN_HOST_WIDTH and height >= self.MIN_HOST_HEIGHT:
                return width, height

        return (
            max(self.host_frame.winfo_width(), 1),
            max(self.host_frame.winfo_height(), 1),
        )

    def _apply_pending_show(self):
        self._pending_show_job = None
        if not self._pending_show or not self._is_running() or self._closing:
            return

        width, height = self._host_size()
        if width < self.MIN_HOST_WIDTH or height < self.MIN_HOST_HEIGHT:
            self._pending_show_job = self.root.after(100, self._apply_pending_show)
            return

        self._pending_show = False
        self._send_command(f"show {width} {height}")

    def _cancel_pending_show(self):
        if self._pending_show_job is not None:
            self.root.after_cancel(self._pending_show_job)
            self._pending_show_job = None

    def _on_host_resize(self, event):
        if not self._visible or not self._is_running():
            return
        if event.width < self.MIN_HOST_WIDTH or event.height < self.MIN_HOST_HEIGHT:
            return
        self._send_command(f"resize {event.width} {event.height}")

    def _on_root_mapped(self, event):
        if event.widget is self.root and self._visible and self._is_running():
            self.root.after_idle(self._refresh_window)

    def _refresh_window(self):
        if not self._visible or not self._is_running():
            return
        self._send_command("refresh")

    def _send_command(self, command: str):
        if self.process is None or self.process.stdin is None:
            return
        try:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    # --- обмен сообщениями с процессом ---

    def _read_process_output(self, process):
        if process.stdout is None:
            return
        try:
            for line in process.stdout:
                message = line.strip()
                if message == "READY" or message.startswith(
                    ("ERROR:", "NAVIGATION_COMPLETED:", "NAVIGATION_FAILED:")
                ):
                    self._output_queue.put(message)
        except (OSError, ValueError):
            # Поток закрыт во время остановки приложения — это ожидаемо.
            pass

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
                self._apply_pending_show()
            elif message.startswith("NAVIGATION_COMPLETED:"):
                self.last_navigation = message
                self._page_loaded = True
                self._navigation_deadline = None
            elif message.startswith("NAVIGATION_FAILED:"):
                self.last_navigation = message
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
                self._error_reported = True
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
                and not self._error_reported
            ):
                self._error_reported = True
                self._page_loaded = True
                self._show_error(
                    "Яндекс.Почта не завершила загрузку. "
                    "Проверьте подключение к Интернету."
                )
            self._poll_job = self.root.after(1000, self._drain_process_output)
            return

        if not self._is_running() and not self._error_reported:
            self._error_reported = True
            self._show_error(
                "Процесс встроенной почты завершился. "
                "Перезапустите приложение и попробуйте снова."
            )

    def _show_error(self, message):
        if not self._closing:
            messagebox.showerror("Почта", message, parent=self.root)
