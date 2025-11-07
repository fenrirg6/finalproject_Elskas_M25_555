import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import (
    BaseApiClient,
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig, get_parser_config
from valutatrade_hub.parser_service.storage import HistoryStorage, RatesStorage

logger = logging.getLogger("valutatrade_hub.parser")


class RatesUpdater:
    """
    Координатор обновления курсов валют.
    Опрашивает все API-клиенты, объединяет данные и сохраняет в хранилище
    """

    def __init__(self,
                 config: Optional[ParserConfig] = None,
                 clients: Optional[List[BaseApiClient]] = None,
                 rates_storage: Optional[RatesStorage] = None,
                 history_storage: Optional[HistoryStorage] = None):
        """
        Инициализация апдейтера
        """
        self.config = config or get_parser_config()

        # инициализация клиентов
        if clients is None:
            self.clients = [
                CoinGeckoClient(self.config),
                ExchangeRateApiClient(self.config)
            ]
        else:
            self.clients = clients

        # инициализация хранилищ
        self.rates_storage = rates_storage or RatesStorage(
            self.config.RATES_FILE_PATH
        )
        self.history_storage = history_storage or HistoryStorage(
            self.config.HISTORY_FILE_PATH
        )

        logger.info(f"RatesUpdater инициализирован с {len(self.clients)} клиентами")

    def run_update(self, source_filter: Optional[str] = None) -> Dict[str, any]:
        """
        Выполнить обновление курсов.
        """
        logger.info("=" * 70)
        logger.info("Начинается обновление курсов валют")
        logger.info(f"Время: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 70)

        start_time = datetime.now(timezone.utc)
        all_rates = {}
        errors = []
        stats_by_source = {}

        # опрашиваем каждый клиент
        for client in self.clients:
            source_name = client.get_source_name()

            # применяем фильтр источника
            if source_filter:
                if (source_filter.lower() == "coingecko" and
                        "CoinGecko" not in source_name):
                    continue
                if (source_filter.lower() == "exchangerate" and
                        "ExchangeRate" not in source_name):
                    continue

            try:
                logger.info(f"Запрос к {source_name}...")

                # получаем курсы
                rates = client.fetch_rates()

                if not rates:
                    logger.warning(f"{source_name}: получено 0 курсов")
                    stats_by_source[source_name] = 0
                    continue

                # сохраняем в кэш
                self.rates_storage.update_rates(rates, source_name)

                # сохраняем в историю
                self._save_to_history(rates, source_name)

                # объединяем с общим результатом
                all_rates.update(rates)

                stats_by_source[source_name] = len(rates)
                logger.info(f"{source_name}: OK ({len(rates)} курсов)")

            except ApiRequestError as e:
                error_msg = f"{source_name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                stats_by_source[source_name] = 0

            except Exception as e:
                error_msg = f"{source_name}: Неожиданная ошибка: {str(e)}"
                logger.exception(error_msg)
                errors.append(error_msg)
                stats_by_source[source_name] = 0

        # подсчитываем статистику
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        success = len(errors) == 0

        logger.info("=" * 70)
        logger.info(f"Обновление завершено за {duration:.2f}с")
        logger.info(f"Всего курсов обновлено: {len(all_rates)}")
        logger.info(f"По источникам: {stats_by_source}")
        if errors:
            logger.warning(f"Ошибок: {len(errors)}")
            for error in errors:
                logger.warning(f"  - {error}")
        logger.info("=" * 70)

        return {
            "success": success,
            "total_rates": len(all_rates),
            "by_source": stats_by_source,
            "errors": errors,
            "duration": duration
        }

    def _save_to_history(self, rates: Dict[str, float], source: str):
        """
        Сохранить курсы в историю
        """
        for pair_key, rate in rates.items():
            # разбираем ключ пары
            parts = pair_key.split("_")
            if len(parts) != 2:
                logger.warning(f"Некорректный ключ пары: {pair_key}")
                continue

            from_currency, to_currency = parts

            # добавляем в историю
            self.history_storage.add_record(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=rate,
                source=source,
                meta={
                    "update_method": "automatic",
                    "pair_key": pair_key
                }
            )

    def close(self):
        """Закрыть все соединения"""
        for client in self.clients:
            if hasattr(client, "close"):
                client.close()

    def __enter__(self):
        """Поддержка with"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие при выходе"""
        self.close()
