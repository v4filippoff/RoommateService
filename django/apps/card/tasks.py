from celery import shared_task

from .models import Card


@shared_task
def change_card_status(card_id: int, status: str) -> None:
    """Поменять статус карточки"""
    card = Card.objects.filter(id=card_id).first()
    if card:
        card.status = status
        card.save()
