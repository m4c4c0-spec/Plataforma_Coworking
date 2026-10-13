from django.core.exceptions import ValidationError

from .exportadores import ExportadorReportes
from .fechas import horas_entre
from .models import Espacio, Reserva, exigir_permiso
from .reportes_dto import (
    DatosReporte, DatosReporteDiario, FiltroReporteDTO, Formato, RangoFecha, TipoReporte,
)

TIPOS_CONTENIDO = {
    Formato.PDF: 'application/pdf',
    Formato.EXCEL: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}


class GeneracionReportes:
    @classmethod
    def generacionreporte_reserva_espacio(cls, filtro, actor):
        exigir_permiso(actor, 'ver_reportes')
        if not isinstance(filtro, FiltroReporteDTO):
            raise ValidationError('Utiliza un FiltroReporteDTO para generar el reporte.')
        reservas = cls.buscarReservas(filtro.como_filtros(), actor).order_by('inicio', 'pk')
        return [cls._fila_reserva(reserva) for reserva in reservas]

    @staticmethod
    def _fila_reserva(reserva):
        return DatosReporte(
            id_reserva=reserva.pk, usuario=str(reserva.usuario),
            espacio=reserva.espacio.nombre, sede=reserva.espacio.sede.nombre,
            inicio=reserva.inicio, fin=reserva.fin,
            estado=reserva.get_estado_display(), cantidad_personas=reserva.cantidad_personas,
        )

    @classmethod
    def resumirReservasDiarias(cls, periodo, actor):
        exigir_permiso(actor, 'ver_reportes')
        if not isinstance(periodo, RangoFecha):
            raise ValidationError('Utiliza un RangoFecha para el reporte diario.')
        espacios = list(Espacio.objects.select_related('sede').order_by('sede__nombre', 'nombre', 'pk'))
        reservas = list(cls._reservas_uso(periodo))
        datos = []
        for fecha, inicio, fin in periodo.dias():
            datos.extend(cls._filas_diarias(fecha, inicio, fin, espacios, reservas))
        return datos

    @staticmethod
    def _reservas_uso(periodo):
        return Reserva.objects.filter(
            estado__in=[Reserva.Estado.CONFIRMADA, Reserva.Estado.FINALIZADA],
            inicio__lt=periodo.hasta, fin__gt=periodo.desde,
        )

    @classmethod
    def _filas_diarias(cls, fecha, inicio, fin, espacios, reservas):
        uso = {espacio.pk: {'reservas': 0, 'horas': 0.0} for espacio in espacios}
        cls._sumar_uso(uso, reservas, inicio, fin)
        return [
            DatosReporteDiario(
                fecha=fecha, espacio=espacio.nombre, sede=espacio.sede.nombre,
                reservas=uso[espacio.pk]['reservas'], horas=round(uso[espacio.pk]['horas'], 6),
            )
            for espacio in espacios
        ]

    @staticmethod
    def _sumar_uso(uso, reservas, inicio, fin):
        for reserva in reservas:
            desde, hasta = max(inicio, reserva.inicio), min(fin, reserva.fin)
            if desde >= hasta or reserva.espacio_id not in uso:
                continue
            uso[reserva.espacio_id]['reservas'] += 1
            uso[reserva.espacio_id]['horas'] += horas_entre(desde, hasta)

    @classmethod
    def generacionreportereserva_espacio_diarias(cls, periodo, actor, formato=Formato.PDF):
        datos = cls.resumirReservasDiarias(periodo, actor)
        return ExportadorReportes(DatosReporteDiario).exportar(datos, formato)

    @classmethod
    def generarDocumento(cls, tipo, formato, actor, *, desde=None, hasta=None, **filtros):
        """Devuelve (contenido, nombre de archivo, tipo de contenido) de un reporte."""
        try:
            tipo, formato = TipoReporte(tipo), Formato(formato)
        except (ValueError, TypeError) as exc:
            raise ValidationError('Selecciona un tipo de reporte y un formato válidos.') from exc
        if tipo == TipoReporte.DIARIO:
            if desde is None or hasta is None:
                raise ValidationError('El reporte diario requiere las fechas desde y hasta.')
            contenido = cls.generacionreportereserva_espacio_diarias(RangoFecha(desde, hasta), actor, formato)
        else:
            filtro = FiltroReporteDTO(desde=desde, hasta=hasta, **filtros)
            datos = cls.generacionreporte_reserva_espacio(filtro, actor)
            contenido = ExportadorReportes(DatosReporte).exportar(datos, formato)
        return contenido, f'reporte-{tipo.value}.{formato.value}', TIPOS_CONTENIDO[formato]
