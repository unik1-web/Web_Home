# -*- coding: utf-8 -*-
import os
import sys
import locale
import codecs

# Set locale and encoding
if sys.platform.startswith('win'):
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'English_United States.1252')
        except locale.Error:
            pass

# Set console encoding for Windows
os.system('chcp 65001')  # Set UTF-8 encoding for Windows console

# Configure encoding for output and input
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
sys.stdin = codecs.getreader('utf-8')(sys.stdin.buffer)

# Set environment variables for Python
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONLEGACYWINDOWSSTDIO'] = 'utf-8'

# Configure console encoding for Windows via WinAPI
if sys.platform.startswith('win'):
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # Set UTF-8
        kernel32.SetConsoleCP(65001)  # Set UTF-8 for input
    except Exception as e:
        print(f"Error setting console encoding: {e}")

import itertools
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import Calendar
import fdb
import json
from uuid import uuid4
from datetime import datetime, timedelta
import requests
import sqlite3
import logging
import os
from itertools import cycle
import base64
import hashlib

# Функция для создания базы данных
def create_database():
    conn = sqlite3.connect('app_data.sqlite')
    cursor = conn.cursor()

    # Создание таблицы new_auto_go
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS new_auto_go (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetimebrutto TEXT NOT NULL,
                datetimetara TEXT NOT NULL,
                nomer_ts TEXT NOT NULL,
                marka_ts TEXT NOT NULL,
                firma_pol TEXT NOT NULL,
                brutto REAL NOT NULL,
                tara REAL NOT NULL,
                netto REAL NOT NULL,
                gruz_name TEXT NOT NULL,
                inn TEXT NOT NULL,
                kpp TEXT NOT NULL
            )
        ''')

    # Создание таблицы list_auto
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS list_auto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nomer_ts2 TEXT NOT NULL,
                marka_ts2 TEXT NOT NULL,
                min_weight REAL NOT NULL,  
                max_weight REAL NOT NULL 
            )
        ''')

    # Создание таблицы list_cargotypes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS list_cargotypes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            reosend INTEGER DEFAULT 1
        )
    ''')

    # Создание таблицы list_companies
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS list_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            inn TEXT NOT NULL,
            kpp TEXT NOT NULL,
            reosend INTEGER DEFAULT 1
        )
    ''')

    # Создание таблицы auto_uid
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_uid (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                moduletype INTEGER NOT NULL,
                datetimebrutto TEXT NOT NULL,
                uid TEXT NOT NULL
            )
        ''')

    # Создание таблицы reo_data
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS reo_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                reostatus INTEGER NOT NULL,
                reodatetime TEXT NOT NULL
            )
        ''')

    # Создание таблицы auto_go
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_go (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetimebrutto TEXT NOT NULL,
                datetimetara TEXT NOT NULL,
                nomer_ts TEXT NOT NULL,
                marka_ts TEXT NOT NULL,
                firma_pol TEXT NOT NULL,
                brutto REAL NOT NULL,
                tara REAL NOT NULL,
                netto REAL NOT NULL,
                gruz_name TEXT NOT NULL,
                inn TEXT NOT NULL,
                kpp TEXT NOT NULL
            )
        ''')

    conn.commit()
    conn.close()

def check_license():
    try:
        # Секретный ключ (должен совпадать с тем, что использовался при генерации)
        secret_key = "BuzulukSecretKey2024"
        
        # Проверяем наличие файла лицензии
        if not os.path.exists("license.key"):
            messagebox.showerror("Ошибка лицензии", "Файл лицензии не найден!")
            return False
            
        # Читаем закодированный ключ
        with open("license.key", "r") as f:
            encoded_key = f.read().strip()
            
        # Декодируем ключ
        try:
            decoded_key = base64.b64decode(encoded_key.encode()).decode()
        except:
            messagebox.showerror("Ошибка лицензии", "Некорректный формат лицензии!")
            return False
            
        # Извлекаем дату и хеш
        date_str = decoded_key[:8]
        stored_hash = decoded_key[8:]
        
        # Проверяем хеш
        data_to_hash = f"{date_str}{secret_key}"
        hash_object = hashlib.sha256(data_to_hash.encode())
        calculated_hash = hash_object.hexdigest()
        
        if stored_hash != calculated_hash:
            messagebox.showerror("Ошибка лицензии", "Лицензия повреждена!")
            return False
            
        # Проверяем дату
        try:
            expiry_date = datetime.strptime(date_str, "%Y%m%d")
            current_date = datetime.now()
            
            if current_date > expiry_date:
                messagebox.showerror("Ошибка лицензии", "Срок действия лицензии истек!")
                return False
                
            return True
            
        except ValueError:
            messagebox.showerror("Ошибка лицензии", "Некорректная дата в лицензии!")
            return False
            
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при проверке лицензии: {str(e)}")
        return False

# Проверяем лицензию перед запуском программы
if not check_license():
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),  # Logs to file
        logging.StreamHandler()  # Logs to console
    ]
)
logger = logging.getLogger(__name__)

# Log program start
logger.info("Program started")

# Константы
CONFIG_FILE = "app_conf.json"

# Функция для считывания конфигурации
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Функция для сохранения конфигурации
def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def check_and_create_files():
    """Check and create necessary files on startup"""
    logger.info("Starting check of required files")
    
    # Check settings file
    if not os.path.exists(CONFIG_FILE):
        logger.info(f"Settings file {CONFIG_FILE} not found. Creating new file with default settings.")
        default_config = {
            "db_path": r'C:\VESYEVENT.GDB',
            "weight_format": "#.##",
            "date_format": "%Y-%m-%d %H:%M:%S",
            "access_key": "",
            "object_id1": "",
            "object_name1": "TKO Processing Facility, Buzuluk",
            "object_id2": "",
            "object_name2": "MSW Landfill, Buzuluk",
            "object_url": "https://httpbin.org/post"
        }
        save_config(default_config)
        logger.info("Settings file successfully created")
    else:
        logger.info(f"Settings file {CONFIG_FILE} found")
        
    # Load settings
    settings = load_config()
    logger.info("Settings loaded")
    
    # Check SQLite database
    if not os.path.exists('app_data.sqlite'):
        logger.warning("Database app_data.sqlite is missing")
        logger.info("Starting creation of new database app_data.sqlite")
        try:
            create_database()
            logger.info("Database app_data.sqlite successfully created with the following tables:")
            logger.info("- new_auto_go (weighing data)")
            logger.info("- list_auto (vehicle list)")
            logger.info("- list_cargotypes (cargo types)")
            logger.info("- list_companies (company list)")
            logger.info("- auto_uid (weighing identifiers)")
            logger.info("- reo_data (REO data)")
            logger.info("- auto_go (weighing archive)")
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            messagebox.showerror("Error", f"Failed to create database: {e}")
    else:
        logger.info("Database app_data.sqlite found")
    
    # Check connection to VESYEVENT.GDB database
    db_path = settings.get("db_path", r'C:\VESYEVENT.GDB')
    try:
        conn = fdb.connect(dsn=db_path, user='SYSDBA', password='masterkey')
        conn.close()
        logger.info(f"Successfully connected to database {db_path}")
    except Exception as e:
        logger.error(f"Error connecting to database {db_path}: {e}")
        messagebox.showerror("Error", f"Error connecting to database: {e}")

    # Check REO connection
    url = settings.get("object_url", "https://httpbin.org/post")
    try:
        response = requests.get('https://api.reo.ru/reo-weight-control-api/api/v1/weight-controls/import')
        if response.status_code == 200:
            logger.info("Successfully connected to REO service")
        elif response.status_code == 403:
            logger.error("Access denied to REO service. Invalid access key")
            messagebox.showerror("Error", "Access denied to REO service. Invalid access key")
        else:
            logger.error(f"Error checking REO connection. Response code: {response.status_code}")
            messagebox.showerror("Error", f"Error checking REO connection. Response code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error checking REO connection: {e}")
        messagebox.showerror("Error", f"Error checking REO connection: {e}")

    # Check log file
    if not os.path.exists('app.log'):
        logger.info("Log file app.log not found. Will be created automatically on first logging.")
    else:
        logger.info("Log file app.log found")

    logger.info("Required files check completed")

# Проверяем и создаем необходимые файлы при запуске
check_and_create_files()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),  # Logs to file
        logging.StreamHandler()  # Logs to console
    ]
)
logger = logging.getLogger(__name__)

# Настройки подключения к базе данных
db_path = r'C:\VESYEVENT.GDB'
user = 'SYSDBA'
password = 'masterkey'


# Функция для выполнения запроса к базе данных
def fetch_data(date_brutto, db_path):
    try:
        conn = fdb.connect(dsn=db_path, user=user, password=password)
        cursor = conn.cursor()

        query = """
        SELECT DATE_BRUTTO + TIME_BRUTTO AS DATETIME_BRUTTO, 
               DATE_TARA + TIME_TARA AS DATETIME_TARA, 
               NOMER_TS || REGION_TS AS NOMER_TS_FULL, 
               MARKA_TS, 
               FIRMA_POL, 
               BRUTTO, 
               TARA, 
               NETTO, 
               GRUZ_NAME,
               DATEDIFF(MINUTE, TIME_BRUTTO, TIME_TARA) AS TIME_DIFF
        FROM EVENTS
        WHERE DATE_TARA IS NOT NULL 
        AND DATE_BRUTTO = ?
        AND ENABLE = 0
        """
        cursor.execute(query, (date_brutto,))
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        logger.info("Data successfully loaded from database for date: %s", date_brutto)
        return rows
    except Exception as e:
        logger.error("Error loading data from database: %s", e)
        messagebox.showerror("Error", f"Error executing query: {e}")
        return []


# Функция для создания JSON-файла
def create_json(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        logger.info("Data successfully saved to file: %s", filename)
        messagebox.showinfo("Success", f"Data successfully saved to {filename}")
    except Exception as e:
        logger.error("Error saving data to file: %s", e)
        messagebox.showerror("Error", f"Error saving file: {e}")


# Функция для отправки данных в РЭО
def send_to_reo(data, url):
    global stat
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            stat = True
            response_data = response.json()
            logger.info("Data successfully sent to REO\nServer response: 200")
            create_json(response_data, 'output.json')
            messagebox.showinfo("Success", f"Data successfully sent to REO\nServer response: 200")
        else:
            logger.error("Error sending data. Response code: %s, Server response: %s", response.status_code,
                         response.text)
            stat = False
            messagebox.showerror("Error",
                                 f"Error sending data: {response.status_code}\nServer response: {response.text}")
    except Exception as e:
        stat = False
        logger.error("Error sending data: %s", e)
        messagebox.showerror("Error",
                             f"Error sending data")
    return stat



# Основное окно приложения
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Региональный экологический оператор 0.15")
        self.geometry("1200x600")

        # Загрузка настроек
        self.settings = load_config()

        # Переменные
        self.current_date = datetime.now().date()
        self.url = self.settings.get("object_url", "https://httpbin.org/post")
        self.db_path = self.settings.get("db_path", "r'C:\VESYEVENT.GDB'")
        self.оbject_id2 = self.settings.get("object_id2", "new_ObjectId")
        self.access_key = self.settings.get("access_key", "insert_AccessKey")

        # Меню
        self.create_menu()

        # Панель управления датой
        self.create_date_controls()

        # Таблица для отображения данных
        self.create_table()

        # Привязка обработчика закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.quit)

    def position_window(self, window):
        """Позиционирует дочернее окно относительно основного окна"""
        self.update_idletasks()  # Обновляем геометрию основного окна
        x = self.winfo_rootx()
        y = self.winfo_rooty()
        window.geometry(f"+{x}+{y}")  # Устанавливаем позицию дочернего окна

    def quit(self):
        """Обработка закрытия приложения"""
        if messagebox.askyesno("Подтверждение", "Вы хотите выйти из программы?"):
            logger.info("Program termination requested by user")
            super().quit()

    def create_additional_json(self, temp_data):
        # Загрузка данных из таблицы list_auto
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT nomer_ts2, marka_ts2, min_weight, max_weight FROM list_auto")
        transport_data = cursor.fetchall()
        conn.close()

        # Создание словаря для быстрого поиска данных по номеру авто
        transport_dict = {nomer: (marka, min_weight, max_weight) for nomer, marka, min_weight, max_weight in
                          transport_data}
        numbers = list(transport_dict.keys())
        number_iterator = itertools.cycle(numbers)

        # Создание нового JSON-файла
        new_json_data = {
            "ObjectId": self.оbject_id2,  # Новый ObjectId
            "AccessKey": self.access_key,  # Ключ доступа из настроек
            "WeightControls": []
        }

        for weight_control in temp_data["WeightControls"]:
            # Получаем данные из temp.json
            date_before = datetime.strptime(weight_control["dateBefore"], "%Y-%m-%d %H:%M:%S+05:00")
            date_after = datetime.strptime(weight_control["dateAfter"], "%Y-%m-%d %H:%M:%S+05:00")
            garbage_weight = float(weight_control["garbageWeight"])

            # Сдвигаем даты на 1 час
            date_before2 = (date_before + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S+05:00")
            date_after2 = (date_after + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S+05:00")

            # Получаем данные из списка "Транспорт"
            while True:
                registration_number2 = next(number_iterator)  # Используем циклический итератор
                marka_ts2, min_weight, max_weight = transport_dict[registration_number2]

                # Рассчитываем новые значения веса
                weight_before2 = garbage_weight * 0.85 + min_weight
                weight_after2 = min_weight
                garbage_weight2 = garbage_weight * 0.85
                if weight_before2 > max_weight:
                    continue
                else:
                    break

            # Формируем новую запись
            new_weight_control = {
                "id": str(uuid4()),  # Новый uid
                "dateBefore": date_before2,
                "dateAfter": date_after2,
                "registrationNumber": registration_number2,
                "garbageTruckType": None,
                "garbageTruckBrand": marka_ts2,
                "garbageTruckModel": None,
                "companyName": 'ООО "Саночистка"',
                "companyInn": "5603013425",
                "companyKpp": "560301001",
                "weightBefore": str(weight_before2),
                "weightAfter": str(weight_after2),
                "weightDriver": None,
                "coefficient": "1",
                "garbageWeight": str(garbage_weight2),
                "garbageType": "ТКО",
                "codeFKKO": None,
                "nameFKKO": None
            }

            # Добавляем запись в новый JSON
            new_json_data["WeightControls"].append(new_weight_control)

        return new_json_data

    def create_menu(self):
        menubar = tk.Menu(self)

        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Настройки", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Закрыть", command=self.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        # Меню "Данные"
        data_menu = tk.Menu(menubar, tearoff=0)
        data_menu.add_command(label="Отправить данные в РЭО", command=self.send_data)
        data_menu.add_command(label="Сохранить данные в файл JSON", command=self.save_data_to_file)
        data_menu.add_command(label="Обновить", command=self.refresh_data)
        menubar.add_cascade(label="Данные", menu=data_menu)

        # Меню "Список"
        list_menu = tk.Menu(menubar, tearoff=0)
        list_menu.add_command(label="Роды груза", command=self.show_garbage_types)
        list_menu.add_command(label="Компании отправители", command=self.show_companies)
        list_menu.add_command(label="Транспорт", command=self.show_auto)  # Новый пункт меню
        menubar.add_cascade(label="Список", menu=list_menu)

        # Меню "Справка"
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.config(menu=menubar)

    def show_companies(self):
        CompaniesWindow(self)  # Открываем окно "Компании отправители"

    def create_date_controls(self):
        date_frame = tk.Frame(self)
        date_frame.pack(pady=10)

        # Кнопка "Назад"
        self.btn_prev = tk.Button(date_frame, text="Назад", command=self.prev_date)
        self.btn_prev.pack(side=tk.LEFT, padx=5)

        # Поле с текущей датой и кнопкой выбора даты
        self.date_frame = tk.Frame(date_frame)
        self.date_frame.pack(side=tk.LEFT, padx=10)

        self.lbl_date = tk.Label(self.date_frame, text=self.current_date.strftime("%d %B %Y"), font=("Arial", 12))
        self.lbl_date.pack(side=tk.LEFT)

        self.btn_calendar = tk.Button(self.date_frame, text="▼", command=self.toggle_calendar)
        self.btn_calendar.pack(side=tk.LEFT)

        # Календарь (скрыт по умолчанию)
        self.cal_frame = tk.Frame(date_frame)
        self.cal = Calendar(self.cal_frame, selectmode='day', year=self.current_date.year,
                            month=self.current_date.month, day=self.current_date.day)
        self.cal.pack(pady=10)
        self.cal_frame.pack_forget()  # Скрываем календарь

        # Кнопка "Применить" для календаря
        self.btn_apply = tk.Button(self.cal_frame, text="Применить", command=self.apply_date)
        self.btn_apply.pack(pady=5)

        # Кнопка "Вперед"
        self.btn_next = tk.Button(date_frame, text="Вперед", command=self.next_date)
        self.btn_next.pack(side=tk.LEFT, padx=5)

        # Кнопка "Отправить в РЭО"
        self.btn_send = tk.Button(date_frame, text="Отправить в РЭО", command=self.send_data)
        self.btn_send.pack(side=tk.LEFT, padx=5)

    def toggle_calendar(self):
        if self.cal_frame.winfo_ismapped():
            self.cal_frame.pack_forget()  # Скрыть календарь
        else:
            self.cal_frame.pack()  # Показать календарь

    def apply_date(self):
        self.current_date = self.cal.selection_get()
        self.lbl_date.config(text=self.current_date.strftime("%d %B %Y"))
        self.cal_frame.pack_forget()  # Скрыть календарь после выбора даты
        self.refresh_data()

    def prev_date(self):
        self.current_date -= timedelta(days=1)
        self.lbl_date.config(text=self.current_date.strftime("%d %B %Y"))
        self.refresh_data()

    def next_date(self):
        self.current_date += timedelta(days=1)
        self.lbl_date.config(text=self.current_date.strftime("%d %B %Y"))
        self.refresh_data()

    def refresh_data(self):
        # Загрузка актуальных настроек
        self.settings = load_config()

        # Обновление шрифта таблицы
        style = ttk.Style()
        font_family = self.settings.get("font_family", "Arial")
        font_size = self.settings.get("font_size", "10")
        style.configure("Treeview", font=(font_family, font_size))
        style.configure("Treeview.Heading", font=(font_family, font_size))

        # Получение выбранной даты
        selected_date = self.current_date.strftime("%Y-%m-%d")

        # Загрузка данных из базы данных VESYEVENT.GDB
        rows = fetch_data(selected_date, self.db_path)

        # Подключение к базе данных app_data.sqlite
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()

        # Загрузка списка отправляемых грузов
        cursor.execute("SELECT name FROM list_cargotypes WHERE reosend = 1")
        sendable_cargotypes = [row[0] for row in cursor.fetchall()]

        # Загрузка списка отправляемых компаний
        cursor.execute("SELECT name FROM list_companies WHERE reosend = 1")
        sendable_companies = [row[0] for row in cursor.fetchall()]

        # Создание списка для хранения обновленных данных
        updated_rows = []

        for row in rows:
            # Получаем данные о грузе и отправителе
            gruz_name = row[8]  # Название груза
            firma_pol = row[4]  # Название отправителя

            # Проверяем, был ли груз отправлен ранее
            cursor.execute("""
                SELECT COUNT(*) FROM auto_go 
                WHERE nomer_ts = ? AND datetimebrutto = ? AND datetimetara = ?
            """, (row[2], row[0], row[1]))
            result = cursor.fetchone()

            updated_row = list(row[:-1])  # Исключаем TIME_DIFF из данных для таблицы
            time_diff = row[-1]  # Разница во времени в минутах
            updated_row.extend(["", ""])  # Добавляем ИНН и КПП (если они есть)
            if result[0] > 0:
                updated_row.extend(["Отправлено", "Уже отправлено"])  # Добавляем статус и дату отправки
            elif gruz_name not in sendable_cargotypes:
                updated_row.extend(["Не отправлять", ""])  # Добавляем статус и пустую дату отправки
            elif firma_pol not in sendable_companies:
                updated_row.extend(["Не отправлять", ""])  # Добавляем статус и пустую дату отправки
            else:
                updated_row.extend(["Готово к отправке", ""])  # Добавляем статус и пустую дату отправки
            updated_row.extend([time_diff, time_diff])

            updated_rows.append(updated_row)

        conn.close()

        # Обновление таблицы с применением текущих форматов
        self.update_table(updated_rows)

    def create_table(self):
        self.table_frame = tk.Frame(self)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Создание стиля для таблицы
        style = ttk.Style()
        font_family = self.settings.get("font_family", "Arial")
        font_size = self.settings.get("font_size", "10")
        style.configure("Treeview", font=(font_family, font_size))
        style.configure("Treeview.Heading", font=(font_family, font_size))

        columns = (
            "Дата провески брутто", "Дата провески тары", "№ авто", "Марка авто", "Отправитель",
            "Брутто", "Тара", "Нетто", "Род груза", "ИНН", "КПП",
            "Статус от объекта 1", "Статус от объекта 2", "Дата отправки"
        )
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            if col in ("Брутто", "Тара", "Нетто"):
                self.tree.column(col, anchor="e")  # Выравнивание по правому краю
            else:
                self.tree.column(col, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Настройка тегов для выделения строк
        self.tree.tag_configure("error", foreground="red")

        # Добавление контекстного меню для копирования данных
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        # Создание контекстного меню
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Копировать", command=self.copy_selected_rows)
        menu.post(event.x_root, event.y_root)

    def copy_selected_rows(self):
        # Получаем выделенные строки
        selected_items = self.tree.selection()
        if not selected_items:
            return

        # Формируем текст для копирования
        copied_text = ""
        for item in selected_items:
            values = self.tree.item(item, "values")
            copied_text += "\t".join(values) + "\n"

        # Копируем текст в буфер обмена
        self.clipboard_clear()
        self.clipboard_append(copied_text)

    def update_table(self, rows):
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Получение форматов из настроек
        weight_format = self.settings.get("weight_format", "#.##")
        date_format = self.settings.get("date_format", "%Y-%m-%d %H:%M:%S")

        # Преобразование формата веса в формат для f-строки
        if weight_format == "#.":
            weight_format_f = ".0f"  # Без знаков после запятой
        elif weight_format == "#.#":
            weight_format_f = ".1f"  # Один знак после запятой
        elif weight_format == "#.##":
            weight_format_f = ".2f"  # Два знака после запятой
        else:
            weight_format_f = ".2f"  # По умолчанию два знака после запятой

        # Загрузка данных из таблицы list_companies
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT name, inn, kpp FROM list_companies")
        companies = cursor.fetchall()
        conn.close()

        # Создание словаря для быстрого поиска ИНН и КПП по названию компании
        company_dict = {name: (inn, kpp) for name, inn, kpp in companies}

        # Заполнение таблицы данными с применением форматов
        for row in rows:
            formatted_row = list(row[:-1])  # Исключаем TIME_DIFF из данных для таблицы
            time_diff = row[-1]  # Разница во времени в минутах

            # Форматирование веса (Брутто, Тара, Нетто)
            formatted_row[5] = f"{float(row[5]):{weight_format_f}}"
            formatted_row[6] = f"{float(row[6]):{weight_format_f}}"
            formatted_row[7] = f"{float(row[7]):{weight_format_f}}"
            # Форматирование даты
            formatted_row[0] = row[0].strftime(date_format)
            formatted_row[1] = row[1].strftime(date_format)

            # Поиск ИНН и КПП по названию отправителя
            sender = row[4]  # Название отправителя
            if sender in company_dict:
                inn, kpp = company_dict[sender]  # Получаем ИНН и КПП из словаря
            else:
                inn, kpp = "", ""  # Если отправитель отсутствует в списке, оставляем пустые значения

            # Добавляем ИНН и КПП в строку данных
            formatted_row[9], formatted_row[10] = [inn, kpp]  # Добавляем ИНН и КПП в конец строки

            # Добавляем статус отправки
            if time_diff <= 0:
                status = "Ошибка времени"
                tag = "error"  # Тег для изменения цвета текста
            else:
                status = row[11]
                tag = ""

            formatted_row[11], formatted_row[12], formatted_row[13] = [status, status, row[
                12]]  # Добавляем статус и пустую дату отправки

            # Вставляем строку в таблицу
            self.tree.insert("", tk.END, values=formatted_row, tags=(tag,))

            # Автоматическая настройка ширины колонок
            self.adjust_column_widths()

    def adjust_column_widths(self):
        # Определение максимальной длины данных в каждой колонке
        for col in self.tree["columns"]:
            # Получаем заголовок колонки
            header_width = len(self.tree.heading(col)["text"]) * 8  # Примерно 8 пикселей на символ

            # Получаем максимальную длину данных в колонке
            data_width = max(len(str(self.tree.set(item, col))) for item in
                             self.tree.get_children()) * 8  # Примерно 8 пикселей на символ

            # Устанавливаем ширину колонки как максимум из ширины заголовка и данных
            if col in ("Брутто", "Тара", "Нетто"):
                self.tree.column(col, width=100)  # +20 пикселей для запаса
            else:
                self.tree.column(col, width=max(header_width, data_width) + 20)  # +20 пикселей для запаса

    def create_json_structure(self, rows):
        # Получаем ObjectId и AccessKey из настроек
        object_id1 = self.settings.get("object_id1", "insert_ObjectId")  # Идентификатор объекта
        access_key = self.settings.get("access_key", "insert_AccessKey")  # Ключ доступа

        data = {
            "ObjectId1": object_id1,  # Используем идентификатор объекта из настроек
            "AccessKey": access_key,  # Используем ключ доступа из настроек
            "WeightControls": []
        }

        for row in rows:
            # Генерация уникального uid для каждой машины
            uid = str(uuid4())

            # Преобразуем строку даты обратно в объект datetime
            date_before = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S+05:00")
            date_after = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S+05:00")
            weight_control = {
                "Id": uid,
                "DateBefore": date_before,
                "DateAfter": date_after,
                "registrationNumber": row[2],  # Номер транспортного средства
                "garbageTruckType": None,  # Тип транспортного средства (не указан)
                "garbageTruckBrand": row[3],  # Марка транспортного средства
                "garbageTruckModel": None,  # Модель транспортного средства (не указана)
                "companyName": row[4],  # Название компании-отправителя
                "companyInn": row[9],  # ИНН компании
                "companyKpp": row[10],  # КПП компании
                "weightBefore": str(row[5]),  # Вес брутто
                "weightAfter": str(row[6]),  # Вес тары
                "weightDriver": None,  # Вес водителя (не указан)
                "coefficient": "1",  # Коэффициент (по умолчанию 1)
                "garbageWeight": str(row[7]),  # Вес нетто
                "garbageType": row[8],  # Тип груза
                "codeFKKO": None,  # Код ФККО (не указан)
                "nameFKKO": None  # Название ФККО (не указано)
            }
            data["WeightControls"].append(weight_control)

        return data

    def save_data_to_file(self):
        # Получаем данные из таблицы
        rows = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values[11] == "Готово к отправке":  # Проверяем статус отправки
                rows.append(values)

        if rows:
            data = self.create_json_structure(rows)
            filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if filename:
                create_json(data, filename)

    def send_data(self):
        # Получаем данные из таблицы
        rows = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values[11] == "Готово к отправке":  # Проверяем статус отправки
                rows.append(values)

        if rows:
            # Подключение к SQLite
            conn = sqlite3.connect('app_data.sqlite')
            cursor = conn.cursor()

            # Создаем список для хранения данных, которые будут записаны в temp.json
            temp_data = []

            # Обработка каждой машины
            for row in rows:
                # Проверяем, была ли машина уже отправлена
                cursor.execute("""
                    SELECT COUNT(*) FROM auto_go 
                    WHERE nomer_ts = ? AND datetimebrutto = ? AND datetimetara = ?
                """, (row[2], row[0], row[1]))
                result = cursor.fetchone()

                if result[0] > 0:
                    # Если машина уже отправлена, обновляем статус в таблице
                    self.tree.set(item, column=11, value="Отправлено")  # Используем индекс 11
                    self.tree.set(item, column=13, value="Уже отправлено")  # Используем индекс 12
                    continue  # Пропускаем отправку этой машины

                # Генерация уникального uid для машины
                uid = str(uuid4())

                # Формирование JSON для отправки в РЭО
                date_before = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S+05:00")
                date_after = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S+05:00")
                weight_control = {
                    "id": uid,  # Используем уникальный uid
                    "dateBefore": date_before,
                    "dateAfter": date_after,
                    "registrationNumber": row[2],  # Номер транспортного средства
                    "garbageTruckType": None,  # Тип транспортного средства (не указан)
                    "garbageTruckBrand": row[3],  # Марка транспортного средства
                    "garbageTruckModel": None,  # Модель транспортного средства (не указана)
                    "companyName": row[4],  # Название компании-отправителя
                    "companyInn": row[9],  # ИНН компании
                    "companyKpp": row[10],  # КПП компании
                    "weightBefore": str(row[5]),  # Вес брутто
                    "weightAfter": str(row[6]),  # Вес тары
                    "weightDriver": None,  # Вес водителя (не указан)
                    "coefficient": "1",  # Коэффициент (по умолчанию 1)
                    "garbageWeight": str(row[7]),  # Вес нетто
                    "garbageType": row[8],  # Тип груза
                    "codeFKKO": None,  # Код ФККО (не указан)
                    "nameFKKO": None  # Название ФККО (не указано)
                }

                # Добавляем данные в список для temp.json
                temp_data.append(weight_control)

            if len(temp_data) == 0:  # 'Нет данных для отправки'
                REO_Data = False
            else:
                REO_Data = True
                # Формирование JSON для отправки в РЭО
                json_data = {
                    "ObjectId": "insert_ObjectId",  # Идентификатор объекта из настроек
                    "AccessKey": "insert_AccessKey",  # Ключ доступа из настроек
                    "WeightControls": temp_data
                }

                # Сохраняем данные в temp.json
                with open("temp.json", "w", encoding="utf-8") as temp_file:
                    json.dump(json_data, temp_file, ensure_ascii=False, indent=4)

                # Отправляем данные в РЭО
                if send_to_reo(json_data, self.url):
                    # После успешной отправки, читаем данные из temp.json и обновляем базу данных
                    with open("temp.json", "r", encoding="utf-8") as temp_file:
                        temp_data = json.load(temp_file)

                    for weight_control in temp_data["WeightControls"]:
                        # Вставка данных в таблицу auto_uid
                        cursor.execute("""
                            INSERT INTO auto_uid (moduletype, datetimebrutto, uid)
                            VALUES (?, ?, ?)
                        """, (
                            100,
                            datetime.strptime(weight_control["dateBefore"], "%Y-%m-%d %H:%M:%S+05:00").strftime(
                                "%Y-%m-%d %H:%M:%S"),
                            weight_control["id"]))  # moduletype = 100, datetimebrutto из строки

                        # Вставка данных в таблицу reo_data
                        cursor.execute("""
                            INSERT INTO reo_data (uid, reostatus, reodatetime)
                            VALUES (?, ?, ?)
                        """, (
                            weight_control["id"], 2,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")))  # reostatus = 2 (отправлено)

                        # Вставка данных в таблицу auto_go
                        cursor.execute("""
                            INSERT INTO auto_go (datetimebrutto, datetimetara, nomer_ts, marka_ts, firma_pol, 
                            brutto, tara, netto, gruz_name, inn, kpp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)                    
                        """, (
                            datetime.strptime(weight_control["dateBefore"], "%Y-%m-%d %H:%M:%S+05:00").strftime(
                                "%Y-%m-%d %H:%M:%S"),
                            datetime.strptime(weight_control["dateAfter"], "%Y-%m-%d %H:%M:%S+05:00").strftime(
                                "%Y-%m-%d %H:%M:%S"),
                            weight_control["registrationNumber"],
                            weight_control["garbageTruckBrand"],
                            weight_control["companyName"],
                            weight_control["weightBefore"],
                            weight_control["weightAfter"],
                            weight_control["garbageWeight"],
                            weight_control["garbageType"],
                            weight_control["companyInn"],
                            weight_control["companyKpp"]
                        ))

                # Создание нового JSON-файла с измененными данными
                new_json_data = self.create_additional_json(temp_data)
                with open("temp_additional.json", "w", encoding="utf-8") as additional_file:
                    json.dump(new_json_data, additional_file, ensure_ascii=False, indent=4)

                # Отправка нового JSON-файла в РЭО
                send_to_reo(new_json_data, self.url)

                # Сохранение новых данных в таблицу new_auto_go
                for weight_control in new_json_data["WeightControls"]:
                    cursor.execute("""
                        INSERT INTO new_auto_go (datetimebrutto, datetimetara, nomer_ts, marka_ts, firma_pol, 
                        brutto, tara, netto, gruz_name, inn, kpp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)                    
                    """, (
                        datetime.strptime(weight_control["dateBefore"], "%Y-%m-%d %H:%M:%S+05:00").strftime(
                            "%Y-%m-%d %H:%M:%S"),
                        datetime.strptime(weight_control["dateAfter"], "%Y-%m-%d %H:%M:%S+05:00").strftime(
                            "%Y-%m-%d %H:%M:%S"),
                        weight_control["registrationNumber"],
                        weight_control["garbageTruckBrand"],
                        weight_control["companyName"],
                        weight_control["weightBefore"],
                        weight_control["weightAfter"],
                        weight_control["garbageWeight"],
                        weight_control["garbageType"],
                        weight_control["companyInn"],
                        weight_control["companyKpp"]
                    ))

            # Сохраняем изменения в базе данных
            conn.commit()
            conn.close()

            # Обновляем статус отправки в таблице
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                if values[11] == "Готово к отправке" and REO_Data:
                    self.tree.set(item, column=11, value="Отправлено")  # Используем индекс 11
                    self.tree.set(item, column=12, value="Отправлено")  # Используем индекс 12
                    self.tree.set(item, column=13,
                                  value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def about(self):
        messagebox.showinfo(
            "О программе", """
            Программа для отправки данных в 
            Региональный экологический оператор.
             
            Версия 0.15 от 24.03.2025.
            Лицензия: ООО "Саночистка"
            Объект обработки ТКО, г.Бузулук
            ПТБО г. Бузулука Оренбургской области. 
            
            ЗАПРЕЩЕНО использование программы
            в коммерческих целях без согласования 
            с автором.
            ЗАПРЕЩЕНО распространение программы
            в коммерческих целях без согласования 
            с автором.
            ЗАПРЕЩЕНО любое изменение, адаптирование, 
            перевод, дизассемблирование данной программы
            Поставляется "КАК ЕСТЬ", то есть автор не дает
            никаких гарантий работоспособности программы, 
            а также не несёт никакой ответственности за 
            любой прямой, косвенный или иной ущерб, 
            понесенный в результате её использования. 
            Вы используете это ПО на свой страх и риск.
                """)

    def show_garbage_types(self):
        CargoTypesWindow(self)

    def open_settings(self):
        SettingsWindow(self)

    def show_auto(self):
        AutoWindow(self)  # Открываем окно "Транспорт"


# Окно Настроек
class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Настройки")
        self.geometry("650x600")
        self.transient(parent)  # Окно поверх родительского
        self.grab_set()  # Делает окно модальным
        
        # Позиционируем окно относительно основного
        parent.position_window(self)

        # Загрузка текущих настроек
        self.settings = load_config()

        # Переменные для хранения настроек
        self.db_path = tk.StringVar(value=self.settings.get("db_path", ""))
        self.weight_format = tk.StringVar(value=self.settings.get("weight_format", "#.##"))
        self.date_format = tk.StringVar(value=self.settings.get("date_format", "%Y-%m-%d %H:%M:%S"))
        self.access_key = tk.StringVar(value=self.settings.get("access_key", ""))
        self.object_id1 = tk.StringVar(value=self.settings.get("object_id1", ""))
        self.object_name1 = tk.StringVar(value=self.settings.get("object_name1", "Объект обработки TKO, г. Бузулук"))
        self.object_id2 = tk.StringVar(value=self.settings.get("object_id2", ""))
        self.object_name2 = tk.StringVar(value=self.settings.get("object_name2", "Полигон ТБО, г. Бузулук"))
        self.object_url = tk.StringVar(value=self.settings.get("object_url", "https://httpbin.org/post"))
        self.font_family = tk.StringVar(value=self.settings.get("font_family", "Arial"))
        self.font_size = tk.StringVar(value=self.settings.get("font_size", "10"))

        # Создание интерфейса
        self.create_widgets()

        # Привязка горячих клавиш
        self.bind("<Control-v>", self.paste_from_clipboard)

    def create_widgets(self):
        # Фрейм для настроек
        settings_frame = ttk.LabelFrame(self, text="Настройки модулей")
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # База данных
        ttk.Label(settings_frame, text="База данных:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.db_entry = ttk.Entry(settings_frame, textvariable=self.db_path, width=40)
        self.db_entry.grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(settings_frame, text="...", command=self.select_db_file, width=3).grid(row=0, column=2, padx=10,
                                                                                          pady=10)

        # Вес
        ttk.Label(settings_frame, text="Формат веса:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.weight_combobox = ttk.Combobox(settings_frame, textvariable=self.weight_format,
                                            values=["#.", "#.#", "#.##"])
        self.weight_combobox.grid(row=1, column=1, padx=10, pady=10)

        # Дата и время
        ttk.Label(settings_frame, text="Формат даты и времени:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.date_combobox = ttk.Combobox(settings_frame, textvariable=self.date_format,
                                          values=["%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S"])
        self.date_combobox.grid(row=2, column=1, padx=10, pady=10)

        # Ключ доступа
        ttk.Label(settings_frame, text="Ключ доступа:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        self.access_key_entry = ttk.Entry(settings_frame, textvariable=self.access_key, show="*", width=60)
        self.access_key_entry.grid(row=3, column=1, padx=10, pady=10)

        # Шрифт
        ttk.Label(settings_frame, text="Шрифт:").grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        self.font_family_combobox = ttk.Combobox(settings_frame, textvariable=self.font_family,
                                                values=["Arial", "Times New Roman", "Courier New", "Verdana"])
        self.font_family_combobox.grid(row=4, column=1, padx=10, pady=10)

        # Размер шрифта
        ttk.Label(settings_frame, text="Размер шрифта:").grid(row=5, column=0, padx=10, pady=10, sticky=tk.W)
        self.font_size_combobox = ttk.Combobox(settings_frame, textvariable=self.font_size,
                                              values=["8", "9", "10", "11", "12", "14", "16"])
        self.font_size_combobox.grid(row=5, column=1, padx=10, pady=10)

        # Идентификатор объекта1
        ttk.Label(settings_frame, text="Идентификатор объекта1:").grid(row=6, column=0, padx=10, pady=10, sticky=tk.W)
        self.object_id1_entry = ttk.Entry(settings_frame, textvariable=self.object_id1, width=60)
        self.object_id1_entry.grid(row=6, column=1, padx=10, pady=10)

        # Наименование объекта1
        ttk.Label(settings_frame, text="Наименование объекта1:").grid(row=7, column=0, padx=10, pady=10, sticky=tk.W)
        self.object_name1_entry = ttk.Entry(settings_frame, textvariable=self.object_name1, width=60)
        self.object_name1_entry.grid(row=7, column=1, padx=10, pady=10)

        # Идентификатор объекта2
        ttk.Label(settings_frame, text="Идентификатор объекта2:").grid(row=8, column=0, padx=10, pady=10, sticky=tk.W)
        self.object_id2_entry = ttk.Entry(settings_frame, textvariable=self.object_id2, width=60)
        self.object_id2_entry.grid(row=8, column=1, padx=10, pady=10)

        # Наименование объекта1
        ttk.Label(settings_frame, text="Наименование объекта2:").grid(row=9, column=0, padx=10, pady=10, sticky=tk.W)
        self.object_name2_entry = ttk.Entry(settings_frame, textvariable=self.object_name2, width=60)
        self.object_name2_entry.grid(row=9, column=1, padx=10, pady=10)

        # Адрес сервиса
        ttk.Label(settings_frame, text="Адрес сервиса:").grid(row=10, column=0, padx=10, pady=10, sticky=tk.W)
        self.object_url_entry = ttk.Entry(settings_frame, textvariable=self.object_url, width=60)
        self.object_url_entry.grid(row=10, column=1, padx=10, pady=10)

        # Фрейм для кнопок проверки
        check_buttons_frame = ttk.Frame(settings_frame)
        check_buttons_frame.grid(row=11, column=1, padx=10, pady=10, sticky=tk.W)

        # Кнопки проверки
        ttk.Button(check_buttons_frame, text="Проверка БД", command=self.check_db_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(check_buttons_frame, text="Проверка РЭО", command=self.check_reo_connection).pack(side=tk.LEFT,
                                                                                                     padx=5)

        # Описание
        self.description_label = ttk.Label(settings_frame, text="", wraplength=500)
        self.description_label.grid(row=13, column=0, columnspan=3, padx=10, pady=10)

        # Кнопки ОК и Отмена
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="ОК", command=self.save_settings).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=10)

        # Привязка событий для отображения описания
        self.db_entry.bind("<FocusIn>", lambda e: self.show_description("Выберите файл базы данных для подключения."))
        self.weight_combobox.bind("<FocusIn>", lambda e: self.show_description("Выберите формат вывода веса."))
        self.date_combobox.bind("<FocusIn>", lambda e: self.show_description("Выберите формат вывода даты и времени."))
        self.access_key_entry.bind("<FocusIn>",
                                   lambda e: self.show_description("Введите ключ доступа для отправки данных."))
        self.font_family_combobox.bind("<FocusIn>", lambda e: self.show_description("Выберите шрифт для отображения данных."))
        self.font_size_combobox.bind("<FocusIn>", lambda e: self.show_description("Выберите размер шрифта."))
        self.object_id1_entry.bind("<FocusIn>", lambda e: self.show_description("Введите идентификатор объекта1."))
        self.object_name1_entry.bind("<FocusIn>", lambda e: self.show_description("Введите наименование объекта1."))
        self.object_id2_entry.bind("<FocusIn>", lambda e: self.show_description("Введите идентификатор объекта2."))
        self.object_name2_entry.bind("<FocusIn>", lambda e: self.show_description("Введите наименование объекта2."))
        self.object_url_entry.bind("<FocusIn>",
                                   lambda e: self.show_description("Введите адрес сервиса для отправки JSON-файла."))

        # Привязка контекстного меню
        self.db_entry.bind("<Button-3>", self.show_context_menu)
        self.weight_combobox.bind("<Button-3>", self.show_context_menu)
        self.date_combobox.bind("<Button-3>", self.show_context_menu)
        self.access_key_entry.bind("<Button-3>", self.show_context_menu)
        self.font_family_combobox.bind("<Button-3>", self.show_context_menu)
        self.font_size_combobox.bind("<Button-3>", self.show_context_menu)
        self.object_id1_entry.bind("<Button-3>", self.show_context_menu)
        self.object_name1_entry.bind("<Button-3>", self.show_context_menu)
        self.object_id2_entry.bind("<Button-3>", self.show_context_menu)
        self.object_name2_entry.bind("<Button-3>", self.show_context_menu)
        self.object_url_entry.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Вставить", command=self.paste_from_clipboard)
        menu.post(event.x_root, event.y_root)

    def paste_from_clipboard(self, event=None):
        try:
            clipboard_text = self.clipboard_get()
            if self.focus_get() == self.db_entry:
                self.db_path.set(clipboard_text)
            elif self.focus_get() == self.weight_combobox:
                self.weight_format.set(clipboard_text)
            elif self.focus_get() == self.date_combobox:
                self.date_format.set(clipboard_text)
            elif self.focus_get() == self.access_key_entry:
                self.access_key.set(clipboard_text)
            elif self.focus_get() == self.font_family_combobox:
                self.font_family.set(clipboard_text)
            elif self.focus_get() == self.font_size_combobox:
                self.font_size.set(clipboard_text)
            elif self.focus_get() == self.object_id1_entry:
                self.object_id1.set(clipboard_text)
            elif self.focus_get() == self.object_name1_entry:
                self.object_name1.set(clipboard_text)
            elif self.focus_get() == self.object_id2_entry:
                self.object_id2.set(clipboard_text)
            elif self.focus_get() == self.object_name2_entry:
                self.object_name2.set(clipboard_text)
            elif self.focus_get() == self.object_url_entry:
                self.object_url.set(clipboard_text)
        except tk.TclError:
            pass

    def check_reo_connection(self):
        try:
            url = self.object_url.get()
            logger.info("Checking REO connection at URL: %s", url)

            response = requests.get(
                'https://api.reo.ru/reo-weight-control-api/api/v1/weight-controls/import')

            if response.status_code == 200:
                logger.info("REO connection check successful")
                messagebox.showinfo("REO Check", "REO connection check successful")
            elif response.status_code == 403:
                logger.error("Access denied. Invalid access key")
                messagebox.showerror("Error", "Access denied. Invalid access key")
            elif response.status_code == 422:
                logger.error("Error checking REO connection: %s", response.text)
                messagebox.showerror("Error", "Check for errors")
            else:
                logger.error("Unknown error checking REO connection: %s",
                             response.status_code)
                messagebox.showerror("Error", f"Unknown error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error("Error checking REO connection: %s", e)
            messagebox.showerror("Error", f"Error checking REO connection: {e}")

    def show_description(self, text):
        self.description_label.config(text=text)

    def select_db_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Database files", "*.gdb *.db")])
        if file_path:
            self.db_path.set(file_path)

    def check_db_connection(self):
        db_path = self.db_path.get()
        if not db_path:
            messagebox.showwarning("Error", "Please specify database path.")
            return

        try:
            conn = fdb.connect(dsn=db_path, user='SYSDBA', password='masterkey')
            conn.close()
            messagebox.showinfo("Success", "Database connection successful.")
            logger.info("Database connection successful.")
        except Exception as e:
            logger.error("Error checking database connection: %s", e)
            messagebox.showerror("Error", f"Database connection failed: {e}")

    def save_settings(self):
        self.settings = {
            "db_path": self.db_path.get(),
            "weight_format": self.weight_format.get(),
            "date_format": self.date_format.get(),
            "access_key": self.access_key.get(),
            "object_id1": self.object_id1.get(),
            "object_name1": self.object_name1.get(),
            "object_id2": self.object_id2.get(),
            "object_name2": self.object_name2.get(),
            "object_url": self.object_url.get(),
            "font_family": self.font_family.get(),
            "font_size": self.font_size.get()
        }
        save_config(self.settings)
        logger.info("Settings saved.")
        self.destroy()


# Окно списка грузов
class CargoTypesWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Роды груза")
        self.geometry("600x300")
        
        # Позиционируем окно относительно основного
        parent.position_window(self)

        # Таблица для отображения данных
        self.create_table()

        # Кнопки управления
        self.create_buttons()

        # Загрузка данных из базы данных
        self.load_data()

        # Привязка горячих клавиш
        self.bind("<Control-v>", self.paste_from_clipboard)

    def create_table(self):
        self.table_frame = tk.Frame(self)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("Наименование груза", "Отправка в РЭО")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=280)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Привязка контекстного меню
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Вставить", command=self.paste_from_clipboard)
        menu.post(event.x_root, event.y_root)

    def paste_from_clipboard(self, event=None):
        try:
            clipboard_text = self.clipboard_get()
            selected_item = self.tree.selection()
            if selected_item:
                current_values = list(self.tree.item(selected_item)['values'])
                # Определяем текущую колонку
                column = self.tree.identify_column(event.x if event else 0)
                column_index = int(column[1]) - 1
                
                # Если вставляем в колонку "Отправка в РЭО"
                if column_index == 1:
                    # Проверяем, является ли вставляемый текст допустимым значением
                    if clipboard_text.lower() in ["отправлять", "не отправлять"]:
                        current_values[column_index] = clipboard_text
                    else:
                        return  # Игнорируем вставку, если текст не соответствует допустимым значениям
                else:
                    # Для колонки "Наименование груза"
                    current_values[column_index] = clipboard_text
                
                # Сохраняем обновленные значения
                self.tree.item(selected_item, values=tuple(current_values))
        except tk.TclError:
            pass

    def create_buttons(self):
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        self.btn_add = tk.Button(button_frame, text="Добавить", command=self.add_cargo_type)
        self.btn_add.pack(side=tk.LEFT, padx=5)

        self.btn_edit = tk.Button(button_frame, text="Изменить", command=self.edit_cargo_type)
        self.btn_edit.pack(side=tk.LEFT, padx=5)

        self.btn_delete = tk.Button(button_frame, text="Удалить", command=self.delete_cargo_type)
        self.btn_delete.pack(side=tk.LEFT, padx=5)

        self.btn_close = tk.Button(button_frame, text="Закрыть", command=self.destroy)
        self.btn_close.pack(side=tk.LEFT, padx=5)

    def load_data(self):
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT name, reosend FROM list_cargotypes")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert("", tk.END, values=(row[0], "Отправлять" if row[1] else "Не отправлять"))

    def add_cargo_type(self):
        add_window = tk.Toplevel(self)
        add_window.title("Добавить род груза")

        tk.Label(add_window, text="Наименование груза:").grid(row=0, column=0, padx=10, pady=10)
        name_entry = tk.Entry(add_window)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(add_window, text="Отправка в РЭО:").grid(row=1, column=0, padx=10, pady=10)
        reosend_var = tk.IntVar(value=1)
        tk.Radiobutton(add_window, text="Отправлять", variable=reosend_var, value=1).grid(row=1, column=1, padx=10,
                                                                                          pady=5)
        tk.Radiobutton(add_window, text="Не отправлять", variable=reosend_var, value=0).grid(row=2, column=1, padx=10,
                                                                                             pady=5)

        def save():
            name = name_entry.get()
            reosend = reosend_var.get()

            if name:
                conn = sqlite3.connect('app_data.sqlite')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO list_cargotypes (name, reosend) VALUES (?, ?)", (name, reosend))
                conn.commit()
                conn.close()

                self.tree.insert("", tk.END, values=(name, "Отправлять" if reosend else "Не отправлять"))
                add_window.destroy()

        tk.Button(add_window, text="Сохранить", command=save).grid(row=3, column=0, columnspan=2, pady=10)

    def edit_cargo_type(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите запись для редактирования")
            return

        item = self.tree.item(selected_item)
        name, reosend = item['values']
        reosend = 1 if reosend == "Отправлять" else 0

        edit_window = tk.Toplevel(self)
        edit_window.title("Изменить род груза")

        tk.Label(edit_window, text="Наименование груза:").grid(row=0, column=0, padx=10, pady=10)
        name_entry = tk.Entry(edit_window)
        name_entry.insert(0, name)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(edit_window, text="Отправка в РЭО:").grid(row=1, column=0, padx=10, pady=10)
        reosend_var = tk.IntVar(value=reosend)
        tk.Radiobutton(edit_window, text="Отправлять", variable=reosend_var, value=1).grid(row=1, column=1, padx=10,
                                                                                           pady=5)
        tk.Radiobutton(edit_window, text="Не отправлять", variable=reosend_var, value=0).grid(row=2, column=1, padx=10,
                                                                                              pady=5)

        def save():
            new_name = name_entry.get()
            new_reosend = reosend_var.get()

            if new_name:
                conn = sqlite3.connect('app_data.sqlite')
                cursor = conn.cursor()
                cursor.execute("UPDATE list_cargotypes SET name = ?, reosend = ? WHERE name = ?",
                               (new_name, new_reosend, name))
                conn.commit()
                conn.close()

                self.tree.item(selected_item, values=(new_name, "Отправлять" if new_reosend else "Не отправлять"))
                edit_window.destroy()

        tk.Button(edit_window, text="Сохранить", command=save).grid(row=3, column=0, columnspan=2, pady=10)

    def delete_cargo_type(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return

        item = self.tree.item(selected_item)
        name = item['values'][0]

        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM list_cargotypes WHERE name = ?", (name,))
        conn.commit()
        conn.close()

        self.tree.delete(selected_item)


# Окно списка отправителей
class CompaniesWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Компании отправители")
        self.geometry("800x300")
        
        # Позиционируем окно относительно основного
        parent.position_window(self)

        # Таблица для отображения данных
        self.create_table()

        # Кнопки управления
        self.create_buttons()

        # Загрузка данных из базы данных
        self.load_data()

        # Привязка горячих клавиш
        self.bind("<Control-v>", self.paste_from_clipboard)

    def create_table(self):
        self.table_frame = tk.Frame(self)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("Наименование отправителя", "ИНН", "КПП", "РЭО")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Привязка контекстного меню
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Вставить", command=self.paste_from_clipboard)
        menu.post(event.x_root, event.y_root)

    def paste_from_clipboard(self, event=None):
        try:
            clipboard_text = self.clipboard_get()
            selected_item = self.tree.selection()
            if selected_item:
                current_values = list(self.tree.item(selected_item)['values'])
                # Определяем текущую колонку
                column = self.tree.identify_column(event.x if event else 0)
                column_index = int(column[1]) - 1
                # Обновляем значение в нужной колонке
                current_values[column_index] = clipboard_text
                # Сохраняем остальные значения
                self.tree.item(selected_item, values=tuple(current_values))
        except tk.TclError:
            pass

    def create_buttons(self):
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        self.btn_add = tk.Button(button_frame, text="Добавить", command=self.add_company)
        self.btn_add.pack(side=tk.LEFT, padx=5)

        self.btn_edit = tk.Button(button_frame, text="Изменить", command=self.edit_company)
        self.btn_edit.pack(side=tk.LEFT, padx=5)

        self.btn_delete = tk.Button(button_frame, text="Удалить", command=self.delete_company)
        self.btn_delete.pack(side=tk.LEFT, padx=5)

        self.btn_close = tk.Button(button_frame, text="Закрыть", command=self.destroy)
        self.btn_close.pack(side=tk.LEFT, padx=5)

    def load_data(self):
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT name, inn, kpp, reosend FROM list_companies")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert("", tk.END, values=(row[0], row[1], row[2], "Отправлять" if row[3] else "Не отправлять"))

    def add_company(self):
        add_window = tk.Toplevel(self)
        add_window.title("Добавить компанию")

        tk.Label(add_window, text="Наименование отправителя:").grid(row=0, column=0, padx=10, pady=10)
        name_entry = tk.Entry(add_window)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(add_window, text="ИНН:").grid(row=1, column=0, padx=10, pady=10)
        inn_entry = tk.Entry(add_window)
        inn_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(add_window, text="КПП:").grid(row=2, column=0, padx=10, pady=10)
        kpp_entry = tk.Entry(add_window)
        kpp_entry.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(add_window, text="РЭО:").grid(row=3, column=0, padx=10, pady=10)
        reosend_var = tk.IntVar(value=1)
        tk.Radiobutton(add_window, text="Отправлять", variable=reosend_var, value=1).grid(row=3, column=1, padx=10,
                                                                                          pady=5)
        tk.Radiobutton(add_window, text="Не отправлять", variable=reosend_var, value=0).grid(row=4, column=1, padx=10,
                                                                                             pady=5)

        def save():
            name = name_entry.get()
            inn = inn_entry.get()
            kpp = kpp_entry.get()
            reosend = reosend_var.get()

            if name and inn and kpp:
                conn = sqlite3.connect('app_data.sqlite')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO list_companies (name, inn, kpp, reosend) VALUES (?, ?, ?, ?)",
                               (name, inn, kpp, reosend))
                conn.commit()
                conn.close()

                self.tree.insert("", tk.END, values=(name, inn, kpp, "Отправлять" if reosend else "Не отправлять"))
                add_window.destroy()

        tk.Button(add_window, text="Сохранить", command=save).grid(row=5, column=0, columnspan=2, pady=10)

    def edit_company(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите запись для редактирования")
            return

        item = self.tree.item(selected_item)
        name, inn, kpp, reosend = item['values']
        reosend = 1 if reosend == "Отправлять" else 0

        edit_window = tk.Toplevel(self)
        edit_window.title("Изменить компанию")

        tk.Label(edit_window, text="Наименование отправителя:").grid(row=0, column=0, padx=10, pady=10)
        name_entry = tk.Entry(edit_window)
        name_entry.insert(0, name)
        name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(edit_window, text="ИНН:").grid(row=1, column=0, padx=10, pady=10)
        inn_entry = tk.Entry(edit_window)
        inn_entry.insert(0, inn)
        inn_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(edit_window, text="КПП:").grid(row=2, column=0, padx=10, pady=10)
        kpp_entry = tk.Entry(edit_window)
        kpp_entry.insert(0, kpp)
        kpp_entry.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(edit_window, text="РЭО:").grid(row=3, column=0, padx=10, pady=10)
        reosend_var = tk.IntVar(value=reosend)
        tk.Radiobutton(edit_window, text="Отправлять", variable=reosend_var, value=1).grid(row=3, column=1, padx=10,
                                                                                           pady=5)
        tk.Radiobutton(edit_window, text="Не отправлять", variable=reosend_var, value=0).grid(row=4, column=1, padx=10,
                                                                                              pady=5)

        def save():
            new_name = name_entry.get()
            new_inn = inn_entry.get()
            new_kpp = kpp_entry.get()
            new_reosend = reosend_var.get()

            if new_name and new_inn and new_kpp:
                conn = sqlite3.connect('app_data.sqlite')
                cursor = conn.cursor()
                cursor.execute("UPDATE list_companies SET name = ?, inn = ?, kpp = ?, reosend = ? WHERE name = ?",
                               (new_name, new_inn, new_kpp, new_reosend, name))
                conn.commit()
                conn.close()

                self.tree.item(selected_item,
                               values=(new_name, new_inn, new_kpp, "Отправлять" if new_reosend else "Не отправлять"))
                edit_window.destroy()

        tk.Button(edit_window, text="Сохранить", command=save).grid(row=5, column=0, columnspan=2, pady=10)

    def delete_company(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return

        item = self.tree.item(selected_item)
        name = item['values'][0]

        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM list_companies WHERE name = ?", (name,))
        conn.commit()
        conn.close()

        self.tree.delete(selected_item)


# Окно списка транспорта
class AutoWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Транспорт")
        self.geometry("800x300")
        
        # Позиционируем окно относительно основного
        parent.position_window(self)

        # Таблица для отображения данных
        self.create_table()

        # Кнопки управления
        self.create_buttons()

        # Загрузка данных из базы данных
        self.load_data()

        # Привязка горячих клавиш
        self.bind("<Control-v>", self.paste_from_clipboard)

    def create_table(self):
        self.table_frame = tk.Frame(self)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("Номер авто", "Марка авто", "Масса без нагрузки, кг", "Максимальная масса, кг")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Привязка контекстного меню
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Вставить", command=self.paste_from_clipboard)
        menu.post(event.x_root, event.y_root)

    def paste_from_clipboard(self, event=None):
        try:
            clipboard_text = self.clipboard_get()
            selected_item = self.tree.selection()
            if selected_item:
                current_values = list(self.tree.item(selected_item)['values'])
                # Определяем текущую колонку
                column = self.tree.identify_column(event.x if event else 0)
                column_index = int(column[1]) - 1
                # Обновляем значение в нужной колонке
                current_values[column_index] = clipboard_text
                # Сохраняем остальные значения
                self.tree.item(selected_item, values=tuple(current_values))
        except tk.TclError:
            pass

    def create_buttons(self):
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        self.btn_add = tk.Button(button_frame, text="Добавить", command=self.add_auto)
        self.btn_add.pack(side=tk.LEFT, padx=5)

        self.btn_edit = tk.Button(button_frame, text="Изменить", command=self.edit_auto)
        self.btn_edit.pack(side=tk.LEFT, padx=5)

        self.btn_delete = tk.Button(button_frame, text="Удалить", command=self.delete_auto)
        self.btn_delete.pack(side=tk.LEFT, padx=5)

        self.btn_close = tk.Button(button_frame, text="Закрыть", command=self.destroy)
        self.btn_close.pack(side=tk.LEFT, padx=5)

    def load_data(self):
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT nomer_ts2, marka_ts2, min_weight, max_weight FROM list_auto")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert("", tk.END, values=(row[0], row[1], row[2], row[3]))

    def add_auto(self):
        add_window = tk.Toplevel(self)
        add_window.title("Добавить транспорт")

        tk.Label(add_window, text="Номер авто:").grid(row=0, column=0, padx=10, pady=10)
        nomer_entry = tk.Entry(add_window)
        nomer_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(add_window, text="Марка авто:").grid(row=1, column=0, padx=10, pady=10)
        marka_entry = tk.Entry(add_window)
        marka_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(add_window, text="Масса без нагрузки, кг:").grid(row=2, column=0, padx=10, pady=10)
        min_weight_entry = tk.Entry(add_window)
        min_weight_entry.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(add_window, text="Максимальная масса, кг:").grid(row=3, column=0, padx=10, pady=10)
        max_weight_entry = tk.Entry(add_window)
        max_weight_entry.grid(row=3, column=1, padx=10, pady=10)

        def save():
            nomer = nomer_entry.get()
            marka = marka_entry.get()
            min_weight = min_weight_entry.get()
            max_weight = max_weight_entry.get()

            if nomer and marka:
                conn = sqlite3.connect('app_data.sqlite')
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO list_auto (nomer_ts2, marka_ts2, min_weight, max_weight) VALUES (?, ?, ?, ?)",
                    (nomer, marka, min_weight, max_weight))
                conn.commit()
                conn.close()

                self.tree.insert("", tk.END, values=(nomer, marka, min_weight, max_weight))
                add_window.destroy()

        tk.Button(add_window, text="Сохранить", command=save).grid(row=4, column=0, columnspan=2, pady=10)

    def edit_auto(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите запись для редактирования")
            return

        item = self.tree.item(selected_item)
        nomer, marka, min_weight, max_weight = item['values']

        edit_window = tk.Toplevel(self)
        edit_window.title("Изменить транспорт")

        tk.Label(edit_window, text="Номер авто:").grid(row=0, column=0, padx=10, pady=10)
        nomer_entry = tk.Entry(edit_window)
        nomer_entry.insert(0, nomer)
        nomer_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(edit_window, text="Марка авто:").grid(row=1, column=0, padx=10, pady=10)
        marka_entry = tk.Entry(edit_window)
        marka_entry.insert(0, marka)
        marka_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(edit_window, text="Масса без нагрузки, кг:").grid(row=2, column=0, padx=10, pady=10)
        min_weight_entry = tk.Entry(edit_window)
        min_weight_entry.insert(0, min_weight)
        min_weight_entry.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(edit_window, text="Максимальная масса, кг:").grid(row=3, column=0, padx=10, pady=10)
        max_weight_entry = tk.Entry(edit_window)
        max_weight_entry.insert(0, max_weight)
        max_weight_entry.grid(row=3, column=1, padx=10, pady=10)

        def save():
            new_nomer = nomer_entry.get()
            new_marka = marka_entry.get()
            new_min_weight = min_weight_entry.get()
            new_max_weight = max_weight_entry.get()

            if new_nomer and new_marka:
                conn = sqlite3.connect('app_data.sqlite')
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE list_auto SET nomer_ts2 = ?, marka_ts2 = ?, min_weight = ?, max_weight = ? WHERE nomer_ts2 = ?",
                    (new_nomer, new_marka, new_min_weight, new_max_weight, nomer))
                conn.commit()
                conn.close()

                self.tree.item(selected_item, values=(new_nomer, new_marka, new_min_weight, new_max_weight))
                edit_window.destroy()

        tk.Button(edit_window, text="Сохранить", command=save).grid(row=4, column=0, columnspan=2, pady=10)

    def delete_auto(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return

        item = self.tree.item(selected_item)
        nomer = item['values'][0]

        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM list_auto WHERE nomer_ts2 = ?", (nomer,))
        conn.commit()
        conn.close()

        self.tree.delete(selected_item)


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        logger.error("Critical error during program execution: %s", e)
    finally:
        logger.info("Program termination") 