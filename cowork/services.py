from django.core.exceptions import ValidationError
from django.db.models import Count, Q

from .fechas import fecha_utc
from .models import Espacio, EventoAuditoria, Reserva, Usuario, exigir_permiso
from .reportes import GeneracionReportes
from .reportes_dto import RangoFecha


class ServicioReportes(GeneracionReportes):
    """Consultas sin escritura. Los reportes globales requieren administración."""

    @staticmethod
    def _validar_periodo(desde, hasta):
        return RangoFecha(desde, hasta)

    @classmethod
    def buscarReservas(cls, filtros, actor):
        actor = exigir_permiso(actor, 'ver_reservas')
        reservas = Reserva.objects.select_related('usuario', 'espacio__sede', 'espacio__tipo')
        if actor.rol != Usuario.Rol.ADMINISTRADOR:
            reservas = reservas.filter(usuario=actor)
        permitidos = {'usuario_id', 'espacio_id', 'estado', 'desde', 'hasta'}
        if set(filtros) - permitidos:
            raise ValidationError('Los filtros contienen campos no permitidos.')
        filtros = dict(filtros)
        reservas = cls._filtrar_fechas(reservas, filtros)
        return reservas.filter(**filtros)

    @classmethod
    def _filtrar_fechas(cls, reservas, filtros):
        desde, hasta = filtros.pop('desde', None), filtros.pop('hasta', None)
        if desde is not None and hasta is not None:
            periodo = cls._validar_periodo(desde, hasta)
            desde, hasta = periodo.desde, periodo.hasta
        if desde is not None:
            reservas = reservas.filter(fin__gt=fecha_utc(desde))
        if hasta is not None:
            reservas = reservas.filter(inicio__lt=fecha_utc(hasta))
        return reservas

    @classmethod
    def calcularUsoEspacios(cls, desde, hasta, actor):
        exigir_permiso(actor, 'ver_reportes')
        periodo = cls._validar_periodo(desde, hasta)
        resultado = {
            espacio.pk: {'nombre': espacio.nombre, 'reservas': 0, 'horas': 0.0}
            for espacio in Espacio.objects.all()
        }
        cls._sumar_uso(resultado, cls._reservas_uso(periodo), periodo.desde, periodo.hasta)
        return resultado

    @staticmethod
    def resumirActividad(desde, hasta, actor):
        exigir_permiso(actor, 'ver_reportes')
        periodo = ServicioReportes._validar_periodo(desde, hasta)
        eventos = EventoAuditoria.objects.filter(fecha__gte=periodo.desde, fecha__lt=periodo.hasta)
        return {
            'total': eventos.count(),
            'por_accion': dict(eventos.values('accion').annotate(total=Count('pk')).values_list('accion', 'total')),
        }

    @staticmethod
    def analizarUsuarios(desde, hasta, actor):
        exigir_permiso(actor, 'ver_reportes')
        periodo = ServicioReportes._validar_periodo(desde, hasta)
        return Usuario.objects.aggregate(
            total=Count('pk', distinct=True), activos=Count('pk', distinct=True, filter=Q(activo=True)),
            registrados=Count('pk', distinct=True, filter=Q(
                fecha_registro__gte=periodo.desde, fecha_registro__lt=periodo.hasta,
            )),
            con_reservas=Count('pk', distinct=True, filter=Q(
                reservas__inicio__lt=periodo.hasta, reservas__fin__gt=periodo.desde,
            )),
        )
