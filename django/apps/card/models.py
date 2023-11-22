from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models

from apps.city.models import City
from apps.user.models import User


class CardTag(models.Model):
    """Тег карточки"""
    name = models.CharField(max_length=255, verbose_name='Название')
    code = models.CharField(max_length=255, verbose_name='Символьный код')
    order = models.PositiveIntegerField(default=0, verbose_name='Сортировка')

    class Meta:
        verbose_name = 'Тег карточки'
        verbose_name_plural = 'Теги карточки'

    def __str__(self):
        return str(self.name)


class Card(models.Model):
    """Карточка"""

    class Statuses(models.TextChoices):
        """Статус"""
        ACTIVE = 'active', 'Активна'
        DRAFT = 'draft', 'Черновик'
        COMPLETED = 'completed', 'Завершено'

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards', verbose_name='Создатель')
    header = models.CharField(max_length=255, verbose_name='Заголовок')
    description = models.CharField(max_length=2048, verbose_name='Описание')
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, related_name='cards', verbose_name='Город')
    limit = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)],
                                        verbose_name='Максимальное количество сожителей')
    created_at = models.DateField(auto_now_add=True, verbose_name='Дата создания')
    deadline = models.DateField(default=None, null=True, verbose_name='Крайний срок')
    status = models.CharField(max_length=100, verbose_name='Статус', choices=Statuses.choices, default=Statuses.ACTIVE)
    tags = models.ManyToManyField(CardTag, verbose_name='Теги')

    class Meta:
        verbose_name = 'Карточка'
        verbose_name_plural = 'Карточки'

    def __str__(self):
        return str(self.header[:100]) + '...'


class CardPhoto(models.Model):
    """Фото карточки"""

    def upload_photo(instance, filename):
        return f'cards/{instance.card_id}/photos/{filename}'

    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='photos', verbose_name='Карточка')
    photo = models.ImageField(upload_to=upload_photo, verbose_name='Фото',
                              validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'heic'])])

    class Meta:
        verbose_name = 'Фото карточки'
        verbose_name_plural = 'Фотки карточки'

    def __str__(self):
        return f'{self.card} {self.photo}'


class CardRequest(models.Model):
    """Заявка на карточку"""

    class Statuses(models.TextChoices):
        """Статус"""
        PENDING = 'pending', 'В ожидании рассмотрения'
        APPROVED = 'approved', 'Одобрена'
        REJECTED = 'rejected', 'Отклонена'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests', verbose_name='Пользователь')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='requests', verbose_name='Карточка')
    status = models.CharField(max_length=100, verbose_name='Статус', choices=Statuses.choices, default=Statuses.PENDING)
    roommates_number = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)],
                                                   verbose_name='Количество предлагаемых сожителей')
    covering_letter = models.CharField(max_length=2048, blank=True, verbose_name='Сопроводительное письмо')

    class Meta:
        verbose_name = 'Заявка на карточку'
        verbose_name_plural = 'Заявки на карточку'

    def __str__(self):
        return f'{self.user} {self.card} {self.status}'
