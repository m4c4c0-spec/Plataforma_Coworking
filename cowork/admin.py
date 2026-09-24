from django.contrib import admin

from .models import Sede, TipoEspacio


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'activa')
    list_filter = ('activa', 'ciudad')
    search_fields = ('nombre', 'ciudad', 'direccion')


@admin.register(TipoEspacio)
class TipoEspacioAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre', 'descripcion')
