from django.db import transaction

from .exceptions import CardActionError
from .models import Card


class CardService:
    """Сервис для работы с карточками"""
    LIMIT_FOR_ACTIVE_CARDS = 3

    def __init__(self, card: Card):
        self._card = card

    @staticmethod
    @transaction.atomic
    def create(**card_data) -> Card:
        """Создать карточку"""
        if Card.objects.filter(owner=card_data['owner'], status=Card.Statuses.ACTIVE).count() >= CardService.LIMIT_FOR_ACTIVE_CARDS:
            raise CardActionError(f'Количество активных карточек не должно быть больше {CardService.LIMIT_FOR_ACTIVE_CARDS}.')

        photos = card_data.pop('photos', None)
        tags = card_data.pop('tags', None)

        card = Card.objects.create(**card_data)
        if photos:
            for p in photos:
                card.photos.create(photo=p)
        if tags:
            for t in tags:
                card.tags.add(t)

        return card

    def update(self, **new_card_data) -> Card:
        """Обновить карточку"""
        pass
