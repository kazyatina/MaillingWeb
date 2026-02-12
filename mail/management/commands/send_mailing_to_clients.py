from config.settings import EMAIL_HOST_USER

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from mail.models import Mailing, EmailAttempt

# class Command(BaseCommand):
#     help = 'Отправка рассылки по требованию'
#
#     def handle(self, *args, **kwargs):
#         # Логика для выбора нужной рассылки
#         mailing = Mailing.objects.get('mailing_id')
#         for client in mailing.clients.all():
#             send_mail(
#                 subject=self.message.theme,
#                 message=self.message.text,
#                 from_email=EMAIL_HOST_USER,
#                 recipient_list=[client.email],
#                 fail_silently=False,
#             )
#         self.stdout.write(self.style.SUCCESS('Рассылка успешно отправлена!'))


class Command(BaseCommand):
    help = "Вручную запускает рассылку для указанной рассылки ID."

    def add_arguments(self, parser):
        """Добавляет аргументы командной строки."""
        parser.add_argument(
            "mailing_id", type=int, help="ID рассылки, которую нужно запустить."
        )

    def handle(self, *args, **kwargs):
        """Основная логика выполнения команды."""
        mailing_id = kwargs["mailing_id"]

        try:
            # Получаем объект рассылки по ID
            mailing = Mailing.objects.get(id=mailing_id)
        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Рассылка с ID {mailing_id} не найдена.")
            )
            return

        now = timezone.now()

        # 1. Проверка времени запуска
        if not (mailing.start_time <= now <= mailing.end_time):
            self.stdout.write(
                self.style.ERROR(
                    f'Невозможно запустить рассылку "{mailing.name}". '
                    f"Текущее время ({now}) вне допустимого диапазона ({mailing.start_time} - {mailing.end_time})."
                )
            )
            return

        self.stdout.write(f'Начинается запуск рассылки "{mailing.name}"...')

        # 2. Определение клиентов
        clients = mailing.clients.all()
        if not clients.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Нет клиентов для данной рассылки. Рассылка не будет отправлена."
                )
            )
            return

        # 3. Отправка писем и логирование попыток
        successful_sends = 0
        for client in clients:
            try:
                # Отправка письма
                send_mail(
                    subject=mailing.message.theme,
                    message=mailing.message.text,
                    from_email=EMAIL_HOST_USER,
                    recipient_list=[client.email],
                    fail_silently=False,
                )
                # Успешная отправка, создаем запись в логах
                EmailAttempt.objects.create(
                    mailing=mailing,
                    attempt_time=now,
                    status="Успешно",
                    server_response="Письмо успешно отправлено.",
                    client=client,
                )
                successful_sends += 1
            except Exception as e:
                # Ошибка при отправке, создаем запись в логах с ошибкой
                EmailAttempt.objects.create(
                    mailing=mailing,
                    attempt_time=now,
                    status="Не успешно",
                    server_response=str(e),
                    client=client,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Рассылка "{mailing.name}" завершена. '
                f'Успешно отправлено: {successful_sends}/ клиентам: {clients.count()}.'
            )
        )
