# Generated by Django 3.2.22 on 2023-11-03 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='dob',
            field=models.DateField(null=True, verbose_name='Дата рождения'),
        ),
    ]
