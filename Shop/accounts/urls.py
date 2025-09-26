from . import views
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    path("register/", views.user_register,    name="register"),
    path("login/",    views.user_login,  name="login"),
    path("logout/",   views.user_logout, name="logout"),
    path("profile/", views.user_profile, name="profile"),
    path("password_change/", views.CustomPasswordChangeView.as_view(), name="password_change"),
path("ajax/cities/", views.cities_by_province, name="ajax_cities"),
]

