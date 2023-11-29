from datetime import date

from rest_framework import serializers

from .models import CardTag, CardPhoto, Card, CardRequest
from .services import CardService
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
        fields = ('id', 'photo',)

        extra_kwargs = {
            'id': {'read_only': False, 'required': False},
            'photo': {'required': False},
        }

    def validate(self, data):
        if 'id' not in data and 'photo' not in data:
            raise serializers.ValidationError('Не передан файл.', code='required')
        if 'id' in data and 'photo' in data:
            raise serializers.ValidationError('Нельзя одновременно передать id и photo', code='invalid')
        return data


class ShortCardSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о карточке"""
    owner = ShortUserSerializer()
    city = CitySerializer()
    photos = CardPhotoSerializer(many=True)
    tags = CardTagSerializer(many=True)
    free_slots_number = serializers.SerializerMethodField()

    class Meta:
        model = Card
        fields = ('id', 'owner', 'header', 'city', 'limit', 'free_slots_number', 'created_at', 'deadline', 'status',
                  'photos', 'tags')

    def get_free_slots_number(self, instance: Card) -> int:
        card_service = CardService(instance)
        return card_service.get_free_slots_number()

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
    free_slots_number = serializers.SerializerMethodField()

    class Meta:
        model = Card
        fields = ('id', 'owner', 'header', 'description', 'city', 'limit', 'free_slots_number', 'created_at',
                  'deadline', 'status', 'photos', 'tags')

    def get_free_slots_number(self, instance: Card) -> int:
        card_service = CardService(instance)
        return card_service.get_free_slots_number()

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
    photos = CardPhotoSerializer(many=True, required=False, default=[])
    tags = serializers.PrimaryKeyRelatedField(queryset=CardTag.objects.all(), many=True, default=[])

    class Meta:
        model = Card
        fields = ('header', 'description', 'city', 'limit', 'deadline', 'status', 'photos', 'tags')
        extra_kwargs = {'city': {'required': True}}

    def validate_deadline(self, value: date):
        if value and value < date.today():
            raise serializers.ValidationError('Дата не может быть прошедшей.')
        return value


class CreateCardRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = CardRequest
        fields = ('card', 'roommates_number', 'covering_letter')
        extra_kwargs = {'card': {'read_only': True}, 'roommates_number': {'required': True}}


class ShortCardRequestWithDetailUserSerializer(serializers.ModelSerializer):
    user = ShortUserSerializer()
    short_covering_letter = serializers.SerializerMethodField()

    class Meta:
        model = CardRequest
        fields = ('user', 'card', 'status', 'roommates_number', 'short_covering_letter')

    def get_short_covering_letter(self, instance: CardRequest) -> str:
        return instance.short_covering_letter


class ShortCardRequestWithDetailCardSerializer(serializers.ModelSerializer):
    card = ShortCardSerializer()
    short_covering_letter = serializers.SerializerMethodField()

    class Meta:
        model = CardRequest
        fields = ('user', 'card', 'status', 'roommates_number', 'short_covering_letter')

    def get_short_covering_letter(self, instance: CardRequest) -> str:
        return instance.short_covering_letter


class FullCardRequestSerializer(serializers.ModelSerializer):
    user = ShortUserSerializer()
    card = ShortCardSerializer()

    class Meta:
        model = CardRequest
        fields = ('user', 'card', 'status', 'roommates_number', 'covering_letter')
