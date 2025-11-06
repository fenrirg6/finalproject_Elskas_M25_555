import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig, get_parser_config

logger = logging.getLogger('valutatrade_hub.parser')


class BaseApiClient(ABC):
    """
    Абстрактный базовый класс для API-клиентов
    """

    def __init__(self, config: Optional[ParserConfig] = None):
        """Инициализация клиента"""
        self.config = config or get_parser_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.USER_AGENT
        })

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """
        Получить курсы валют из API

        Returns:
            Dict[str, float]: словарь курсов в формате {"BTC_USD": 59337.21, ...}
        """
        pass  # абстрактный метод БЕЗ реализации

    @abstractmethod
    def get_source_name(self) -> str:
        """Получить название источника данных"""
        pass

    def _make_request(self, url: str, retries: int = None) -> requests.Response:
        """Выполнить HTTP-запрос с повторными попытками"""
        retries = retries if retries is not None else self.config.MAX_RETRIES
        last_exception = None

        for attempt in range(1, retries + 1):
            try:
                logger.debug(f"Запрос к {url} (попытка {attempt}/{retries})")

                response = self.session.get(
                    url,
                    timeout=self.config.REQUEST_TIMEOUT
                )

                if response.status_code == 200:
                    logger.debug(f"Успешный ответ от {url}")
                    return response
                elif response.status_code == 429:
                    raise ApiRequestError(
                        "Превышен лимит запросов (429). Попробуйте позже"
                    )
                elif response.status_code == 401:
                    raise ApiRequestError(
                        "Неверный API ключ (401). Проверьте EXCHANGERATE_API_KEY"
                    )
                else:
                    raise ApiRequestError(
                        f"HTTP {response.status_code}: {response.text[:100]}"
                    )

            except requests.exceptions.Timeout as e:
                last_exception = ApiRequestError(
                    f"Превышено время ожидания ({self.config.REQUEST_TIMEOUT}s)"
                )
                logger.warning(f"Таймаут при запросе к {url}: {e}")

            except requests.exceptions.ConnectionError as e:
                last_exception = ApiRequestError(
                    "Ошибка подключения. Проверьте интернет-соединение"
                )
                logger.warning(f"Ошибка подключения к {url}: {e}")

            except requests.exceptions.RequestException as e:
                last_exception = ApiRequestError(f"Ошибка запроса: {str(e)}")
                logger.warning(f"Ошибка при запросе к {url}: {e}")

            except ApiRequestError:
                raise

            if attempt < retries:
                time.sleep(self.config.RETRY_DELAY)

        raise last_exception or ApiRequestError("Все попытки запроса исчерпаны")

    def close(self):
        """Закрыть сессию"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class CoinGeckoClient(BaseApiClient):
    """Клиент для получения курсов криптовалют из CoinGecko API"""

    def get_source_name(self) -> str:
        return "CoinGecko"

    def fetch_rates(self) -> Dict[str, float]:
        """Получить курсы криптовалют из CoinGecko"""
        try:
            url = self.config.get_coingecko_url()
            logger.info(f"Запрос к CoinGecko: {len(self.config.CRYPTO_CURRENCIES)} валют")

            response = self._make_request(url)
            data = response.json()

            rates = {}

            for crypto_id, values in data.items():
                try:
                    ticker = self.config.get_ticker_by_id(crypto_id)
                    usd_key = self.config.BASE_CURRENCY.lower()

                    if usd_key not in values:
                        logger.warning(f"Курс для {crypto_id} не содержит {usd_key}")
                        continue

                    rate = values[usd_key]

                    if not isinstance(rate, (int, float)) or rate <= 0:
                        logger.warning(f"Некорректный курс для {crypto_id}: {rate}")
                        continue

                    rate_key = f"{ticker}_{self.config.BASE_CURRENCY}"
                    rates[rate_key] = float(rate)

                except ValueError:
                    logger.warning(f"Неизвестный ID криптовалюты: {crypto_id}")
                    continue
                except KeyError as e:
                    logger.warning(f"Отсутствует ключ {e} для {crypto_id}")
                    continue

            logger.info(f"CoinGecko: успешно получено {len(rates)} курсов")
            return rates

        except ApiRequestError:
            raise
        except Exception as e:
            raise ApiRequestError(f"Ошибка при парсинге ответа CoinGecko: {str(e)}")


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для получения курсов фиатных валют из ExchangeRate-API"""

    def get_source_name(self) -> str:
        return "ExchangeRate-API"

    def fetch_rates(self) -> Dict[str, float]:
        """
        Получить курсы фиатных валют из ExchangeRate-API
        """
        try:
            url = self.config.get_exchangerate_url()
            logger.info(f"Запрос к ExchangeRate-API: база {self.config.BASE_CURRENCY}")

            response = self._make_request(url)
            data = response.json()

            # проверяем статус
            if data.get("result") != "success":
                error_type = data.get("error-type", "unknown")
                raise ApiRequestError(f"ExchangeRate-API вернул ошибку: {error_type}")

            raw_rates = data.get("conversion_rates") or data.get("rates") or {}

            if not raw_rates:
                raise ApiRequestError(
                    f"ExchangeRate-API вернул пустой список курсов. "
                    f"Ключи ответа: {list(data.keys())}"
                )

            # преобразуем в стандартный формат
            rates = {}
            matched = []

            for currency_code, rate in raw_rates.items():
                if currency_code not in self.config.FIAT_CURRENCIES:
                    continue

                matched.append(currency_code)

                if not isinstance(rate, (int, float)) or rate <= 0:
                    logger.warning(f"Некорректный курс для {currency_code}: {rate}")
                    continue

                # ExchangeRate-API: FROM USD TO currency
                # FROM currency TO USD
                rate_key = f"{currency_code}_{self.config.BASE_CURRENCY}"
                rates[rate_key] = 1.0 / float(rate)

                print(f"  ✓ {currency_code}: {rate} → {rate_key}: {rates[rate_key]:.8f}")

            if len(rates) == 0:
                raise ApiRequestError(
                    f"После фильтрации не осталось валют. "
                    f"Ищем: {self.config.FIAT_CURRENCIES}, "
                    f"Нашли: {matched}"
                )

            logger.info(f"ExchangeRate-API: успешно получено {len(rates)} курсов")
            return rates

        except ApiRequestError:
            raise
        except Exception as e:
            import traceback
            print(f"\n[ERROR] Исключение в fetch_rates:")
            print(traceback.format_exc())
            raise ApiRequestError(
                f"Ошибка при парсинге ответа ExchangeRate-API: {str(e)}"
            )
