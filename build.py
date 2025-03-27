import PyInstaller.__main__
import os

# Получаем текущую директорию
current_dir = os.path.dirname(os.path.abspath(__file__))

# Путь к иконке
icon_path = os.path.join(current_dir, 'MAINICON.ico')

# Проверяем существование иконки
if not os.path.exists(icon_path):
    print(f"Ошибка: Файл иконки {icon_path} не найден!")
    exit(1)

# Параметры для PyInstaller
PyInstaller.__main__.run([
    'app.py',  # Основной файл приложения
    '--name=Web',  # Имя выходного файла
    '--onefile',  # Создать один исполняемый файл
    '--console',  # Добавить консоль
    f'--icon={icon_path}',  # Путь к иконке
    '--add-data=templates;templates',  # Добавить папку с шаблонами
    '--add-data=static;static',  # Добавить папку со статическими файлами
    '--clean',  # Очистить временные файлы
    '--noconfirm',  # Не спрашивать подтверждения
    '--log-level=INFO'  # Уровень логирования
]) 