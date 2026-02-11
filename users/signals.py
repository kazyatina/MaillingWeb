from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group


@receiver(post_save, sender=User)
def assign_permissions(sender, instance, created, **kwargs):
    if created:
        # Например, добавляем пользователя в группу "Новички"
        group = Group.objects.get(name="Пользователи")
        instance.groups.add(group)


# Для автоматического сброса кэша
# from django.core.cache import cache
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Review
#
# @receiver(post_save, sender=Review)
# def clear_cache(sender, instance, **kwargs):
#     cache_key = f'book_detail_{instance.book.id}'
#     cache.delete(cache_key)
