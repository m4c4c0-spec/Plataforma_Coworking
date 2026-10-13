from abc import ABC, abstractmethod

from django.core.exceptions import ValidationError

from .reportes_dto import DatosReporte, DatosReporteDiario, Formato


class ReporteExportar(ABC):
    @abstractmethod
    def exportar(self, datos, formato):
        """Devuelve los bytes de un documento en el formato solicitado."""

    @abstractmethod
    def generar_pdf(self, datos):
        pass

    @abstractmethod
    def generar_excel(self, datos):
        pass


class ExportadorReportes(ReporteExportar):
    def __init__(self, tipo_dato=DatosReporte):
        if tipo_dato not in (DatosReporte, DatosReporteDiario):
            raise ValidationError('El tipo de datos del reporte no es válido.')
        self.tipo_dato = tipo_dato

    def _filas(self, datos):
        filas = [self.tipo_dato.columnas]
        for dato in datos:
            if not isinstance(dato, self.tipo_dato):
                raise ValidationError('Las filas deben corresponder al tipo de reporte.')
            filas.append(dato.valores())
        return filas

    def exportar(self, datos, formato):
        try:
            formato = Formato(formato)
        except (ValueError, TypeError) as exc:
            raise ValidationError('Selecciona PDF o Excel (xlsx).') from exc
        if formato == Formato.PDF:
            return self.generar_pdf(datos)
        return self.generar_excel(datos)

    def generar_pdf(self, datos):
        from .reportes_pdf import GeneradorPDF

        return GeneradorPDF().generar(self._filas(datos))

    def generar_excel(self, datos):
        from .reportes_excel import GeneradorExcel

        return GeneradorExcel().generar(self._filas(datos))
