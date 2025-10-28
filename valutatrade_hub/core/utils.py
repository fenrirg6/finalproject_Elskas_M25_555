import hashlib
import os
import json
from datetime import datetime

# move to utils.py?
DATA_PATH = os.path.join(os.getcwd(), "data")

def convert_timestamp(timestamp):
    # если уже datetime объект
    if isinstance(timestamp, datetime):
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')

    # если это числовой timestamp (Unix time)
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    # если это строка
    if isinstance(timestamp, str):
        # пробуем разные форматы
        formats = [
            '%Y-%m-%d',  # "2025-10-29"
            '%Y-%m-%d %H:%M:%S',  # "2025-10-29 14:30:00"
            '%d.%m.%Y',  # "29.10.2025"
            '%d.%m.%Y %H:%M:%S',  # "29.10.2025 14:30:00"
            '%d.%m.%Y %H:%M',  # "29.10.2025 14:30"
            '%Y/%m/%d',  # "2025/10/29"
            '%d-%m-%Y',  # "29-10-2025"
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp, fmt)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue

        # если ни один формат не подошёл
        raise ValueError(f"Не удалось распознать формат даты: {timestamp}")
    raise TypeError(f"Неподдерживаемый тип для timestamp: {type(timestamp)}")

def save_to_json(obj):
    class_name = obj.__class__.__name__.lower()
    file_path = os.path.join(DATA_PATH, f"{class_name}s.json")

    # создаем директорию если ее нет
    os.makedirs(DATA_PATH, exist_ok=True)

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    obj_dict = object_to_dict(obj)
    data.append(obj_dict)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Успешно: сохранено в {file_path}")

# сделать функцию save to json ЗДЕСЬ
# нужно сохранять данные в соответствующий json в зависимости от КЛАССА
# н, если класс user, то складывать в data/users.json
# н, если класс wallet, то складывать в data/wallet.json

# функция для сериализации вложенных кастомных объектов (bug Portfolio -> Wallet)
def object_to_dict(obj):
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj

    if isinstance(obj, (list, tuple)):
        return [object_to_dict(item) for item in obj]

    if isinstance(obj, datetime):
        return obj.isoformat()

    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            clean_key = key if isinstance(key, str) else str(key)
            result[clean_key] = object_to_dict(value)
        return result

    if hasattr(obj, "__dict__"):
        result = {}
        for key, value in obj.__dict__.items():
            clean_key = key.lstrip("_")
            result[clean_key] = object_to_dict(value)
        return result

    return str(obj)

def generate_password_salt(): # случайная соль на 16 байт
    return os.urandom(16).hex()

def hash_password(salt: str, password: str):
    return hashlib.sha256((salt + password).encode()).hexdigest()