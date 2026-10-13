from datetime import date, datetime
from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .fechas import hora_local_sin_zona


class GeneradorPDF:
    """Convierte filas ya validadas en un documento PDF."""

    def generar(self, filas):
        salida = BytesIO()
        documento = self._documento(salida)
        contenido = self._encabezado()
        contenido.append(self._tabla(filas, documento.width))
        if len(filas) == 1:
            contenido.append(Paragraph('Sin reservas en el período solicitado.', getSampleStyleSheet()['Normal']))
        documento.build(contenido)
        return salida.getvalue()

    @staticmethod
    def _documento(salida):
        return SimpleDocTemplate(
            salida, pagesize=landscape(A4), title='Reservas de espacios',
            leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24,
        )

    @staticmethod
    def _encabezado():
        estilos = getSampleStyleSheet()
        zona = escape(timezone.get_current_timezone_name())
        return [
            Paragraph('Reservas de espacios', estilos['Title']),
            Paragraph(f'Zona horaria: {zona}', estilos['Normal']), Spacer(1, 12),
        ]

    def _tabla(self, filas, ancho):
        estilo = ParagraphStyle('celda', fontName='Helvetica', fontSize=8, leading=11)
        celdas = [[Paragraph(self._texto(valor), estilo) for valor in fila] for fila in filas]
        tabla = Table(celdas, colWidths=[ancho / len(filas[0])] * len(filas[0]), repeatRows=1, splitInRow=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ]))
        return tabla

    @staticmethod
    def _texto(valor):
        if isinstance(valor, datetime):
            valor = hora_local_sin_zona(valor).strftime('%Y-%m-%d %H:%M')
        elif isinstance(valor, date):
            valor = valor.isoformat()
        elif isinstance(valor, float):
            valor = f'{valor:.2f}'
        return escape(str(valor)).replace('\n', '<br/>')
