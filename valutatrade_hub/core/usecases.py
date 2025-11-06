from valutatrade_hub.logging_config import get_logger
import sys
sys.path.append('.')

from valutatrade_hub.core.models import User, Portfolio
from valutatrade_hub.core import utils

from valutatrade_hub.core.exceptions import (
    InsufficientFundsError,
    CurrencyNotFoundError,
    ApiRequestError,
    AuthenticationError,
    ValidationError
)
from valutatrade_hub.core.currencies import get_currency, get_supported_currencies
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.decorators import log_action

# хранение текущей сессии
_current_user = None
_current_portfolio = None

# логгер
logger = get_logger("valutatrade_hub.usecases")

@log_action("REGISTER")
def register_user(username, password):
    """
    Обрабатывает логику регистрации пользователя
    """
    try:
        # валидация логина + эдж-кейсы с кавычками
        if not username or not username.strip() or (username == '""' or username == "''"):
            raise ValidationError("Имя пользователя не может быть пустым")

        # валидация длины пароля
        if len(password) < 4:
            raise ValidationError("Пароль должен быть не короче 4 символов")

        db = DatabaseManager()

        # проверка уникальности логина
        if db.find_user_by_username(username):
            raise ValidationError(f"Имя пользователя {username} уже занято")

        # создание пользователя
        user_id = db.get_next_user_id()
        user = User(user_id=user_id, username=username, password=password)

        # сохранение
        db.update_user(user.to_dict())

        # создание пустого портфеля
        portfolio = Portfolio(user_id=user_id)
        db.update_portfolio(portfolio.to_dict())

        return True, f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username <логин> --password <пароль>"

    except (ValidationError, Exception) as e:
        return False, f"Ошибка регистрации: {str(e)}"

@log_action("LOGIN")
def login_user(username, password):
    """Обрабатывает аутентификацию пользователя"""
    global _current_user, _current_portfolio

    try:
        db = DatabaseManager()
        # ищем пользователя
        user_data = utils.find_user_by_username(username)
        if not user_data:
            return False, f"Пользователь '{username}' не найден"

        # создаем экземпляр
        user = User.from_dict(user_data)

        # проверка пароля
        if not user.verify_password(password):
            return False, "Неверный пароль"

        # загружаем портфель
        portfolio_data = db.find_portfolio_by_user_id(user.user_id)
        if portfolio_data:
            portfolio = Portfolio.from_dict(portfolio_data)
        else:
            # создаем портфель если он отсутствует (just in case)
            portfolio = Portfolio(user_id=user.user_id)
            db.update_portfolio(portfolio.to_dict())

        # сохранение в сессию
        _current_user = user
        _current_portfolio = portfolio

        return True, f"Успешно: вы вошли как '{username}'"

    except Exception as e:
        return False, f"Ошибка входа: {str(e)}"

def get_current_user():
    """Возвращает пользователя по текущей сессии"""
    return _current_user

def get_current_portfolio():
    """Возвращает портфолио по текущей сессии"""
    return _current_portfolio

def is_authenticated():
    """Возвращает статус, аутентифицирован ли пользователь в текущей сессии"""
    return _current_user is not None

def require_authentication():
    """Запрашивает аутентификацию для выполнения команд"""
    if not is_authenticated():
        raise AuthenticationError("Ошибка: Сначала выполните login")


def show_portfolio(base_currency: str = 'USD'):
    """Показать портфель (без изменений, но с валидацией currency)"""
    try:
        require_authentication()

        base_currency = base_currency.upper()
        get_currency(base_currency)  # валидация

        portfolio = get_current_portfolio()
        user = get_current_user()

        wallets_dict = portfolio._wallets

        if not wallets_dict:
            return True, f"Портфель пользователя '{user.username}' пуст. Добавьте валюту командой buy"

        db = DatabaseManager()

        output = [f"Портфель пользователя '{user.username}' (база: {base_currency}):"]
        total_value = 0.0

        for currency_code, wallet in sorted(wallets_dict.items()):
            balance = wallet.balance

            if currency_code == base_currency:
                value_in_base = balance
            else:
                rate = db.get_rate(currency_code, base_currency)
                if rate is None:
                    output.append(f"- {currency_code}: {balance:.4f} → курс недоступен")
                    continue
                value_in_base = balance * rate

            total_value += value_in_base

            balance_str = f"{balance:.2f}" if balance >= 1 else f"{balance:.4f}"
            value_str = f"{value_in_base:,.2f}".replace(",", " ")
            output.append(f"- {currency_code}: {balance_str} → {value_str} {base_currency}")

        output.append("-" * 33)
        output.append(f"ИТОГО: {total_value:,.2f} {base_currency}".replace(",", " "))

        return True, "\n".join(output)

    except (AuthenticationError, CurrencyNotFoundError) as e:
        return False, str(e)
    except Exception as e:
        return False, f"Ошибка отображения портфеля: {str(e)}"

@log_action("BUY")
def buy_currency(currency_code: str, amount: float):
    """Обработка покупки фиатной или криптовалюты"""
    try:
        require_authentication()

        if not currency_code or not isinstance(amount, (int, float)) or (amount <= 0):
            raise ValidationError("Ошибка: 'amount' должен быть положительным числом")

        # валидация через валюты
        currency_code = currency_code.upper().strip()
        currency = get_currency(currency_code) # проброска CurrencyNotFoundError

        # чтобы нельзя было купить USD за USD (?)
        if currency_code == "USD":
            return False, "Нельзя купить USD за USD. Используйте другую валюту"

        portfolio = get_current_portfolio()
        db = DatabaseManager()
        settings = SettingsLoader()

        # получаем курс покупаемой валюты к USD
        rate = _get_rate_with_ttl(currency_code, "USD", db, settings)
        if not rate:
            raise ApiRequestError(f"Курс {currency_code} → USD недоступен")

        # рассчитываем стоимость в USD
        cost_in_usd = amount * rate

        # проверяем наличие USD кошелька и достаточность средств
        usd_wallet = portfolio.get_or_create_wallet("USD")
        if usd_wallet.balance < cost_in_usd:
            return InsufficientFundsError(
                available = usd_wallet.balance,
                required = cost_in_usd,
                currency_code = "USD"
            )

        # списываем USD
        usd_wallet.withdraw(cost_in_usd)

        # получаем или создаём кошелёк покупаемой валюты
        wallet = portfolio.get_or_create_wallet(currency_code)
        old_balance = wallet.balance
        wallet.deposit(amount)

        # сохраняем портфель
        db.update_portfolio(portfolio.to_dict())

        # формируем вывод
        output = []
        output.append(
            f"Покупка выполнена: {amount:.4f} {currency_code} {currency.get_display_info()}")
        output.append(f"Курс: {rate:.4f} USD/{currency_code}")
        output.append("Изменения в портфеле:")
        output.append(f"- {currency_code}: было {old_balance:.4f} → стало {wallet.balance:.4f}")
        output.append(f"- USD: списано {cost_in_usd:.4f} USD")
        output.append(f"Стоимость покупки: {cost_in_usd:.4f} USD")

        return True, "\n".join(output)

    except (AuthenticationError, CurrencyNotFoundError, ValidationError,
            InsufficientFundsError, ApiRequestError) as e:
        return False, str(e)
    except Exception as e:
        return False, f"Ошибка покупки: {str(e)}"

@log_action("SELL")
def sell_currency(currency_code: str, amount: float):
    """Обработка продажи фиатной или криптовалюты"""
    try:
        require_authentication()

        # валидация
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValidationError("'amount' должен быть положительным числом")

        currency_code = currency_code.upper().strip()
        currency = get_currency(currency_code)  # пробрасываем CurrencyNotFoundError

        if currency_code == "USD":
            raise ValidationError("Нельзя продать USD за USD")

        portfolio = get_current_portfolio()
        db = DatabaseManager()
        settings = SettingsLoader()

        # проверяем наличие кошелька
        wallet = portfolio.get_or_create_wallet(currency_code)
        if not wallet:
            supported = ", ".join(get_supported_currencies())
            raise ValidationError(
                f"Ошибка: у вас нет кошелька '{currency_code}'. "
                f"Поддерживаемые валюты: {supported}"
            )

        # получаем курс
        rate = _get_rate_with_ttl(currency_code, "USD", db, settings)
        if not rate:
            raise ApiRequestError(f"Курс {currency_code} → USD недоступен")

        revenue_in_usd = amount * rate

        # снимаем (бросает InsufficientFundsError)
        old_balance = wallet.balance
        wallet.withdraw(amount)

        # начисляем USD
        usd_wallet = portfolio.get_or_create_wallet("USD")
        old_usd = usd_wallet.balance
        usd_wallet.deposit(revenue_in_usd)

        # сохраняем
        db.update_portfolio(portfolio.to_dict())

        # формируем вывод
        output = []
        output.append(f"Продажа выполнена: {amount:.4f} {currency_code} ({currency.get_display_info()})")
        output.append(f"Курс: {rate:.2f} USD/{currency_code}")
        output.append("Изменения в портфеле:")
        output.append(f"- {currency_code}: было {old_balance:.4f} → стало {wallet.balance:.4f}")
        output.append(f"- USD: было {old_usd:.2f} → стало {usd_wallet.balance:.2f} USD")
        output.append(f"Выручка: {revenue_in_usd:.2f} USD")

        return True, "\n".join(output)

    except (AuthenticationError, CurrencyNotFoundError, ValidationError,
            InsufficientFundsError, ApiRequestError) as e:
        return False, str(e)
    except Exception as e:
        return False, f"Ошибка продажи: {str(e)}"

def get_exchange_rate(from_currency: str, to_currency: str):
    """Получение обменного курса"""
    try:
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        # валидация через иерархию валют
        from_curr = get_currency(from_currency)
        to_curr = get_currency(to_currency)

        # обрабатываем случай одинаковых валют
        if from_currency == to_currency:
            output = []
            output.append(f"Информация о валюте:")
            output.append(f"  {from_curr.get_display_info()}")
            output.append("")
            output.append(f"Курс {from_currency} → {to_currency}: 1.00000000")
            output.append(f"Обратный курс {to_currency} → {from_currency}: 1.00000000")
            output.append(f"Обновлено: not applicable")
            return True, "\n".join(output)

        db = DatabaseManager()
        settings = SettingsLoader()

        # получаем курс с TTL
        rate = _get_rate_with_ttl(from_currency, to_currency, db, settings)
        if not rate:
            raise ApiRequestError(
                f"Курс {from_currency} → {to_currency} недоступен. "
                f"Повторите попытку позже или выполните 'update-rates'"
            )

        # обратный курс
        reverse_rate = 1.0 / rate if rate != 0 else 0

        # получаем время обновления из кэша
        from valutatrade_hub.parser_service.storage import RatesStorage
        storage = RatesStorage()
        data = storage.get_all_rates()
        pairs = data.get("pairs", {})

        rate_key = f"{from_currency}_{to_currency}"
        reverse_key = f"{to_currency}_{from_currency}"

        updated_at = "неизвестно"
        if rate_key in pairs:
            updated_at = pairs[rate_key].get("updated_at", "неизвестно")
        elif reverse_key in pairs:
            updated_at = pairs[reverse_key].get("updated_at", "неизвестно")

        output = []
        output.append(f"Информация о валютах:")
        output.append(f"  От: {from_curr.get_display_info()}")
        output.append(f"  К:  {to_curr.get_display_info()}")
        output.append("")
        output.append(f"Курс {from_currency} → {to_currency}: {rate:.8f}")
        output.append(f"Обратный курс {to_currency} → {from_currency}: {reverse_rate:.8f}")
        output.append(f"Обновлено: {updated_at}")

        return True, "\n".join(output)

    except CurrencyNotFoundError as e:
        supported = ", ".join(get_supported_currencies())
        return False, f"{str(e)}\nПоддерживаемые валюты: {supported}"
    except ApiRequestError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Ошибка получения курса: {str(e)}"


def _get_rate_with_ttl(from_currency: str, to_currency: str, db: DatabaseManager, settings: SettingsLoader):
    """
    Получить курс с проверкой TTL (Time To Live).
    """
    # сначала пробуем через DatabaseManager
    rate = db.get_rate(from_currency, to_currency)

    if rate is not None:
        logger.debug(f"Курс {from_currency} → {to_currency} найден через DatabaseManager: {rate}")
        return rate

    # если не нашли через DatabaseManager пробуем напрямую из rates.json
    from valutatrade_hub.parser_service.storage import RatesStorage

    try:
        storage = RatesStorage(settings.get("RATES_FILE_PATH", "data/rates.json"))
        data = storage.get_all_rates()
        pairs = data.get("pairs", {})

        # прямой курс
        rate_key = f"{from_currency}_{to_currency}"
        if rate_key in pairs:
            rate_info = pairs[rate_key]
            rate_value = rate_info.get("rate")

            if rate_value:
                logger.debug(f"Курс {from_currency} → {to_currency} найден в кэше: {rate_value}")
                return float(rate_value)

        # обратный курс
        reverse_key = f"{to_currency}_{from_currency}"
        if reverse_key in pairs:
            rate_info = pairs[reverse_key]
            reverse_rate = rate_info.get("rate")

            if reverse_rate and reverse_rate != 0:
                direct_rate = 1.0 / float(reverse_rate)
                logger.debug(f"Курс {from_currency} → {to_currency} вычислен из обратного: {direct_rate}")
                return direct_rate

        logger.warning(f"Курс {from_currency} → {to_currency} не найден в кэше")
        return None

    except Exception as e:
        logger.error(f"Ошибка чтения курса из кэша: {e}")
        return None
