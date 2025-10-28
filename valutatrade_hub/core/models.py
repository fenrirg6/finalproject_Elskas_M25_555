from .utils import generate_password_salt, save_to_json, convert_timestamp, hash_password

class User:
    def __init__(self, user_id: int, username: str, password: str, registration_date):
        self._user_id = user_id
        self._username = username
        self._salt = generate_password_salt() # случайная соль на 16 байт
        self._hashed_password = hash_password(self._salt, password)
        self._registration_date = convert_timestamp(registration_date)

        # автоматическое сохранение экземпляра в JSON
        save_to_json(self)

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, new_user_id):
        if not isinstance(new_user_id, int):
            raise ValueError("not int") # to change
        self._user_id = new_user_id
        # save_to_json(self)

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
        # save_to_json(self)

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
            raise ValueError("password must be at least 4 characters") # to change
        self._hashed_password = hash_password(self._salt, new_password)
        # save_to_json(self)
        return "Успешно: пароль изменен."

    def verify_password(self, password: str):
        # проверяет введённый пароль на совпадение
        inputted_hashed_password = hash_password(self._salt, password)
        return inputted_hashed_password == self._hashed_password

class Wallet:
    def __init__(self, currency_code, balance):
        self.currency_code = currency_code
        self._balance = balance # по умолчанию 0.0 - to change?

        # автоматическое сохранение экземпляра в JSON
        save_to_json(self)

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, new_balance):
        if not isinstance(new_balance, float):
            raise TypeError("Wrong data type") # to change
        if new_balance < 0:
            raise ValueError("Balance cannot be negative") # to change
        self._balance = new_balance

    def deposit(self, amount: float):
        if amount < 0:
            raise ValueError("Amount cannot be negative")  # to change
        self._balance += amount

    def withdraw(self, amount: float):
        if amount > self._balance:
            raise ValueError("Not enough balance") # to change
        if amount < 0:
            raise ValueError("Amount cannot be negative") # to change
        self._balance -= amount

    def get_balance_into(self):
        return f"Баланс: {self._balance}" # to change

class Portfolio:
    def __init__(self, user_id: int, wallets: dict[str, Wallet]):
        self._user_id = user_id
        self._wallets = wallets

        # автоматическое сохранение экземпляра в JSON
        save_to_json(self)

    @property
    def user_id(self):
        return self._user_id # to change

    @property
    def wallets(self):
        return self._wallets.copy() # to change

    def add_currency(self, currency_code:str):
        currency_code = currency_code.upper()

        if currency_code in self._wallets:
            raise ValueError(f"Currency code {currency_code} already exists") # to change
        else:
            new_wallet = Wallet(currency_code, 0.0)
            self._wallets[currency_code] = new_wallet
            print(f"Added {currency_code} to Portfolio") # to change

            return new_wallet

    def get_total_value(self, base_currency="USD"):
        # возвращает общую стоимость всех валют пользователя в указанной базовой валюте
        # (по курсам, полученным из API или фиктивным данным).
        pass

    def get_wallet(self, currency_code):
        # возвращает объект Wallet по коду валюты.
        currency_code = currency_code.upper()

        if currency_code not in self._wallets:
            raise ValueError(f"Currency code {currency_code} does not exist") # to change
        else:
            return self._wallets[currency_code]
