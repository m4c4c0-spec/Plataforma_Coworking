from dataclasses import astuple, dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import ClassVar

from django.core.exceptions import ValidationError
from django.utils import timezone

from .fechas import fecha_con_hora, fecha_utc


class Formato(str, Enum):
    PDF = 'pdf'
    EXCEL = 'xlsx'


class TipoReporte(str, Enum):
    RESERVAS = 'reservas'
    DIARIO = 'diario'


@dataclass(frozen=True)
class RangoFecha:
    desde: date | datetime
    hasta: date | datetime

    def __post_init__(self):
        desde, hasta = fecha_utc(self.desde), fecha_utc(self.hasta)
        if hasta <= desde:
            raise ValidationError('El fin del período debe ser posterior al inicio.')
        object.__setattr__(self, 'desde', desde)
        object.__setattr__(self, 'hasta', hasta)

    def dias(self):
        """Intervalos por día local, recortados al rango [desde, hasta)."""
        inicio = timezone.localtime(self.desde)
        while inicio < self.hasta:
            siguiente = fecha_con_hora(inicio.date() + timedelta(days=1))
            fin = min(siguiente, self.hasta)
            yield inicio.date(), inicio, fin
            inicio = siguiente


@dataclass(frozen=True)
class FiltroReporteDTO:
    usuario_id: int | None = None
    espacio_id: int | None = None
    estado: str | None = None
    desde: date | datetime | None = None
    hasta: date | datetime | None = None

    def como_filtros(self):
        filtros = self._identificadores()
        if self.estado is not None:
            self._validar_estado()
            filtros['estado'] = self.estado
        filtros.update(self._fechas())
        return filtros

    def _identificadores(self):
        filtros = {}
        for campo in ('usuario_id', 'espacio_id'):
            valor = getattr(self, campo)
            if valor is None:
                continue
            if type(valor) is not int or valor < 1:
                raise ValidationError({campo: 'El identificador debe ser un entero positivo.'})
            filtros[campo] = valor
        return filtros

    def _validar_estado(self):
        from .models import Reserva

        if self.estado not in Reserva.Estado.values:
            raise ValidationError({'estado': 'El estado de reserva no es válido.'})

    def _fechas(self):
        filtros = {}
        if self.desde is not None:
            filtros['desde'] = fecha_utc(self.desde)
        if self.hasta is not None:
            filtros['hasta'] = fecha_utc(self.hasta)
        if self.desde is not None and self.hasta is not None:
            RangoFecha(filtros['desde'], filtros['hasta'])
        return filtros


@dataclass(frozen=True)
class DatosReporte:
    id_reserva: int
    usuario: str
    espacio: str
    sede: str
    inicio: datetime
    fin: datetime
    estado: str
    cantidad_personas: int

    columnas: ClassVar[tuple[str, ...]] = (
        'Reserva', 'Usuario', 'Espacio', 'Sede', 'Inicio', 'Fin', 'Estado', 'Personas',
    )

    def valores(self):
        return astuple(self)


@dataclass(frozen=True)
class DatosReporteDiario:
    fecha: date
    espacio: str
    sede: str
    reservas: int
    horas: float

    columnas: ClassVar[tuple[str, ...]] = ('Fecha', 'Espacio', 'Sede', 'Reservas', 'Horas de uso')

    def valores(self):
        return astuple(self)
