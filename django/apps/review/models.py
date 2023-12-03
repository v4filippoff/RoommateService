from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.user.models import User
from apps.card.models import Card


class Review(models.Model):
    """Отзыв о пользователе"""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_reviews', verbose_name='Автор')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='onme_reviews', verbose_name='Целевой пользователь')
    text = models.CharField(max_length=2048, verbose_name='Текст')
    points = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name='Оценка от 1 до 5')
    created_at = models.DateField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Отзыв о пользователе'
        verbose_name_plural = 'Отзывы о пользователе'

    def __str__(self):
        return f'{self.author} {self.target_user} {self.text}'
