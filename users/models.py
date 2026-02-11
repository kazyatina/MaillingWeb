from django.contrib.auth.models import AbstractUser
from django.db import models
from django_countries.fields import CountryField


class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, verbose_name="Ник", unique=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="Телефон"
    )
    token = models.CharField(
        max_length=100, verbose_name="token", blank=True, null=True
    )
    avatar = models.ImageField(
        upload_to="users/avatars/", blank=True, null=True, verbose_name="Аватар"
    )
    country = CountryField(max_length=50, blank=True, null=True, verbose_name="Страна")
    is_block = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        permissions = [
            ("can_all_view_users", "Просмотр всех пользователей"),
            ("can_blocked_user", "Блокировка пользователя"),
        ]

    def __str__(self):
        return self.email
