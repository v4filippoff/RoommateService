from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import UserViewSet

router = DefaultRouter()
router.register('', UserViewSet, basename='users')
urlpatterns = [
    path('users/', include(router.urls)),
    path('users/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
