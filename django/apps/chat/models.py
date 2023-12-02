from django.db import models

from apps.card.models import Card
from apps.user.models import User


class ChatMessage(models.Model):
    """Сообщение для чата с пользователем"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='sent_messages',
                               verbose_name='Отправитель (если None, то сообщение является системным)')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages',
                                 verbose_name='Получатель')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='chat_messages',
                             verbose_name='Связанная карточка')
    content = models.CharField(max_length=2048, verbose_name='Содержимое')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания')

    class Meta:
        verbose_name = 'Сообщение для чата с пользователем'
        verbose_name_plural = 'Сообщения для чата с пользователем'

    def __str__(self):
        return f'{self.sender} {self.receiver} {self.short_content}'

    @property
    def is_system(self) -> bool:
        """Является ли сообщение системным"""
        return not bool(self.sender)

    @property
    def short_content(self) -> str:
        """Отрывок сообщения"""
        if len(self.content) > 100:
            return self.content[:100].rstrip() + '...'
        return self.content
