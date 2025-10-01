from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.product_list, name="list"),
    path("category/<str:slug>/", views.category_detail, name="category"),
    path("brand/<str:slug>/", views.brand_detail, name="brand"),
    path("<str:slug>/", views.product_detail, name="detail"),
]
