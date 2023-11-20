from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets

from apps.city.models import City
from apps.city.serializers import CitySerializer


@extend_schema_view(
    list=extend_schema(
        summary='Список городов',
    ),
    retrieve=extend_schema(
        summary='Детальный просмотр города',
    )
)
class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all().order_by('-order')
    serializer_class = CitySerializer
