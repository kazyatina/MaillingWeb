from django.shortcuts import render
from django.urls import path
from django.contrib.auth.views import LoginView
from .views import (
    UserCreateView,
    logout_view,
    confirm_email,
    UserListView,
    UserDetailView,
    UserUpdateView,
    UserBlockView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

app_name = "users"

urlpatterns = [
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", UserCreateView.as_view(), name="register"),
    path("email-confirm/<str:token>/", confirm_email, name="email-confirm"),
    path("users_list/", UserListView.as_view(), name="users_list"),
    path("user_detail/<int:pk>/", UserDetailView.as_view(), name="user_detail"),
    path("user_update/<int:pk>/", UserUpdateView.as_view(), name="user_update"),
    path("user/block/<int:pk>/", UserBlockView.as_view(), name="user_block"),
    path(
        "password-reset/",
        PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password-reset/done/",
        lambda request: render(request, "users/password_reset_done.html"),
        name="password_reset_done",
    ),  # страница, сообщающая об отправке письма
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]
