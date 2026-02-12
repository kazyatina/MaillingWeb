from datetime import time, datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from users.models import CustomUser


class Clients(models.Model):
    """Модель «Получатель рассылки»"""

    email = models.CharField(max_length=150, verbose_name="почта", unique=True)
    name = models.CharField(max_length=150, verbose_name="ФИО")
    comment = models.TextField(verbose_name="Комментарий", null=True, blank=True)

    owner = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="subscriber_owner", default=1
    )

    def __str__(self):
        """Определяет строковое представление объекта"""
        return f"{self.name}, {self.email}, {self.comment}"

    class Meta:
        """Используется для добавления метаданных к модели. Он определяет такие свойства, как порядок сортировки,
        наименование модели в единственном и множественном числе и другие"""

        # verbose_name определяют отображаемое имя модели в единственном и множественном числе
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"

        permissions = [
            ("can_all_view_clients", "Просмотр всех получателей"),
            ("can_delete_client", "Удаление получателя"),
            ("can_create_client", "Добавление получателя"),
        ]


class Message(models.Model):
    """Управление сообщениями"""

    theme = models.CharField(max_length=150, verbose_name="Тема")
    text = models.TextField(null=True, blank=True, verbose_name="Содержание")

    created_at = models.DateTimeField(
        default=timezone.now, null=False, verbose_name="Дата и время создания"
    )
    owner = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="message_owner", default=1
    )

    def __str__(self):
        """Определяет строковое представление объекта"""
        return self.theme

    class Meta:
        """Используется для добавления метаданных к модели. Он определяет такие свойства, как порядок сортировки,
        наименование модели в единственном и множественном числе и другие"""

        # verbose_name определяют отображаемое имя модели в единственном и множественном числе
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

        permissions = [
            ("can_all_view_messages", "Просмотр всех сообщений"),
            ("can_delete_message", "Удаление сообщения"),
            ("can_update_message", "Обновление сообщения"),
            ("can_create_message", "Добавление сообщения"),
        ]


class Mailing(models.Model):
    """Модель «Рассылка»"""

    STATUS_CREATED = "Создана"
    STATUS_STARTED = "Запущена"
    STATUS_COMPLETED = "Завершена"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_STARTED, "Запущена"),
        (STATUS_COMPLETED, "Завершена"),
    ]
    name = models.CharField(
        max_length=100, verbose_name="Название рассылки", default="Введите название"
    )
    start_time = models.DateTimeField(
        verbose_name="Дата и время начала рассылки",
        default=timezone.make_aware(
            datetime.combine(timezone.now().date(), time(12, 0))
        ),
    )
    end_time = models.DateTimeField(
        verbose_name="Дата и время окончания отправки",
        default=timezone.make_aware(
            datetime.combine(timezone.now().date(), time(22, 0))
        ),
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name="Статус",
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        verbose_name="Сообщение",
        related_name="mailings",
    )
    clients = models.ManyToManyField(
        Clients, related_name="clients", verbose_name="Получатели"
    )

    status_active = models.CharField(
        max_length=20,
        default="active",
        choices=[("active", "Активна"), ("inactive", "Неактивна")],
        verbose_name="Активность",
    )

    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="mailing_owner",
        default=1,
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        permissions = [
            ("can_all_view_mailing", "Просмотр всех рассылок"),
            ("can_delete_mailing", "Удаление рассылки"),
            ("can_update_mailing", "Обновление рассылки"),
            ("can_create_mailing", "Добавление рассылки"),
            ("can_deactivate_mailing", "Отключение рассылки"),
        ]

    def __str__(self):
        return self.name

    def add_name_clients(self):
        clients = self.clients.all()
        client_names = [client.name for client in clients]
        return ", ".join(client_names)

    def update_status(self):
        now = timezone.now()
        if self.status_active is True:
            if now < self.start_time:
                new_status = "Создана"
            elif self.start_time <= now <= self.end_time:
                new_status = "Запущена"
            else:
                new_status = "Завершена"

            if self.status != new_status:
                self.status = new_status
                self.save(update_fields=["status"])
        # else:
        #     raise ValidationError("Невозможно запустить рассылку")

    def clean(self):
        """Валидация: start_time не может быть в прошлом.start_time должен быть раньше end_time."""

        if not self.start_time and not isinstance(self.start_time, datetime):
            raise ValidationError(
                "Неправильный формат даты. Используйте формат ДД.ММ.ГГГГ ЧЧ:ММ:СС."
            )

        if not self.end_time and not isinstance(self.end_time, datetime):
            raise ValidationError(
                "Неправильный формат даты. Используйте формат ДД.ММ.ГГГГ ЧЧ:ММ:СС."
            )

        if self.start_time < timezone.now():
            raise ValidationError("Время начала не может быть в прошлом.")

        if self.start_time >= self.end_time:
            raise ValidationError("Время начала должно быть меньше времени окончания.")


class EmailAttempt(models.Model):
    """Модель «Попытка отправки письма»"""

    STATUS_CHOICES = (
        ("successful", "Успешно"),
        ("failed", "Не успешно"),
    )

    attempt_time = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата и время попытки"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, verbose_name="Статус"
    )
    server_response = models.TextField(verbose_name="Ответ почтового сервера")
    mailing = models.ForeignKey(
        Mailing, on_delete=models.CASCADE, verbose_name="Рассылка"
    )

    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name="emails")
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="emailattempt_owner",
        default=1,
    )

    def __str__(self):
        return f"Попытка отправки для {self.client.email} - {self.status}"

    def clean(self):
        now = timezone.now()
        if self.mailing.start_time <= now <= self.mailing.end_time:
            print("Отправка разрешена.")
        else:
            raise ValidationError("Отправка запрещена.")
