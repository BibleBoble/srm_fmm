# -*- coding: utf-8 -*-
"""Проверка Qt WebEngine, используемого в разделе «Почта» SRM FMM."""
import importlib.metadata
import sys
import traceback


def main():
    print("Интерпретатор:", sys.executable)
    print("Версия Python:", sys.version)
    try:
        version = importlib.metadata.version("PySide6")
        print("Версия PySide6:", version)

        from PySide6.QtCore import QLibraryInfo
        from PySide6.QtWebEngineCore import QWebEngineProfile
        from PySide6.QtWebEngineWidgets import QWebEngineView

        print("Qt WebEngine доступен.")
        print(
            "Путь к библиотекам Qt:",
            QLibraryInfo.path(QLibraryInfo.LibraryPath.LibrariesPath)
        )
        print(
            "Политика постоянных cookies:",
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )
        print("Класс браузера:", QWebEngineView.__name__)
    except Exception:
        print("Qt WebEngine не загрузился:")
        traceback.print_exc()
        return 1

    print(
        "Профиль Яндекс.Почты хранится в "
        "%LOCALAPPDATA%\\SRM FMM\\mail-profile-qt."
    )
    print(
        "Если почта не отображается во встроенном окне, "
        "пришлите вывод диагностики и ошибку из окна «Почта»."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
