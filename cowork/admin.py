from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import UsuarioForm
from .models import (
    Administrador, Espacio, EventoAuditoria, HistorialEstadoReserva, Reserva, Sede, TipoEspacio, Usuario,
)

FECHAS = ('created_at', 'updated_at')


class RegistroConsultaAdmin(admin.ModelAdmin):
    """El historial y la auditoría son registros: solo se consultan."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class GestionAdmin(admin.ModelAdmin):
    """CRUD desde el admin con guardar(actor) y eliminar(actor): mismas reglas y auditoría que las pantallas."""

    @staticmethod
    def actor(request):
        return Usuario.desde_cuenta(request.user)

    def save_model(self, request, obj, form, change):
        obj.guardar(self.actor(request))

    def delete_model(self, request, obj):
        obj.eliminar(self.actor(request))

    def delete_queryset(self, request, queryset):
        actor = self.actor(request)
        for obj in queryset:
            obj.eliminar(actor)

    def _aplicar_reglas(self, request, vista, *args, volver=None):
        """Si una regla rechaza la operación, la revierte completa y muestra el motivo."""
        try:
            with transaction.atomic():
                return vista(request, *args)
        except ValidationError as error:
            self.message_user(request, ' '.join(error.messages), messages.ERROR)
        except IntegrityError:
            self.message_user(request, 'No se pudo completar: el registro tiene datos relacionados.', messages.ERROR)
        return HttpResponseRedirect(volver or request.get_full_path())

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        return self._aplicar_reglas(request, super().changeform_view, object_id, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        return self._aplicar_reglas(request, super().changelist_view, extra_context)

    def delete_view(self, request, object_id, extra_context=None):
        volver = reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_change', args=[object_id])
        return self._aplicar_reglas(request, super().delete_view, object_id, extra_context, volver=volver)


class SedeAdmin(GestionAdmin):
    list_display = ('nombre', 'ciudad', 'activa')
    list_filter = ('activa', 'ciudad')
    search_fields = ('nombre', 'ciudad', 'direccion')
    readonly_fields = FECHAS


class TipoEspacioAdmin(GestionAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre', 'descripcion')
    readonly_fields = FECHAS


class UsuarioAdminForm(UsuarioForm):
    class Meta(UsuarioForm.Meta):
        fields = [*UsuarioForm.Meta.fields, 'activo']


class UsuarioAdmin(GestionAdmin):
    form = UsuarioAdminForm
    list_display = ('nombre', 'apellido', 'correo', 'rol', 'activo')
    list_filter = ('rol', 'activo')
    search_fields = ('nombre', 'apellido', 'correo')
    readonly_fields = ('fecha_registro', 'updated_at')

    def get_form(self, request, obj=None, **kwargs):
        formulario = super().get_form(request, obj, **kwargs)
        actor = self.actor(request)

        class FormularioConActor(formulario):
            def __init__(self, *args, **kw):
                super().__init__(*args, actor=actor, **kw)

        return FormularioConActor

    def save_form(self, request, form, change):
        # UsuarioForm crea la cuenta y guarda el perfil juntos en save_model.
        return form.instance

    def save_model(self, request, obj, form, change):
        form.save()


class EspacioAdmin(GestionAdmin):
    list_display = ('nombre', 'sede', 'tipo', 'capacidad', 'estado')
    list_filter = ('estado', 'sede', 'tipo')
    readonly_fields = FECHAS


class ReservaAdmin(GestionAdmin):
    """Crea, edita (solo pendientes) y elimina; los cambios de estado se hacen en las pantallas o la API."""

    list_display = ('usuario', 'espacio', 'inicio', 'fin', 'estado')
    list_filter = ('estado',)
    fields = (
        'usuario', 'espacio', 'inicio', 'fin', 'cantidad_personas', 'observaciones',
        'estado', 'motivo_cancelacion', 'fecha_creacion', 'updated_at',
    )

    def get_readonly_fields(self, request, obj=None):
        solo_lectura = ('estado', 'motivo_cancelacion', 'fecha_creacion', 'updated_at')
        return ('usuario', *solo_lectura) if obj else solo_lectura

    def get_deleted_objects(self, objs, request):
        # eliminar(actor) borra el historial junto con la reserva: no bloquea el borrado ni exige permiso aparte.
        eliminados, conteo, permisos, _ = super().get_deleted_objects(objs, request)
        permisos.discard(HistorialEstadoReserva._meta.verbose_name)
        return eliminados, conteo, permisos, []


class HistorialEstadoReservaAdmin(RegistroConsultaAdmin):
    list_display = ('reserva', 'estado_anterior', 'estado_nuevo', 'responsable', 'fecha_cambio')


class EventoAuditoriaAdmin(RegistroConsultaAdmin):
    list_display = ('fecha', 'actor', 'accion', 'tipo_entidad', 'id_entidad')
    list_filter = ('accion', 'tipo_entidad')


class AdministradorAdmin(RegistroConsultaAdmin):
    """Lista de perfiles administradores. Se crean, editan y cambian de rol desde Usuarios."""

    list_display = ('nombre', 'apellido', 'correo', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'apellido', 'correo')
    readonly_fields = ('fecha_registro', 'updated_at')


# Registro de los modelos en el administrador de Django, como indica la guía.
admin.site.register(Sede, SedeAdmin)
admin.site.register(TipoEspacio, TipoEspacioAdmin)
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Espacio, EspacioAdmin)
admin.site.register(Reserva, ReservaAdmin)
admin.site.register(HistorialEstadoReserva, HistorialEstadoReservaAdmin)
admin.site.register(EventoAuditoria, EventoAuditoriaAdmin)
admin.site.register(Administrador, AdministradorAdmin)
