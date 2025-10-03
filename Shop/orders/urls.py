from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("success/<int:order_id>/", views.order_success, name="success"),
    path("payment-failed/<int:order_id>/", views.payment_failed, name="payment_failed_with_id"),
    path("payment-failed/", views.payment_failed, name="payment_failed"),
]
