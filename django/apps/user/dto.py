from dataclasses import dataclass


@dataclass
class JWTTokenDTO:
    """JWT Токен"""
    access: str
    refresh: str


@dataclass
class UserAuthorizationAttemptDTO:
    """Данные для авторизации пользователя"""
    login: str
    code: str
