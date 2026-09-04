from django.urls import path

from . import views


urlpatterns = [
    path('', views.bienvenida, name='bienvenida'),
    path('inicio/', views.inicio, name='inicio'),
]
