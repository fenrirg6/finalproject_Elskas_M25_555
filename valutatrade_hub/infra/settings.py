import json
from pathlib import Path
from typing import Any, Dict, Optional


class SingletonMeta(type):
    """
    Метакласс для реализации паттерна Singleton.
    Гарантирует, что класс будет иметь только один экземпляр.
    Потокобезопасная версия не требуется для однопоточного CLI приложения
    """

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        """
        Переопределяет создание экземпляра класса.
        При первом вызове создает экземпляр и сохраняет его.
        При последующих вызовах возвращает сохраненный экземпляр
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class SettingsLoader(metaclass=SingletonMeta):
    """
    Singleton для загрузки и кеширования конфигурации приложения.
    Конфигурация загружается из файла config.json или использует значения по умолчанию.
    Гарантируется единственный экземпляр в приложении
    """

    # значения по умолчанию
    DEFAULT_CONFIG = {
        # пути к данным
        "DATA_DIR": "data",
        "USERS_FILE": "data/users.json",
        "PORTFOLIOS_FILE": "data/portfolios.json",
        "RATES_FILE": "data/rates.json",

        # настройки курсов валют
        "CACHE_TTL_SECONDS": 300,  # 5 минут
        "BASE_CURRENCY": "USD",

        # настройки логирования
        "LOG_DIR": "logs",
        "LOG_FILE": "logs/actions.log",
        "LOG_LEVEL": "DEBUG",
        "LOG_FORMAT": "%(asctime)s - %(levelname)s - %(message)s",
        "LOG_MAX_BYTES": 10485760,  # 10 MB
        "LOG_BACKUP_COUNT": 5,
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Инициализация загрузчика настроек
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
        Загрузить конфигурацию из JSON файла
        """
        # создание файла если его не существует
        if not self._config_path.exists():
            print(f"[INFO] Файл конфигурации не найден, создается: {self._config_path}")
            try:
                self._config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._config_path, "w", encoding="utf-8") as f:
                    json.dump(self.DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
                print(f"[INFO] Создан файл конфигурации по умолчанию:"
                      f"{self._config_path}")
            except IOError as e:
                print(f"[WARNING] Не удалось создать файл конфигурации: {e}")
            return

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                # обновляем только те ключи которые предоставлены
                self._config.update(user_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[WARNING] Не удалось загрузить конфигурацию"
                  f"из {self._config_path}: {e}")
            print("[WARNING] Используются настройки по умолчанию")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получить значение настройки по ключу
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Установить значение настройки (в памяти, без сохранения в файл)
        """
        self._config[key] = value

    def get_all(self) -> Dict[str, Any]:
        """
        Получить всю конфигурацию
        """
        return self._config.copy()

    def __repr__(self) -> str:
        """Отладочное представление"""
        return (f"SettingsLoader(config_path='{self._config_path}',"
                f"keys={len(self._config)})")