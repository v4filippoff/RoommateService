from rest_framework import permissions


class IsFullRegistered(permissions.BasePermission):
    """Проверка зарегистрирован ли пользователь в системе"""
    message = 'Необходимо пройти регистрацию.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_registered)
