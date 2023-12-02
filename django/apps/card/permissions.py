from rest_framework import permissions

from .models import Card


class IsCardOwner(permissions.BasePermission):
    message = 'Вы не имеете доступ к данной карточке.'

    def has_object_permission(self, request, view, obj: Card):
        return obj.owner == request.user
