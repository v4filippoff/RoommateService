from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .exceptions import CardActionError
from .models import Card, CardTag
from .serializers import CreateCardSerializer, MyCardSerializer, CardTagSerializer
from .services import CardService
from ..user.permissions import IsFullRegistered


@extend_schema_view(
    create=extend_schema(
        summary='Создание карточки',
        request=CreateCardSerializer,
        responses={201: MyCardSerializer}
    ),
    tags=extend_schema(
        summary='Список доступных тегов',
        responses={200: CardTagSerializer}
    ),
)
class CardViewSet(viewsets.GenericViewSet):
    """ViewSet для карточек"""
    queryset = Card.objects.all()

    def get_serializer_class(self):
        match self.action:
            case 'create':
                return CreateCardSerializer
            case 'tags':
                return CardTagSerializer

    def get_permissions(self):
        match self.action:
            case 'tags':
                self.permission_classes = (AllowAny,)
            case _:
                self.permission_classes = (IsAuthenticated, IsFullRegistered)
        return [permission() for permission in self.permission_classes]

    def create(self, request):
        """Создать карточку"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['owner'] = request.user
        try:
            card = CardService.create(**serializer.validated_data)
        except CardActionError as exc:
            raise ValidationError(str(exc))
        return Response(MyCardSerializer(card).data, status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=False, url_path='tags', url_name='tags')
    def tags(self, request):
        queryset = CardTag.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
