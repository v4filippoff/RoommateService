from datetime import date

from _decimal import Decimal
from django.utils import timezone
from rest_framework import serializers

from .models import AuthorizationCode, User, UserSocialLink
from ..review.services import ReviewService


class JWTTokenSerializer(serializers.Serializer):
    """Сериализатор для JWT Токена"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    is_registered = serializers.BooleanField()


class CreateOTPSerializer(serializers.ModelSerializer):
    """Сериализатор для генерации кода авторизации"""

    class Meta:
        model = AuthorizationCode
        fields = ('login',)


class AuthorizationSerializer(serializers.ModelSerializer):
    """Сериализатор для авторизации пользователя по логину и коду"""

    class Meta:
        model = AuthorizationCode
        fields = ('login', 'code')


class UserSocialLinkSerializer(serializers.ModelSerializer):
    """Сериализатор для ссылки на соц. сеть пользователя"""

    class Meta:
        model = UserSocialLink
        fields = ('user', 'type', 'url')
        read_only_fields = ('user',)


class RegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""
    social_links = UserSocialLinkSerializer(many=True, required=False)
    consent_to_processing_of_personal_data = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'patronymic', 'email', 'dob', 'gender', 'status', 'about_me', 'avatar',
                  'social_links', 'consent_to_processing_of_personal_data')
        extra_kwargs = {f: {'required': True} for f in fields
                        if f not in ('patronymic', 'avatar', 'social_links')}

    def validate(self, attrs):
        if not attrs['consent_to_processing_of_personal_data']:
            raise serializers.ValidationError('Необходимо дать согласие на обработку персональных данных.')
        attrs.pop('consent_to_processing_of_personal_data')
        attrs['datetime_consent_to_processing_of_personal_data'] = timezone.now()
        return attrs

    def validate_dob(self, value: date):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise serializers.ValidationError('Регистрация доступна только при достижении 18 лет.')
        return value

    def validate_avatar(self, value):
        # Максимальный допустимый размер файла в байтах (10 МБ)
        max_size = 10 * 1024 * 1024

        if value and value.size > max_size:
            raise serializers.ValidationError("Размер файла превышает максимальный размер (10 МБ).")

        return value


class MyUserSerializer(serializers.ModelSerializer):
    """Сериализатор для личных данных пользователя"""
    social_links = UserSocialLinkSerializer(many=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'phone_number', 'first_name', 'last_name', 'patronymic', 'email', 'dob', 'gender', 'status',
                  'about_me', 'avatar', 'social_links',)
        extra_kwargs = {f: {'required': True} for f in fields
                        if f not in ('patronymic', 'avatar', 'social_links')}
        read_only_fields = ('phone_number',)

    def validate_avatar(self, value):
        # Максимальный допустимый размер файла в байтах (10 МБ)
        max_size = 10 * 1024 * 1024

        if value and value.size > max_size:
            raise serializers.ValidationError("Размер файла превышает максимальный размер (10 МБ).")

        return value


class RetrieveUserSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра пользователя другими пользователями"""
    age = serializers.SerializerMethodField()
    social_links = UserSocialLinkSerializer(many=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'age', 'gender', 'status', 'about_me', 'avatar', 'social_links',)

    def get_age(self, instance: User) -> int:
        return instance.age


class ShortUserSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о пользователе"""
    short_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    average_points = serializers.SerializerMethodField(allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'short_name', 'age', 'avatar_preview', 'average_points')

    def get_short_name(self, instance: User) -> str:
        return instance.short_name

    def get_age(self, instance: User) -> int:
        return instance.age

    def get_average_points(self, instance: User) -> Decimal:
        return ReviewService.get_average_points(instance.onme_reviews.all())
