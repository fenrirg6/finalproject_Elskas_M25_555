import json
from pathlib import Path
from typing import Any, Dict, Optional

class SingletonMeta(type):
    """
    Метакласс для реализации паттерна Singleton.
    Гарантирует, что класс будет иметь только один экземпляр.
    Потокобезопасная версия не требуется для однопоточного CLI приложения.
    """

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        """
        Переопределяет создание экземпляра класса.
        При первом вызове создаёт экземпляр и сохраняет его.
        При последующих вызовах возвращает сохранённый экземпляр.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class SettingsLoader(metaclass=SingletonMeta):
    """
    Singleton для загрузки и кеширования конфигурации приложения.
    Конфигурация загружается из файла config.json или использует значения по умолчанию.
    Гарантируется единственный экземпляр в приложении.
    """

    # значения по умолчанию
    DEFAULT_CONFIG = {
        # пути к данным
        "DATA_DIR": "data",
        "USERS_FILE": "data/users.json",
        "PORTFOLIOS_FILE": "data/portfolios.json",
        "RATES_FILE": "data/rates.json",

        # настройки курсов валют
        "RATES_TTL_SECONDS": 300,  # 5 минут
        "BASE_CURRENCY": "USD",

        # настройки логирования
        "LOG_DIR": "logs",
        "LOG_FILE": "logs/actions.log",
        "LOG_LEVEL": "INFO",
        "LOG_FORMAT": "%(asctime)s - %(levelname)s - %(message)s",
        "LOG_MAX_BYTES": 10485760,  # 10 MB
        "LOG_BACKUP_COUNT": 5,
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Инициализация загрузчика настроек.
        """
        # проверяем не была ли уже выполнена инициализация
        if hasattr(self, "_initialized"):
            return

        self._config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        self._config_path = Path(config_path) if config_path else Path("config.json")

        # загружаем конфигурацию из файла если он существует
        self._load_from_file()

        self._initialized = True

    def _load_from_file(self) -> None:
        """
        Загрузить конфигурацию из JSON файла.
        """
        if not self._config_path.exists():
            return

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                # обновляем только те ключи которые предоставлены
                self._config.update(user_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[WARNING] Не удалось загрузить конфигурацию из {self._config_path}: {e}")
            print("[WARNING] Используются настройки по умолчанию")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получить значение настройки по ключу.
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Установить значение настройки (в памяти, без сохранения в файл).
        """
        self._config[key] = value

    def reload(self) -> None:
        """
        Перезагрузить конфигурацию из файла.
        Сбрасывает все изменения, сделанные через set().
        """
        self._config = self.DEFAULT_CONFIG.copy()
        self._load_from_file()

    def save_to_file(self, path: Optional[Path] = None) -> None:
        """
        Сохранить текущую конфигурацию в файл.
        """
        save_path = path or self._config_path

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[ERROR] Не удалось сохранить конфигурацию в {save_path}: {e}")

    def get_all(self) -> Dict[str, Any]:
        """
        Получить всю конфигурацию.
        """
        return self._config.copy()

    def __repr__(self) -> str:
        """Отладочное представление"""
        return f"SettingsLoader(config_path='{self._config_path}', keys={len(self._config)})"