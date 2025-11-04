import json
from pathlib import Path
from typing import Any, List, Dict, Optional
from threading import Lock


class DatabaseManager(metaclass=type):
    """
    Singleton для управления JSON-хранилищем.
    Предоставляет унифицированный интерфейс для работы с users.json,
    portfolios.json и rates.json.
    """

    _instance: Optional['DatabaseManager'] = None
    _lock: Lock = Lock()

    def __new__(cls):
        """
        Реализация Singleton через __new__.
        """
        if cls._instance is None:
            with cls._lock:
                # double-checked locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Инициализация менеджера БД.
        """
        # проверяем, не была ли уже выполнена инициализация
        if hasattr(self, "_initialized"):
            return

        # импортируем настройки
        from valutatrade_hub.infra.settings import SettingsLoader
        settings = SettingsLoader()

        # инициализируем пути
        self.data_dir = Path(settings.get("DATA_DIR", "data"))
        self.users_file = Path(settings.get("USERS_FILE", "data/users.json"))
        self.portfolios_file = Path(settings.get("PORTFOLIOS_FILE", "data/portfolios.json"))
        self.rates_file = Path(settings.get("RATES_FILE", "data/rates.json"))

        # кеш для минимизации чтения с диска
        self._cache: Dict[str, Any] = {}
        self._cache_enabled = True

        # создаем директорию данных
        self._ensure_data_directory()

        self._initialized = True

    def _ensure_data_directory(self) -> None:
        """Создать директорию для данных, если она не существует"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _load_json(self, file_path: Path, default: Any = None) -> Any:
        """
        Безопасная загрузка JSON файла.
        """
        # проверяем кеш
        cache_key = str(file_path)
        if self._cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        if not file_path.exists():
            result = default if default is not None else []
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content.strip():
                        result = default if default is not None else []
                    else:
                        result = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"[WARNING] Ошибка парсинга JSON в {file_path}: {e}")
                result = default if default is not None else []
            except Exception as e:
                print(f"[WARNING] Ошибка чтения {file_path}: {e}")
                result = default if default is not None else []

        # кешируем результат
        if self._cache_enabled:
            self._cache[cache_key] = result

        return result

    def _save_json(self, file_path: Path, data: Any) -> bool:
        """
        Безопасное сохранение в JSON файл.
        """
        self._ensure_data_directory()

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # обновляем кеш
            if self._cache_enabled:
                self._cache[str(file_path)] = data

            return True
        except Exception as e:
            print(f"[ERROR] Не удалось сохранить {file_path}: {e}")
            return False

    def invalidate_cache(self, file_path: Optional[Path] = None) -> None:
        """
        Сбросить кеш.
        """
        if file_path:
            cache_key = str(file_path)
            if cache_key in self._cache:
                del self._cache[cache_key]
        else:
            self._cache.clear()

    # методы для работы с пользователями
    def load_users(self) -> List[dict]:
        """Загрузить всех пользователей"""
        return self._load_json(self.users_file, default=[])

    def save_users(self, users: List[dict]) -> bool:
        """Сохранить список пользователей"""
        return self._save_json(self.users_file, users)

    def find_user_by_username(self, username: str) -> Optional[dict]:
        """Найти пользователя по имени"""
        users = self.load_users()
        for user in users:
            if user.get("username") == username:
                return user
        return None

    def find_user_by_id(self, user_id: int) -> Optional[dict]:
        """Найти пользователя по ID"""
        users = self.load_users()
        for user in users:
            if user.get("user_id") == user_id:
                return user
        return None

    def update_user(self, user_data: dict) -> bool:
        """
        Обновить или добавить пользователя.
        """
        users = self.load_users()

        # ищем существующего пользователя
        found = False
        for i, user in enumerate(users):
            if user.get("user_id") == user_data.get("user_id"):
                users[i] = user_data
                found = True
                break

        # если не найден - добавляем
        if not found:
            users.append(user_data)

        return self.save_users(users)

    def get_next_user_id(self) -> int:
        """Получить следующий свободный ID пользователя"""
        users = self.load_users()
        if not users:
            return 1
        return max(user.get("user_id", 0) for user in users) + 1

    # Методы для работы с портфелями

    def load_portfolios(self) -> List[dict]:
        """Загрузить все портфели"""
        return self._load_json(self.portfolios_file, default=[])

    def save_portfolios(self, portfolios: List[dict]) -> bool:
        """Сохранить список портфелей"""
        return self._save_json(self.portfolios_file, portfolios)

    def find_portfolio_by_user_id(self, user_id: int) -> Optional[dict]:
        """Найти портфель по ID пользователя"""
        portfolios = self.load_portfolios()
        for portfolio in portfolios:
            if portfolio.get("user_id") == user_id:
                return portfolio
        return None

    def update_portfolio(self, portfolio_data: dict) -> bool:
        """
        Обновить или добавить портфель.
        """
        portfolios = self.load_portfolios()

        # ищем существующий портфель
        found = False
        for i, portfolio in enumerate(portfolios):
            if portfolio.get("user_id") == portfolio_data.get("user_id"):
                portfolios[i] = portfolio_data
                found = True
                break

        # если не найден - добавляем
        if not found:
            portfolios.append(portfolio_data)

        return self.save_portfolios(portfolios)

    # Методы для работы с курсами валют
    def load_rates(self) -> dict:
        """Загрузить курсы валют"""
        return self._load_json(self.rates_file, default={})

    def save_rates(self, rates: dict) -> bool:
        """Сохранить курсы валют"""
        return self._save_json(self.rates_file, rates)

    def get_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Получить курс конвертации.
        """
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        if from_currency == to_currency:
            return 1.0

        rates = self.load_rates()

        # прямой курс
        rate_key = f"{from_currency}_{to_currency}"
        if rate_key in rates:
            return rates[rate_key].get("rate")

        # обратный курс
        reverse_key = f"{to_currency}_{from_currency}"
        if reverse_key in rates:
            reverse_rate = rates[reverse_key].get("rate")
            if reverse_rate and reverse_rate != 0:
                return 1.0 / reverse_rate

        return None

    def update_rate(self, from_currency: str, to_currency: str, rate: float) -> bool:
        """
        Обновить курс валюты.
        """
        from datetime import datetime

        rates = self.load_rates()

        rate_key = f"{from_currency.upper()}_{to_currency.upper()}"
        rates[rate_key] = {
            "rate": rate,
            "updated_at": datetime.now().isoformat()
        }

        rates["last_refresh"] = datetime.now().isoformat()

        return self.save_rates(rates)

    def __repr__(self) -> str:
        """Отладочное представление"""
        return f"DatabaseManager(data_dir='{self.data_dir}')"