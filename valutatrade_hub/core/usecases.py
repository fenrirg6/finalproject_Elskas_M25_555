from .utils import load_json, get_next_user_id, hash_password
from datetime import datetime
from .models import User, Portfolio

def register(input_username: str, input_password: str):
    user_data = load_json("users")

    if len(input_password) < 4:
        raise ValueError("Ошибка: пароль должен содержать от 4-х символов.")

    for user in user_data:
        if user["username"] == input_username:
            raise KeyError(f"Ошибка: имя пользователя {input_username} уже занято. Попробуйте другое имя.")




    new_user_id = get_next_user_id()



def login(input_username: str, input_password: str):
    pass

def show_portfolio(user_id, base_currency = "USD"):
    pass

def buy():
    pass

def sell():
    pass

def get_rate():
    return load_json("rates")

