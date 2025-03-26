import datetime
import base64
import hashlib
import os

def generate_license_key(expiry_date):
    # Преобразуем дату в строку
    date_str = expiry_date.strftime("%Y%m%d")
    
    # Создаем секретный ключ (в реальном приложении должен храниться в безопасном месте)
    secret_key = "BuzulukSecretKey2024"
    
    # Создаем строку для хеширования
    data_to_hash = f"{date_str}{secret_key}"
    
    # Создаем хеш
    hash_object = hashlib.sha256(data_to_hash.encode())
    hash_value = hash_object.hexdigest()
    
    # Создаем финальный ключ (дата + хеш)
    license_key = f"{date_str}{hash_value}"
    
    # Кодируем ключ в base64
    encoded_key = base64.b64encode(license_key.encode()).decode()
    
    return encoded_key

def save_license_key(key, filename="license.key"):
    with open(filename, "wb") as f:
        f.write(key.encode())
    print(f"Лицензионный ключ сохранен в файл {filename}")

if __name__ == "__main__":
    # Устанавливаем дату окончания лицензии (13 мая 2025)
    expiry_date = datetime.datetime(2025, 5, 13)
    
    # Генерируем ключ
    license_key = generate_license_key(expiry_date)
    
    # Сохраняем ключ в файл
    save_license_key(license_key)
    print("Лицензионный ключ успешно создан") 