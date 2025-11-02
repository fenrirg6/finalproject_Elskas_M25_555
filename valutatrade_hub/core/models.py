from .utils import generate_password_salt, hash_password, generate_timestamp
from copy import deepcopy
from typing import Optional

class User:
    def __init__(self, user_id: int,
                 username: str,
                 password: Optional[str] = None,
                 hashed_password: Optional[str] = None,
                 salt: Optional[str] = None,
                 registration_date: Optional[str] = None):
        self._user_id = user_id
        self._username = username

        # создание нового пользователя (передан password)
        if password is not None:
            self._salt = generate_password_salt() # случайная соль на 16 байт
            self._hashed_password = hash_password(self._salt, password)
            self._registration_date = generate_timestamp()

        # загрузка из JSON
        elif hashed_password is not None and salt is not None:
            self._salt = salt
            self._hashed_password = hashed_password
            self._registration_date = registration_date or generate_timestamp()

        # если не передан ни password, ни hashed_password
        else:
            raise ValueError("Ошибка: необходимо передать либо password, либо hashed_password!")

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, new_user_id):
        if not isinstance(new_user_id, int):
            raise ValueError("not int") # to change
        old_user_id = self._user_id
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
        self._username = new_username.strip()

    @property
    def salt(self):
        return self._salt

    @property
    def hashed_password(self):
        return self._hashed_password

    @property
    def registration_date(self):
        return self._registration_date

    def get_user_into(self):
        # выводит информацию о пользователе
        return f"'user_id': {self._user_id}, 'username': {self._username}, 'registration date': {self._registration_date}"

    def change_password(self, new_password: str):
        # изменяет пароль пользователя, с хешированием нового пароля.
        if len(new_password) < 4:
            raise ValueError("Ошибка: пароль не может быть короче 4-х символов.") # to change
        self._salt = generate_password_salt()
        self._hashed_password = hash_password(self._salt, new_password)
        # save_to_json(self)

    def verify_password(self, password: str):
        # проверяет введённый пароль на совпадение
        inputted_hashed_password = hash_password(self._salt, password)
        return inputted_hashed_password == self._hashed_password

    def to_dict(self):
        # преобразование в словарь для сохранения в JSON
        return {
            "user_id": self._user_id,
            "username": self._username,
            "salt": self._salt,
            "hashed_password": self._hashed_password,
            "registration_date": self._registration_date
        }

    @classmethod
    def from_dict(cls, data: dict):
        # создание из словаря для загрузки из JSON

        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=data["registration_date"]
        )

class Wallet:
    def __init__(self, currency_code, balance):
        if not currency_code or not currency_code.strip():
            raise ValueError("Ошибка: код валюты не может быть пустым.")
        self.currency_code = currency_code.upper().strip()
        self._balance = balance

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, new_balance):
        if not isinstance(new_balance, (int, float)):
            raise TypeError("Ошибка: баланс должен быть числом.")
        if new_balance < 0:
            raise ValueError("Ошибка: баланс не может быть отрицательным.") # to change
        self._balance = float(new_balance) # явно преобразуем

    def deposit(self, amount: float):
        if not amount or not isinstance(amount, (int, float)):
            raise TypeError("Ошибка: сумма пополнения должна быть числом.")
        if amount < 0:
            raise ValueError("Ошибка: сумма пополнения должна быть положительным числом.")
        self._balance += amount

    def withdraw(self, amount: float):
        if not amount or not isinstance(amount, (int, float)):
            raise TypeError("Ошибка: сумма снятия должна быть числом.")
        if amount > self._balance:
            raise ValueError(f"Ошибка: недостаточно средств. Доступно {self._balance} {self.currency_code}.")
        if amount < 0:
            raise ValueError("Ошибка: сумма снятия должна быть положительным числом.") # to change
        self._balance -= amount

    def get_balance_into(self):
        return {"currency_code": self.currency_code, "balance": self._balance}

    def to_dict(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )


class Portfolio:
    def __init__(self, user_id: int, wallets: dict[str, Wallet] = None):
        self._user_id = user_id
        self._wallets = wallets if wallets is not None else {} # опционально

    @property
    def user_id(self):
        return self._user_id

    @property
    def wallets(self):
        return deepcopy(self._wallets)

    def add_currency(self, currency_code:str):
        currency_code = currency_code.upper().strip()

        if currency_code in self._wallets:
            raise ValueError(f"Кошелек {currency_code} уже существует в портфеле")
        else:
            new_wallet = Wallet(currency_code, 0.0)
            self._wallets[currency_code] = new_wallet
            print(f"Кошелек {currency_code} добавлен в портфолио.")
            return new_wallet

    def get_total_value(self, exchange_rates: dict[str, float], base_currency: str = "USD"):
        # возвращает общую стоимость всех валют пользователя в указанной базовой валюте
        # (по курсам, полученным из API или фиктивным данным).
        if exchange_rates is None:
            exchange_rates = {}

        total = 0.0
        base_currency = base_currency.upper().strip()

        for currency_code, wallet in self._wallets.items():
            if currency_code == base_currency:
                # если совпадает - добавляем в тотал
                total += wallet.balance
            else:
                rate_key = f"{currency_code}_{base_currency}"
                rate = exchange_rates.get(rate_key)

                if rate is not None:
                    total += wallet.balance * rate
                    # если курса нет - скипаем валюту
        return total

    def get_wallet(self, currency_code):
        # возвращает объект Wallet по коду валюты или создает новый
        currency_code = currency_code.upper().strip()

        if currency_code not in self._wallets:
            self._wallets[currency_code] = Wallet(currency_code, 0.0) # to change???

        return self._wallets[currency_code]

    def to_dict(self):
        return {
            "user_id": self._user_id,
            "wallets": {
                code: wallet.to_dict()
                for code, wallet in self._wallets.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict):
        wallets_data = data.get("wallets", {})

        # проверяем что словарь
        if not isinstance(wallets_data, dict):
            wallets_data = {}

        wallets = {}
        for code, wallet_data in wallets_data.items():
            # проверяем что словарь с нужными полями
            if isinstance(wallet_data, dict):
                wallets[code] = Wallet.from_dict(wallet_data)

        return cls(user_id=data["user_id"], wallets=wallets)