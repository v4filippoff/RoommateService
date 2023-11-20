from dataclasses import dataclass


@dataclass
class JWTTokenDTO:
    """JWT Токен"""
    access: str
    refresh: str
    is_registered: bool


@dataclass
class UserAuthorizationAttemptDTO:
    """Данные для авторизации пользователя"""
    login: str
    code: str
