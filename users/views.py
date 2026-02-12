import secrets

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from dotenv import load_dotenv

from django.core.mail import send_mail, EmailMultiAlternatives
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, DetailView, UpdateView, ListView, FormView
from django.contrib.auth import logout

from config.settings import EMAIL_HOST_USER
from mail.models import Mailing
from users.forms import CustomUserCreationForm, PasswordResetRequestForm
from django.shortcuts import get_object_or_404, redirect, render

from users.models import CustomUser

load_dotenv(override=True)


class UserCreateView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "users/users_form.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = form.save()
        user.is_block = True
        token = secrets.token_hex(16)
        user.token = token
        user.save()
        host = self.request.get_host()
        url = f"http://{host}/users/email-confirm/{token}/"
        send_mail(
            subject="Подтверждение регистрации",
            message=f"Пожалуйста, подтвердите свою регистрацию, перейдя по ссылке: {url}",
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        user = form.save()
        send_mail(
            subject="Добро пожаловать в наш сервис",
            message="Спасибо, что зарегистрировались в нашем сервисе!",
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        return super().form_valid(form)


def confirm_email(request, token):
    """Обработать подтверждение"""
    # Найти пользователя по токену
    user = get_object_or_404(CustomUser, token=token)
    user.is_block = False
    user.save()
    return redirect(reverse("users:login"))


# Представление для выхода


def logout_view(request):
    logout(request)
    return redirect("mail:main_page")


class UserListView(ListView):
    model = CustomUser
    template_name = "users/users_list.html"


class UserDetailView(DetailView):
    model = CustomUser
    template_name = "users/user_detail.html"


class UserUpdateView(UpdateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = "users/users_form.html"

    def get_success_url(self):
        return reverse("users:user_detail", kwargs={"pk": self.object.pk})


class UserBlockView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = CustomUser
    fields = ["is_block"]
    template_name = "users/user_confirm_block.html"
    success_url = reverse_lazy("users:users_list")
    permission_required = "users.can_blocked_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_status"] = (
            "заблокирован" if self.object.is_block else "активен"
        )
        context["new_status_action"] = (
            "разблокировать" if self.object.is_block else "заблокировать"
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_block:
            new_status = False
        else:
            new_status = True

        self.object.is_block = new_status
        self.object.save()
        Mailing.objects.filter(owner=self.object, status=True).update(status=False)
        return redirect(self.success_url)


class PasswordResetRequestView(FormView):
    """
    Представление для запроса сброса пароля.
    Пользователь вводит email, на который будет отправлена ссылка для сброса.
    """

    template_name = "users/password_reset_request.html"
    success_url = reverse_lazy(
        "users:password_reset_done"
    )  # URL после успешной отправки письма
    form_class = PasswordResetRequestForm

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        try:
            user = CustomUser.objects.get(email=email)
            # Генерируем уникальный токен и UID пользователя
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_url = f"{self.request.scheme}://{self.request.get_host()}{reverse_lazy('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"

            self._send_reset_email(user, reset_url)

            messages.success(
                self.request, "Ссылка для сброса пароля отправлена на ваш email."
            )
            return redirect(self.success_url)
        except CustomUser.DoesNotExist:
            messages.warning(
                self.request,
                "Если такой email существует, ссылка для сброса пароля будет отправлена.",
            )
            return redirect(self.success_url)
        except Exception as e:
            messages.error(self.request, f"Произошла ошибка при отправке письма: {e}")
            return redirect("users:password_reset_request")  # Возврат на форму запроса

    def _send_reset_email(self, user, reset_url):
        """
        Отправляет письмо со ссылкой для сброса пароля.
        Использует render_to_string для создания HTML-сообщения из шаблона.
        """
        subject = "Восстановление пароля"
        from_email = EMAIL_HOST_USER
        to_email = [user.email]

        context = {
            "user": user,
            "reset_url": reset_url,
        }
        message_html = render_to_string("users/password_reset_email.html", context)

        # Создаем и отправляем письмо
        msg = EmailMultiAlternatives(subject, message_html, from_email, to_email)
        msg.attach_alternative(message_html, "text/html")  # Отправляем как HTML
        msg.send()


class PasswordResetConfirmView(View):
    """
    Представление для подтверждения сброса пароля.
    Проверяет токен и UID, затем показывает форму для ввода нового пароля.
    """

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (CustomUser.DoesNotExist, ValueError, TypeError, OverflowError):
            user = None

        if user and default_token_generator.check_token(user, token):
            # Токен валиден, показываем форму для ввода нового пароля
            return render(
                request,
                "users/password_reset_confirm.html",
                {"uidb64": uidb64, "token": token},
            )
        else:
            # Токен невалиден или истек
            messages.error(
                request, "Ссылка для сброса пароля недействительна или истекла."
            )
            return redirect("users:password_reset_request")

    def post(self, request, uidb64, token):
        form_password1 = request.POST.get("password_new")
        form_password2 = request.POST.get("password_new_confirm")

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (CustomUser.DoesNotExist, ValueError, TypeError, OverflowError):
            user = None

        if user and default_token_generator.check_token(user, token):
            if form_password1 and form_password1 == form_password2:
                user.set_password(form_password1)
                user.save()
                messages.success(request, "Ваш пароль был успешно изменен.")
                return redirect("users:login")
            else:
                messages.error(request, "Пароли не совпадают или не были введены.")
        else:
            messages.error(request, "Ошибка при сбросе пароля. Ссылка недействительна.")

        return redirect("users:password_reset_request")
