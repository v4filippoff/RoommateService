from django.db import models


class City(models.Model):
    """Город"""
    name = models.CharField(max_length=255, verbose_name='Название')
    order = models.PositiveIntegerField(default=0, verbose_name='Сортировка')

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

    def __str__(self):
        return str(self.name)
