import random
import re
import string
from datetime import timedelta, datetime

import phonenumbers
from constance import config
from django.db import transaction
from django.utils import timezone
from phonenumbers import NumberParseException
from rest_framework_simplejwt.tokens import RefreshToken

from .dto import UserAuthorizationAttemptDTO, JWTTokenDTO
from .enums import UserIdentifierType
from .exceptions import AuthorizationError
from .models import AuthorizationCode, User, CodeAbstract
from ..message.dto import MessageDTO, MessageResultDTO
from ..message.enums import MessageType, MessageSendingStatus
from ..message.service import MessageSender, get_message_sender


class UserService:
    """Сервис для работы с пользователем"""

    def __init__(self, user: User):
        self._user = user

    @staticmethod
    @transaction.atomic
    def registration(user_login: str, **user_data) -> User:
        """Регистрация пользователя"""
        user_login_kwargs = {User.USERNAME_FIELD: user_login}
        user = User.objects.get(**user_login_kwargs)
        for field, value in user_data.items():
            setattr(user, field, value)
        user.save()

        if 'email' in user_data:
            message_service = UserMessageService(recipients=[user.email])
            message_service.send_notification_after_success_registration(user_name=user.get_short_name())

        return user

    @staticmethod
    def get_user_identifier_type_by_value(value: str) -> UserIdentifierType:
        """Получить тип идентификации пользователя по значению"""
        try:
            parsed_number = phonenumbers.parse(value, None)
            if phonenumbers.is_valid_number(parsed_number):
                return UserIdentifierType.PHONE_NUMBER
        except NumberParseException:
            pass

        if re.search(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            return UserIdentifierType.EMAIL

        return UserIdentifierType.UNDEFINED


class UserAuthorizationService:
    """Сервис для авторизации пользователя"""

    @transaction.atomic
    def authorization(self, user_authorization_attempt: UserAuthorizationAttemptDTO) -> JWTTokenDTO:
        """Авторизовать пользователя"""
        authorization_code_service = AuthorizationCodeService(user_authorization_attempt.login)
        authorization_code = authorization_code_service.validate(user_authorization_attempt.code)
        authorization_code_service.use(authorization_code)
        user_login_kwargs = {User.USERNAME_FIELD: user_authorization_attempt.login}
        user, _ = User.objects.get_or_create(**user_login_kwargs)
        refresh = RefreshToken.for_user(user)
        return JWTTokenDTO(access=str(refresh.access_token), refresh=str(refresh))


class AuthorizationCodeService:
    """Сервис для кода авторизации"""

    def __init__(self, login: str):
        self._login = login

    @transaction.atomic
    def create(self) -> AuthorizationCode:
        """Создать код для авторизации"""

        if not self._is_login_valid():
            raise AuthorizationError('Некорректный логин.')

        countdown = self._get_countdown()
        if countdown:
            raise AuthorizationError(f'Отправка кода для авторизации будет возможна через {countdown} секунд.')

        new_authorization_code = AuthorizationCode.objects.create(
            login=self._login,
            code=self._generate_code(),
            expiration_date=self._generate_expiration_date()
        )
        message_service = UserMessageService(recipients=[new_authorization_code.login])
        message_service.send_authorization_code(code=new_authorization_code.code)
        return new_authorization_code

    def use(self, authorization_code: AuthorizationCode) -> None:
        """Использовать код авторизации"""
        authorization_code.is_used = True
        authorization_code.save()

    def validate(self, code: str) -> AuthorizationCode:
        """Проверка, что пара логин-код существует, а так же код пригоден к использованию"""
        authorization_code = AuthorizationCode.objects.filter(login=self._login, code=code).first()

        if not authorization_code:
            raise AuthorizationError('Некорректный код.')
        elif authorization_code.is_used:
            raise AuthorizationError('Этот код уже был использован.')
        elif authorization_code.expiration_date <= timezone.now():
            raise AuthorizationError('Срок действия кода истек.')

        return authorization_code

    def _get_countdown(self) -> int:
        """Получить время в секундах, по истечении которого можно будет отправить код для авторизации.
        Если вернулось значение = 0, значит можно снова отправить код авторизации пользователю
        """
        authorization_code = AuthorizationCode.objects.filter(login=self._login).order_by('created_at').last()
        config_countdown = config.AUTHORIZATION_CODE_COUNTDOWN
        if authorization_code and authorization_code.created_at > timezone.now() - timedelta(minutes=config_countdown):
            countdown = authorization_code.created_at + timedelta(minutes=config_countdown) - timezone.now()
            return countdown.seconds
        else:
            return 0

    def _is_login_valid(self) -> bool:
        """Проверка валиден ли логин"""
        user_identifier_type = UserService.get_user_identifier_type_by_value(self._login)
        return (user_identifier_type == UserIdentifierType.PHONE_NUMBER and User.USERNAME_FIELD == 'phone_number' or
                user_identifier_type == UserIdentifierType.EMAIL and User.USERNAME_FIELD == 'email')

    def _generate_code(self) -> str:
        """Генерация самого кода"""
        return ''.join(random.choice(string.digits) for i in range(CodeAbstract.CODE_LENGTH))

    def _generate_expiration_date(self) -> datetime:
        """Генерация времени истечения токена"""
        return timezone.now() + timedelta(minutes=config.AUTHORIZATION_CODE_EXPIRES_IN)


class UserMessageService:
    """Сервис для отправки сообщений пользователю (SMS, email, звонок и тд.)

    recipient: Идентифицируемое значение пользователя, представленное в виде номера телефона, почты или другого варианта
    """
    user_identifier_to_message_types_map: dict[UserIdentifierType, MessageType] = {
        UserIdentifierType.PHONE_NUMBER: MessageType.SMS,
        UserIdentifierType.EMAIL: MessageType.EMAIL,
    }

    def __init__(self, recipients: list[str]):
        self._recipients = recipients

    def send_authorization_code(self, code: str) -> None:
        """Отправить код для авторизации"""
        message = f'Ваш код для авторизации: {code}'
        self._send_message(message)

    def send_notification_after_success_registration(self, user_name: str) -> None:
        message = f'{user_name.title()}, вы успешно зарегистрировались!'
        self._send_message(message)

    def _send_message(self, message_text: str) -> MessageResultDTO:
        """Отправить сообщение пользователю"""
        message = MessageDTO(
            content=message_text,
            recipients=self._recipients
        )
        message_sender = self._get_message_sender(message)
        if message_sender:
            return message_sender.send()
        else:
            return MessageResultDTO(status=MessageSendingStatus.OTHER, content='Отправитель сообщения не определен.')

    def _get_message_sender(self, message: MessageDTO) -> MessageSender | None:
        """Получить экземпляр для отправки сообщения пользователю"""
        message_type = self._get_message_type_by_recipients()
        if message_type:
            return get_message_sender(message_type, message)

    def _get_message_type_by_recipients(self) -> MessageType | None:
        """Получить тип сообщения для пользователя"""
        are_user_identifiers_unique = len(set(map(UserService.get_user_identifier_type_by_value, self._recipients))) <= 1
        if self._recipients and are_user_identifiers_unique:
            user_login_type = UserService.get_user_identifier_type_by_value(self._recipients[0])
            return self.user_identifier_to_message_types_map[user_login_type]
