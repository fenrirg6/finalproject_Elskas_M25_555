from .utils import generate_password_salt, USERS_JSON_PATH

import hashlib
import os
import json


class Users:
    def __init__(self, user_id: int, username: str, password: str, registration_date):
        # hash from def_pass (via func), salt as func?, reg date as datetime
        self._user_id = user_id
        self._username = username
        self._salt = generate_password_salt() # случайная соль на 16 байт
        self._hashed_password = hashlib.sha256((self._salt + password).encode()).hexdigest() # тоже в utils.py?
        self._registration_date = registration_date

        # автоматическое сохранение экземпляра в JSON
        self._save_to_json()

    def _save_to_json(self): # перенести в utils.py
        file_path = USERS_JSON_PATH

        # создаем директорию если ее нет
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                users = json.load(f)
        else:
            users = []

        user_data_to_append = {
            "user_id": self._user_id,
            "username": self._username,
            "salt": self._salt,
            "hashed_password": self._hashed_password,
            "registration_date": self._registration_date
        }

        users.append(user_data_to_append)

        # сохраняем

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, new_user_id):
        if not isinstance(new_user_id, int):
            raise ValueError("not int") # to change
        self._user_id = new_user_id

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, new_username):
        if not isinstance(new_username, str):
            raise ValueError("not str") # to change
        if new_username.strip() == "":
            raise ValueError("empty str")
        self._username = new_username

    @property # нужно ли?
    # + setter?
    def salt(self):
        return self._salt

    @property # нужно ли? или просто pass?
    # + setter?
    def hashed_password(self):
        return self._hashed_password

    @property
    # + setter?
    def registration_date(self):
        return self._registration_date

    def get_user_into(self):
        # выводит информацию о пользователе (без пароля) (или print?????)
        return f"ID: {self._user_id}, Username: {self._username}, Registration Date: {self._registration_date}"

    def change_password(self, new_password: str):
        # изменяет пароль пользователя, с хешированием нового пароля.
        if len(new_password) < 4:
            raise ValueError("password must be at least 4 characters")
        self._hashed_password = hashlib.sha256((self._salt + new_password).encode()).hexdigest()
        return "Успешно: пароль изменен."

    def verify_password(self, password: str):
        # проверяет введённый пароль на совпадение
        inputted_hashed_password = hashlib.sha256((self._salt + password).encode()).hexdigest()
        return inputted_hashed_password == self._hashed_password

class Wallet:
    def __init__(self, currency_code, balance):
        self.currency_code = currency_code
        self._balance = balance


    def _save_to_json(self):
        pass
        # to change - нужно имплементировать в составе wallet


    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, new_balance):
        if not isinstance(new_balance, int):
            raise TypeError("Wrong data type") # to change
        if new_balance < 0:
            raise ValueError("Balance cannot be negative") # to change
        self._balance = new_balance

    def deposit(self, amount: float):
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        self._balance += amount

    def withdraw(self, amount: float):
        if amount > self._balance:
            raise ValueError("Not enough balance")
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        self._balance -= amount

    def get_balance_into(self):
        return f"Баланс: {self._balance}" # to change

class Portfolio:
    def __init__(self, user_id: int, wallets: dict[str, Wallet]):
        self._user_id = user_id
        self._wallets = wallets

    def add_wallet(self, wallet: Wallet):
        if self._wallets[self._user_id] in self._wallets:
            raise ValueError("Wallet already exists")
        self._wallets[self._user_id] = wallet