from datetime import datetime
import sys
sys.path.append('.')

from valutatrade_hub.core.models import User, Wallet, Portfolio
from valutatrade_hub.core import utils

class AuthenticationError(Exception):
    pass

class ValidationError(Exception):
    pass

class InsufficientFundsError(Exception):
    pass

# хранение текущей сессии
_current_user = None
_current_portfolio = None

def register_user(username, password):
    try:
        # валидация логина
        if not username or not username.strip():
            return False, "Ошибка: имя пользователя не может быть пустым"

        # валидация длины пароля
        if len(password) < 4:
            return False, "Ошибка: пароль должен быть не короче 4 символов"

        # проверка уникальности логина
        if utils.find_user_by_username(username):
            return False, f"Ошибка: имя пользователя '{username}' уже занято"

        # создание пользователя
        user_id = utils.get_next_user_id()
        user = User(user_id=user_id, username=username, password=password)

        # сохранение
        utils.update_user(user.to_dict())

        # создание пустого портфеля
        portfolio = Portfolio(user_id=user_id)
        utils.update_portfolio(portfolio.to_dict())

        return True, f"Успешно: пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username <логин> --password <пароль>"

    except Exception as e:
        return False, f"Ошибка регистрации: {str(e)}"

def login_user(username, password):
    global _current_user, _current_portfolio

    try:
        # ищем пользователя
        user_data = utils.find_user_by_username(username)
        if not user_data:
            return False, f"Ошибка: пользователь '{username}' не найден"

        # создаем экземпляр
        user = User.from_dict(user_data)

        # проверка пароля
        if not user.verify_password(password):
            return False, "Ошибка: неверный пароль"

        # загружаем портфель
        portfolio_data = utils.find_portfolio_by_user_id(user.user_id)
        if portfolio_data:
            portfolio = Portfolio.from_dict(portfolio_data)
        else:
            # создаем портфель если он отсутствует (just in case)
            portfolio = Portfolio(user_id=user.user_id)
            utils.update_portfolio(portfolio.to_dict())

        # сохранение в сессию
        _current_user = user
        _current_portfolio = portfolio

        return True, f"Успешно: вы вошли как '{username}'"

    except Exception as e:
        return False, f"Ошибка входа: {str(e)}"

# to drop? по тз не требовалось
def logout_user():
    global _current_user, _current_portfolio
    _current_user = None
    _current_portfolio = None

# to drop? по тз не требовалось
def get_current_user() :
    return _current_user

# to drop? по тз не требовалось
def get_current_portfolio():
    return _current_portfolio

def is_authenticated():
    return _current_user is not None

def require_authentication():
    if not is_authenticated():
        raise AuthenticationError("Ошибка: Сначала выполните login")

def show_portfolio(base_currency: str = 'USD'):
    try:
        require_authentication()

        base_currency = base_currency.upper()
        portfolio = get_current_portfolio()
        user = get_current_user()

        # получаем все кошельки
        wallets_dict = portfolio._wallets

        if not wallets_dict:
            return True, f"Портфель пользователя '{user.username}' пуст. Добавьте валюту командой buy."

        # загружаем курсы - скорее всего понадобится в последующей реализации с АПИ
        rates = utils.load_rates()

        # формируем вывод
        output = [f"Портфель пользователя '{user.username}' (база: {base_currency}):"]
        total_value = 0.0

        for currency_code, wallet in sorted(wallets_dict.items()):
            balance = wallet.balance

            # конвертируем в базовую валюту
            if currency_code == base_currency:
                value_in_base = balance
            else:
                rate = utils.get_rate(currency_code, base_currency)
                if rate is None:
                    output.append(f"- {currency_code}: {balance:.4f}  → курс недоступен")
                    continue
                value_in_base = balance * rate

            total_value += value_in_base

            # форматирование вывода
            if balance >= 1:
                balance_str = f"{balance:.2f}"
            else:
                balance_str = f"{balance:.4f}"

            value_str = utils.format_number(value_in_base, 2)
            output.append(f"- {currency_code}: {balance_str}  → {value_str} {base_currency}")

        output.append("-" * 33)
        output.append(f"ИТОГО: {utils.format_number(total_value, 2)} {base_currency}")

        return True, "\n".join(output)

    except AuthenticationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Ошибка отображения портфеля: {str(e)}"


def buy_currency(currency_code, amount):
    try:
        require_authentication()

        # валидация
        currency_code = currency_code.upper().strip()

        if not currency_code:
            return False, "Ошибка: код валюты не может быть пустым"

        if not isinstance(amount, (int, float)) or amount <= 0:
            return False, "Ошибка: 'amount' должен быть положительным числом"

        # чтобы нельзя было купить USD за USD (?)
        if currency_code == 'USD':
            return False, "Нельзя купить USD за USD. Используйте другую валюту."

        portfolio = get_current_portfolio()

        # получаем курс покупаемой валюты к USD
        rate = utils.get_rate(currency_code, 'USD')

        if not rate:
            return False, f"Ошибка: не удалось получить курс для {currency_code} → USD. Повторите попытку позже."

        # рассчитываем стоимость в USD
        cost_in_usd = amount * rate

        # проверяем наличие USD кошелька и достаточность средств
        usd_wallet = portfolio.get_wallet('USD')

        if usd_wallet.balance < cost_in_usd:
            return False, (
                f"Ошибка: недостаточно USD для покупки {amount:.4f} {currency_code}. "
                f"Требуется: {utils.format_number(cost_in_usd, 2)} USD, "
                f"доступно: {utils.format_number(usd_wallet.balance, 2)} USD"
            )

        # списываем USD
        usd_wallet.withdraw(cost_in_usd)

        # получаем или создаём кошелёк покупаемой валюты
        wallet = portfolio.get_wallet(currency_code)
        old_balance = wallet.balance

        # пополняем баланс покупаемой валюты
        wallet.deposit(amount)
        new_balance = wallet.balance

        # сохраняем портфель
        utils.update_portfolio(portfolio.to_dict())

        # формируем вывод
        output = []
        output.append(
            f"Покупка выполнена: {amount:.4f} {currency_code} по курсу {utils.format_number(rate, 2)} USD/{currency_code}")
        output.append("Изменения в портфеле:")
        output.append(f"- {currency_code}: было {old_balance:.4f} → стало {new_balance:.4f}")
        output.append(f"- USD: списано {utils.format_number(cost_in_usd, 2)} USD")
        output.append(f"Стоимость покупки: {utils.format_number(cost_in_usd, 2)} USD")

        return True, "\n".join(output)

    except AuthenticationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Ошибка покупки: {str(e)}"


def sell_currency(currency_code: str, amount: float):
    try:
        require_authentication()

        # валидация
        currency_code = currency_code.upper().strip()

        if not currency_code:
            return False, "Ошибка: код валюты не может быть пустым"

        if not isinstance(amount, (int, float)) or amount <= 0:
            return False, "Ошибка: 'amount' должен быть положительным числом"

        # чтобы нельзя было продать USD за USD (?)
        if currency_code == 'USD':
            return False, "Нельзя продать USD за USD. Используйте другую валюту."

        portfolio = get_current_portfolio()

        # проверяем наличие кошелька
        wallet = portfolio.get_wallet(currency_code)
        if not wallet:
            return False, f"У вас нет кошелька '{currency_code}'. Добавьте валюту: она создаётся автоматически при первой покупке."

        old_balance = wallet.balance

        # проверяем достаточность средств
        if wallet.balance < amount:
            return False, f"Недостаточно средств: доступно {wallet.balance:.4f} {currency_code}, требуется {amount:.4f} {currency_code}"

        # получаем курс продаваемой валюты к USD
        rate = utils.get_rate(currency_code, 'USD')

        if not rate:
            return False, f"Не удалось получить курс для {currency_code}→USD. Повторите попытку позже."

        # рассчитываем выручку в USD
        revenue_in_usd = amount * rate

        # снимаем средства с продаваемой валюты
        wallet.withdraw(amount)
        new_balance = wallet.balance

        # начисляем USD
        usd_wallet = portfolio.get_wallet('USD')
        old_usd_balance = usd_wallet.balance
        usd_wallet.deposit(revenue_in_usd)
        new_usd_balance = usd_wallet.balance

        # сохраняем портфель
        utils.update_portfolio(portfolio.to_dict())

        # формируем вывод
        output = []
        output.append(
            f"Продажа выполнена: {amount:.4f} {currency_code} по курсу {utils.format_number(rate, 2)} USD/{currency_code}")
        output.append("Изменения в портфеле:")
        output.append(f"- {currency_code}: было {old_balance:.4f} → стало {new_balance:.4f}")
        output.append(
            f"- USD: было {utils.format_number(old_usd_balance, 2)} → стало {utils.format_number(new_usd_balance, 2)} USD")
        output.append(f"Выручка: {utils.format_number(revenue_in_usd, 2)} USD")

        return True, "\n".join(output)

    except AuthenticationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Ошибка продажи: {str(e)}"

def get_exchange_rate(from_currency: str, to_currency: str):

    try:
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        if not from_currency or not to_currency:
            return False, "Коды валют не могут быть пустыми"

        # получаем информацию о курсе
        rate_info = utils.get_rate_info(from_currency, to_currency)

        if not rate_info:
            return False, f"Курс {from_currency} → {to_currency} недоступен. Повторите попытку позже."

        rate = rate_info["rate"]
        updated_at = rate_info.get("updated_at", "неизвестно")

        # парсим дату если возможно
        try:
            dt = datetime.fromisoformat(updated_at)
            updated_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            updated_str = updated_at

        # вычисляем обратный курс
        reverse_rate = 1.0 / rate if rate != 0 else 0

        output = []
        output.append(f"Курс {from_currency} → {to_currency}: {rate:.8f} (обновлено: {updated_str})")
        output.append(f"Обратный курс {to_currency} → {from_currency}: {utils.format_number(reverse_rate, 2)}")

        return True, "\n".join(output)

    except Exception as e:
        return False, f"Ошибка получения курса: {str(e)}"
