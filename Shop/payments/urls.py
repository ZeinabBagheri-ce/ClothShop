from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("zarinpal/start/<int:order_id>/", views.zarinpal_start, name="zarinpal_start"),
    path("zarinpal/callback/", views.zarinpal_callback, name="zarinpal_callback"),
]
