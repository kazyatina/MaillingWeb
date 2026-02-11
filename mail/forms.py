from django import forms
from django.core.exceptions import ValidationError
from django.forms import BooleanField, ModelForm, DateTimeInput

from mail.models import Clients, Message, Mailing


class ClientForm(forms.ModelForm):
    class Meta:
        model = Clients
        fields = ["name", "email", "comment"]
        exclude = ("owner",)

    def __init__(self, *args, **kwargs):
        """Стилизация формы."""
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, BooleanField):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"

        self.fields["name"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Введите имя клиента",
            }
        )
        self.fields["email"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Введите email",
            }
        )
        self.fields["comment"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Комментарий",
            }
        )

    def clean_email(self):
        """Валидация почты при рег-ции нового клиента."""
        email = self.cleaned_data.get("email")
        if email and not self.instance.pk:  # Если объект новый, pk будет None
            if Clients.objects.filter(email=email).exists():
                raise ValidationError("email уже существует")
        return email


class MessageForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)

        for field in self._meta.fields:
            self.fields[field].widget.attrs.update({"class": "form-control"})

    class Meta:
        model = Message
        fields = "theme", "text"
        exclude = ("owner",)


class MailingForm(ModelForm):
    clients = forms.ModelMultipleChoiceField(
        queryset=Clients.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["message"].queryset = Message.objects.filter(owner=user)
            self.fields["clients"].queryset = Clients.objects.filter(owner=user)

        for field in self._meta.fields:
            self.fields[field].widget.attrs.update({"class": "form-control"})

    class Meta:
        model = Mailing
        fields = ["name", "message", "clients", "start_time", "end_time"]
        exclude = ("status_active", "owner")

        widgets = {
            "start_date": DateTimeInput(
                attrs={"placeholder": "ДД.ММ.ГГГГ ЧЧ:ММ:СС", "type": "datetime-local"}
            ),
            "end_date": DateTimeInput(
                attrs={"placeholder": "ДД.ММ.ГГГГ ЧЧ:ММ:СС", "type": "datetime-local"}
            ),
        }


class MailingUpdateForm(ModelForm):
    clients = forms.ModelMultipleChoiceField(
        queryset=Clients.objects.all(),
        widget=forms.SelectMultiple(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super(MailingUpdateForm, self).__init__(*args, **kwargs)
        elems = self.fields
        elems["message"].widget.attrs.update({"class": "form-control"})
        elems["clients"].widget.attrs.update({"class": "form-control"})

    class Meta:
        model = Mailing
        fields = "message", "clients", "status_active"
