import enum


class UserIdentifierType(enum.Enum):
    """Тип идентификации пользователя"""
    PHONE_NUMBER = 'phone_number'
    EMAIL = 'email'
    UNDEFINED = 'undefined'
