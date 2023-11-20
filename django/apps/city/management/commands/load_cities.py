from os import listdir
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ...models import City


class Command(BaseCommand):
    help = 'Загрузить города из текстового файла в БД'

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='?', type=str, default='cities.txt')

    def handle(self, *args, **options):
        big_cities = ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань', 'Нижний Новгород',
                      'Красноярск', 'Челябинск', 'Самара', 'Уфа', 'Ростов-на-Дону', 'Краснодар', 'Омск', 'Воронеж',
                      'Пермь', 'Волгоград']

        file_path = Path(__file__).parent.parent.parent / Path(options['filename'])
        try:
            with open(file_path, 'r') as f:
                for city in f:
                    normalized_city = city.strip().title()
                    City.objects.get_or_create(
                        name=normalized_city,
                        order=(10000 - big_cities.index(normalized_city) if normalized_city in big_cities else 0)
                    )
        except FileNotFoundError:
            raise CommandError('Файл не найден.')
