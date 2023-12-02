from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ChatMessageViewSet

router = DefaultRouter()
router.register('', ChatMessageViewSet, basename='chat_messages')
urlpatterns = [
    path('chat-messages/', include(router.urls)),
]
