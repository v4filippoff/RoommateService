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


class CardStatusSerializer(serializers.Serializer):
    """Сериализатор для статуса карточки"""
    value = serializers.CharField()
    label = serializers.CharField()


class ShortCardSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о карточке"""
    owner = ShortUserSerializer()
    city = CitySerializer()
    photos = CardPhotoSerializer(many=True)
    tags = CardTagSerializer(many=True)

    class Meta:
        model = Card
        fields = ('id', 'owner', 'header', 'city', 'limit', 'created_at', 'deadline', 'status', 'photos', 'tags')

    def to_representation(self, instance):
        user = self.context['request'].user
        if instance.owner == user:
            return super().to_representation(instance)
        else:
            excluded_fields = ['created_at', 'status']
            data = super().to_representation(instance)
            for field in excluded_fields:
                data.pop(field, None)
            return data


class FullCardSerializer(serializers.ModelSerializer):
    """Сериализатор для полной информации о карточке"""
    owner = ShortUserSerializer()
    city = CitySerializer()
    photos = CardPhotoSerializer(many=True)
    tags = CardTagSerializer(many=True)

    class Meta:
        model = Card
        fields = ('id', 'owner', 'header', 'description', 'city', 'limit', 'created_at', 'deadline', 'status', 'photos',
                  'tags')

    def to_representation(self, instance):
        user = self.context['request'].user
        if instance.owner == user:
            return super().to_representation(instance)
        else:
            excluded_fields = ['created_at', 'status']
            data = super().to_representation(instance)
            for field in excluded_fields:
                data.pop(field, None)
            return data


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
