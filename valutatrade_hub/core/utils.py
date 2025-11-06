import hashlib
import os
from datetime import datetime

def format_number(value: float, decimals: int = 2):
    """Форматирование числа с разделителями"""
    return f"{value:,.{decimals}f}".replace(",", " ")

def generate_timestamp():
    """Генерация ISO таймпстемпа"""
    return datetime.now().isoformat()

def generate_password_salt():
    """Генерация случайное соли на 16 байт"""
    return os.urandom(16).hex()

def hash_password(salt: str, password: str):
    """Хеширует пароль с солью через sha256"""
    return hashlib.sha256((salt + password).encode()).hexdigest()