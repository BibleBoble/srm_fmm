# Тест синтаксиса
try:
    from views.tasks_view import TasksView
    print("Синтаксис tasks_view.py корректен")
except SyntaxError as e:
    print(f"Синтаксическая ошибка: {e}")
except Exception as e:
    print(f"Другая ошибка: {e}")
