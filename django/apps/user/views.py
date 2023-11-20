import os
from dataclasses import asdict

from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .dto import UserAuthorizationAttemptDTO
from .exceptions import AuthorizationError, RegistrationError
from .models import User
from .permissions import IsFullRegistered
from .serializers import AuthorizationSerializer, CreateOTPSerializer, RegistrationSerializer, UserSerializer
from .services import UserAuthorizationService, AuthorizationCodeService, UserService


@extend_schema_view(
    create_otp=extend_schema(
        summary='Создание одноразового кода (OTP)',
        request=CreateOTPSerializer,
        responses={204: None}
    ),
    authorization=extend_schema(
        summary='Получение токена авторизации',
        request=AuthorizationSerializer,
        responses={200: inline_serializer('authorization', {'access': serializers.CharField(),
                                                            'refresh': serializers.CharField(),
                                                            'is_registered': serializers.BooleanField()})}
    ),
    registration=extend_schema(
        summary='Регистрация пользователя',
        request=RegistrationSerializer,
        responses={201: UserSerializer}
    ),
    show_me=extend_schema(
        summary='Получить данные пользователя',
        responses={200: UserSerializer}
    ),
    update_me=extend_schema(
        summary='Обновить данные пользователя',
        request=UserSerializer,
        responses={200: UserSerializer}
    ),
)
class UserViewSet(viewsets.GenericViewSet):
    """ViewSet для пользователей"""
    queryset = User.objects.all()

    def get_serializer_class(self):
        match self.action:
            case'create_otp':
                return CreateOTPSerializer
            case 'authorization':
                return AuthorizationSerializer
            case 'registration':
                return RegistrationSerializer
            case 'show_me':
                return UserSerializer
            case 'update_me':
                return UserSerializer

    def get_permissions(self):
        if self.action in ('create_otp', 'authorization',):
            self.permission_classes = (AllowAny,)
        elif self.action in ('registration',):
            self.permission_classes = (IsAuthenticated,)
        else:
            self.permission_classes = (IsAuthenticated, IsFullRegistered)
        return [permission() for permission in self.permission_classes]

    @action(methods=['POST'], detail=False, url_path='create-otp', url_name='create_otp')
    def create_otp(self, request):
        """Создать одноразовый код (OTP)"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        authorization_code_service = AuthorizationCodeService(serializer.validated_data['login'])

        try:
            authorization_code = authorization_code_service.create()
        except AuthorizationError as exc:
            raise ValidationError(str(exc))

        if os.getenv('APP_DEBUG') == '0':
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(data=AuthorizationSerializer(authorization_code).data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='authorization', url_name='authorization')
    def authorization(self, request):
        """Авторизация по логину и OTP"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_authorization_attempt = UserAuthorizationAttemptDTO(login=serializer.validated_data['login'],
                                                                 code=serializer.validated_data['code'])
        try:
            authorization_service = UserAuthorizationService()
            token = authorization_service.authorization(user_authorization_attempt)
        except AuthorizationError as exc:
            raise ValidationError(str(exc))
        else:
            return Response(asdict(token), status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='registration', url_name='registration')
    def registration(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_login = request.user.get_username()
        try:
            user = UserService.registration(user_login=user_login, **serializer.validated_data)
        except RegistrationError as exc:
            raise ValidationError(str(exc))
        else:
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=False, url_path='show-me', url_name='show_me')
    def show_me(self, request):
        serializer = self.get_serializer(instance=request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['PATCH'], detail=False, url_path='update-me', url_name='update_me')
    def update_me(self, request):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user_service = UserService(request.user)
        user = user_service.update_user(**serializer.validated_data)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
