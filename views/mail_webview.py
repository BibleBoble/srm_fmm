"""WebView2-процесс, встроенный в HWND-контейнер Tkinter."""
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
WS_CLIPCHILDREN = 0x02000000
WS_CLIPSIBLINGS = 0x04000000
GWL_STYLE = -16
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020
SW_HIDE = 0
RDW_INVALIDATE = 0x0001
RDW_FRAME = 0x0400
RDW_ALLCHILDREN = 0x0080
RDW_UPDATENOW = 0x0100


def _read_commands(commands):
    for line in sys.stdin:
        parts = line.strip().split()
        if not parts:
            continue
        command = parts[0]
        try:
            if command in {"show", "refresh", "quit"} and len(parts) == 1:
                commands.put((command,))
            elif command == "resize" and len(parts) == 3:
                commands.put((command, int(parts[1]), int(parts[2])))
        except ValueError:
            continue
        if command == "quit":
            return


def _create_mail_window(webview, width, height):
    """Creates the browser hidden so it never flashes as a separate window."""
    return webview.create_window(
        "Яндекс.Почта",
        MAIL_URL,
        width=max(width, 1),
        height=max(height, 1),
        min_size=(400, 300),
        frameless=True,
        hidden=True,
        focus=False
    )


def _set_embedded_window_size(user32, native_handle, width, height):
    """Applies the host size without changing the child's visibility."""
    if not user32.SetWindowPos(
        ctypes.c_void_p(native_handle),
        None,
        0,
        0,
        max(width, 1),
        max(height, 1),
        SWP_NOZORDER
    ):
        raise ctypes.WinError()


def _show_embedded_window(window, user32, native_handle, width, height):
    """Sizes the child first, then lets WinForms show its WebView control."""
    _set_embedded_window_size(user32, native_handle, width, height)
    window.show()


def _refresh_embedded_window(user32, native_handle):
    """Forces WebView2 and its child controls to repaint after a restore."""
    user32.RedrawWindow.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint
    ]
    user32.RedrawWindow.restype = ctypes.c_int
    if not user32.RedrawWindow(
        ctypes.c_void_p(native_handle),
        None,
        None,
        RDW_INVALIDATE | RDW_FRAME | RDW_ALLCHILDREN | RDW_UPDATENOW
    ):
        raise ctypes.WinError()


def _attach_navigation_diagnostics(window):
    """Reports the actual WebView2 navigation result, not JS bridge readiness."""
    browser = window.native.browser.webview

    def on_navigation_completed(sender, event):
        host = urlsplit(str(sender.Source)).hostname or "неизвестный адрес"
        if event.IsSuccess:
            print(f"NAVIGATION_COMPLETED: {host}", flush=True)
            return

        print(
            f"NAVIGATION_FAILED: {host}; статус {event.WebErrorStatus}",
            flush=True
        )

    browser.NavigationCompleted += on_navigation_completed


def _embed_window(window, parent_handle, width, height):
    native_handle = int(window.native.Handle.ToInt64())
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

    parent_style = get_window_long(ctypes.c_void_p(parent_handle), GWL_STYLE)
    if (parent_style & WS_CLIPCHILDREN) == 0:
        kernel32.SetLastError(0)
        set_window_long(
            ctypes.c_void_p(parent_handle),
            GWL_STYLE,
            parent_style | WS_CLIPCHILDREN
        )
        if kernel32.GetLastError():
            raise ctypes.WinError()

    style = get_window_long(ctypes.c_void_p(native_handle), GWL_STYLE)
    style = (style | WS_CHILD | WS_CLIPSIBLINGS) & ~(
        WS_POPUP
        | WS_CAPTION
        | WS_THICKFRAME
        | WS_SYSMENU
        | WS_MINIMIZEBOX
        | WS_MAXIMIZEBOX
    )
    kernel32.SetLastError(0)
    set_window_long(ctypes.c_void_p(native_handle), GWL_STYLE, style)
    if kernel32.GetLastError():
        raise ctypes.WinError()

    if not user32.SetWindowPos(
        ctypes.c_void_p(native_handle),
        None,
        0,
        0,
        max(width, 1),
        max(height, 1),
        SWP_NOZORDER | SWP_FRAMECHANGED
    ):
        raise ctypes.WinError()
    return native_handle


def _prepare_embedded_window(window, parent_handle, width, height, ready, errors):
    """Embeds the native form synchronously before pywebview first displays it."""
    try:
        _attach_navigation_diagnostics(window)
        _embed_window(window, parent_handle, width, height)
    except Exception as error:
        errors.put(str(error))
    finally:
        ready.set()


def _run_commands(
    window,
    width,
    height,
    commands,
    shutting_down,
    embedding_ready,
    embedding_errors
):
    if not embedding_ready.wait(25):
        embedding_errors.put("Истекло время ожидания создания контейнера WebView2.")

    try:
        embedding_error = embedding_errors.get_nowait()
    except queue.Empty:
        embedding_error = None

    if embedding_error is not None:
        print(f"ERROR: {embedding_error}", flush=True)
        while True:
            command = commands.get()
            if command[0] == "quit":
                shutting_down.set()
                window.destroy()
                return

    try:
        native_handle = int(window.native.Handle.ToInt64())
        print("READY", flush=True)
    except Exception as error:
        print(f"ERROR: {error}", flush=True)
        shutting_down.set()
        window.destroy()
        return

    user32 = ctypes.windll.user32
    current_width = width
    current_height = height
    window_shown = False
    while True:
        command = commands.get()
        if command[0] == "show":
            try:
                if not window_shown:
                    _show_embedded_window(
                        window,
                        user32,
                        native_handle,
                        current_width,
                        current_height
                    )
                    window_shown = True
                else:
                    _set_embedded_window_size(
                        user32,
                        native_handle,
                        current_width,
                        current_height
                    )
                    _refresh_embedded_window(user32, native_handle)
            except Exception as error:
                print(f"ERROR: show: {error}", flush=True)
                continue
        elif command[0] == "refresh" and window_shown:
            try:
                _refresh_embedded_window(user32, native_handle)
            except Exception as error:
                print(f"ERROR: refresh: {error}", flush=True)
        elif command[0] == "resize":
            current_width = command[1]
            current_height = command[2]
            try:
                _set_embedded_window_size(
                    user32,
                    native_handle,
                    current_width,
                    current_height
                )
            except OSError as error:
                print(f"ERROR: resize: {error}", flush=True)
        elif command[0] == "quit":
            shutting_down.set()
            window.destroy()
            return


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
        import webview
    except ModuleNotFoundError as error:
        if error.name != "webview":
            raise
        install_command = (
            f'"{sys.executable}" -m pip install -r requirements.txt'
        )
        print(
            "ERROR: Не установлена зависимость pywebview. "
            f"Установите её командой: {install_command}",
            flush=True
        )
        return

    try:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            raise RuntimeError("В Windows не задан путь LOCALAPPDATA.")

        storage_path = Path(local_app_data) / "SRM FMM" / "mail-profile"
        storage_path.mkdir(parents=True, exist_ok=True)

        commands = queue.Queue()
        shutting_down = threading.Event()
        embedding_ready = threading.Event()
        embedding_errors = queue.Queue()
        threading.Thread(
            target=_read_commands,
            args=(commands,),
            daemon=True
        ).start()

        window = _create_mail_window(webview, width, height)
        window.events.before_show += lambda: _prepare_embedded_window(
            window,
            parent_handle,
            width,
            height,
            embedding_ready,
            embedding_errors
        )
        window.events.loaded += lambda: print("PYWEBVIEW_READY", flush=True)

        def prevent_native_close():
            return shutting_down.is_set()

        window.events.closing += prevent_native_close
        webview.start(
            func=lambda: _run_commands(
                window,
                width,
                height,
                commands,
                shutting_down,
                embedding_ready,
                embedding_errors
            ),
            gui="edgechromium",
            private_mode=False,
            storage_path=str(storage_path)
        )
    except Exception as error:
        print(f"ERROR: {error}", flush=True)


if __name__ == "__main__":
    main()