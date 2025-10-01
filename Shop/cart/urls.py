from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="detail"),
    path("add/", views.add_to_cart, name="add"),
    path("remove/<int:variation_id>/", views.remove_from_cart, name="remove"),
    path("update/<int:variation_id>/", views.update_cart, name="update"),
]
