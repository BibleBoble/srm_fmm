"""Отдельный Qt WebEngine процесс для вкладки Яндекс.Почты."""
import ctypes
import os
import queue
import sys
import threading
from pathlib import Path
from urllib.parse import urlsplit


MAIL_URL = "https://mail.yandex.ru"
WS_CHILD = 0x40000000
WS_POPUP = 0x80000000
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
WS_CLIPSIBLINGS = 0x04000000
WS_CLIPCHILDREN = 0x02000000
GWL_STYLE = -16
HWND_TOP = 0
SW_HIDE = 0
SW_SHOW = 5
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040


def _read_commands(commands):
    """Читает команды управления из stdin, не блокируя цикл Qt."""
    for line in sys.stdin:
        parts = line.strip().split()
        if not parts:
            continue

        command = parts[0]
        try:
            if command in {"show", "hide", "refresh", "quit"} and len(parts) == 1:
                commands.put((command,))
            elif command == "resize" and len(parts) == 3:
                commands.put((command, int(parts[1]), int(parts[2])))
        except ValueError:
            continue

        if command == "quit":
            return


def _window_style_api(user32, kernel32):
    get_window_long = user32.GetWindowLongPtrW
    get_window_long.argtypes = [ctypes.c_void_p, ctypes.c_int]
    get_window_long.restype = ctypes.c_ssize_t
    set_window_long = user32.SetWindowLongPtrW
    set_window_long.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_ssize_t
    ]
    set_window_long.restype = ctypes.c_ssize_t
    kernel32.SetLastError(0)
    return get_window_long, set_window_long


def _embed_window(native_handle, parent_handle, width, height):
    """Reparents the Qt top-level HWND into the Tk mail host."""
    if sys.platform != "win32":
        raise OSError("Встраивание почты поддерживается только в Windows.")

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.ShowWindow(ctypes.c_void_p(native_handle), SW_HIDE)
    user32.SetParent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    user32.SetParent.restype = ctypes.c_void_p
    kernel32.SetLastError(0)
    previous_parent = user32.SetParent(
        ctypes.c_void_p(native_handle),
        ctypes.c_void_p(parent_handle)
    )
    if not previous_parent and kernel32.GetLastError():
        raise ctypes.WinError()

    get_window_long, set_window_long = _window_style_api(user32, kernel32)
    parent = ctypes.c_void_p(parent_handle)
    parent_style = get_window_long(parent, GWL_STYLE)
    if not parent_style & WS_CLIPCHILDREN:
        kernel32.SetLastError(0)
        set_window_long(parent, GWL_STYLE, parent_style | WS_CLIPCHILDREN)
        if kernel32.GetLastError():
            raise ctypes.WinError()

    child = ctypes.c_void_p(native_handle)
    style = get_window_long(child, GWL_STYLE)
    style = (style | WS_CHILD | WS_CLIPSIBLINGS) & ~(
        WS_POPUP
        | WS_CAPTION
        | WS_THICKFRAME
        | WS_SYSMENU
        | WS_MINIMIZEBOX
        | WS_MAXIMIZEBOX
    )
    kernel32.SetLastError(0)
    set_window_long(child, GWL_STYLE, style)
    if kernel32.GetLastError():
        raise ctypes.WinError()
    _resize_window(user32, native_handle, width, height, frame_changed=True)


def _resize_window(user32, native_handle, width, height, frame_changed=False):
    flags = SWP_NOZORDER | SWP_NOACTIVATE
    if frame_changed:
        flags |= SWP_FRAMECHANGED
    if not user32.SetWindowPos(
        ctypes.c_void_p(native_handle),
        None,
        0,
        0,
        max(width, 1),
        max(height, 1),
        flags
    ):
        raise ctypes.WinError()


def _show_window(user32, native_handle, width, height):
    """Sizes and shows the embedded browser without taking application focus."""
    if not user32.SetWindowPos(
        ctypes.c_void_p(native_handle),
        ctypes.c_void_p(HWND_TOP),
        0,
        0,
        max(width, 1),
        max(height, 1),
        SWP_NOACTIVATE | SWP_SHOWWINDOW
    ):
        raise ctypes.WinError()


def _page_host(url):
    return urlsplit(url).hostname or "неизвестный адрес"


def _create_browser(app, width, height, storage_path):
    """Creates a persistent Chromium profile and the embedded browser widget."""
    from PySide6.QtCore import QUrl, Qt
    from PySide6.QtWidgets import QVBoxLayout, QWidget
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
    from PySide6.QtWebEngineWidgets import QWebEngineView

    profile = QWebEngineProfile("YandexMail", app)
    profile.setPersistentStoragePath(str(storage_path / "storage"))
    profile.setCachePath(str(storage_path / "cache"))
    profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
    )

    container = QWidget()
    container.setWindowTitle("Яндекс.Почта")
    container.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
    container.setGeometry(0, 0, max(width, 1), max(height, 1))

    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    browser = QWebEngineView(container)
    browser.setPage(QWebEnginePage(profile, browser))
    layout.addWidget(browser)

    browser.loadFinished.connect(
        lambda success: print(
            (
                "NAVIGATION_COMPLETED: "
                if success else "NAVIGATION_FAILED: "
            )
            + _page_host(browser.url().toString())
            + ("" if success else "; загрузка завершилась с ошибкой"),
            flush=True
        )
    )
    browser.page().renderProcessTerminated.connect(
        lambda status, exit_code: print(
            f"ERROR: Процесс отрисовки почты завершился: {status}, код {exit_code}.",
            flush=True
        )
    )

    container.winId()
    app.processEvents()
    browser.setUrl(QUrl(MAIL_URL))
    return container, browser


def _run_commands(app, container, native_handle, commands):
    user32 = ctypes.windll.user32
    current_width = max(container.width(), 1)
    current_height = max(container.height(), 1)

    while True:
        try:
            command = commands.get_nowait()
        except queue.Empty:
            break

        try:
            if command[0] == "quit":
                app.quit()
                return
            if command[0] == "show":
                container.show()
                app.processEvents()
                container.update()
                container.repaint()
                _show_window(
                    user32,
                    native_handle,
                    current_width,
                    current_height
                )
            elif command[0] == "hide":
                container.hide()
                user32.ShowWindow(ctypes.c_void_p(native_handle), SW_HIDE)
            elif command[0] == "refresh":
                container.update()
                container.repaint()
            elif command[0] == "resize":
                current_width, current_height = command[1:]
                container.resize(current_width, current_height)
                _resize_window(
                    user32,
                    native_handle,
                    current_width,
                    current_height
                )
        except Exception as error:
            print(f"ERROR: {command[0]}: {error}", flush=True)


def main():
    if len(sys.argv) != 4:
        print("ERROR: Не переданы параметры встроенного окна почты.", flush=True)
        return
    if sys.platform != "win32":
        print("ERROR: Встроенная почта поддерживается только в Windows.", flush=True)
        return

    try:
        parent_handle, width, height = (int(value) for value in sys.argv[1:])
        if parent_handle <= 0:
            raise ValueError("Некорректный HWND-контейнер.")
    except ValueError as error:
        print(f"ERROR: {error}", flush=True)
        return

    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication
    except ModuleNotFoundError as error:
        if error.name != "PySide6":
            raise
        print(
            "ERROR: Не установлена зависимость PySide6 с Qt WebEngine. "
            "Установите её командой: "
            f'"{sys.executable}" -m pip install -r requirements.txt',
            flush=True
        )
        return

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        print("ERROR: В Windows не задан путь LOCALAPPDATA.", flush=True)
        return

    storage_path = Path(local_app_data) / "SRM FMM" / "mail-profile-qt"
    try:
        storage_path.mkdir(parents=True, exist_ok=True)
        app = QApplication(sys.argv[:1])
        app.setQuitOnLastWindowClosed(False)
        container, _ = _create_browser(app, width, height, storage_path)
        native_handle = int(container.winId())
        _embed_window(native_handle, parent_handle, width, height)

        commands = queue.Queue()
        threading.Thread(
            target=_read_commands,
            args=(commands,),
            daemon=True
        ).start()
        timer = QTimer()
        timer.timeout.connect(
            lambda: _run_commands(app, container, native_handle, commands)
        )
        timer.start(30)
        print("READY", flush=True)
        app.exec()
        container.close()
    except Exception as error:
        print(f"ERROR: {error}", flush=True)


if __name__ == "__main__":
    main()
