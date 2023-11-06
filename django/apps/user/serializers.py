from django.db import transaction
from rest_framework import serializers

from .models import AuthorizationCode, User


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


class RegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""
    consent_to_processing_of_personal_data = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'patronymic', 'email', 'dob', 'gender', 'status', 'about_me', 'avatar',
                  'consent_to_processing_of_personal_data')
        extra_kwargs = {f: {'required': True} for f in fields
                        if f not in ('patronymic', 'avatar')}

    def validate(self, attrs):
        if not attrs['consent_to_processing_of_personal_data']:
            raise serializers.ValidationError('Необходимо дать согласие на обработку персональных данных.')
        attrs.pop('consent_to_processing_of_personal_data')
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для данных пользователя"""

    class Meta:
        model = User
        fields = ('phone_number', 'first_name', 'last_name', 'patronymic', 'email', 'dob', 'gender', 'status',
                  'about_me', 'avatar')
        read_only_fields = fields
