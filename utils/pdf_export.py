# -*- coding: utf-8 -*-
"""Пакетный экспорт DOCX в PDF через Microsoft Word.

Запускается отдельным процессом из DocumentService: приложение не
блокируется, а Word гарантированно закрывается после конвертации.
"""
import json
import sys
from pathlib import Path


def main() -> int:
    try:
        pairs = json.loads(sys.stdin.read() or "[]")
    except json.JSONDecodeError as error:
        print(f"ERROR: некорректные входные данные: {error}", flush=True)
        return 2

    try:
        import pythoncom
        import win32com.client
    except ImportError as error:  # pragma: no cover - зависит от окружения
        print(f"ERROR: не установлен pywin32: {error}", flush=True)
        return 3

    pythoncom.CoInitialize()
    word = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        for docx_path, pdf_path in pairs:
            if not Path(docx_path).is_file():
                raise FileNotFoundError(f"Не найден документ: {docx_path}")
            document = word.Documents.Open(docx_path, False, True, False)
            try:
                document.ExportAsFixedFormat(pdf_path, 17)
            finally:
                document.Close(0)
        print("OK", flush=True)
        return 0
    except Exception as error:  # noqa: BLE001 - сообщение уходит в сервис
        print(f"ERROR: {error}", flush=True)
        return 1
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:  # noqa: BLE001
                pass
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    sys.exit(main())
