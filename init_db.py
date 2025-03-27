import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def init_database():
    try:
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
                nomer_ts TEXT NOT NULL,
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

        # Проверяем, есть ли данные в таблице list_auto
        cursor.execute("SELECT COUNT(*) FROM list_auto")
        count = cursor.fetchone()[0]

        # Если таблица пуста, добавляем стандартные данные
        if count == 0:
            default_transport = [
                ("У707СА56", "Мусоровоз", 12550, 22400),
                ("Т945УН56", "Камаз", 9780, 15630),
                ("М709ВВ116", "Камаз", 12550, 22400)
            ]
            cursor.executemany("""
                INSERT INTO list_auto (nomer_ts2, marka_ts2, min_weight, max_weight)
                VALUES (?, ?, ?, ?)
            """, default_transport)
            logger.info("Added default transport data to list_auto table")

        # Проверяем, есть ли данные в таблице list_cargotypes
        cursor.execute("SELECT COUNT(*) FROM list_cargotypes")
        count = cursor.fetchone()[0]

        # Если таблица пуста, добавляем стандартные данные
        if count == 0:
            default_cargotypes = [
                ("ТКО", 1),
                ("КГО", 1),
                ("Строительный мусор", 0),
                ("Промышленные отходы", 0),
                ("Опасные отходы", 0)
            ]
            cursor.executemany("""
                INSERT INTO list_cargotypes (name, reosend)
                VALUES (?, ?)
            """, default_cargotypes)
            logger.info("Added default cargo types to list_cargotypes table")

        # Проверяем, есть ли данные в таблице list_companies
        cursor.execute("SELECT COUNT(*) FROM list_companies")
        count = cursor.fetchone()[0]

        # Если таблица пуста, добавляем стандартные данные
        if count == 0:
            default_companies = [
                ('ООО "Саночистка"', "5603013425", "560301001", 1),
                ('ООО "Природа"', "612167252", "561101001", 1),
                ('ООО "ЭКОСЕРВИС"', "5638059967", "563801001", 1)
            ]
            cursor.executemany("""
                INSERT INTO list_companies (name, inn, kpp, reosend)
                VALUES (?, ?, ?, ?)
            """, default_companies)
            logger.info("Added default companies to list_companies table")

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

if __name__ == '__main__':
    init_database() 