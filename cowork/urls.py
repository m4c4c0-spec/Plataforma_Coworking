from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    path('', views.bienvenida, name='bienvenida'),
    path('inicio/', views.inicio, name='inicio'),
    path('ingresar/', auth_views.LoginView.as_view(template_name='cowork/ingresar.html'), name='login'),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('usuarios/nuevo/', views.usuario_formulario, name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.usuario_formulario, name='usuario_editar'),
    path('usuarios/<int:pk>/desactivar/', views.usuario_desactivar, name='usuario_desactivar'),
    path('espacios/', views.espacios, name='espacios'),
    path('espacios/nuevo/', views.espacio_formulario, name='espacio_crear'),
    path('espacios/<int:pk>/editar/', views.espacio_formulario, name='espacio_editar'),
    path('espacios/<int:pk>/desactivar/', views.espacio_desactivar, name='espacio_desactivar'),
    path('reservas/', views.reservas, name='reservas'),
    path('reservas/nueva/', views.reserva_formulario, name='reserva_crear'),
    path('reservas/<int:pk>/', views.reserva_detalle, name='reserva_detalle'),
    path('reservas/<int:pk>/editar/', views.reserva_formulario, name='reserva_editar'),
    path('reservas/<int:pk>/cancelar/', views.reserva_cancelar, name='reserva_cancelar'),
    path('reservas/<int:pk>/confirmar/', views.reserva_confirmar, name='reserva_confirmar'),
    path('reservas/<int:pk>/finalizar/', views.reserva_finalizar, name='reserva_finalizar'),
]
