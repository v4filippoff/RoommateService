from django.contrib import admin

from .models import City


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    """Админ-панель городов"""
    ordering = ['-order']
