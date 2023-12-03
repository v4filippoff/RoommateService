from _decimal import Decimal
from django.db import transaction
from django.db.models import Q, QuerySet, Avg

from apps.card.models import Card, CardRequest
from .exceptions import ReviewActionError
from .models import Review


class ReviewService:

    def __init__(self, review: Review):
        self._review = review

    @staticmethod
    @transaction.atomic
    def create(**review_data) -> Review:
        """Создать отзыв"""
        if review_data['author'] == review_data['target_user']:
            raise ReviewActionError('Нельзя оставить отзыв на самого себя.')
        if not Card.objects.filter(Q(status=Card.Statuses.COMPLETED) & (
            Q(owner=review_data['author']) & Q(requests__user=review_data['target_user']) & Q(requests__status=CardRequest.Statuses.APPROVED) |
            Q(owner=review_data['target_user']) & Q(requests__user=review_data['author']) & Q(requests__status=CardRequest.Statuses.APPROVED)
        )).exists():
            raise ReviewActionError('Нельзя оставить отзыв на пользователя, с которым нет завершенной карточки.')
        review = Review.objects.create(**review_data)
        return review

    @staticmethod
    def get_average_points(queryset: QuerySet[Review]) -> Decimal | None:
        """Получить среднюю оценку пользователя"""
        value = queryset.aggregate(average_points=Avg('points'))['average_points']
        if value:
            return Decimal(value).quantize(Decimal('0.01'))
