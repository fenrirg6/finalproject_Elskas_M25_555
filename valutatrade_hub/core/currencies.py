from abc import ABC, abstractmethod
from typing import Dict, Optional

class Currency(ABC):
    """
    Абстрактный базовый класс для всех типов валют.
    Определяет общий интерфейс для фиатных и криптовалют.
    """

    def __init__(self, code: str, name: str):
        # валидация кода
        if not code or not isinstance(code, str):
            raise ValueError("Код валюты должен быть непустой строкой")

        code = code.strip().upper()
        if len(code) < 2 or len(code) > 5:
            raise ValueError(f"Код валюты должен быть длиной 2-5 символов, получено: '{code}'")

        if " " in code:
            raise ValueError(f"Код валюты не может содержать пробелы: '{code}'")

        # валидация имени
        if not name or not isinstance(name, str):
            raise ValueError("Имя валюты должно быть непустой строкой")

        name = name.strip()
        if not name:
            raise ValueError("Имя валюты не может быть пустым")

        self.code = code
        self.name = name

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Получить строковое представление для UI/логов.
        Формат определяется в наследниках
        """
        pass

    def __str__(self) -> str:
        """Строковое представление"""
        return self.get_display_info()

    def __repr__(self) -> str:
        """Отладочное представление"""
        return f"{self.__class__.__name__}(code='{self.code}', name='{self.name}')"


class FiatCurrency(Currency):
    """
    Фиатная валюта
    """

    def __init__(self, code: str, name: str, issuing_country: str):
        """
        Инициализация фиатной валюты
        """
        super().__init__(code, name)

        if not issuing_country or not isinstance(issuing_country, str):
            raise ValueError("Страна эмиссии должна быть непустой строкой")

        self.issuing_country = issuing_country.strip()

    def get_display_info(self) -> str:
        """
        Форматированное представление фиатной валюты
        """
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """
    Криптовалюта
    """

    def __init__(self, code: str, name: str, algorithm: str, market_cap: Optional[float] = None):
        """
        Инициализация криптовалюты
        """
        super().__init__(code, name)

        if not algorithm or not isinstance(algorithm, str):
            raise ValueError("Алгоритм должен быть непустой строкой")

        self.algorithm = algorithm.strip()
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        """
        Форматированное представление криптовалюты
        """
        info = f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}"

        if self.market_cap is not None:
            info += f", MCAP: {self.market_cap:.2e}"

        info += ")"
        return info

# реестр валют
_CURRENCY_REGISTRY: Dict[str, Currency] = {
    # фиатные валюты
    "USD": FiatCurrency("USD", "US Dollar", "United States"),
    "EUR": FiatCurrency("EUR", "Euro", "Eurozone"),
    "RUB": FiatCurrency("RUB", "Russian Ruble", "Russian Federation"),
    "GBP": FiatCurrency("GBP", "British Pound", "United Kingdom"),
    "JPY": FiatCurrency("JPY", "Japanese Yen", "Japan"),
    "CNY": FiatCurrency("CNY", "Chinese Yuan", "China"),

    # криптовалюты
    "BTC": CryptoCurrency("BTC", "Bitcoin", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("ETH", "Ethereum", "Ethash", 4.5e11),
    "USDT": CryptoCurrency("USDT", "Tether", "Omni Layer", 8.3e10),
    "BNB": CryptoCurrency("BNB", "Binance Coin", "BFT", 7.2e10),
    "XRP": CryptoCurrency("XRP", "Ripple", "RPCA", 2.8e10),
}


def get_currency(code: str) -> Currency:
    """
    Получить объект валюты по коду (фабричный метод)
    """
    from valutatrade_hub.core.exceptions import CurrencyNotFoundError

    code = code.strip().upper()

    if code not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)

    return _CURRENCY_REGISTRY[code]


def register_currency(currency: Currency) -> None:
    """
    Зарегистрировать новую валюту в реестре
    """
    _CURRENCY_REGISTRY[currency.code] = currency


def get_supported_currencies() -> list[str]:
    """
    Получить список кодов поддерживаемых валют
    """
    return sorted(_CURRENCY_REGISTRY.keys())


def is_currency_supported(code: str) -> bool:
    """
    Проверить, поддерживается ли валюта
    """
    return code.strip().upper() in _CURRENCY_REGISTRY