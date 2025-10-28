#!/usr/bin/env python3

from valutatrade_hub.core.models import *

def main():
    print("ValutaTradeHub project is running!")

    # test - to drop
    new_user = User(1, "Test", "qwerty123", "2025-10-29")
    new_user_2 = User(2, "Test", "31233rtsdfdsf", "29.10.2025")
    new_wallet = Wallet("USD", 0.0)
    new_portfolio = Portfolio(1, {"USD": new_wallet})


    print("\n========== TESTIGN METHODS for user ==========\n")

    # user 1
    print(f"new_user id: {new_user.user_id}")
    new_user.user_id = 4
    print(f"changes new_user id: {new_user.user_id}")

    print(f"new_user username: {new_user.username}")
    new_user.username = "Andrew98"
    print(f"changed new_user username: {new_user.username}")

    print(f"new_user salt: {new_user.salt}")

    print(f"new_user hashed_password: {new_user.hashed_password}")
    new_user.change_password("TestTest123")
    print(f"changed new_user hashed_password {new_user.hashed_password}")

    print("Результат проверки пароля с TestTest", new_user.verify_password("TestTest"))
    print("Результат проверки пароля с TestTest123", new_user.verify_password("TestTest123"))

    print(f"Дата регистрации new_user: {new_user.registration_date}")

    print("new_user get_info()", new_user.get_user_into())

    print("\n========== TESTIGN METHODS for Wallet ==========\n")

    print(f"new_wallet balance: {new_wallet.balance}")
    # set new balance
    new_wallet.balance = 99.0
    print(f"new_wallet balance: {new_wallet.balance}")

    new_wallet.deposit(1.0)
    print(f"new_wallet balance after deposit: {new_wallet.balance}")

    # print("new_wallet withdraw negative funds:", new_wallet.withdraw(-1.0))
    # print(f"new_wallet withdraw lot of funds: {new_wallet.withdraw(10000.0)}")
    print(f"new_wallet withdraw funds: {new_wallet.withdraw(50)}")

    print(f"new_wallet balance: {new_wallet.balance}")

    print(f"new_wallet get balance into", new_wallet.get_balance_into())

    print("\n========== TESTIGN METHODS for Portfolio ==========\n")

    print(f"new portfolio user_id: {new_portfolio.user_id}")
    print(f"new portfolio wallets: {new_portfolio.wallets}")

    print(f"add new currency", new_portfolio.add_currency("EUR"))
    print(f"new portfolio wallets: {new_portfolio.wallets}")

    # print(f"get RUR from new_porfolio", new_portfolio.get_wallet("rur"))
    print(f"get USD from new_portfolio", new_portfolio.get_wallet("usd"))



if __name__ == "__main__":
    main()