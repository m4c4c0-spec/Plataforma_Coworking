from django.contrib import admin

from .models import Espacio, EventoAuditoria, HistorialEstadoReserva, Reserva, Sede, TipoEspacio, Usuario


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'activa')
    list_filter = ('activa', 'ciudad')
    search_fields = ('nombre', 'ciudad', 'direccion')


@admin.register(TipoEspacio)
class TipoEspacioAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre', 'descripcion')


class RegistroConsultaAdmin(admin.ModelAdmin):
    """Las escrituras de negocio pasan por el CRUD para aplicar sus reglas."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Usuario)
class UsuarioAdmin(RegistroConsultaAdmin):
    list_display = ('nombre', 'apellido', 'correo', 'rol', 'activo')
    list_filter = ('rol', 'activo')
    search_fields = ('nombre', 'apellido', 'correo')


@admin.register(Espacio)
class EspacioAdmin(RegistroConsultaAdmin):
    list_display = ('nombre', 'sede', 'tipo', 'capacidad', 'estado')
    list_filter = ('estado', 'sede', 'tipo')


@admin.register(Reserva)
class ReservaAdmin(RegistroConsultaAdmin):
    list_display = ('usuario', 'espacio', 'inicio', 'fin', 'estado')
    list_filter = ('estado',)


@admin.register(HistorialEstadoReserva)
class HistorialEstadoReservaAdmin(RegistroConsultaAdmin):
    list_display = ('reserva', 'estado_anterior', 'estado_nuevo', 'responsable', 'fecha_cambio')


@admin.register(EventoAuditoria)
class EventoAuditoriaAdmin(RegistroConsultaAdmin):
    list_display = ('fecha', 'actor', 'accion', 'tipo_entidad', 'id_entidad')
    list_filter = ('accion', 'tipo_entidad')
