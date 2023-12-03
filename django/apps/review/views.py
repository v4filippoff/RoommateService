from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .exceptions import ReviewActionError
from .models import Review
from .serializers import CreateReviewSerializer, DetailReviewSerializer, UserListReviewSerializer
from .services import ReviewService
from ..user.permissions import IsFullRegistered


@extend_schema_view(
    list=extend_schema(
        summary='Список отзывов',
        responses={200: UserListReviewSerializer}
    ),
    create=extend_schema(
        summary='Создание отзыва',
        request=CreateReviewSerializer,
        responses={201: DetailReviewSerializer}
    ),
)
class ReviewViewSet(viewsets.GenericViewSet):
    """ViewSet для отзывов"""
    queryset = Review.objects.all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['target_user']

    def get_serializer_class(self):
        match self.action:
            case 'list':
                return UserListReviewSerializer
            case 'create':
                return CreateReviewSerializer

    def get_permissions(self):
        match self.action:
            case _:
                self.permission_classes = (IsAuthenticated, IsFullRegistered)
        return [permission() for permission in self.permission_classes]

    def list(self, request):
        """Список отзывов"""
        queryset = self.filter_queryset(self.get_queryset())
        average_points = ReviewService.get_average_points(queryset)
        serializer = self.get_serializer({'average_points': average_points, 'reviews': queryset})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """Создать отзыв"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['author'] = request.user
        try:
            review = ReviewService.create(**serializer.validated_data)
        except ReviewActionError as exc:
            raise ValidationError(str(exc))
        return Response(DetailReviewSerializer(review).data,status=status.HTTP_201_CREATED)
