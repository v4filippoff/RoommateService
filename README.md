Сервис для поиска сожителей
=====================

Первоначальная установка
------------------------

- Скопируйте и настройте переменные окружения .env:
  `cp .env.dist .env`
  
- Запустите контейнеры:
  `docker-compose up -d --build`

---  

Полезные команды
------------------------

Накатить миграции
```
docker-compose exec django python manage.py migrate
```

Создать супер-пользователя (для локальной базы)
```
docker-compose exec django python manage.py createsuperuser
```

Команда, если не грузится статика в админке
```
docker-compose exec django python manage.py collectstatic
```

Применить фикстуры
```
docker-compose exec -T django bash -c "python manage.py loaddata apps/*/fixtures/*.yaml apps/*/fixtures/dev/*.yaml"
```

Полезные ссылки
------------------------

Документация по api
```
/api/docs/
```

Админка
```
/admin/
```
