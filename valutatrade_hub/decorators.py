import functools
from typing import Callable, Any
from datetime import datetime

def log_action(action_name: str = None, verbose: bool = False):
    """
    Декоратор для логирования доменных операций
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            from valutatrade_hub.logging_config import get_logger
            logger = get_logger("valutatrade_hub.actions")

            # определяем операцию
            operation = action_name or func.__name__.upper()

            # извлечение параметров для операции
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "action": operation,
                "function": func.__name__,
            }

            # добавление аргументов
            if args:
                log_data["function_args"] = str(args)
            if kwargs:
                # извлекаем важные параметры
                if "currency_code" in kwargs:
                    log_data["currency_code"] = kwargs["currency_code"]
                if "amount" in kwargs:
                    log_data["amount"] = kwargs["amount"]
                if "username" in kwargs:
                    log_data["username"] = kwargs["username"]

                log_data["function_kwargs"] = str(kwargs)

            try:
                # выполняем функцию
                result = func(*args, **kwargs)

                # логирование успеха
                log_data["result"] = "OK"

                # если кортеж - забираем результаты
                if isinstance(result, tuple) and len(result) >= 2:
                    success, message = result[0], result[1]
                    log_data["success"] = success
                    log_data["response_message"] = message[:100] if message else None  # обрезка длинных сообщений

                # формирование сообщения для лога
                log_message = f"{operation}"
                if "username" in log_data:
                    log_message += f" user='{log_data['username']}'"
                if "currency_code" in log_data:
                    log_message += f" currency='{log_data['currency_code']}'"
                if "amount" in log_data:
                    log_message += f" amount={log_data['amount']}"
                log_message += f" result={log_data['result']}"

                logger.info(log_message, extra=log_data)

                return result

            except Exception as e:
                # логирование ошибки
                log_data["result"] = "ERROR"
                log_data["error_type"] = type(e).__name__
                log_data["error_message"] = str(e)

                log_message = f"{operation}"
                if "username" in log_data:
                    log_message += f" user='{log_data['username']}'"
                if "currency_code" in log_data:
                    log_message += f" currency='{log_data['currency_code']}'"
                log_message += f" result=ERROR error={log_data['error_type']}: {log_data['error_message']}"

                logger.error(log_message, extra=log_data, exc_info=verbose)

                # пробрасываем дальше
                raise

        return wrapper

    return decorator

