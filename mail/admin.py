from django.contrib import admin
from .models import Clients, Message, Mailing


@admin.register(Clients)
class ClientsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "comment")
    list_filter = ("name",)
    search_fields = ("name", "email")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "theme", "text")
    list_filter = ("theme",)
    search_fields = ("theme", "text")


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "message")
    list_filter = ("status",)
    search_fields = ("status", "message")
