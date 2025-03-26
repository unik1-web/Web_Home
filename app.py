from flask import Flask, render_template, jsonify, request
import sqlite3
import json
import logging
from datetime import datetime, timedelta
import fdb
import os
import requests
import uuid

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
        SELECT 
            a.nomer_ts, 
            a.datetimebrutto, 
            a.datetimetara,
            r.reostatus, 
            r.reodatetime,
            u.moduletype
        FROM auto_go a
        JOIN auto_uid u ON a.datetimebrutto = u.datetimebrutto AND a.nomer_ts = a.nomer_ts
        JOIN reo_data r ON u.uid = r.uid
    """)
    status_data = {}
    for row in cursor.fetchall():
        key = (row[0], row[1], row[2])  # nomer_ts, datetimebrutto, datetimetara
        if key not in status_data:
            status_data[key] = {'status1': '', 'status2': '', 'date': ''}
        
        if row[5] == 100:  # Object 1
            status_data[key]['status1'] = 'Отправлено' if row[3] == 2 else 'Ошибка'
        elif row[5] == 200:  # Object 2
            status_data[key]['status2'] = 'Отправлено' if row[3] == 2 else 'Ошибка'
            
        if row[4] > status_data[key]['date']:  # Keep the latest date
            status_data[key]['date'] = row[4]
    
    conn.close()
    
    # Format data for display
    formatted_rows = []
    for row in rows:
        formatted_row = list(row[:-1])  # Exclude TIME_DIFF
        
        # Format dates
        formatted_row[0] = row[0].strftime(config.get("date_format", "%Y-%m-%d %H:%M:%S"))
        formatted_row[1] = row[1].strftime(config.get("date_format", "%Y-%m-%d %H:%M:%S"))
        
        # Format weights
        weight_format = config.get("weight_format", "#.##").count('#') - 1
        formatted_row[5] = f"{float(row[5]):.{weight_format}f}"
        formatted_row[6] = f"{float(row[6]):.{weight_format}f}"
        formatted_row[7] = f"{float(row[7]):.{weight_format}f}"
        
        # Add company data (INN, KPP)
        company_data = companies.get(row[4], {})
        formatted_row = {
            'data': formatted_row,
            'inn': company_data.get('inn', ''),
            'kpp': company_data.get('kpp', ''),
        }
        
        # Add sending status
        status_key = (row[2], row[0], row[1])  # nomer_ts, datetime_brutto, datetime_tara
        status = status_data.get(status_key, {'status1': 'Готово к отправке', 'status2': 'Готово к отправке', 'date': ''})
        formatted_row['status1'] = status['status1'] or 'Готово к отправке'
        formatted_row['status2'] = status['status2'] or 'Готово к отправке'
        formatted_row['send_date'] = status['date']
        
        formatted_rows.append(formatted_row)
    
    return render_template('index.html', rows=formatted_rows, current_date=current_date)

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

@app.route('/send_to_reo', methods=['POST'])
def send_to_reo():
    try:
        config = load_config()
        data = request.get_json()
        
        # Get required data from the request
        date_brutto = data.get('date')
        selected_rows = data.get('selected_rows', [])
        
        if not date_brutto or not selected_rows:
            return jsonify({'status': 'error', 'message': 'Missing required data'}), 400
            
        # Get data from database for selected rows
        db_path = config.get("db_path", r'C:\VESYEVENT.GDB')
        rows = fetch_data(date_brutto, db_path)
        
        # Connect to SQLite database to check already sent records
        conn = sqlite3.connect('app_data.sqlite')
        cursor = conn.cursor()
        
        # Get list of already sent records
        cursor.execute("""
            SELECT DISTINCT a.nomer_ts, a.datetimebrutto, a.datetimetara, u.moduletype
            FROM auto_go a
            JOIN auto_uid u ON a.datetimebrutto = u.datetimebrutto AND a.nomer_ts = a.nomer_ts
            JOIN reo_data r ON u.uid = r.uid
            WHERE r.reostatus = 2
        """)
        sent_records = {(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()}
        
        # Filter only selected rows that haven't been sent yet
        selected_data = []
        for i in selected_rows:
            if i >= len(rows):
                continue
                
            row = rows[i]
            record_key1 = (row[2], row[0], row[1], 100)  # Object 1
            record_key2 = (row[2], row[0], row[1], 200)  # Object 2
            
            if record_key1 not in sent_records:
                selected_data.append((row, 100))  # Add for Object 1
            if record_key2 not in sent_records:
                selected_data.append((row, 200))  # Add for Object 2
        
        if not selected_data:
            return jsonify({'status': 'warning', 'message': 'All selected records have already been sent'})
        
        # Format data for REO and prepare database records
        reo_data = []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get company data for INN and KPP
        cursor.execute("SELECT name, inn, kpp FROM list_companies")
        companies = {row[0]: {'inn': row[1], 'kpp': row[2]} for row in cursor.fetchall()}
        
        # Track processed records to avoid duplicates
        processed_records = set()
        
        for row, module_type in selected_data:
            # Generate unique ID for this record
            uid = str(uuid.uuid4())
            
            # Get object details based on module type
            object_name = config.get('object_name1' if module_type == 100 else 'object_name2', '')
            object_id = config.get('object_id1' if module_type == 100 else 'object_id2', '')
            
            # Format data for REO service
            reo_record = {
                'datetime_brutto': row[0].strftime("%Y-%m-%d %H:%M:%S"),
                'datetime_tara': row[1].strftime("%Y-%m-%d %H:%M:%S"),
                'nomer_ts': row[2],
                'marka_ts': row[3],
                'firma_pol': row[4],
                'brutto': float(row[5]),
                'tara': float(row[6]),
                'netto': float(row[7]),
                'gruz_name': row[8],
                'object_name': object_name,
                'object_id': object_id
            }
            reo_data.append(reo_record)
            
            # Get company data
            company_data = companies.get(row[4], {'inn': '', 'kpp': ''})
            
            # Create unique key for this record
            record_key = (row[2], row[0].strftime("%Y-%m-%d %H:%M:%S"), row[1].strftime("%Y-%m-%d %H:%M:%S"))
            
            # Insert record into auto_go table only if not processed yet
            if record_key not in processed_records:
                cursor.execute("""
                    INSERT INTO auto_go (
                        datetimebrutto, datetimetara, nomer_ts, marka_ts, firma_pol,
                        brutto, tara, netto, gruz_name, inn, kpp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row[0].strftime("%Y-%m-%d %H:%M:%S"),
                    row[1].strftime("%Y-%m-%d %H:%M:%S"),
                    row[2], row[3], row[4], row[5], row[6], row[7], row[8],
                    company_data['inn'], company_data['kpp']
                ))
                processed_records.add(record_key)
            
            # Insert record into auto_uid table
            cursor.execute("""
                INSERT INTO auto_uid (moduletype, datetimebrutto, uid)
                VALUES (?, ?, ?)
            """, (module_type, row[0].strftime("%Y-%m-%d %H:%M:%S"), uid))
            
            # Insert record into reo_data table
            cursor.execute("""
                INSERT INTO reo_data (uid, reostatus, reodatetime)
                VALUES (?, ?, ?)
            """, (uid, 2, current_time))  # status 2 means "sent"
            
            # Insert record into new_auto_go table only if not processed yet
            if record_key not in processed_records:
                cursor.execute("""
                    INSERT INTO new_auto_go (
                        datetimebrutto, datetimetara, nomer_ts, marka_ts, firma_pol,
                        brutto, tara, netto, gruz_name, inn, kpp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row[0].strftime("%Y-%m-%d %H:%M:%S"),
                    row[1].strftime("%Y-%m-%d %H:%M:%S"),
                    row[2], row[3], row[4], row[5], row[6], row[7], row[8],
                    company_data['inn'], company_data['kpp']
                ))
        
        # Commit changes to database
        conn.commit()
        
        # Send data to REO service
        try:
            # Try both possible URL config keys
            service_url = config.get('object_url') or config.get('service_url')
            if not service_url:
                raise ValueError("Service URL is not configured. Please check settings and make sure 'Адрес сервиса' is filled in.")
                
            if not service_url.startswith(('http://', 'https://')):
                service_url = 'https://' + service_url
                
            access_key = config.get('access_key')
            if not access_key:
                raise ValueError("Access key is not configured. Please check settings.")
                
            headers = {
                'Content-Type': 'application/json',
                'AccessKey': access_key
            }
            
            logger.info(f"Sending data to REO service at: {service_url}")
            logger.info(f"Request data: {json.dumps(reo_data, ensure_ascii=False)}")
            
            response = requests.post(
                service_url,
                headers=headers,
                json={'data': reo_data}
            )
            
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response content: {response.text}")
            
            if response.status_code == 200:
                logger.info("Data successfully sent to REO")
                status_message = "Data successfully sent to REO"
            else:
                logger.error(f"Error from REO service: {response.status_code}, Response: {response.text}")
                status_message = f"Error from REO service: {response.status_code}"
                # If request failed, rollback database changes
                cursor.execute("DELETE FROM reo_data WHERE reodatetime = ?", (current_time,))
                cursor.execute("DELETE FROM auto_uid WHERE datetimebrutto IN (SELECT datetimebrutto FROM auto_go WHERE datetimebrutto = ?)", 
                             (current_time,))
                cursor.execute("DELETE FROM auto_go WHERE datetimebrutto = ?", (current_time,))
                cursor.execute("DELETE FROM new_auto_go WHERE datetimebrutto = ?", (current_time,))
                conn.commit()
                
        except ValueError as ve:
            logger.error(f"Configuration error: {str(ve)}")
            status_message = str(ve)
            # Rollback database changes
            cursor.execute("DELETE FROM reo_data WHERE reodatetime = ?", (current_time,))
            cursor.execute("DELETE FROM auto_uid WHERE datetimebrutto IN (SELECT datetimebrutto FROM auto_go WHERE datetimebrutto = ?)", 
                         (current_time,))
            cursor.execute("DELETE FROM auto_go WHERE datetimebrutto = ?", (current_time,))
            cursor.execute("DELETE FROM new_auto_go WHERE datetimebrutto = ?", (current_time,))
            conn.commit()
        except Exception as e:
            logger.error(f"Error sending data to REO: {str(e)}")
            status_message = f"Error sending data to REO: {str(e)}"
            # Rollback database changes
            cursor.execute("DELETE FROM reo_data WHERE reodatetime = ?", (current_time,))
            cursor.execute("DELETE FROM auto_uid WHERE datetimebrutto IN (SELECT datetimebrutto FROM auto_go WHERE datetimebrutto = ?)", 
                         (current_time,))
            cursor.execute("DELETE FROM auto_go WHERE datetimebrutto = ?", (current_time,))
            cursor.execute("DELETE FROM new_auto_go WHERE datetimebrutto = ?", (current_time,))
            conn.commit()
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully processed {len(reo_data)} records. {status_message}',
            'data': reo_data
        })
        
    except Exception as e:
        logger.error(f"Error in send_to_reo: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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