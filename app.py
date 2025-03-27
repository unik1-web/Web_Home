from flask import Flask, render_template, jsonify, request
import sqlite3
import json
import logging
from datetime import datetime, timedelta
import fdb
import os
import requests
import uuid
import itertools
from tkcalendar import Calendar
from init_db import init_database

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

app = Flask(__name__)

# Проверяем и создаем базу данных при запуске
if not os.path.exists('app_data.sqlite'):
    logger.info("Database not found. Initializing...")
    if init_database():
        logger.info("Database initialized successfully")
    else:
        logger.error("Failed to initialize database")
        raise Exception("Failed to initialize database")

def load_config():
    if os.path.exists("app_conf.json"):
        with open("app_conf.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def fetch_data(date_brutto, db_path):
    try:
        conn = fdb.connect(dsn=db_path, user='SYSDBA', password='masterkey')
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
        return []

@app.route('/')
def index():
    config = load_config()
    current_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Get data from database
    db_path = config.get("db_path", r'C:\VESYEVENT.GDB')
    rows = fetch_data(current_date, db_path)
    
    # Connect to SQLite database
    conn = sqlite3.connect('app_data.sqlite')
    cursor = conn.cursor()
    
    # Get companies data for INN and KPP lookup
    cursor.execute("SELECT name, inn, kpp FROM list_companies")
    companies = {row[0]: {'inn': row[1], 'kpp': row[2]} for row in cursor.fetchall()}
    
    # Get sending status data - check both objects
    cursor.execute("""
        WITH combined_data AS (
            SELECT nomer_ts, datetimebrutto, datetimetara, 100 as moduletype FROM auto_go
            UNION ALL
            SELECT nomer_ts, datetimebrutto, datetimetara, 200 as moduletype FROM new_auto_go
        )
        SELECT 
            c.nomer_ts, 
            c.datetimebrutto, 
            c.datetimetara,
            r.reostatus, 
            r.reodatetime,
            c.moduletype
        FROM combined_data c
        LEFT JOIN auto_uid u ON c.datetimebrutto = u.datetimebrutto 
            AND c.nomer_ts = u.nomer_ts 
            AND c.moduletype = u.moduletype
        LEFT JOIN reo_data r ON u.uid = r.uid
    """)
    status_data = {}
    for row in cursor.fetchall():
        if not row[0]:  # Skip if nomer_ts is None
            continue
            
        key = (row[0], row[1], row[2])  # nomer_ts, datetimebrutto, datetimetara
        if key not in status_data:
            status_data[key] = {'status1': '', 'status2': '', 'date': ''}
        
        if row[5] == 100:  # Object 1
            status_data[key]['status1'] = 'Отправлено' if row[3] == 2 else 'Ошибка'
        elif row[5] == 200:  # Object 2
            status_data[key]['status2'] = 'Отправлено' if row[3] == 2 else 'Ошибка'
            
        if row[4] and (not status_data[key]['date'] or row[4] > status_data[key]['date']):
            status_data[key]['date'] = row[4]
    
    conn.close()
    
    # Format data for display
    formatted_rows = []
    for row in rows:
        # Format dates
        datetime_brutto = row[0].strftime(config.get("date_format", "%Y-%m-%d %H:%M:%S"))
        datetime_tara = row[1].strftime(config.get("date_format", "%Y-%m-%d %H:%M:%S"))
        
        # Format weights
        weight_format = config.get("weight_format", "#.##").count('#') - 1
        brutto = f"{float(row[5]):.{weight_format}f}"
        tara = f"{float(row[6]):.{weight_format}f}"
        netto = f"{float(row[7]):.{weight_format}f}"
        
        # Get company data
        company_data = companies.get(row[4], {})
        inn = company_data.get('inn', '')
        kpp = company_data.get('kpp', '')
        
        # Get sending status
        status_key = (row[2], datetime_brutto, datetime_tara)
        status = status_data.get(status_key, {'status1': 'Готово к отправке', 'status2': 'Готово к отправке', 'date': ''})
        
        # Create formatted row
        formatted_row = [
            datetime_brutto,
            datetime_tara,
            row[2],  # nomer_ts
            row[3],  # marka_ts
            row[4],  # firma_pol
            brutto,
            tara,
            netto,
            row[8],  # gruz_name
            inn,
            kpp,
            status['status1'],
            status['status2'],
            status['date']
        ]
        formatted_rows.append(formatted_row)
    
    # Calculate date range for calendar
    current_date_obj = datetime.strptime(current_date, '%Y-%m-%d')
    prev_date = (current_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
    next_date = (current_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
    
    return render_template('index.html', 
                         data=formatted_rows, 
                         current_date=current_date,
                         prev_date=prev_date,
                         next_date=next_date)

@app.route('/settings')
def settings():
    config = load_config()
    return render_template('settings.html', config=config)

@app.route('/cargo_types')
def cargo_types():
    conn = sqlite3.connect('app_data.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT name, reosend FROM list_cargotypes")
    rows = cursor.fetchall()
    conn.close()
    return render_template('cargo_types.html', rows=rows)

@app.route('/companies')
def companies():
    conn = sqlite3.connect('app_data.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT name, inn, kpp, reosend FROM list_companies")
    rows = cursor.fetchall()
    conn.close()
    return render_template('companies.html', rows=rows)

@app.route('/auto')
def auto():
    conn = sqlite3.connect('app_data.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT nomer_ts2, marka_ts2, min_weight, max_weight FROM list_auto")
    rows = cursor.fetchall()
    conn.close()
    return render_template('auto.html', rows=rows)

@app.route('/save_settings', methods=['POST'])
def save_settings():
    try:
        new_config = {
            'db_path': request.form.get('db_path'),
            'weight_format': request.form.get('weight_format'),
            'date_format': request.form.get('date_format'),
            'access_key': request.form.get('access_key'),
            'object_name1': request.form.get('object_name1'),
            'object_id1': request.form.get('object_id1'),
            'object_name2': request.form.get('object_name2'),
            'object_id2': request.form.get('object_id2'),
            'object_url': request.form.get('object_url'),
            'font_family': request.form.get('font_family'),
            'font_size': request.form.get('font_size')
        }
        
        # Remove None values
        new_config = {k: v for k, v in new_config.items() if v is not None}
        
        # Load existing config to preserve any values not in the form
        existing_config = load_config()
        existing_config.update(new_config)
        
        with open('app_conf.json', 'w', encoding='utf-8') as f:
            json.dump(existing_config, f, ensure_ascii=False, indent=4)
            
        logger.info("Settings saved successfully")
        return jsonify({'status': 'success', 'message': 'Settings saved successfully'})
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def send_to_reo_service(json_data, url):
    try:
        headers = {
            'Content-Type': 'application/json',
            'AccessKey': json_data.get('AccessKey', '')
        }
        response = requests.post(url, json=json_data, headers=headers)
        response.raise_for_status()
        logger.info(f"Data successfully sent to REO service for object {json_data.get('ObjectId', 'unknown')}")
        return True, None
    except requests.exceptions.RequestException as e:
        error_msg = f"Error sending data to REO service: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

@app.route('/send_to_reo', methods=['POST'])
def send_to_reo():
    try:
        data = request.get_json()
        if not data:
            logger.error("No data received in send_to_reo request")
            return jsonify({'success': False, 'error': 'Нет данных для отправки'})

        # Загрузка данных из таблицы list_auto
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT nomer_ts2, marka_ts2, min_weight, max_weight FROM list_auto")
        transport_data = cursor.fetchall()
        conn.close()

        if not transport_data:
            logger.error("No transport data found in list_auto table")
            return jsonify({'success': False, 'error': 'Не найдены данные о транспорте'})

        # Создание словаря для быстрого поиска данных по номеру авто
        transport_dict = {nomer: (marka, min_weight, max_weight) for nomer, marka, min_weight, max_weight in transport_data}
        numbers = list(transport_dict.keys())
        number_iterator = itertools.cycle(numbers)

        # Получаем настройки из конфига
        config = load_config()
        object_id = config.get('object_id1', '')
        access_key = config.get('access_key', '')
        service_url = config.get('object_url', '')

        if not all([object_id, access_key, service_url]):
            logger.error("Missing required configuration parameters")
            return jsonify({'success': False, 'error': 'Отсутствуют обязательные параметры конфигурации'})

        # Формирование JSON для отправки в РЭО
        json_data = {
            "ObjectId": object_id,
            "AccessKey": access_key,
            "WeightControls": []
        }

        for record in data:
            try:
                # Генерация уникального uid для машины
                uid = str(uuid.uuid4())

                # Преобразуем строку даты обратно в объект datetime
                date_before = datetime.strptime(record["datetimebrutto"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S+05:00")
                date_after = datetime.strptime(record["datetimetara"], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S+05:00")
                
                weight_control = {
                    "id": uid,
                    "dateBefore": date_before,
                    "dateAfter": date_after,
                    "registrationNumber": record["nomer_ts"],
                    "garbageTruckType": None,
                    "garbageTruckBrand": record["marka_ts"],
                    "garbageTruckModel": None,
                    "companyName": record["firma_pol"],
                    "companyInn": record["inn"],
                    "companyKpp": record["kpp"],
                    "weightBefore": str(record["brutto"]),
                    "weightAfter": str(record["tara"]),
                    "weightDriver": None,
                    "coefficient": "1",
                    "garbageWeight": str(record["netto"]),
                    "garbageType": record["gruz_name"],
                    "codeFKKO": None,
                    "nameFKKO": None
                }
                json_data["WeightControls"].append(weight_control)
            except Exception as e:
                logger.error(f"Error processing record: {str(e)}")
                continue

        if not json_data["WeightControls"]:
            logger.error("No valid records to send")
            return jsonify({'success': False, 'error': 'Нет валидных записей для отправки'})

        # Сохраняем данные в temp.json с правильной кодировкой
        try:
            with open("temp.json", "w", encoding="utf-8") as temp_file:
                json.dump(json_data, temp_file, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Error saving temp.json: {str(e)}")
            return jsonify({'success': False, 'error': f'Ошибка при сохранении временного файла: {str(e)}'})

        # Отправляем данные в РЭО
        success, error = send_to_reo_service(json_data, service_url)
        if not success:
            return jsonify({'success': False, 'error': error})

        # После успешной отправки, обновляем базу данных
        try:
            conn = sqlite3.connect('app_data.sqlite')
            cursor = conn.cursor()

            for weight_control in json_data["WeightControls"]:
                # Вставка данных в таблицу auto_uid
                cursor.execute("""
                    INSERT INTO auto_uid (moduletype, datetimebrutto, nomer_ts, uid)
                    VALUES (?, ?, ?, ?)
                """, (
                    100,
                    datetime.strptime(weight_control["dateBefore"], "%Y-%m-%d %H:%M:%S+05:00").strftime("%Y-%m-%d %H:%M:%S"),
                    weight_control["registrationNumber"],
                    weight_control["id"]))

                # Вставка данных в таблицу reo_data
                cursor.execute("""
                    INSERT INTO reo_data (uid, reostatus, reodatetime)
                    VALUES (?, ?, ?)
                """, (
                    weight_control["id"], 2,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

                # Вставка данных в таблицу auto_go
                cursor.execute("""
                    INSERT INTO auto_go (datetimebrutto, datetimetara, nomer_ts, marka_ts, firma_pol, 
                    brutto, tara, netto, gruz_name, inn, kpp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)                    
                """, (
                    datetime.strptime(weight_control["dateBefore"], "%Y-%m-%d %H:%M:%S+05:00").strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.strptime(weight_control["dateAfter"], "%Y-%m-%d %H:%M:%S+05:00").strftime("%Y-%m-%d %H:%M:%S"),
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

            # Создание и отправка данных для второго объекта
            logger.info("Creating data for object 2...")
            new_json_data = create_additional_json(json_data)
            
            if not new_json_data:
                logger.error("Failed to create data for object 2")
                return jsonify({'success': False, 'error': 'Не удалось создать данные для объекта 2'})
                
            logger.info(f"Created {len(new_json_data['WeightControls'])} records for object 2")
            
            # Сохраняем данные для объекта 2 в отдельный файл для отладки
            try:
                with open("temp_additional.json", "w", encoding="utf-8") as temp_file:
                    json.dump(new_json_data, temp_file, ensure_ascii=False, indent=4)
                logger.info("Saved object 2 data to temp_additional.json")
            except Exception as e:
                logger.error(f"Error saving temp_additional.json: {str(e)}")
                return jsonify({'success': False, 'error': f'Ошибка при сохранении данных объекта 2: {str(e)}'})

            # Отправляем данные для объекта 2
            logger.info("Sending data for object 2...")
            success, error = send_to_reo_service(new_json_data, service_url)
            
            if not success:
                logger.error(f"Failed to send data for object 2: {error}")
                return jsonify({'success': False, 'error': f'Ошибка при отправке данных для объекта 2: {error}'})
                
            logger.info("Successfully sent data for object 2")
            
            # Обновляем базу данных для объекта 2
            try:
                for weight_control in new_json_data["WeightControls"]:
                    # Вставка данных в таблицу auto_uid для объекта 2
                    cursor.execute("""
                        INSERT INTO auto_uid (moduletype, datetimebrutto, nomer_ts, uid)
                        VALUES (?, ?, ?, ?)
                    """, (
                        200,
                        datetime.strptime(weight_control["dateBefore"], "%Y-%m-%d %H:%M:%S+05:00").strftime("%Y-%m-%d %H:%M:%S"),
                        weight_control["registrationNumber"],
                        weight_control["id"]))
                    logger.info(f"Inserted auto_uid record for object 2: {weight_control['id']}")

                    # Вставка данных в таблицу reo_data для объекта 2
                    cursor.execute("""
                        INSERT INTO reo_data (uid, reostatus, reodatetime)
                        VALUES (?, ?, ?)
                    """, (
                        weight_control["id"], 2,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    logger.info(f"Inserted reo_data record for object 2: {weight_control['id']}")

                    # Вставка данных в таблицу new_auto_go
                    cursor.execute("""
                        INSERT INTO new_auto_go (datetimebrutto, datetimetara, nomer_ts, marka_ts, firma_pol, 
                        brutto, tara, netto, gruz_name, inn, kpp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)                    
                    """, (
                        datetime.strptime(weight_control["dateBefore"], "%Y-%m-%d %H:%M:%S+05:00").strftime("%Y-%m-%d %H:%M:%S"),
                        datetime.strptime(weight_control["dateAfter"], "%Y-%m-%d %H:%M:%S+05:00").strftime("%Y-%m-%d %H:%M:%S"),
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
                    logger.info(f"Inserted new_auto_go record for object 2: {weight_control['registrationNumber']}")
            except Exception as e:
                logger.error(f"Error updating database for object 2: {str(e)}")
                return jsonify({'success': False, 'error': f'Ошибка при обновлении базы данных для объекта 2: {str(e)}'})

            conn.commit()
            conn.close()
            logger.info("All data successfully sent and saved to database")
            return jsonify({'success': True, 'message': 'Данные успешно отправлены'})
        except Exception as e:
            logger.error(f"Error updating database: {str(e)}")
            return jsonify({'success': False, 'error': f'Ошибка при обновлении базы данных: {str(e)}'})

    except Exception as e:
        logger.error(f"Unexpected error in send_to_reo: {str(e)}")
        return jsonify({'success': False, 'error': f'Неожиданная ошибка: {str(e)}'})

def create_additional_json(temp_data):
    try:
        if not temp_data or "WeightControls" not in temp_data or not temp_data["WeightControls"]:
            logger.error("No data in temp_data for creating additional JSON")
            return None

        # Загрузка данных из таблицы list_auto
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT nomer_ts2, marka_ts2, min_weight, max_weight FROM list_auto")
        transport_data = cursor.fetchall()
        conn.close()

        if not transport_data:
            logger.error("No transport data found in list_auto table")
            return None

        # Создание словаря для быстрого поиска данных по номеру авто
        transport_dict = {nomer: (marka, min_weight, max_weight) for nomer, marka, min_weight, max_weight in transport_data}
        numbers = list(transport_dict.keys())
        number_iterator = itertools.cycle(numbers)

        # Получаем настройки из конфига
        config = load_config()
        object_id2 = config.get('object_id2', '')
        access_key = config.get('access_key', '')

        if not object_id2 or not access_key:
            logger.error("Missing required configuration parameters for object 2")
            return None

        # Создание нового JSON-файла
        new_json_data = {
            "ObjectId": object_id2,
            "AccessKey": access_key,
            "WeightControls": []
        }

        for weight_control in temp_data["WeightControls"]:
            try:
                # Получаем данные из temp.json
                date_before = datetime.strptime(weight_control["dateBefore"], "%Y-%m-%d %H:%M:%S+05:00")
                date_after = datetime.strptime(weight_control["dateAfter"], "%Y-%m-%d %H:%M:%S+05:00")
                garbage_weight = float(weight_control["garbageWeight"])

                # Сдвигаем даты на 1 час
                date_before2 = (date_before + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S+05:00")
                date_after2 = (date_after + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S+05:00")

                # Получаем данные из списка "Транспорт"
                while True:
                    registration_number2 = next(number_iterator)
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
                    "id": str(uuid.uuid4()),
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
                logger.info(f"Created new weight control for object 2: {registration_number2}")
            except Exception as e:
                logger.error(f"Error processing record in create_additional_json: {str(e)}")
                continue

        if not new_json_data["WeightControls"]:
            logger.error("No valid records created for object 2")
            return None

        logger.info(f"Successfully created {len(new_json_data['WeightControls'])} records for object 2")
        return new_json_data
    except Exception as e:
        logger.error(f"Error in create_additional_json: {str(e)}")
        return None

# Cargo Types Management
@app.route('/cargo_types/add', methods=['POST'])
def add_cargo_type():
    try:
        data = request.get_json()
        name = data.get('name')
        reosend = data.get('reosend', 0)
        
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO list_cargotypes (name, reosend) VALUES (?, ?)", (name, reosend))
        conn.commit()
        conn.close()
        
        logger.info(f"Added new cargo type: {name}")
        return jsonify({'status': 'success', 'message': 'Cargo type added successfully'})
    except Exception as e:
        logger.error(f"Error adding cargo type: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/cargo_types/edit', methods=['POST'])
def edit_cargo_type():
    try:
        data = request.get_json()
        old_name = data.get('old_name')
        new_name = data.get('new_name')
        reosend = data.get('reosend', 0)
        
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("UPDATE list_cargotypes SET name = ?, reosend = ? WHERE name = ?", 
                      (new_name, reosend, old_name))
        conn.commit()
        conn.close()
        
        logger.info(f"Updated cargo type: {old_name} -> {new_name}")
        return jsonify({'status': 'success', 'message': 'Cargo type updated successfully'})
    except Exception as e:
        logger.error(f"Error updating cargo type: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/cargo_types/delete', methods=['POST'])
def delete_cargo_type():
    try:
        data = request.get_json()
        name = data.get('name')
        
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM list_cargotypes WHERE name = ?", (name,))
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted cargo type: {name}")
        return jsonify({'status': 'success', 'message': 'Cargo type deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting cargo type: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Companies Management
@app.route('/companies/add', methods=['POST'])
def add_company():
    try:
        data = request.get_json()
        name = data.get('name')
        inn = data.get('inn')
        kpp = data.get('kpp')
        reosend = data.get('reosend', 0)
        
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO list_companies (name, inn, kpp, reosend) VALUES (?, ?, ?, ?)", 
                      (name, inn, kpp, reosend))
        conn.commit()
        conn.close()
        
        logger.info(f"Added new company: {name}")
        return jsonify({'status': 'success', 'message': 'Company added successfully'})
    except Exception as e:
        logger.error(f"Error adding company: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/companies/edit', methods=['POST'])
def edit_company():
    try:
        data = request.get_json()
        old_name = data.get('old_name')
        new_name = data.get('new_name')
        inn = data.get('inn')
        kpp = data.get('kpp')
        reosend = data.get('reosend', 0)
        
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("UPDATE list_companies SET name = ?, inn = ?, kpp = ?, reosend = ? WHERE name = ?", 
                      (new_name, inn, kpp, reosend, old_name))
        conn.commit()
        conn.close()
        
        logger.info(f"Updated company: {old_name} -> {new_name}")
        return jsonify({'status': 'success', 'message': 'Company updated successfully'})
    except Exception as e:
        logger.error(f"Error updating company: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/companies/delete', methods=['POST'])
def delete_company():
    try:
        data = request.get_json()
        name = data.get('name')
        
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM list_companies WHERE name = ?", (name,))
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted company: {name}")
        return jsonify({'status': 'success', 'message': 'Company deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting company: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Auto Management
@app.route('/auto/add', methods=['POST'])
def add_auto():
    try:
        data = request.get_json()
        nomer_ts2 = data.get('nomer_ts2')
        marka_ts2 = data.get('marka_ts2')
        min_weight = data.get('min_weight')
        max_weight = data.get('max_weight')
        
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO list_auto (nomer_ts2, marka_ts2, min_weight, max_weight) VALUES (?, ?, ?, ?)", 
                      (nomer_ts2, marka_ts2, min_weight, max_weight))
        conn.commit()
        conn.close()
        
        logger.info(f"Added new auto: {nomer_ts2}")
        return jsonify({'status': 'success', 'message': 'Auto added successfully'})
    except Exception as e:
        logger.error(f"Error adding auto: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/auto/edit', methods=['POST'])
def edit_auto():
    try:
        data = request.get_json()
        old_nomer = data.get('old_nomer')
        nomer_ts2 = data.get('nomer_ts2')
        marka_ts2 = data.get('marka_ts2')
        min_weight = data.get('min_weight')
        max_weight = data.get('max_weight')
        
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("UPDATE list_auto SET nomer_ts2 = ?, marka_ts2 = ?, min_weight = ?, max_weight = ? WHERE nomer_ts2 = ?", 
                      (nomer_ts2, marka_ts2, min_weight, max_weight, old_nomer))
        conn.commit()
        conn.close()
        
        logger.info(f"Updated auto: {old_nomer} -> {nomer_ts2}")
        return jsonify({'status': 'success', 'message': 'Auto updated successfully'})
    except Exception as e:
        logger.error(f"Error updating auto: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/auto/delete', methods=['POST'])
def delete_auto():
    try:
        data = request.get_json()
        nomer_ts2 = data.get('nomer_ts2')
        
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM list_auto WHERE nomer_ts2 = ?", (nomer_ts2,))
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted auto: {nomer_ts2}")
        return jsonify({'status': 'success', 'message': 'Auto deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting auto: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/check_db_connection', methods=['POST'])
def check_db_connection():
    try:
        data = request.get_json()
        db_path = data.get('db_path')
        
        if not db_path:
            return jsonify({'status': 'error', 'message': 'Путь к базе данных не указан'})
            
        conn = fdb.connect(dsn=db_path, user='SYSDBA', password='masterkey')
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Подключение к базе данных успешно'})
    except Exception as e:
        logger.error(f"Error checking database connection: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/check_reo_connection', methods=['POST'])
def check_reo_connection():
    try:
        data = request.get_json()
        access_key = data.get('access_key')
        service_url = data.get('service_url')
        
        if not access_key or not service_url:
            return jsonify({'status': 'error', 'message': 'Не указан ключ доступа или адрес сервиса'})
            
        headers = {
            'Content-Type': 'application/json',
            'AccessKey': access_key
        }
        
        response = requests.get(
            'https://api.reo.ru/reo-weight-control-api/api/v1/weight-controls/import',
            headers=headers
        )
        
        if response.status_code == 200:
            return jsonify({'status': 'success', 'message': 'Подключение к РЭО успешно'})
        elif response.status_code == 403:
            return jsonify({'status': 'error', 'message': 'Доступ запрещен. Неверный ключ доступа'})
        else:
            return jsonify({'status': 'error', 'message': f'Ошибка подключения: {response.status_code}'})
            
    except Exception as e:
        logger.error(f"Error checking REO connection: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True) 