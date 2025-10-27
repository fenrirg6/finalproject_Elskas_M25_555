import hashlib
import os
import json

# move to utils.py?
USERS_JSON_PATH = os.path.join(os.getcwd(), "data", "users.json")


# сделать функцию save to json ЗДЕСЬ
# нужно сохранять данные в соответствующий json в зависимости от КЛАССА
# н, если класс user, то складывать в data/users.json
# н, если класс wallet, то складывать в data/wallet.json

def generate_password_salt(): # случайная соль на 16 байт
    return os.urandom(16).hex()