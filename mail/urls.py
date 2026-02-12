from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from mail.views import (
    main_page,
    ClientsListView,
    ClientsCreateView,
    ClientsUpdateView,
    ClientsDetailView,
    ClientsDeleteView,
    MailingListView,
    MailingCreateView,
    MailingUpdateView,
    MailingDeleteView,
    MessageListView,
    MessageCreateView,
    MessageUpdateView,
    MessageDeleteView,
    EmailAttemptListView,
    MailingDetailView,
    MessageDetailView,
    MailingAttemptDetailView,
    StatisticListView,
    MailingActiveStatusView,
)

app_name = "mail"

urlpatterns = [
    path("", main_page, name="main_page"),
    path("clients/", ClientsListView.as_view(), name="clients_list"),
    path("clients/create/", ClientsCreateView.as_view(), name="client_create"),
    path("clients/update/<int:pk>/", ClientsUpdateView.as_view(), name="client_update"),
    path("clients/detail/<int:pk>/", ClientsDetailView.as_view(), name="client_detail"),
    path("clients/<int:pk>/delete/", ClientsDeleteView.as_view(), name="client_delete"),
    path("mail/", MailingListView.as_view(), name="mailing"),
    path("detail_mailing/<int:pk>", MailingDetailView.as_view(), name="detail_mailing"),
    path("create_mailing/", MailingCreateView.as_view(), name="create_mailing"),
    path("update_mailing/<int:pk>", MailingUpdateView.as_view(), name="update_mailing"),
    path("delete_mailing/<int:pk>", MailingDeleteView.as_view(), name="delete_mailing"),
    path("success/<int:pk>", MailingDetailView.as_view(), name="mailing_sending"),
    path("status/<int:pk>/", MailingActiveStatusView.as_view(), name="mailing_status"),
    path("message/", MessageListView.as_view(), name="message"),
    path("create_message/", MessageCreateView.as_view(), name="create_message"),
    path("detail_message/<int:pk>", MessageDetailView.as_view(), name="detail_message"),
    path("update_message/<int:pk>", MessageUpdateView.as_view(), name="update_message"),
    path("delete_message/<int:pk>", MessageDeleteView.as_view(), name="delete_message"),
    path("attempts/", EmailAttemptListView.as_view(), name="mailing_attempts_list"),
    path(
        "attempts/<int:pk>/",
        MailingAttemptDetailView.as_view(),
        name="mailing_attempt_detail",
    ),
    path("statistic/", StatisticListView.as_view(), name="statistic"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
