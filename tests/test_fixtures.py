from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cowork.models import Espacio, Reserva, Sede, TipoEspacio, Usuario
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


class DatosDemostracionTests(TestCase):
    FIXTURES = ('sedes', 'tipos_espacio', 'usuarios_demo', 'espacios_demo', 'reservas_demo')

    def setUp(self):
        self.client.defaults['HTTP_HOST'] = 'localhost'
        call_command('loaddata', *self.FIXTURES, verbosity=0)

    def test_reservas_vigentes_cumplen_las_reglas_del_negocio(self):
        vigentes = Reserva.objects.filter(estado__in=[Reserva.Estado.PENDIENTE, Reserva.Estado.CONFIRMADA])
        self.assertTrue(vigentes.exists())
        for reserva in vigentes:
            with self.subTest(reserva=reserva.pk):
                reserva.full_clean()
        for reserva in Reserva.objects.filter(estado=Reserva.Estado.FINALIZADA):
            self.assertLess(reserva.fin, timezone.now())

    def test_historial_termina_en_el_estado_actual(self):
        for reserva in Reserva.objects.all():
            with self.subTest(reserva=reserva.pk):
                cambios = list(reserva.historial.order_by('fecha_cambio', 'pk'))
                self.assertEqual(cambios[0].estado_anterior, '')
                self.assertEqual(cambios[-1].estado_nuevo, reserva.estado)
        self.assertEqual(set(Reserva.objects.values_list('estado', flat=True)), set(Reserva.Estado.values))

    def test_cuentas_permiten_ingresar_salvo_la_inactiva(self):
        for usuario, esperado in (('admin_demo', True), ('ana_demo', True), ('diego_demo', False)):
            with self.subTest(usuario=usuario):
                self.assertEqual(self.client.login(username=usuario, password='Coworking-Demo-2026'), esperado)

    def test_flujo_completo_sobre_los_datos_de_demostracion(self):
        ana = Usuario.objects.get(cuenta__username='ana_demo')
        admin = Usuario.objects.get(cuenta__username='admin_demo')
        self.client.login(username='ana_demo', password='Coworking-Demo-2026')
        self.assertContains(self.client.get(reverse('reservas')), 'Sala Andes')
        self.assertNotContains(self.client.get(reverse('espacios')), 'Sala Biobío')
        pendiente = Reserva.objects.get(pk=101)
        self.client.login(username='admin_demo', password='Coworking-Demo-2026')
        self.client.post(reverse('reserva_confirmar', args=[pendiente.pk]))
        pendiente.refresh_from_db()
        self.assertEqual(pendiente.estado, Reserva.Estado.CONFIRMADA)
        self.assertEqual(pendiente.historial.last().responsable, admin)
        respuesta = self.client.get(reverse('reportes'), {
            'tipo': 'diario', 'formato': 'pdf', 'desde': '2026-10-01', 'hasta': '2026-10-08',
        })
        self.assertTrue(respuesta.content.startswith(b'%PDF-'))
        self.assertEqual(ana.reservas.count(), 4)
