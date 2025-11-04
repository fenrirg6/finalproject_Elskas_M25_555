import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    log_format: Optional[str] = None,
    max_bytes: int = 10485760,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Настроить систему логирования приложения.
    """
    # загружаем настройки
    from valutatrade_hub.infra.settings import SettingsLoader
    settings = SettingsLoader()

    # используем параметры из настроек, если не переданы явно
    log_file = log_file or settings.get("LOG_FILE", "logs/actions.log")
    log_level = log_level or settings.get("LOG_LEVEL", "INFO")
    log_format = log_format or settings.get(
        "LOG_FORMAT",
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    max_bytes = max_bytes or settings.get("LOG_MAX_BYTES", 10485760)
    backup_count = backup_count or settings.get('LOG_BACKUP_COUNT', 5)

    # создаём директорию для логов
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # получаем корневой логгер приложения
    logger = logging.getLogger("valutatrade_hub")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # очищаем существующие обработчики
    logger.handlers.clear()

    # создаём форматтер
    formatter = logging.Formatter(
        fmt=log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # обработчик для файла с ротацией
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # файл получает все сообщения
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # обработчик для консоли (только WARNING и выше)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # не пробрасываем в root logger
    logger.propagate = False

    logger.info("="*70)
    logger.info("Система логирования инициализирована")
    logger.info(f"Файл логов: {log_file}")
    logger.info(f"Уровень: {log_level}")
    logger.info("="*70)

    return logger


def get_logger(name: str = "valutatrade_hub") -> logging.Logger:
    """
    Получить логгер для модуля.
    """
    logger = logging.getLogger(name)

    # если логгер не настроен - настраиваем
    if not logger.handlers:
        setup_logging()

    return logger


# JSON формат логов
class JsonFormatter(logging.Formatter):
    """
    Форматтер для вывода логов в JSON формате.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в JSON"""
        import json
        from datetime import datetime

        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # добавляем дополнительные поля
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "username"):
            log_data["username"] = record.username
        if hasattr(record, "action"):
            log_data["action"] = record.action
        if hasattr(record, "currency_code"):
            log_data["currency_code"] = record.currency_code
        if hasattr(record, "amount"):
            log_data["amount"] = record.amount

        # добавляем информацию об исключении
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_json_logging(log_file: str = "logs/actions.json") -> logging.Logger:
    """
    Настроить логирование в JSON формате.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("valutatrade_hub.json")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=10485760,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)
    logger.propagate = False

    return logger