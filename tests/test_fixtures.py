from django.core.management import call_command
from django.test import TestCase

from cowork.models import Espacio, Sede, TipoEspacio
from .test_gestion import DatosCoworkTests


class DatosInicialesTests(TestCase):
    def cargar(self):
        call_command('loaddata', 'sedes', 'tipos_espacio', verbosity=0)

    def test_carga_sedes_y_tipos_de_espacio(self):
        self.cargar()
        self.assertEqual(Sede.objects.count(), 4)
        self.assertTrue(all(Sede.objects.values_list('activa', flat=True)))
        self.assertEqual(TipoEspacio.objects.count(), 6)
        self.assertTrue(TipoEspacio.objects.filter(nombre='Sala de reuniones').exists())

    def test_cargar_dos_veces_no_duplica(self):
        self.cargar()
        self.cargar()
        self.assertEqual(Sede.objects.count(), 4)
        self.assertEqual(TipoEspacio.objects.count(), 6)


class DatosInicialesCrudTests(DatosCoworkTests):
    def test_permiten_crear_espacios_desde_el_crud(self):
        call_command('loaddata', 'sedes', 'tipos_espacio', verbosity=0)
        espacio = Espacio(
            sede=Sede.objects.get(nombre='Sede Providencia'),
            tipo=TipoEspacio.objects.get(nombre='Oficina privada'),
            nombre='Oficina 1', capacidad=4,
        )
        espacio.guardar(self.admin)
        self.assertTrue(espacio.estaDisponible(self.inicio, self.fin))
