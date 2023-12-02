from rest_framework import permissions

from apps.chat.models import ChatMessage


class IsChatMessageSender(permissions.BasePermission):
    message = 'Вы не являетесь отправителем данного сообщения.'

    def has_object_permission(self, request, view, obj: ChatMessage):
        return obj.sender == request.user


class IsChatMessageSenderOrReceiver(permissions.BasePermission):
    message = 'Вы не являетесь отправителем или получателем данного сообщения.'

    def has_object_permission(self, request, view, obj: ChatMessage):
        return obj.sender == request.user or obj.receiver == request.user
