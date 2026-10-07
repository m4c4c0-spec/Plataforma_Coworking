from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class MigracionDiagramaTests(TransactionTestCase):
    anterior = [('cowork', '0002_espacio_y_reserva')]
    actual = [('cowork', '0004_interaccion_del_usuario')]

    def migrar(self, destino):
        executor = MigrationExecutor(connection)
        executor.migrate(destino)
        return executor.loader.project_state(destino).apps

    def tearDown(self):
        self.migrar(self.actual)
        super().tearDown()

    def test_conserva_datos_y_restaura_referencias_al_revertir(self):
        apps = self.migrar(self.anterior)
        Cuenta = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
        primera = Cuenta.objects.create(username='legacy', email='Repetido@example.com')
        segunda = Cuenta.objects.create(username='duplicado', email='repetido@example.com')
        sede = apps.get_model('cowork', 'Sede').objects.create(
            nombre='Centro', direccion='Calle 1', ciudad='Santiago',
        )
        tipo = apps.get_model('cowork', 'TipoEspacio').objects.create(nombre='Sala')
        espacio = apps.get_model('cowork', 'Espacio').objects.create(
            sede=sede, tipo=tipo, nombre='Antigua', capacidad=5, activo=False,
            descripcion='Descripción que debe conservarse',
        )
        inicio = timezone.now() + timedelta(days=1)
        reserva = apps.get_model('cowork', 'Reserva').objects.create(
            usuario=primera, espacio=espacio, inicio=inicio,
            fin=inicio + timedelta(hours=1), cantidad_personas=2,
        )
        fecha_creacion = reserva.creada_en

        apps = self.migrar(self.actual)
        Usuario = apps.get_model('cowork', 'Usuario')
        Reserva = apps.get_model('cowork', 'Reserva')
        reserva_nueva = Reserva.objects.get(pk=reserva.pk)
        espacio_nuevo = apps.get_model('cowork', 'Espacio').objects.get(pk=espacio.pk)
        self.assertEqual(reserva_nueva.usuario_id, primera.pk)
        self.assertEqual(reserva_nueva.fecha_creacion, fecha_creacion)
        self.assertEqual(espacio_nuevo.descripcion_publica, 'Descripción que debe conservarse')
        self.assertEqual(espacio_nuevo.estado, 'inactivo')
        self.assertEqual(Usuario.objects.get(cuenta_id=primera.pk).correo, 'repetido@example.com')
        self.assertTrue(Usuario.objects.get(cuenta_id=segunda.pk).correo.endswith('@example.invalid'))
        self.assertEqual(apps.get_model('cowork', 'HistorialEstadoReserva').objects.filter(reserva_id=reserva.pk).count(), 1)

        # Los perfiles nuevos pueden tener una clave distinta de su cuenta.
        cuenta_nueva = Cuenta.objects.create(username='nueva', email='nueva@example.com')
        perfil_nuevo = Usuario.objects.create(
            pk=999, cuenta_id=cuenta_nueva.pk, nombre='Nueva', correo='nueva@example.com',
        )
        pendiente = Reserva.objects.create(
            usuario=perfil_nuevo, espacio=espacio_nuevo, inicio=inicio,
            fin=inicio + timedelta(hours=1), cantidad_personas=1,
        )
        apps = self.migrar(self.anterior)
        reserva_restaurada = apps.get_model('cowork', 'Reserva').objects.get(pk=pendiente.pk)
        self.assertEqual(reserva_restaurada.usuario_id, cuenta_nueva.pk)
        self.assertEqual(reserva_restaurada.estado, 'confirmada')
        self.assertFalse(apps.get_model('cowork', 'Espacio').objects.get(pk=espacio.pk).activo)
        self.assertEqual(apps.get_model('cowork', 'Reserva').objects.get(pk=reserva.pk).creada_en, fecha_creacion)
