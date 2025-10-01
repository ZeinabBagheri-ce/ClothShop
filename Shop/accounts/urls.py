from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.user_register, name="register"),
    path("login/",    views.user_login,    name="login"),
    path("logout/",   views.user_logout,   name="logout"),

    path("profile/",          views.user_profile,       name="profile"),          # هوشمند
    path("profile/user/",     views.user_profile_user,  name="profile_user"),     # قالب کاربر
    path("profile/staff/",    views.user_profile_staff, name="profile_staff"),    # قالب کارکنان
    path("password/change/", views.CustomPasswordChangeView.as_view(), name="password_change"),
    path("ajax/cities/",      views.cities_by_province, name="ajax_cities"),
    path("orders/<int:order_id>/status/",
         views.staff_set_order_status, name="staff_set_order_status"),
]
