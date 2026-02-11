from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from mail.forms import ClientForm, MessageForm, MailingForm, MailingUpdateForm
from mail.models import Clients, Mailing, EmailAttempt, Message

from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404


def main_page(request: HttpRequest):
    context = {
        "count_active_mailing": Mailing.objects.filter(status="Запущена").count(),
        "count_mailing": Mailing.objects.all().count(),
        "count_clients": Clients.objects.all().count(),
    }

    return render(request, template_name="main_page.html", context=context)


class ClientsListView(ListView):
    model = Clients
    template_name = "mail/clients_list.html"

    def get_queryset(self):
        user = self.request.user
        if user.has_perm("can_all_view_clients"):
            return Clients.objects.all()
        else:
            return Clients.objects.filter(owner=user)


@method_decorator(cache_page(60 * 15), name="dispatch")
class ClientsDetailView(DetailView):
    model = Clients


class ClientsCreateView(CreateView):
    model = Clients
    form_class = ClientForm
    template_name = "mail/clients_form.html"
    success_url = reverse_lazy("mail:clients_list")

    def form_valid(self, form):
        client = form.save()
        user = self.request.user  # Устанавливаем владельца на текущего пользователя
        client.owner = user
        client.save()
        return super().form_valid(form)


class ClientsUpdateView(UpdateView):
    model = Clients
    template_name = "mail/clients_form.html"
    form_class = ClientForm
    success_url = reverse_lazy("mail:clients_list")

    def get_object(self, queryset=None):
        user_id = self.kwargs.get("pk")
        return Clients.objects.get(pk=user_id)


class ClientsDeleteView(DeleteView):
    model = Clients
    success_url = reverse_lazy("mail:clients_list")


class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "mail/message_list.html"

    def get_queryset(self):
        user = self.request.user
        if user.has_perm("can_all_view_messages"):
            return Message.objects.all()
        else:
            return Message.objects.filter(owner=user)


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    context_object_name = "message"

    # низкоуровневое кеширование деталей сообщений
    def get_queryset(self):
        queryset = cache.get("message_queryset")
        if not queryset:
            queryset = super().get_queryset()
            cache.set(
                "message_queryset", queryset, 60 * 15
            )  # Кешируем данные на 15 минут
        return queryset


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mail/message_form.html"
    success_url = reverse_lazy("mail:message")

    def form_valid(self, form):
        message = form.save()
        user = self.request.user  # Устанавливаем владельца на текущего пользователя
        message.owner = user
        message.save()
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mail/message_form.html"
    success_url = reverse_lazy("mail:message")

    def form_valid(self, form):
        message = form.save(commit=False)
        user = self.request.user
        if (
            user.is_superuser
            or user.has_perm("mail.can_update_message")
            or message.owner == self.request.user
        ):
            message.save()
            return super().form_valid(form)
        raise PermissionDenied


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = "mail/message_delete.html"
    success_url = reverse_lazy("mail:message")

    def delete(self, request, *args, **kwargs):
        user = self.request.user
        if (
            user.is_superuser
            or user.has_perm("mail.can_delete_message")
            or user.owner == self.request.user
        ):
            return super().delete(request, *args, **kwargs)
        raise PermissionDenied


class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mail/mailing_list.html"

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.has_perm("mail.can_all_view_mailing"):
            return Mailing.objects.all()
        return Mailing.objects.filter(owner=user.pk)


@method_decorator(cache_page(60 * 15), name="dispatch")
class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = "mail/mailing_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["client_names"] = self.object.add_name_clients()
        return context

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        return obj

    def post(self, request, *args, **kwargs):
        mailing = self.get_object()
        if "send_mailing_to_clients" in request.POST:
            try:
                mailing.update_status()
                messages.success(request, "Рассылка запущена.")
            except ValueError as e:
                messages.error(request, str(e))
        return redirect("mail:mailing_sending", pk=mailing.pk)


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mail/mailing_form.html"
    success_url = reverse_lazy("mail:mailing")

    def get(self, request, *args, **kwargs):
        form = MailingForm(
            user=request.user, *args, **kwargs
        )  # Передача user через kwargs
        return render(request, "mail/mailing_form.html", {"form": form})

    def form_valid(self, form):
        mailing: Mailing = form.save(commit=False)
        user = self.request.user  # Устанавливаем владельца на текущего пользователя
        mailing.owner = user

        if not (user.is_superuser or user.has_perm("mail.can_create_mailing")):
            raise PermissionDenied

        mailing.save()
        form.save_m2m()
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingUpdateForm
    template_name = "mail/mailing_form.html"
    success_url = reverse_lazy("mail:mailing")

    def form_valid(self, form):
        mailing = form.save(commit=False)
        user = self.request.user

        if (
            user.is_superuser
            or user.has_perm("mail.can_update_mailing")
            or mailing.owner == self.request.user
        ):
            mailing.save()
            return super().form_valid(form)
        raise PermissionDenied


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mail/mailing_delete.html"
    success_url = reverse_lazy("mail:mailing")

    def delete(self, request, *args, **kwargs):
        user = self.request.user
        if (
            user.is_superuser
            or user.has_perm("mail.can_update_mailing")
            or user.owner == self.request.user
        ):
            return super().delete(request, *args, **kwargs)
        raise PermissionDenied


class EmailAttemptListView(LoginRequiredMixin, ListView):
    """Отображение отчетов по рассылкам"""

    model = EmailAttempt
    template_name = "mail/mailing_attempts_list.html"
    context_object_name = "emailattempts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emailattempts = self.get_queryset()

        count_successful = emailattempts.filter(status="Успешно").count()
        count_failed = emailattempts.filter(status="Отклонено").count()
        count_all = emailattempts.all().count()

        context["count_successful"] = count_successful
        context["count_failed"] = count_failed
        context["count_all"] = count_all
        context["mailing_attempts"] = emailattempts

        return context


class MailingAttemptDetailView(DetailView):
    model = EmailAttempt
    template_name = "mail/mailing_attempt_detail.html"


class StatisticListView(LoginRequiredMixin, ListView):
    """Отображение статистики"""

    model = EmailAttempt
    template_name = "mail/statistic_list.html"
    context_object_name = "statistic"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emailattempts = self.get_queryset()

        count_successful = emailattempts.filter(status="Успешно").count()
        count_failed = emailattempts.filter(status="Отклонено").count()
        count_all = emailattempts.all().count()

        context["count_successful"] = count_successful
        context["count_failed"] = count_failed
        context["count_all"] = count_all

        return context


class MailingActiveStatusView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Mailing
    fields = ["status_active"]
    template_name = "mail/mailing_active_status_confirm.html"
    success_url = reverse_lazy("mail:mailing")
    permission_required = "mail.can_deactivate_mailing"

    def get_object(self, queryset=None):
        return get_object_or_404(Mailing, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_status"] = self.object.status_active
        context["new_status"] = (
            "Отключить" if self.object.status_active == "active" else "Включить"
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status_active == "active":
            new_status = "inactive"
        elif self.object.status_active == "inactive":
            new_status = "active"
        else:
            return redirect(self.success_url)

        self.object.status_active = new_status
        self.object.save()

        return redirect(self.success_url)
