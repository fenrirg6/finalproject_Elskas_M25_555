import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from threading import Lock


logger = logging.getLogger("valutatrade_hub.parser")


class RatesStorage:
    """
    Хранилище для кэша курсов валют (rates.json)
    """

    def __init__(self, file_path: str = "data/rates.json"):
        """
        Инициализация хранилища кэша
        """
        self.file_path = Path(file_path)
        self._lock = Lock()
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Создать файл и директорию, если они не существуют"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self._write_data({"pairs": {}, "last_refresh": None})

    def _read_data(self) -> dict:
        """
        Прочитать данные из файла.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Файл {self.file_path} повреждён, создаём новый")
            return {"pairs": {}, "last_refresh": None}
        except Exception as e:
            logger.error(f"Ошибка чтения {self.file_path}: {e}")
            return {"pairs": {}, "last_refresh": None}

    def _write_data(self, data: dict):
        """
        Записать данные в файл атомарно
        """
        # атомарная запись через временный файл
        temp_path = self.file_path.with_suffix('.tmp')

        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # атомарная замена
            temp_path.replace(self.file_path)

        except Exception as e:
            logger.error(f"Ошибка записи {self.file_path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise

    def update_rates(self, rates: Dict[str, float], source: str):
        """
        Обновить курсы в кэше
        """
        with self._lock:
            data = self._read_data()
            pairs = data.get("pairs", {})

            timestamp = datetime.now().isoformat() + "Z"

            # обновляем каждую пару
            for pair_key, rate in rates.items():
                pairs[pair_key] = {
                    "rate": rate,
                    "updated_at": timestamp,
                    "source": source
                }

            # обновляем метку последнего обновления
            data["pairs"] = pairs
            data["last_refresh"] = timestamp

            self._write_data(data)

            logger.info(
                f"Обновлено {len(rates)} курсов в кэше "
                f"(источник: {source}, время: {timestamp})"
            )

    def get_all_rates(self) -> dict:
        """
        Получить все курсы из кэша
        """
        with self._lock:
            return self._read_data()

    def get_rate(self, from_currency: str, to_currency: str) -> Optional[Dict]:
        """
        Получить конкретный курс из кэша.
        """
        with self._lock:
            data = self._read_data()
            pairs = data.get("pairs", {})

            pair_key = f"{from_currency}_{to_currency}"
            return pairs.get(pair_key)

    def clear_cache(self):
        """Очистить кэш"""
        with self._lock:
            self._write_data({"pairs": {}, "last_refresh": None})
            logger.info("Кэш очищен")


class HistoryStorage:
    """
    Хранилище исторических данных (exchange_rates.json).
    Это полный журнал всех измерений курсов с уникальными ID.
    Формат: список объектов с полями id, from_currency, to_currency, rate, timestamp, source, meta
    """

    def __init__(self, file_path: str = "data/exchange_rates.json"):
        """
        Инициализация хранилища истории.
        """
        self.file_path = Path(file_path)
        self._lock = Lock()
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Создать файл и директорию, если они не существуют"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self._write_data([])

    def _read_data(self) -> List[dict]:
        """
        Прочитать историю из файла.
        """
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return []
                return json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"Файл {self.file_path} поврежден, создаем новый")
            return []
        except Exception as e:
            logger.error(f"Ошибка чтения {self.file_path}: {e}")
            return []

    def _write_data(self, data: List[dict]):
        """
        Записать историю в файл атомарно.
        """
        temp_path = self.file_path.with_suffix(".tmp")

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            temp_path.replace(self.file_path)

        except Exception as e:
            logger.error(f"Ошибка записи {self.file_path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise

    def add_record(self, from_currency: str, to_currency: str,
                   rate: float, source: str, meta: Optional[dict] = None):
        """
        Добавить запись в историю
        """
        with self._lock:
            history = self._read_data()

            # генерируем timestamp и ID
            timestamp = datetime.now().isoformat() + "Z"
            record_id = f"{from_currency}_{to_currency}_{timestamp}"

            # создаем запись
            record = {
                "id": record_id,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": rate,
                "timestamp": timestamp,
                "source": source,
                "meta": meta or {}
            }

            # проверяем уникальность ID (на всякий случай)
            if any(r.get("id") == record_id for r in history):
                logger.warning(f"Запись с ID {record_id} уже существует, пропускаем")
                return

            # добавляем запись
            history.append(record)

            # ограничиваем размер истории
            history = self._cleanup_old_records(history, max_per_pair=1000)

            self._write_data(history)

            logger.debug(f"Добавлена запись в историю: {record_id}")

    def add_records_batch(self, records: List[dict]):
        """
        Добавить несколько записей за раз батчами (может быть эффективнее на больших объемах)
        """
        with self._lock:
            history = self._read_data()

            for record in records:
                # проверяем уникальность ID
                record_id = record.get("id")
                if not record_id or any(r.get("id") == record_id for r in history):
                    continue

                history.append(record)

            history = self._cleanup_old_records(history, max_per_pair=1000)
            self._write_data(history)

            logger.info(f"Добавлено {len(records)} записей в историю")

    def _cleanup_old_records(self, history: List[dict], max_per_pair: int) -> List[dict]:
        """
        Удалить старые записи, оставляя только max_per_pair последних для каждой пары.
        """
        # группируем по парам
        pairs = {}
        for record in history:
            pair_key = f"{record['from_currency']}_{record['to_currency']}"
            if pair_key not in pairs:
                pairs[pair_key] = []
            pairs[pair_key].append(record)

        # оставляем только последние N записей для каждой пары
        cleaned = []
        for pair_key, records in pairs.items():
            # сортируем по timestamp в обратном порядке
            sorted_records = sorted(
                records,
                key=lambda r: r.get("timestamp", ""),
                reverse=True
            )
            cleaned.extend(sorted_records[:max_per_pair])

        return cleaned

    def get_history(self, from_currency: Optional[str] = None,
                   to_currency: Optional[str] = None,
                   limit: Optional[int] = None) -> List[dict]:
        """
        Получить историю с фильтрацией
        """
        with self._lock:
            history = self._read_data()

            # применяем фильтры
            if from_currency:
                history = [r for r in history if r.get("from_currency") == from_currency]

            if to_currency:
                history = [r for r in history if r.get("to_currency") == to_currency]

            # сортируем по времени (новые сначала)
            history.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

            # ограничиваем количество
            if limit:
                history = history[:limit]

            return history

    def clear_history(self):
        """Очистить всю историю"""
        with self._lock:
            self._write_data([])
            logger.info("История очищена")