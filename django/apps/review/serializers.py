from rest_framework import serializers

from apps.user.serializers import ShortUserSerializer
from .models import Review


class CreateReviewSerializer(serializers.ModelSerializer):
    """Создать отзыв"""

    class Meta:
        model = Review
        fields = ('target_user', 'text', 'points')


class DetailReviewSerializer(serializers.ModelSerializer):
    """Детальное отображение отзыва"""
    author = ShortUserSerializer()
    target_user = ShortUserSerializer()

    class Meta:
        model = Review
        fields = ('author', 'target_user', 'text', 'points', 'created_at')


class UserListReviewSerializer(serializers.Serializer):
    """Список отзывов о пользователе"""
    average_points = serializers.DecimalField(max_digits=3, decimal_places=2, allow_null=True)
    reviews = DetailReviewSerializer(many=True)
