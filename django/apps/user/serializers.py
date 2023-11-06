from rest_framework import serializers

from .models import AuthorizationCode


class CreateAuthorizationCodeSerializer(serializers.ModelSerializer):
    """Сериализатор для генерации кода авторизации"""

    class Meta:
        model = AuthorizationCode
        fields = ('login',)


class AuthorizationSerializer(serializers.ModelSerializer):
    """Сериализатор для авторизации пользователя по логину и коду"""

    class Meta:
        model = AuthorizationCode
        fields = ('login', 'code')
