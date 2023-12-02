from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .exceptions import CardActionError
from .models import Card, CardTag
from .permissions import IsCardOwner
from .serializers import CreateCardSerializer, CardTagSerializer, ShortCardSerializer, FullCardSerializer, \
    CreateCardRequestSerializer, ShortCardRequestWithDetailUserSerializer, FullCardRequestSerializer, \
    ShortCardRequestWithDetailCardSerializer, HandleCardRequestSerializer
from .services import CardService, CardRequestService
from ..user.permissions import IsFullRegistered


@extend_schema_view(
    list=extend_schema(
        summary='Список карточек для просмотра',
        responses={200: ShortCardSerializer}
    ),
    create=extend_schema(
        summary='Создание карточки',
        request=CreateCardSerializer,
        responses={201: FullCardSerializer}
    ),
    by_owner=extend_schema(
        summary='Список карточек пользователя',
        responses={200: ShortCardSerializer}
    ),
    retrieve=extend_schema(
        summary='Детальный просмотр карточки',
        responses={200: FullCardSerializer}
    ),
    update=extend_schema(
        summary='Редактирование карточки',
        request=CreateCardSerializer,
        responses={200: FullCardSerializer}
    ),
    tags=extend_schema(
        summary='Список доступных тегов',
        responses={200: CardTagSerializer}
    ),
    get_requests=extend_schema(
        summary='Список заявок на данную карточку',
        responses={200: ShortCardRequestWithDetailUserSerializer}
    ),
    my_requests=extend_schema(
        summary='Посмотреть собственные заявки на карточки',
        responses={200: ShortCardRequestWithDetailCardSerializer}
    ),
    create_request=extend_schema(
        summary='Создание заявки на карточку',
        request=CreateCardRequestSerializer,
        responses={201: FullCardRequestSerializer}
    ),
    cancel_request=extend_schema(
        summary='Отмена заявки на карточку',
        request=None,
        responses=204
    ),
    skip_card=extend_schema(
        summary='Пропустить карточку (пойти дальше по ленте)',
        request=None,
        responses=200
    ),
    handle_request=extend_schema(
        summary='Обработать запрос на карточку',
        request=HandleCardRequestSerializer,
        responses={200: ShortCardRequestWithDetailUserSerializer}
    ),
)
class CardViewSet(viewsets.GenericViewSet):
    """ViewSet для карточек"""
    queryset = Card.objects.all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['city', 'tags']

    def get_serializer_class(self):
        match self.action:
            case 'list':
                return ShortCardSerializer
            case 'create':
                return CreateCardSerializer
            case 'by_owner':
                return ShortCardSerializer
            case 'retrieve':
                return FullCardSerializer
            case 'update':
                return CreateCardSerializer
            case 'tags':
                return CardTagSerializer
            case 'get_requests':
                return ShortCardRequestWithDetailUserSerializer
            case 'my_requests':
                return ShortCardRequestWithDetailCardSerializer
            case 'create_request':
                return CreateCardRequestSerializer
            case 'handle_request':
                return HandleCardRequestSerializer

    def get_permissions(self):
        match self.action:
            case 'tags':
                self.permission_classes = (AllowAny,)
            case 'update' | 'get_requests' | 'handle_request':
                self.permission_classes = (IsAuthenticated, IsFullRegistered, IsCardOwner)
            case _:
                self.permission_classes = (IsAuthenticated, IsFullRegistered)
        return [permission() for permission in self.permission_classes]

    def list(self, request):
        """Список карточек"""
        base_queryset = self.filter_queryset(self.get_queryset())
        queryset = CardService.get_cards_for_user_feed(user=request.user, base_queryset=base_queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """Создать карточку"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['owner'] = request.user
        try:
            card = CardService.create(**serializer.validated_data)
        except CardActionError as exc:
            raise ValidationError(str(exc))
        return Response(FullCardSerializer(card, context=self.get_serializer_context()).data,
                        status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=False, url_path=r'by-owner/(?P<owner_id>\d+)', url_name='by_owner')
    def by_owner(self, request, owner_id):
        queryset = self.get_queryset().filter(owner_id=owner_id)
        if request.user.id == int(owner_id):
            card_status = request.query_params.get('status')
            if card_status:
                queryset = queryset.filter(status=card_status)
            queryset = CardService.get_cards_sorted_by_status(queryset)
        else:
            queryset = queryset.filter(status=Card.Statuses.ACTIVE)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = self.get_object()
        card_service = CardService(obj)
        try:
            updated_card = card_service.update(**serializer.validated_data)
        except CardActionError as exc:
            raise ValidationError(str(exc))
        else:
            return Response(FullCardSerializer(updated_card, context=self.get_serializer_context()).data,
                            status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='tags', url_name='tags')
    def tags(self, request):
        queryset = CardTag.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True, url_path='get-requests', url_name='get_requests')
    def get_requests(self, request, pk):
        card = self.get_object()
        queryset = CardRequestService.get_card_requests_sorted_by_status(card.requests.all())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True, url_path='create-request', url_name='create_request')
    def create_request(self, request, pk):
        """Создать заявку на карточку"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['card'] = self.get_object()
        serializer.validated_data['user'] = request.user
        try:
            card_request = CardRequestService.create(**serializer.validated_data)
        except CardActionError as exc:
            raise ValidationError(str(exc))
        return Response(FullCardRequestSerializer(card_request, context=self.get_serializer_context()).data,
                        status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=True, url_path='cancel-request', url_name='cancel_request')
    def cancel_request(self, request, pk):
        """Отменить заявку на карточку"""
        try:
            CardRequestService.cancel(user=request.user, card=self.get_object())
        except CardActionError as exc:
            raise ValidationError(str(exc))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST'], detail=True, url_path='skip', url_name='skip_card')
    def skip_card(self, request, pk):
        """Пропустить карточку карточку"""
        card_service = CardService(self.get_object())
        try:
            card_service.skip_card_by_user(user=request.user)
        except CardActionError as exc:
            raise ValidationError(str(exc))
        return Response(status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='my-requests', url_name='my_requests')
    def my_requests(self, request):
        queryset = CardRequestService.get_card_requests_sorted_by_status(request.user.requests.all())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True, url_path='handle-request', url_name='handle_request')
    def handle_request(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated_card_request = CardRequestService.handle_request(user=serializer.validated_data['user'],
                                                                     card=self.get_object(),
                                                                     new_status=serializer.validated_data['status'])
        except CardActionError as exc:
            raise ValidationError(str(exc))
        else:
            return Response(ShortCardRequestWithDetailUserSerializer(updated_card_request).data, status=status.HTTP_200_OK)
