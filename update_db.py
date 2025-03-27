import sqlite3

def update_database():
    conn = sqlite3.connect('app_data.sqlite')
    cursor = conn.cursor()

    # Создаем временную таблицу с новой структурой
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auto_uid_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            moduletype INTEGER NOT NULL,
            datetimebrutto TEXT NOT NULL,
            nomer_ts TEXT NOT NULL,
            uid TEXT NOT NULL
        )
    ''')

    # Копируем данные из старой таблицы в новую
    cursor.execute('''
        INSERT INTO auto_uid_new (moduletype, datetimebrutto, uid)
        SELECT moduletype, datetimebrutto, uid FROM auto_uid
    ''')

    # Удаляем старую таблицу
    cursor.execute('DROP TABLE IF EXISTS auto_uid')

    # Переименовываем новую таблицу
    cursor.execute('ALTER TABLE auto_uid_new RENAME TO auto_uid')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_database() 