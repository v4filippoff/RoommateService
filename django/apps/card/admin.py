from django.contrib import admin

from .models import CardTag


@admin.register(CardTag)
class CardTagAdmin(admin.ModelAdmin):
    """Админ-панель тегов карточек"""
    pass
