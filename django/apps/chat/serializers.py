from rest_framework import serializers

from .models import ChatMessage
from ..card.serializers import ShortCardSerializer
from ..user.serializers import ShortUserSerializer


class CreateChatMessageSerializer(serializers.ModelSerializer):
    """Сериализатор для отправки сообщения в чате пользователю"""

    class Meta:
        model = ChatMessage
        fields = ('receiver', 'content')


class ShortChatMessageSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о сообщении из чата"""
    short_content = serializers.SerializerMethodField()
    is_system = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ('id', 'sender', 'receiver', 'card', 'short_content', 'created_at', 'is_system')

    def get_short_content(self, instance: ChatMessage) -> str:
        return instance.short_content

    def get_is_system(self, instance: ChatMessage) -> bool:
        return instance.is_system


class ListChatSerializer(serializers.ModelSerializer):
    """Посмотреть список чатов"""
    sender = ShortUserSerializer(allow_null=True)
    receiver = ShortUserSerializer()
    card = ShortCardSerializer()
    short_content = serializers.SerializerMethodField()
    is_system = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ('id', 'sender', 'receiver', 'card', 'short_content', 'created_at', 'is_system')

    def get_short_content(self, instance: ChatMessage) -> str:
        return instance.short_content

    def get_is_system(self, instance: ChatMessage) -> bool:
        return instance.is_system


class MessageInChatSerializer(serializers.ModelSerializer):
    """Сообщение в чате"""
    sender = ShortUserSerializer(allow_null=True)
    receiver = ShortUserSerializer()
    card = ShortCardSerializer()
    is_system = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ('id', 'sender', 'receiver', 'card', 'content', 'created_at', 'is_system')

    def get_is_system(self, instance: ChatMessage) -> bool:
        return instance.is_system
