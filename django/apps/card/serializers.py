from datetime import date

from rest_framework import serializers

from .models import CardTag, CardPhoto, Card
from ..city.serializers import CitySerializer
from ..user.serializers import ShortUserSerializer


class CardTagSerializer(serializers.ModelSerializer):
    """Сериализатор для тега карточки"""

    class Meta:
        model = CardTag
        fields = ('id', 'name', 'order',)


class CardPhotoSerializer(serializers.ModelSerializer):
    """Сериализатор для фото карточки"""

    class Meta:
        model = CardPhoto
        fields = ('photo',)


class ShortCardSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о карточке"""
    owner = ShortUserSerializer()
    city = CitySerializer()
    photos = CardPhotoSerializer(many=True)
    tags = CardTagSerializer(many=True)

    class Meta:
        model = Card
        fields = ('id', 'owner', 'header', 'city', 'limit', 'deadline', 'photos', 'tags')


class FullCardSerializer(serializers.ModelSerializer):
    """Сериализатор для полной информации о карточке"""
    owner = ShortUserSerializer()
    city = CitySerializer()
    photos = CardPhotoSerializer(many=True)
    tags = CardTagSerializer(many=True)

    class Meta:
        model = Card
        fields = ('id', 'owner', 'header', 'description', 'city', 'limit', 'created_at', 'deadline', 'photos', 'tags')


class MyCardSerializer(serializers.ModelSerializer):
    """Сериализатор для полной информации о собственной карточке пользователя"""
    owner = ShortUserSerializer()
    city = CitySerializer()
    photos = CardPhotoSerializer(many=True)
    tags = CardTagSerializer(many=True)

    class Meta:
        model = Card
        fields = ('id', 'owner', 'header', 'description', 'city', 'limit', 'created_at', 'deadline', 'status', 'photos',
                  'tags')


class CreateCardSerializer(serializers.ModelSerializer):
    """Сериализатор для создания карточки"""
    photos = serializers.ListField(child=serializers.ImageField(), required=False, write_only=True)

    class Meta:
        model = Card
        fields = ('header', 'description', 'city', 'limit', 'deadline', 'photos', 'tags')

    def validate_deadline(self, value: date):
        if value < date.today():
            raise serializers.ValidationError('Дата не может быть прошедшей.')
        return value
