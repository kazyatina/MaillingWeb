from django.core.management import BaseCommand
from users.models import CustomUser


class Command(BaseCommand):
    help = "Добавление Супер пользователя"

    def handle(self, *args, **kwargs):
        user = CustomUser.objects.create(email="pro@yandex.ru")
        user.set_password("iuytre")
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
