from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Добавление группы Менеджеры"

    def handle(self, *args, **options):
        managers_group, created = Group.objects.get_or_create(name="Менеджеры")
        if created:
            permissions = Permission.objects.filter(
                codename__in=[
                    "can_all_view_clients",
                    "can_all_view_mailing",
                    "can_all_view_users",
                    "can_blocked_user",
                    "can_deactivate_mailing",
                ]
            )
            managers_group.permissions.add(permissions)
            self.stdout.write(self.style.SUCCESS("Группа создана, права добавлены."))
        else:
            self.stdout.write(self.style.WARNING("Группа уже существует."))
