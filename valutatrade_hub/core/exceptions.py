class ValutaTradeError(Exception):
    """Базовое исключение для всех ошибок приложения"""
    pass

class InsufficientFundsError(ValutaTradeError):
    """
    Исключение при недостаточности средств на кошельке
    """

    def __init__(self, available: float, required: float, currency_code: str):
        self.available = available
        self.required = required
        self.currency_code = currency_code

        message = (
            f"✗ Недостаточно средств: доступно {available:.4f} {currency_code}, "
            f"требуется {required:.4f} {currency_code}"
        )
        super().__init__(message)

class CurrencyNotFoundError(ValutaTradeError):
    """
    Исключение при попытке использовать неизвестную валюту
    """

    def __init__(self, currency_code: str):
        """
        Иницализация экземпляра
        """
        self.currency_code = currency_code
        message = f"✗ Неизвестная валюта '{currency_code}'"
        super().__init__(message)

class ApiRequestError(ValutaTradeError):
    """
    Исключение при сбое обращения к внешнему API
    """

    def __init__(self, reason: str):
        """
        Иницализация экземпляра
        """
        self.reason = reason
        message = f"✗ Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)

class AuthenticationError(ValutaTradeError):
    """Исключение при ошибках аутентификации"""
    pass

class ValidationError(ValutaTradeError):
    """Исключение при ошибках валидации данных"""
    pass