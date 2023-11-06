from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator, FileExtensionValidator
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class CustomUserManager(BaseUserManager):
    """Переопределенный менеджер модели пользователя."""

    def create_user(self, phone_number, password=None, **kwargs):
        user = self.model(phone_number=phone_number, **kwargs)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, phone_number, password, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        return self.create_user(phone_number=phone_number, password=password, **kwargs)


class User(AbstractBaseUser, PermissionsMixin):
    """Пользователь"""

    class Genders(models.TextChoices):
        """Пол"""
        MALE = 'male', 'Мужчина'
        FEMALE = 'female', 'Женщина'

    class Statuses(models.TextChoices):
        """Статус"""
        LOOKING_FOR = 'looking_for', 'В поиске сожителя'
        NOT_LOOKING_FOR_ANYONE = 'not_looking_for_anyone', 'Никого не ищу'

    def upload_avatar(instance, filename):
        return f'users/{instance.id}/avatar/{filename}'

    phone_number = PhoneNumberField(verbose_name='Номер телефона', unique=True,
                                    error_messages={'unique': 'Пользователь с таким номером телефона уже существует.'})
    first_name = models.CharField(max_length=150, verbose_name='Имя', blank=True,
                                  validators=[RegexValidator(regex=r'^[a-zA-Zа-яА-Я]+$', message='Возможны только буквы.')])
    last_name = models.CharField(max_length=150, verbose_name='Фамилия', blank=True,
                                 validators=[RegexValidator(regex=r'^[a-zA-Zа-яА-Я]+$', message='Возможны только буквы.')])
    patronymic = models.CharField(max_length=150, verbose_name='Отчество', blank=True,
                                  validators=[RegexValidator(regex=r'^[a-zA-Zа-яА-Я]+$', message='Возможны только буквы.')])
    email = models.EmailField(verbose_name='Email', blank=True)
    dob = models.DateField(verbose_name='Дата рождения', null=True, blank=True,)
    gender = models.CharField(max_length=6, verbose_name='Пол', choices=Genders.choices, blank=True,)
    status = models.CharField(max_length=100, verbose_name='Статус', choices=Statuses.choices,
                              default=Statuses.LOOKING_FOR, blank=True)
    about_me = models.CharField(max_length=2048, verbose_name='Обо мне', blank=True)
    avatar = models.ImageField(upload_to=upload_avatar, verbose_name='Аватарка', blank=True, null=True,
                               validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'heic'])])

    is_staff = models.BooleanField(verbose_name='Статус персонала', default=False,
                                   help_text='Определяет, может ли пользователь войти на сайт администратора.')
    is_active = models.BooleanField(verbose_name='Активный', default=True,
                                    help_text='Указывает, следует ли считать этого пользователя активным')
    date_joined = models.DateTimeField('Дата создания', default=timezone.now)

    USERNAME_FIELD = 'phone_number'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.get_full_name()} ({self.phone_number})'

    def get_full_name(self) -> str:
        self.last_name: str
        self.first_name: str
        self.patronymic: str
        return f'{self.last_name.title()} {self.first_name.title()} {self.patronymic.title()}'.strip()

    def get_short_name(self) -> str:
        self.first_name: str
        return self.first_name.title().strip()


class CodeAbstract(models.Model):
    """Абстрактная модель для шестизначного кода"""
    CODE_LENGTH = 6

    code = models.CharField(validators=[
        RegexValidator(regex=r'^\d{' + str(CODE_LENGTH) + r'}$', message=f'Возможны только {CODE_LENGTH} цифр от 0 до 9')
    ], max_length=CODE_LENGTH, verbose_name='Код')
    expiration_date = models.DateTimeField(verbose_name='Срок годности')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Время создания')
    is_used = models.BooleanField(default=False, verbose_name='Использован')

    class Meta:
        verbose_name = 'Абстрактный код'
        verbose_name_plural = 'Абстрактные коды'
        abstract = True


class AuthorizationCode(CodeAbstract):
    """Модель для кода авторизации
    login: номер телефона, email и тд.
    """
    login = models.CharField(max_length=100, verbose_name='Логин')

    class Meta:
        verbose_name = 'Код для авторизации'
        verbose_name_plural = 'Коды для авторизации'

    def __str__(self):
        return f'{self.login} - {self.code}'
