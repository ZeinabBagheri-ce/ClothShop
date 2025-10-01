from django.urls import include, path
from .views import *

app_name = 'home'

urlpatterns = [
    path('', home, name='index'),
    path('about/',about, name='about'),
]