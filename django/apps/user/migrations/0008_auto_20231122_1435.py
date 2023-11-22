# Generated by Django 3.2.23 on 2023-11-22 11:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0007_user_city'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='city',
        ),
        migrations.AlterField(
            model_name='user',
            name='status',
            field=models.CharField(choices=[('looking_for', 'В поиске сожителя'), ('not_looking_for_anyone', 'Никого не ищу')], default='looking_for', max_length=100, verbose_name='Статус'),
        ),
    ]