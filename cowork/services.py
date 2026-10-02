from django.core.exceptions import ValidationError
from django.db.models import Count, Q

from .models import Espacio, EventoAuditoria, Reserva, Usuario, exigir_permiso


class ServicioReportes:
    """Consultas sin escritura. Los reportes globales requieren administración."""

    @staticmethod
    def _validar_periodo(desde, hasta):
        if not desde or not hasta or hasta <= desde:
            raise ValidationError('El fin del período debe ser posterior al inicio.')

    @staticmethod
    def buscarReservas(filtros, actor):
        actor = exigir_permiso(actor, 'ver_reservas')
        reservas = Reserva.objects.select_related('usuario', 'espacio__sede', 'espacio__tipo')
        if actor.rol != Usuario.Rol.ADMINISTRADOR:
            reservas = reservas.filter(usuario=actor)
        permitidos = {'usuario_id', 'espacio_id', 'estado', 'desde', 'hasta'}
        if set(filtros) - permitidos:
            raise ValidationError('Los filtros contienen campos no permitidos.')
        filtros = dict(filtros)
        desde, hasta = filtros.pop('desde', None), filtros.pop('hasta', None)
        if desde and hasta:
            ServicioReportes._validar_periodo(desde, hasta)
        if desde:
            reservas = reservas.filter(fin__gt=desde)
        if hasta:
            reservas = reservas.filter(inicio__lt=hasta)
        return reservas.filter(**filtros)

    @staticmethod
    def calcularUsoEspacios(desde, hasta, actor):
        exigir_permiso(actor, 'ver_reportes')
        ServicioReportes._validar_periodo(desde, hasta)
        resultado = {
            espacio.pk: {'nombre': espacio.nombre, 'reservas': 0, 'horas': 0.0}
            for espacio in Espacio.objects.all()
        }
        reservas = Reserva.objects.filter(
            estado__in=[Reserva.Estado.CONFIRMADA, Reserva.Estado.FINALIZADA],
            inicio__lt=hasta, fin__gt=desde,
        )
        for reserva in reservas:
            uso = resultado[reserva.espacio_id]
            uso['reservas'] += 1
            uso['horas'] += (min(reserva.fin, hasta) - max(reserva.inicio, desde)).total_seconds() / 3600
        return resultado

    @staticmethod
    def resumirActividad(desde, hasta, actor):
        exigir_permiso(actor, 'ver_reportes')
        ServicioReportes._validar_periodo(desde, hasta)
        eventos = EventoAuditoria.objects.filter(fecha__gte=desde, fecha__lt=hasta)
        return {
            'total': eventos.count(),
            'por_accion': dict(eventos.values('accion').annotate(total=Count('pk')).values_list('accion', 'total')),
        }

    @staticmethod
    def analizarUsuarios(desde, hasta, actor):
        exigir_permiso(actor, 'ver_reportes')
        ServicioReportes._validar_periodo(desde, hasta)
        return Usuario.objects.aggregate(
            total=Count('pk', distinct=True), activos=Count('pk', distinct=True, filter=Q(activo=True)),
            registrados=Count('pk', distinct=True, filter=Q(fecha_registro__gte=desde, fecha_registro__lt=hasta)),
            con_reservas=Count('pk', distinct=True, filter=Q(
                reservas__inicio__lt=hasta, reservas__fin__gt=desde,
            )),
        )
