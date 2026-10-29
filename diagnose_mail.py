# -*- coding: utf-8 -*-
"""Диагностика раздела «Почта» SRM FMM.

Запуск (из папки проекта, в ТОМ интерпретаторе, который использует приложение):

    .venv\\Scripts\\python.exe diagnose_mail.py

или, если виртуального окружения нет:

    python diagnose_mail.py

Скрипт НЕ меняет проект. Он проверяет по шагам:
  1. импортируется ли pywebview в этом интерпретаторе;
  2. установлен ли Microsoft Edge WebView2 Runtime;
  3. открывается ли обычное (не встроенное) окно с Яндекс.Почтой.
Если шаг 3 проходит — проблема во встраивании (views/mail_webview.py),
если падает — причина в ошибке, которую скрипт и покажет.
"""
import sys
import traceback

LINE = "=" * 60


def step(title):
    print(f"\n{LINE}\n{title}\n{LINE}")


# --- Шаг 0: какой это интерпретатор -------------------------------
step("Шаг 0. Интерпретатор")
print("sys.executable =", sys.executable)
print("Версия Python  =", sys.version)

# --- Шаг 1: что на самом деле импортируется как "webview" ----------
step("Шаг 1. Модуль webview — что реально импортируется")
try:
    import webview
    print("OK: import webview прошёл")
    print("Файл модуля (webview.__file__) =", getattr(webview, "__file__", "<нет __file__>"))
except Exception:
    print("ОШИБКА: import webview не удался:")
    traceback.print_exc()
    print("Лечение:  <интерпретатор> -m pip install -r requirements.txt")
    sys.exit(1)

import importlib.metadata as importlib_metadata
try:
    real_version = importlib_metadata.version("pywebview")
    print("Дистрибутив pywebview найден, версия:", real_version)
    if int(real_version.split(".")[0]) >= 6:
        print("ВНИМАНИЕ: установлен pywebview 6.x, а код встраивания писался под 5.x.")
        print("Раздел почты мог сломаться именно после обновления pywebview.")
        print("Лечение:  <интерпретатор> -m pip install \"pywebview>=5.4,<6\"")
except importlib_metadata.PackageNotFoundError:
    print("!!! Дистрибутив 'pywebview' НЕ найден в этом окружении.")
    print("!!! Значит import webview взял одноимённый ЧУЖОЙ пакет 'webview'.")
    print("Лечение:")
    print("    <интерпретатор> -m pip uninstall -y webview")
    print("    <интерпретатор> -m pip install \"pywebview>=5.4,<7\"")

for attr in ("create_window", "start"):
    if not hasattr(webview, attr):
        print(f"!!! У импортированного webview НЕТ {attr}() — это точно НЕ pywebview.")

# --- Шаг 2: WebView2 Runtime --------------------------------------
step("Шаг 2. Microsoft Edge WebView2 Runtime")
try:
    import winreg

    def find_webview2():
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\EdgeUpdate\Clients"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\EdgeUpdate\Clients"),
        ]
        for root, path in keys:
            try:
                with winreg.OpenKey(root, path) as clients:
                    index = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(clients, index)
                        except OSError:
                            break
                        index += 1
                        try:
                            with winreg.OpenKey(clients, subkey_name) as subkey:
                                try:
                                    name, _ = winreg.QueryValueEx(subkey, "name")
                                except OSError:
                                    continue
                                if "WebView2" in str(name):
                                    try:
                                        version, _ = winreg.QueryValueEx(subkey, "pv")
                                    except OSError:
                                        version = "?"
                                    return f"{name} {version}"
                        except OSError:
                            continue
            except OSError:
                continue
        return None

    found = find_webview2()
    if found:
        print("OK: найден", found)
    else:
        print("НЕ НАЙДЕН в реестре!")
        print("Лечение: скачать и установить 'Microsoft Edge WebView2 Runtime'")
        print("(Evergreen Bootstrapper) с сайта Microsoft:")
        print("https://developer.microsoft.com/microsoft-edge/webview2/")
except Exception:
    traceback.print_exc()

# --- Шаг 3: обычное окно с Яндекс.Почтой --------------------------
step("Шаг 3. Открытие Яндекс.Почты в обычном окне pywebview")
print("Если сейчас откроется окно с почтой — WebView2 и pywebview работают,")
print("и проблема кроется во встраивании (views/mail_webview.py).")
print("Если окно пустое/белое или упадёт с ошибкой — причина ниже.")
try:
    import webview as wv

    wv.create_window(
        "Почта — диагностика",
        "https://mail.yandex.ru",
        width=1100,
        height=700,
    )
    wv.start(gui="edgechromium", private_mode=False)
    print("\nOK: окно отработало штатно.")
except Exception:
    print("\nОШИБКА при открытии окна:")
    traceback.print_exc()

step("Диагностика завершена")
print("Пришлите весь вывод этого скрипта — по нему назову точную причину.")
input("\nНажмите Enter для выхода... ")