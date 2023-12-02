import json
from datetime import date

from django.core.files import File
from django.db import transaction
from django.db.models import QuerySet
from django_celery_beat.models import PeriodicTask, ClockedSchedule

from .exceptions import CardActionError
from .models import Card, CardPhoto, CardRequest, CardTag
from ..chat.services import ChatMessageService
from ..user.models import User


class CardService:
    """Сервис для работы с карточками"""
    LIMIT_FOR_ACTIVE_CARDS = 3

    def __init__(self, card: Card):
        self._card = card

    @staticmethod
    @transaction.atomic
    def create(**card_data) -> Card:
        """Создать карточку"""
        card_owner: User = card_data['owner']
        if card_owner.cards.filter(status=Card.Statuses.ACTIVE).count() >= CardService.LIMIT_FOR_ACTIVE_CARDS:
            raise CardActionError(f'Количество активных карточек не должно быть больше {CardService.LIMIT_FOR_ACTIVE_CARDS}.')

        photos: list[dict[str, File]] = card_data.pop('photos', None)
        tags: list[CardTag] = card_data.pop('tags', None)

        card = Card.objects.create(**card_data)
        if photos:
            for p in photos:
                if 'photo' not in p:
                    continue
                card.photos.create(photo=p['photo'])
        if tags:
            card.tags.add(*tags)

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

    @staticmethod
    def get_cards_for_user_feed(user: User, base_queryset: QuerySet[Card] = None) -> QuerySet[Card]:
        """Получить карточки для ленты пользователя"""
        queryset = base_queryset or Card.objects.all()
        active_card_ids: set[int] = set(queryset.filter(status=Card.Statuses.ACTIVE).exclude(owner=user).values_list('id', flat=True))
        skipped_card_ids: set[int] = set(user.card_skips.values_list('id', flat=True))
        diff_ids = active_card_ids - skipped_card_ids
        if diff_ids:
            return queryset.filter(id__in=diff_ids).order_by('-created_at')
        else:
            user.card_skips.clear()
            return queryset.filter(id__in=active_card_ids).order_by('-created_at')

    def skip_card_by_user(self, user: User) -> None:
        """Пропустить карточку"""
        if self._card.owner == user:
            raise CardActionError('Нельзя пропустить собственную карточку.')
        self._card.user_skips.add(user)

    def change_status(self, new_status: Card.Statuses, save: bool = True) -> None:
        """Обновить статус карточки"""
        if self._card.status == Card.Statuses.COMPLETED:
            raise CardActionError('Нельзя поменять статус завершенной карточки.')
        self._card.status = new_status
        if save:
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

    def get_free_slots_number(self) -> int:
        """Получить количество свободных слотов, доступных для отправки заявки на совместное проживание"""
        return self._card.limit - self._card.requests.filter(status=CardRequest.Statuses.APPROVED).count()


class CardRequestService:
    LIMIT_FOR_REJECTED_CARDS = 3
    LIMIT_FOR_APPROVED_CARDS = 1

    def __init__(self, card_request: CardRequest):
        self._card_request = card_request

    @staticmethod
    @transaction.atomic
    def create(**card_request_data) -> CardRequest:
        """Создать заявку на карточку"""
        user: User = card_request_data['user']
        card: Card = card_request_data['card']

        card_service = CardService(card_request_data['card'])
        if card_service.get_free_slots_number() < card_request_data['roommates_number']:
            raise CardActionError('Количество предлагаемых сожителей больше допустимого.')
        if user == card.owner:
            raise CardActionError('Нельзя подать заявку на собственную карточку.')
        if user.requests.filter(status=CardRequest.Statuses.APPROVED).exists():
            raise CardActionError('У вас уже есть одобренная заявка.')
        if user.requests.filter(card=card_request_data['card'], status=CardRequest.Statuses.PENDING).exists():
            raise CardActionError('Вы уже подали заявку на данную карточку.')
        if user.requests.filter(card=card_request_data['card'], status=CardRequest.Statuses.REJECTED).count() >= CardRequestService.LIMIT_FOR_REJECTED_CARDS:
            raise CardActionError(f'Вы превысили лимит подачи заявок на данную карточку: {CardRequestService.LIMIT_FOR_REJECTED_CARDS}.')
        if CardRequestService.get_active_card_request_by_owner(user=card.owner, owner=user):
            raise CardActionError('Вы не можете подать заявку на данную карточку, '
                                  'т.к. ее владелец имеет активную заявку на вашей карточке.')

        card_request = CardRequest.objects.create(**card_request_data)

        # Системное сообщение-уведомление создателю карточки
        chat_message_to_owner = {
            'sender': None,
            'receiver': card.owner,
            'card': card,
            'content': f'Новая заявка на карточку!\n\n{card_request_data["covering_letter"]}'
        }
        ChatMessageService.create(**chat_message_to_owner)

        return card_request

    @staticmethod
    def cancel(user: User, card: Card) -> None:
        """Отменить заявку на карточку"""
        card_request = CardRequestService.get_active_card_request_by_card(user=user, card=card)
        if card_request:
            card_request.delete()

            chat_message_to_owner = {
                'sender': None,
                'receiver': card_request.card.owner,
                'card': card_request.card,
                'content': 'Отмена заявки!'
            }
            ChatMessageService.create(**chat_message_to_owner)
        else:
            raise CardActionError('У вас нет активной заявки на данную карточку.')

    @staticmethod
    def get_active_card_request_by_card(user: User, card: Card) -> CardRequest | None:
        """Получить активную заявку, созданную user, на карточку card"""
        return CardRequest.objects.filter(user=user, card=card, status__in=[CardRequest.Statuses.PENDING,
                                                                            CardRequest.Statuses.APPROVED]).first()

    @staticmethod
    def get_active_card_request_by_owner(user: User, owner: User) -> CardRequest | None:
        """Получить активную заявку, созданную user, на карточку владельцем которой является owner"""
        return CardRequest.objects.filter(user=user, card__owner=owner, status__in=[CardRequest.Statuses.PENDING,
                                                                                    CardRequest.Statuses.APPROVED]).first()

    @staticmethod
    @transaction.atomic
    def handle_request(user: User, card: Card, new_status: CardRequest.Statuses) -> CardRequest:
        """Обработать заявку на карточку - поменять статус"""
        active_card_request = CardRequestService.get_active_card_request_by_card(user=user, card=card)
        if not active_card_request:
            raise CardActionError('Нет активной заявки пользователя на данную карточку.')
        if active_card_request.status == CardRequest.Statuses.REJECTED:
            raise CardActionError('Данная заявка отклонена.')
        active_card_request.status = new_status
        active_card_request.save()

        status_label = next(item[1] for item in CardRequest.Statuses.choices if item[0] == new_status)
        chat_message_to_owner = {
            'sender': None,
            'receiver': user,
            'card': card,
            'content': f'Новый статус по заявке: "{status_label}".'
        }
        ChatMessageService.create(**chat_message_to_owner)

        return active_card_request

    @staticmethod
    def get_card_requests_sorted_by_status(queryset: QuerySet[CardRequest]) -> list[CardRequest]:
        """Получить заявки отсортированные по статусу (В ожидании рассмотрения, Одобрена, Отклонена)"""
        pending_requests: list[CardRequest] = []
        approved_requests: list[CardRequest] = []
        rejected_requests: list[CardRequest] = []
        for request in queryset:
            match request.status:
                case CardRequest.Statuses.PENDING:
                    pending_requests.append(request)
                case CardRequest.Statuses.APPROVED:
                    approved_requests.append(request)
                case CardRequest.Statuses.REJECTED:
                    rejected_requests.append(request)
        return pending_requests + approved_requests + rejected_requests
