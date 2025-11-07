import os
from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class ParserConfig:
    """
    Конфигурация Parser Service.
    Все чувствительные данные (API ключи) загружаются из переменных окружения.
    """
    # API Ключи из переменных окружения

    EXCHANGERATE_API_KEY: str = field(
        default_factory=lambda: os.getenv(
            "EXCHANGERATE_API_KEY",
            "demo"  # демо ключ для тестирования (ограниченный доступ)
        )
    )

    # эндпоинты внешних API

    # CoinGecko API (бесплатный без ключа)
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    # ExchangeRate-API (требует ключ)
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # валюты для отслеживания

    # базовая валюта (для всех запросов)
    BASE_CURRENCY: str = "USD"

    # фиатные валюты
    FIAT_CURRENCIES: Tuple[str, ...] = ("EUR", "GBP", "RUB", "JPY", "CNY")

    # криптовалюты (тикеры)
    CRYPTO_CURRENCIES: Tuple[str, ...] = ("BTC", "ETH", "SOL", "BNB", "XRP")

    # маппинг тикеров криптовалют на их ID в CoinGecko
    CRYPTO_ID_MAP: Dict[str, str] = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "BNB": "binancecoin",
        "XRP": "ripple",
        "USDT": "tether",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "DOT": "polkadot",
        "MATIC": "polygon",
    })

    # параметры запросов

    # таймаут ожидания ответа от API (секунды)
    REQUEST_TIMEOUT: int = 30

    # количество повторных попыток при ошибке
    MAX_RETRIES: int = 3

    # задержка между попытками (секунды)
    RETRY_DELAY: int = 2

    # user-agent для запросов
    USER_AGENT: str = "ValutaTradeHub/1.0"

    # пути к файлам

    # локальный кэш для Core Service (быстрый доступ)
    RATES_FILE_PATH: str = "data/rates.json"

    # исторические данные Parser Service (полный журнал)
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    # логи Parser Service
    PARSER_LOG_PATH: str = "logs/parser.log"

    # параметры кэширования

    # TTL для кэша = 5 минут (в секундах)
    CACHE_TTL_SECONDS: int = 300

    # максимальное количество исторических записей на пару валют
    MAX_HISTORY_PER_PAIR: int = 1000

    # параметры планировщика

    # интервал автоматического обновления = 5 минут (в секундах)
    UPDATE_INTERVAL_SECONDS: int = 300

    # запускать планировщик при старте
    AUTO_START_SCHEDULER: bool = False

    def __post_init__(self):
        """Валидация конфигурации после инициализации"""
        if self.EXCHANGERATE_API_KEY == "demo":
            import warnings
            warnings.warn(
                "Используется демо-ключ для ExchangeRate-API. "
                "Установите переменную окружения EXCHANGERATE_API_KEY "
                "для полного доступа",
                UserWarning
            )

        # проверяем, что все криптовалюты имеют маппинг
        for ticker in self.CRYPTO_CURRENCIES:
            if ticker not in self.CRYPTO_ID_MAP:
                raise ValueError(
                    f"Криптовалюта {ticker} не имеет маппинга в CRYPTO_ID_MAP"
                )

    def get_exchangerate_url(self, base: str = None) -> str:
        """
        Получить полный URL для ExchangeRate-API
        """
        base = base or self.BASE_CURRENCY
        return f"{self.EXCHANGERATE_API_URL}/{self.EXCHANGERATE_API_KEY}/latest/{base}"

    def get_coingecko_url(self, crypto_ids: list = None) -> str:
        """
        Получить полный URL для CoinGecko API
        """
        if crypto_ids is None:
            # используем все криптовалюты из конфига
            crypto_ids = [self.CRYPTO_ID_MAP[ticker] for
                          ticker in self.CRYPTO_CURRENCIES]

        ids_str = ",".join(crypto_ids)
        return (f"{self.COINGECKO_URL}?ids="
                f"{ids_str}&vs_currencies={self.BASE_CURRENCY.lower()}")

    def get_crypto_id(self, ticker: str) -> str:
        """
        Получить CoinGecko ID по тикеру
        """
        return self.CRYPTO_ID_MAP[ticker.upper()]

    def get_ticker_by_id(self, crypto_id: str) -> str:
        """
        Получить тикер по CoinGecko ID
        """
        for ticker, cg_id in self.CRYPTO_ID_MAP.items():
            if cg_id == crypto_id:
                return ticker
        raise ValueError(f"Тикер для ID '{crypto_id}' не найден")


# глобальный экземпляр конфигурации
_config_instance = None


def get_parser_config() -> ParserConfig:
    """
    Получить глобальный экземпляр конфигурации Parser Service
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ParserConfig()
    return _config_instance