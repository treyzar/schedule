"""
Модуль исключений приложения.
Предоставляет единую иерархию исключений для консистентной обработки ошибок.
"""

from typing import Dict, Optional, Any


class AppException(Exception):
    """
    Базовое исключение приложения.
    
    Пример использования:
        try:
            raise AppException("Что-то пошло не так", code="INTERNAL_ERROR")
        except AppException as e:
            logger.error(f"{e.code}: {e.message}")
    """
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code or self.__class__.__name__.upper()
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует исключение в dict для API ответа"""
        return {
            'error': self.code,
            'message': self.message,
            'details': self.details,
        }


# =============================================================================
# Credential Exceptions
# =============================================================================

class CredentialError(AppException):
    """Базовое исключение для ошибок credentials"""
    code = "CREDENTIAL_ERROR"


class CredentialNotFoundError(CredentialError):
    """Credentials не найдены"""
    code = "CREDENTIAL_NOT_FOUND"
    
    def __init__(self, service: str, user_id: Optional[str] = None):
        super().__init__(
            message=f"Credentials для сервиса '{service}' не найдены",
            code=self.code,
            details={'service': service, 'user_id': user_id}
        )


class CredentialExpiredError(CredentialError):
    """Credentials истекли и не могут быть обновлены"""
    code = "CREDENTIAL_EXPIRED"
    
    def __init__(self, service: str, can_refresh: bool = False):
        if can_refresh:
            message = f"Credentials для сервиса '{service}' истекли, но могут быть обновлены"
        else:
            message = f"Credentials для сервиса '{service}' истекли и требуют повторной авторизации"
        
        super().__init__(
            message=message,
            code=self.code,
            details={'service': service, 'can_refresh': can_refresh}
        )


class CredentialInvalidError(CredentialError):
    """Credentials невалидны"""
    code = "CREDENTIAL_INVALID"
    
    def __init__(self, service: str, reason: str):
        super().__init__(
            message=f"Credentials для сервиса '{service}' невалидны: {reason}",
            code=self.code,
            details={'service': service, 'reason': reason}
        )


class CredentialEncryptionError(CredentialError):
    """Ошибка шифрования/дешифрования credentials"""
    code = "CREDENTIAL_ENCRYPTION_ERROR"


# =============================================================================
# External Service Exceptions
# =============================================================================

class ExternalServiceError(AppException):
    """
    Базовое исключение для ошибок внешних сервисов.
    
    Пример использования:
        raise ExternalServiceError("google_calendar", "API unavailable", status_code=503)
    """
    
    def __init__(
        self, 
        service: str, 
        message: str, 
        status_code: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code=f"{service.upper()}_ERROR",
            details={
                'service': service,
                'status_code': status_code,
            }
        )
        self.original_error = original_error


class ServiceUnavailableError(ExternalServiceError):
    """Сервис недоступен"""
    
    def __init__(self, service: str, message: str = "Сервис временно недоступен"):
        super().__init__(
            service=service,
            message=message,
            status_code=503
        )


class ServiceTimeoutError(ExternalServiceError):
    """Превышено время ожидания ответа от сервиса"""
    
    def __init__(self, service: str, timeout: int):
        super().__init__(
            service=service,
            message=f"Превышено время ожидания ответа от сервиса ({timeout}с)",
            status_code=504,
            details={'service': service, 'timeout': timeout}
        )


class ServiceRateLimitError(ExternalServiceError):
    """Превышен лимит запросов к сервису"""
    
    def __init__(self, service: str, retry_after: Optional[int] = None):
        super().__init__(
            service=service,
            message="Превышен лимит запросов к сервису",
            status_code=429,
            details={'service': service, 'retry_after': retry_after}
        )


# =============================================================================
# Google Calendar Exceptions
# =============================================================================

class GoogleCalendarError(ExternalServiceError):
    """Базовое исключение для ошибок Google Calendar"""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            service="google_calendar",
            message=message,
            status_code=status_code,
            original_error=original_error
        )


class GoogleAuthError(GoogleCalendarError):
    """Ошибка аутентификации Google"""
    code = "GOOGLE_AUTH_ERROR"
    
    def __init__(self, message: str, needs_reauth: bool = False):
        super().__init__(message=message)
        self.details['needs_reauth'] = needs_reauth


class GoogleTokenExpiredError(GoogleAuthError):
    """Токен Google истек"""
    
    def __init__(self, can_refresh: bool = False):
        if can_refresh:
            message = "Токен Google истек, но может быть обновлён"
        else:
            message = "Токен Google истек и требует повторной авторизации"
        super().__init__(message=message, needs_reauth=not can_refresh)
        self.details['can_refresh'] = can_refresh


class GoogleCalendarNotFoundError(GoogleCalendarError):
    """Календарь не найден"""
    
    def __init__(self, calendar_id: str):
        super().__init__(
            message=f"Календарь '{calendar_id}' не найден",
            status_code=404,
            details={'calendar_id': calendar_id}
        )


class GoogleEventNotFoundError(GoogleCalendarError):
    """Событие не найдено"""
    
    def __init__(self, event_id: str):
        super().__init__(
            message=f"Событие '{event_id}' не найдено",
            status_code=404,
            details={'event_id': event_id}
        )


class GoogleEventConflictError(GoogleCalendarError):
    """Конфликт событий (например, overlapping time)"""
    
    def __init__(self, message: str, conflicting_events: Optional[list] = None):
        super().__init__(
            message=message,
            status_code=409,
            details={'conflicting_events': conflicting_events or []}
        )


# =============================================================================
# Skyeng Exceptions
# =============================================================================

class SkyengError(ExternalServiceError):
    """Базовое исключение для ошибок Skyeng"""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            service="skyeng",
            message=message,
            status_code=status_code,
            original_error=original_error
        )


class SkyengAuthError(SkyengError):
    """Ошибка аутентификации Skyeng"""
    
    def __init__(self, message: str = "Ошибка аутентификации Skyeng"):
        super().__init__(message=message)


class SkyengInvalidCredentialsError(SkyengAuthError):
    """Неверный логин или пароль"""
    
    def __init__(self, message: str = "Неверный логин или пароль"):
        super().__init__(message=message)


class SkyengTokenExpiredError(SkyengAuthError):
    """Токен Skyeng истек"""
    
    def __init__(self, can_refresh: bool = False):
        if can_refresh:
            message = "Токен Skyeng истек, но может быть обновлён"
        else:
            message = "Токен Skyeng истек и требует повторной авторизации"
        super().__init__(message=message)
        self.details['can_refresh'] = can_refresh


class SkyengNetworkError(SkyengError):
    """Ошибка сети при запросе к Skyeng"""
    
    def __init__(self, message: str = "Ошибка сети при подключении к Skyeng"):
        super().__init__(message=message)


class SkyengParseError(SkyengError):
    """Ошибка парсинга данных Skyeng"""
    
    def __init__(self, message: str, element: Optional[str] = None):
        super().__init__(
            message=message,
            details={'element': element}
        )


# =============================================================================
# AI Exceptions
# =============================================================================

class AIError(AppException):
    """Базовое исключение для ошибок AI"""
    code = "AI_ERROR"


class AIUnavailableError(AIError):
    """AI сервис недоступен"""
    
    def __init__(self, service: str = "ollama"):
        super().__init__(
            message=f"AI сервис '{service}' недоступен",
            code="AI_UNAVAILABLE",
            details={'service': service}
        )


class AITimeoutError(AIError):
    """Превышено время ожидания ответа от AI"""
    
    def __init__(self, timeout: int):
        super().__init__(
            message=f"Превышено время ожидания ответа от AI ({timeout}с)",
            code="AI_TIMEOUT",
            details={'timeout': timeout}
        )


class AIParseError(AIError):
    """Ошибка парсинга ответа AI"""
    
    def __init__(self, message: str, raw_response: Optional[str] = None):
        super().__init__(
            message=message,
            code="AI_PARSE_ERROR",
            details={'raw_response': raw_response}
        )


class AIIntentParseError(AIParseError):
    """Ошибка парсинга намерения из ответа AI"""
    
    def __init__(self, message: str, raw_response: Optional[str] = None):
        super().__init__(
            message=f"Не удалось распарсить намерение: {message}",
            raw_response=raw_response
        )


# =============================================================================
# Validation Exceptions
# =============================================================================

class ValidationError(AppException):
    """Ошибка валидации входных данных"""
    code = "VALIDATION_ERROR"
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code=self.code,
            details={'field': field} if field else {}
        )


class MissingRequiredFieldError(ValidationError):
    """Отсутствует обязательное поле"""
    
    def __init__(self, field: str):
        super().__init__(
            message=f"Отсутствует обязательное поле: {field}",
            field=field
        )


class InvalidFormatError(ValidationError):
    """Неверный формат поля"""
    
    def __init__(self, field: str, expected_format: str):
        super().__init__(
            message=f"Неверный формат поля '{field}'. Ожидалось: {expected_format}",
            field=field,
            details={'field': field, 'expected_format': expected_format}
        )
