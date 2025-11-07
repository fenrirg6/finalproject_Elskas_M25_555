"""
Модуль parser_service - микросервис для получения курсов валют.

Включает:
- config: конфигурация API и параметров
- api_clients: клиенты для CoinGecko и ExchangeRate-API
- storage: работа с rates.json и exchange_rates.json
- updater: координатор обновления курсов
- scheduler: планировщик автоматического обновления
"""

from .api_clients import BaseApiClient, CoinGeckoClient, ExchangeRateApiClient
from .config import ParserConfig, get_parser_config
from .scheduler import RatesScheduler
from .storage import HistoryStorage, RatesStorage
from .updater import RatesUpdater

__all__ = [
    'ParserConfig',
    'get_parser_config',
    'BaseApiClient',
    'CoinGeckoClient',
    'ExchangeRateApiClient',
    'RatesStorage',
    'HistoryStorage',
    'RatesUpdater',
    'RatesScheduler',
]
