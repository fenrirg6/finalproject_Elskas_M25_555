import logging
import threading
from typing import Optional

from valutatrade_hub.parser_service.config import ParserConfig, get_parser_config
from valutatrade_hub.parser_service.updater import RatesUpdater

logger = logging.getLogger('valutatrade_hub.parser')


class RatesScheduler:
    """
    Планировщик периодического обновления курсов.
    """

    def __init__(self,
                 updater: Optional[RatesUpdater] = None,
                 config: Optional[ParserConfig] = None,
                 interval_seconds: Optional[int] = None):
        """
        Инициализация планировщика
        """
        self.config = config or get_parser_config()
        self.updater = updater or RatesUpdater(self.config)
        self.interval_seconds = interval_seconds or self.config.UPDATE_INTERVAL_SECONDS

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

        logger.info(
            f"RatesScheduler инициализирован "
            f"(интервал: {self.interval_seconds}с)"
        )

    def start(self):
        """Запустить планировщик в фоновом потоке"""
        if self._running:
            logger.warning("Планировщик уже запущен")
            return

        self._running = True
        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="RatesScheduler"
        )
        self._thread.start()

        logger.info("Планировщик запущен")

    def stop(self):
        """Остановить планировщик"""
        if not self._running:
            return

        logger.info("Останавливаем планировщик...")
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        self._running = False
        logger.info("Планировщик остановлен")

    def is_running(self) -> bool:
        """Проверить, запущен ли планировщик"""
        return self._running

    def _run_loop(self):
        """Основной цикл планировщика (выполняется в отдельном потоке)"""
        logger.info(f"Цикл планировщика запущен (интервал: {self.interval_seconds}с)")

        while not self._stop_event.is_set():
            try:
                # выполняем обновление
                logger.info("Плановое обновление курсов...")
                result = self.updater.run_update()

                if result["success"]:
                    logger.info(
                        f"Обновление успешно: {result['total_rates']} курсов"
                    )
                else:
                    logger.warning(
                        f"Обновление с ошибками: {len(result['errors'])} ошибок"
                    )

            except Exception as e:
                logger.exception(f"Ошибка в цикле планировщика: {e}")

            # ждем до следующего обновления с возможностью прерывания
            logger.info(f"Следующее обновление через {self.interval_seconds}с")
            self._stop_event.wait(self.interval_seconds)

        logger.info("Цикл планировщика завершен")

    def run_once(self):
        """Запустить обновление один раз (синхронно)"""
        return self.updater.run_update()

    def __enter__(self):
        """Поддержка context manager"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Остановка при выходе"""
        self.stop()
