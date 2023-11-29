from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CardViewSet

router = DefaultRouter()
router.register('', CardViewSet, basename='cards')
urlpatterns = [
    path('cards/', include(router.urls)),
]
