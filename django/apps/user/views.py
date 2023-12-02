import os

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .dto import UserAuthorizationAttemptDTO
from .exceptions import AuthorizationError, RegistrationError
from .models import User
from .permissions import IsFullRegistered
from .serializers import AuthorizationSerializer, CreateOTPSerializer, RegistrationSerializer, MyUserSerializer, \
    RetrieveUserSerializer, JWTTokenSerializer
from .services import UserAuthorizationService, AuthorizationCodeService, UserService
from ..chat.services import ChatMessageService


@extend_schema_view(
    create_otp=extend_schema(
        summary='Создание одноразового кода (OTP)',
        request=CreateOTPSerializer,
        responses={201: None}
    ),
    authorization=extend_schema(
        summary='Получение токена авторизации',
        request=AuthorizationSerializer,
        responses={200: JWTTokenSerializer}
    ),
    registration=extend_schema(
        summary='Регистрация пользователя',
        request=RegistrationSerializer,
        responses={201: MyUserSerializer}
    ),
    show_me=extend_schema(
        summary='Получить данные пользователя',
        responses={200: MyUserSerializer}
    ),
    update_me=extend_schema(
        summary='Обновить данные пользователя',
        request=MyUserSerializer,
        responses={200: MyUserSerializer}
    ),
    retrieve=extend_schema(
        summary='Посмотреть профиль пользователя',
        responses={200: RetrieveUserSerializer}
    ),
)
class UserViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    """ViewSet для пользователей"""
    queryset = User.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        match self.action:
            case 'registration' | 'show_me' | 'update_me' | 'retrieve':
                return queryset.prefetch_related('social_links')
            case _:
                return queryset

    def get_serializer_class(self):
        match self.action:
            case'create_otp':
                return CreateOTPSerializer
            case 'authorization':
                return AuthorizationSerializer
            case 'registration':
                return RegistrationSerializer
            case 'show_me':
                return MyUserSerializer
            case 'update_me':
                return MyUserSerializer
            case 'retrieve':
                return RetrieveUserSerializer

    def get_permissions(self):
        match self.action:
            case 'create_otp' | 'authorization':
                self.permission_classes = (AllowAny,)
            case 'registration':
                self.permission_classes = (IsAuthenticated,)
            case _:
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
            return Response(JWTTokenSerializer(token).data, status=status.HTTP_200_OK)

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
            return Response(MyUserSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=False, url_path='show-me', url_name='show_me')
    def show_me(self, request):
        serializer = self.get_serializer(instance=request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['PUT'], detail=False, url_path='update-me', url_name='update_me')
    def update_me(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_service = UserService(request.user)
        user = user_service.update_user(**serializer.validated_data)
        return Response(MyUserSerializer(user).data, status=status.HTTP_200_OK)
