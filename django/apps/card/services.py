import json
from datetime import date

from django.core.files import File
from django.db import transaction
from django.db.models import QuerySet
from django_celery_beat.models import PeriodicTask, ClockedSchedule

from .exceptions import CardActionError
from .models import Card, CardPhoto


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

        photos: list[dict[str, File]] = card_data.pop('photos', None)
        tags: list[int] = card_data.pop('tags', None)

        card = Card.objects.create(**card_data)
        if photos:
            for p in photos:
                if 'photo' not in p:
                    continue
                card.photos.create(photo=p['photo'])
        if tags:
            card.tags.add(tags)

        if card.deadline and card.status == Card.Statuses.ACTIVE:
            card_service = CardService(card)
            card_service.create_task_to_change_status_after_deadline()

        return card

    @staticmethod
    def get_cards_sorted_by_status(queryset: QuerySet[Card]) -> list[Card]:
        """Получить карточки отсортированные по статусу (Активные, Черновики, Завершенные)"""
        active_cards: list[Card] = []
        draft_cards: list[Card] = []
        completed_cards: list[Card] = []
        for card in queryset:
            match card.status:
                case Card.Statuses.ACTIVE:
                    active_cards.append(card)
                case Card.Statuses.DRAFT:
                    draft_cards.append(card)
                case Card.Statuses.COMPLETED:
                    completed_cards.append(card)
        return active_cards + draft_cards + completed_cards

    def change_status(self, new_status: Card.Statuses, save: bool = True) -> None:
        """Обновить статус карточки"""
        if self._card.status == Card.Statuses.COMPLETED:
            raise CardActionError('Нельзя поменять статус завершенной карточки.')
        self._card.status = new_status
        self._card.save()

    def create_task_to_change_status_after_deadline(self) -> PeriodicTask:
        """Перевести статус карточки в черновик после дедлайна"""
        existing_task = PeriodicTask.objects.filter(name=f'change card status to draft card_id={self._card.id}').first()
        if existing_task:
            existing_task.clocked = ClockedSchedule.objects.get_or_create(clocked_time=self._card.deadline)[0]
            existing_task.enabled = True
            existing_task.save()
            return existing_task

        new_task = PeriodicTask.objects.create(
            name=f'change card status to draft card_id={self._card.id}',
            task='apps.card.tasks.change_card_status',
            kwargs=json.dumps({'card_id': self._card.id, 'status': str(Card.Statuses.DRAFT)}),
            one_off=True,
            clocked=ClockedSchedule.objects.get_or_create(clocked_time=self._card.deadline)[0]
        )
        return new_task

    def disable_task_to_change_status_after_deadline(self) -> None:
        """Отменить задачу по переводу статуса карточки в черновик после дедлайна"""
        PeriodicTask.objects.filter(
            name=f'change card status to draft card_id={self._card.id}'
        ).update(enabled=False)

    def delete_task_to_change_status_after_deadline(self) -> None:
        """Удалить задачу по переводу статуса карточки в черновик после дедлайна"""
        PeriodicTask.objects.filter(
            name=f'change card status to draft card_id={self._card.id}'
        ).delete()

    @transaction.atomic
    def update(self, **new_card_data) -> Card:
        """Обновить карточку"""
        new_card_status: Card.Statuses | None = None
        is_deadline_changed = False
        new_card_deadline: date | None = None
        for field, value in new_card_data.items():
            match field:
                case 'status':
                    new_card_status = value
                case 'deadline':
                    new_card_deadline = value
                    is_deadline_changed = (new_card_deadline != self._card.deadline)
                case 'photos':
                    CardPhoto.objects.exclude(id__in=[p['id'] for p in value if 'id' in p]).delete()
                    for p in value:
                        if 'photo' not in p:
                            continue
                        self._card.photos.create(photo=p['photo'])
                case 'tags':
                    tags_to_remove = list(self._card.tags.exclude(id__in=[t.id for t in value]).values_list('id', flat=True))
                    self._card.tags.remove(*tags_to_remove)
                    self._card.tags.add(*value)
                case _:
                    setattr(self._card, field, value)

        if self._card.status == Card.Statuses.ACTIVE and new_card_status == Card.Statuses.DRAFT:
            self.disable_task_to_change_status_after_deadline()
        if new_card_status == Card.Statuses.COMPLETED or is_deadline_changed and not new_card_deadline:
            self.delete_task_to_change_status_after_deadline()

        if new_card_status:
            self.change_status(new_card_status, save=False)
        if is_deadline_changed:
            self._card.deadline = new_card_deadline

        if new_card_deadline and new_card_status == Card.Statuses.ACTIVE:
            self.create_task_to_change_status_after_deadline()

        self._card.save()
        return self._card
