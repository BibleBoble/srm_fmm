# -*- coding: utf-8 -*-
"""Фоновое формирование PDF для документов клиента.

DOCX создаётся синхронно и мгновенно, а конвертация в PDF выполняется
отдельным процессом: интерфейс не блокируется, Word запускается один раз
на всю пачку документов.
"""
import json
import queue
import subprocess
import sys
import threading
from pathlib import Path

_CREATE_NO_WINDOW = 0x08000000
_POLL_INTERVAL_MS = 120


class DocumentService:
    """Отвечает за фоновую конвертацию готовых DOCX в PDF."""

    def __init__(self, tk_root=None):
        self.tk_root = tk_root
        self._results = queue.Queue()
        self._poll_job = None
        if self.tk_root is not None:
            self._schedule_poll()

    def convert_pdf(self, pairs, on_done=None):
        """Запустить конвертацию в фоне.

        Args:
            pairs: список пар (docx_path, pdf_path).
            on_done: функция (success: bool, error: str); вызывается в
                потоке Tk, если он задан.
        """
        jobs = [
            (Path(docx).resolve(), Path(pdf).resolve())
            for docx, pdf in pairs
        ]
        if not jobs:
            self._publish(on_done, True, "")
            return

        threading.Thread(
            target=self._run,
            args=(jobs, on_done),
            daemon=True,
        ).start()

    # --- внутреннее ---

    def _run(self, jobs, on_done):
        payload = json.dumps(
            [[str(docx), str(pdf)] for docx, pdf in jobs],
            ensure_ascii=True,
        )
        success = False
        error = ""
        try:
            completed = subprocess.run(
                [self._interpreter(), "-X", "utf8", str(self._script())],
                input=payload,
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=_CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            success = completed.returncode == 0
            if not success:
                error = (completed.stdout + "\n" + completed.stderr).strip()
        except Exception as exception:  # noqa: BLE001 - показываем пользователю
            error = str(exception)

        self._publish(on_done, success, error)

    def _publish(self, on_done, success, error):
        if on_done is None:
            return
        if self.tk_root is None:
            on_done(success, error)
            return
        self._results.put((on_done, success, error))

    def _schedule_poll(self):
        try:
            self._poll_job = self.tk_root.after(_POLL_INTERVAL_MS, self._poll)
        except Exception:  # noqa: BLE001 - окно уже закрыто
            self._poll_job = None

    def _poll(self):
        self._poll_job = None
        while True:
            try:
                on_done, success, error = self._results.get_nowait()
            except queue.Empty:
                break
            try:
                on_done(success, error)
            except Exception:  # noqa: BLE001 - карточка могла быть закрыта
                pass
        self._schedule_poll()

    def close(self):
        """Остановить опрос результатов (вызывается при выходе)."""
        if self._poll_job is not None and self.tk_root is not None:
            try:
                self.tk_root.after_cancel(self._poll_job)
            except Exception:  # noqa: BLE001
                pass
        self._poll_job = None

    @staticmethod
    def _interpreter():
        project_root = Path(__file__).resolve().parent.parent
        candidate = project_root / ".venv" / "Scripts" / "python.exe"
        return str(candidate) if candidate.is_file() else sys.executable

    @staticmethod
    def _script():
        return Path(__file__).resolve().parent.parent / "utils" / "pdf_export.py"
