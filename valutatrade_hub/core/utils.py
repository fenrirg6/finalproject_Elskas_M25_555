import hashlib
import os
import json
from datetime import datetime
from pathlib import Path

# константы путей
DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
RATES_FILE = DATA_DIR / "rates.json"

def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)

def load_json(file_path: Path, default=None):

    if not file_path.exists():
        return default if default is not None else []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.decoder.JSONDecodeError:
        return default if default is not None else []

def save_json(file_path: Path, data):
    ensure_data_dir()

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        raise

def load_users():
    return load_json(USERS_FILE, default=[])

def save_users(users):
    save_json(USERS_FILE, users)

def load_portfolios():
    return load_json(PORTFOLIOS_FILE, default=[])

def save_portfolios(portfolios):
    save_json(PORTFOLIOS_FILE, portfolios)

def load_rates():
    return load_json(RATES_FILE, default={})

def save_rates(rates):
    save_json(RATES_FILE, rates)

def get_next_user_id():
    users = load_users()
    if not users:
        return 1
    else:
        return max(user["user_id"] for user in users) + 1

def find_user_by_username(username):
    users = load_users()
    for user in users:
        if user["username"] == username:
            return user
    return None

def find_user_by_id(user_id):
    users = load_users()
    for user in users:
        if user["user_id"] == user_id:
            return user
    return None

def update_user(user_data):
    users = load_users()

    for i, user in enumerate(users):
        if user["user_id"] == user_data["user_id"]:
            users[i] = user_data
            break
    else:
        users.append(user_data)

    save_users(users)

def find_portfolio_by_user_id(user_id):
    portfolios = load_portfolios()
    for portfolio in portfolios:
        if portfolio["user_id"] == user_id:
            return portfolio
    return None

def update_portfolio(portfolio_data):

    portfolios = load_portfolios()

    for i, portfolio in enumerate(portfolios):
        if portfolio["user_id"] == portfolio_data["user_id"]:
            portfolios[i] = portfolio_data
            break
    else:
        portfolios.append(portfolio_data)

    save_portfolios(portfolios)

def get_rate(from_currency: str, to_currency: str):
    from_currency, to_currency = from_currency.upper().strip(), to_currency.upper().strip()
    if from_currency == to_currency:
        return 1.0

    rates = load_rates()
    rate_key = f"{from_currency}_{to_currency}"
    if rate_key in rates:
        return rates[rate_key].get("rate")

    reverse_key = f"{to_currency}_{from_currency}"
    if reverse_key in rates:
        reverse_rate = rates[reverse_key].get("rate")
        if reverse_rate and reverse_rate != 0:
            return 1.0 / reverse_rate

    return None

def get_rate_info(from_currency: str, to_currency: str):

    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency == to_currency:
        return {
            "rate": 1.0,
            "updated_at": datetime.now().isoformat(),
            "is_direct": True
        }

    rates = load_rates()
    rate_key = f"{from_currency}_{to_currency}"

    if rate_key in rates:
        info = rates[rate_key].copy()
        info["is_direct"] = True
        return info

    # обратный курс?
    reverse_key = f"{to_currency}_{from_currency}"
    if reverse_key in rates:
        reverse_info = rates[reverse_key]
        reverse_rate = reverse_info.get("rate")
        if reverse_rate and reverse_rate != 0:
            return {
                "rate": 1.0 / reverse_rate,
                "updated_at": reverse_info.get("updated_at"),
                "is_direct": False
            }

    return None

def update_rate(from_currency: str, to_currency: str, rate: float):

    rates = load_rates()

    rate_key = f"{from_currency.upper()}_{to_currency.upper()}"
    rates[rate_key] = {
        "rate": rate,
        "updated_at": datetime.now().isoformat()
    }
    # перезаписываем время последнего обновления
    rates["last_refresh"] = datetime.now().isoformat()

    save_rates(rates)

def format_number(value: float, decimals: int = 2):
    return f"{value:,.{decimals}f}".replace(",", " ")

def generate_timestamp():
    return datetime.now().isoformat()

def generate_password_salt(): # случайная соль на 16 байт
    return os.urandom(16).hex()

def hash_password(salt: str, password: str):
    return hashlib.sha256((salt + password).encode()).hexdigest()