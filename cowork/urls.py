"""Rutas de las pantallas (path()) y de las APIs (DefaultRouter)."""

from django.urls import include, path
from rest_framework import routers

from . import views


# API de consulta MySQL con SQLAlchemy: GET de colección y detalle.
enrutador_mysql = routers.DefaultRouter(use_regex_path=False)
enrutador_mysql.register(r'sedes', views.SedeMySQLViewSet, basename='sede')
enrutador_mysql.register(r'tipos-espacio', views.TipoEspacioMySQLViewSet, basename='tipo-espacio')
enrutador_mysql.register(r'usuarios', views.UsuarioMySQLViewSet, basename='usuario')
enrutador_mysql.register(r'espacios', views.EspacioMySQLViewSet, basename='espacio')
enrutador_mysql.register(r'reservas', views.ReservaMySQLViewSet, basename='reserva')

# API de gestión: el router genera las rutas de los métodos que implementa cada
# ViewSet (list, create, retrieve, update, partial_update, destroy) y de sus @action.
enrutador = routers.DefaultRouter(use_regex_path=False)
enrutador.register(r'sedes', views.SedeViewSet, basename='sede')
enrutador.register(r'tipos-espacio', views.TipoEspacioViewSet, basename='tipo-espacio')
enrutador.register(r'usuarios', views.UsuarioViewSet, basename='usuario')
enrutador.register(r'espacios', views.EspacioViewSet, basename='espacio')
enrutador.register(r'reservas', views.ReservaViewSet, basename='reserva')
enrutador.register(r'historial-reservas', views.HistorialEstadoReservaViewSet, basename='historial-reserva')
enrutador.register(r'eventos-auditoria', views.EventoAuditoriaViewSet, basename='evento-auditoria')
enrutador.register(r'reportes', views.ReporteViewSet, basename='reporte')

urlpatterns = [
    path('', views.bienvenida, name='bienvenida'),
    path('inicio/', views.inicio, name='inicio'),
    path(
        'ingresar/', views.AutenticacionViewSet.as_view({'get': 'ingresar', 'post': 'ingresar'}),
        name='login',
    ),
    path(
        'salir/', views.AutenticacionViewSet.as_view({'post': 'salir'}),
        name='logout',
    ),
    path(
        'usuarios/', views.UsuarioPantallaViewSet.as_view({'get': 'list'}),
        name='usuarios',
    ),
    path(
        'usuarios/nuevo/', views.UsuarioPantallaViewSet.as_view({'get': 'crear', 'post': 'crear'}),
        name='usuario_crear',
    ),
    path(
        'usuarios/<int:pk>/editar/', views.UsuarioPantallaViewSet.as_view({'get': 'editar', 'post': 'editar'}),
        name='usuario_editar',
    ),
    path(
        'usuarios/<int:pk>/desactivar/', views.UsuarioPantallaViewSet.as_view({'get': 'desactivar', 'post': 'desactivar'}),
        name='usuario_desactivar',
    ),
    path(
        'usuarios/<int:pk>/activar/', views.UsuarioPantallaViewSet.as_view({'get': 'activar', 'post': 'activar'}),
        name='usuario_activar',
    ),
    path(
        'usuarios/<int:pk>/eliminar/', views.UsuarioPantallaViewSet.as_view({'get': 'eliminar', 'post': 'eliminar'}),
        name='usuario_eliminar',
    ),
    path(
        'espacios/', views.EspacioPantallaViewSet.as_view({'get': 'list'}),
        name='espacios',
    ),
    path(
        'espacios/nuevo/', views.EspacioPantallaViewSet.as_view({'get': 'crear', 'post': 'crear'}),
        name='espacio_crear',
    ),
    path(
        'espacios/<int:pk>/editar/', views.EspacioPantallaViewSet.as_view({'get': 'editar', 'post': 'editar'}),
        name='espacio_editar',
    ),
    path(
        'espacios/<int:pk>/desactivar/', views.EspacioPantallaViewSet.as_view({'get': 'desactivar', 'post': 'desactivar'}),
        name='espacio_desactivar',
    ),
    path(
        'espacios/<int:pk>/eliminar/', views.EspacioPantallaViewSet.as_view({'get': 'eliminar', 'post': 'eliminar'}),
        name='espacio_eliminar',
    ),
    path(
        'sedes/', views.SedePantallaViewSet.as_view({'get': 'list'}),
        name='sedes',
    ),
    path(
        'sedes/nueva/', views.SedePantallaViewSet.as_view({'get': 'crear', 'post': 'crear'}),
        name='sede_crear',
    ),
    path(
        'sedes/<int:pk>/editar/', views.SedePantallaViewSet.as_view({'get': 'editar', 'post': 'editar'}),
        name='sede_editar',
    ),
    path(
        'sedes/<int:pk>/desactivar/', views.SedePantallaViewSet.as_view({'get': 'desactivar', 'post': 'desactivar'}),
        name='sede_desactivar',
    ),
    path(
        'sedes/<int:pk>/eliminar/', views.SedePantallaViewSet.as_view({'get': 'eliminar', 'post': 'eliminar'}),
        name='sede_eliminar',
    ),
    path(
        'tipos-espacio/', views.TipoEspacioPantallaViewSet.as_view({'get': 'list'}),
        name='tipos_espacio',
    ),
    path(
        'tipos-espacio/nuevo/', views.TipoEspacioPantallaViewSet.as_view({'get': 'crear', 'post': 'crear'}),
        name='tipo_espacio_crear',
    ),
    path(
        'tipos-espacio/<int:pk>/editar/', views.TipoEspacioPantallaViewSet.as_view({'get': 'editar', 'post': 'editar'}),
        name='tipo_espacio_editar',
    ),
    path(
        'tipos-espacio/<int:pk>/eliminar/', views.TipoEspacioPantallaViewSet.as_view({'get': 'eliminar', 'post': 'eliminar'}),
        name='tipo_espacio_eliminar',
    ),
    path(
        'reservas/', views.ReservaPantallaViewSet.as_view({'get': 'list'}),
        name='reservas',
    ),
    path(
        'reservas/nueva/', views.ReservaPantallaViewSet.as_view({'get': 'crear', 'post': 'crear'}),
        name='reserva_crear',
    ),
    path(
        'reservas/<int:pk>/', views.ReservaPantallaViewSet.as_view({'get': 'retrieve'}),
        name='reserva_detalle',
    ),
    path(
        'reservas/<int:pk>/editar/', views.ReservaPantallaViewSet.as_view({'get': 'editar', 'post': 'editar'}),
        name='reserva_editar',
    ),
    path(
        'reservas/<int:pk>/cancelar/', views.ReservaPantallaViewSet.as_view({'get': 'cancelar', 'post': 'cancelar'}),
        name='reserva_cancelar',
    ),
    path(
        'reservas/<int:pk>/confirmar/', views.ReservaPantallaViewSet.as_view({'post': 'confirmar'}),
        name='reserva_confirmar',
    ),
    path(
        'reservas/<int:pk>/finalizar/', views.ReservaPantallaViewSet.as_view({'post': 'finalizar'}),
        name='reserva_finalizar',
    ),
    path(
        'reservas/<int:pk>/eliminar/', views.ReservaPantallaViewSet.as_view({'get': 'eliminar', 'post': 'eliminar'}),
        name='reserva_eliminar',
    ),
    path(
        'reportes/', views.ReportePantallaViewSet.as_view({'get': 'generar'}),
        name='reportes',
    ),
    path('api/mysql/', include((enrutador_mysql.urls, 'api_mysql'))),
    # CRUD de la API en /cowork/ (por ejemplo /cowork/sedes/), como indica la guía.
    path('cowork/', include((enrutador.urls, 'api'))),
]
