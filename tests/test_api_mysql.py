from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from cowork.database import obtener_motor_mysql, sesion_mysql
from cowork.models import Espacio, Reserva, Sede, TipoEspacio, Usuario
from cowork.models_sqlalchemy import Base, EspacioSQL, ReservaSQL, SedeSQL, TipoEspacioSQL, UsuarioSQL


class ConexionMySQLTests(SimpleTestCase):
    @patch('cowork.database.settings.DATABASES', {})
    def test_sin_base_principal_es_error_de_configuracion(self):
        with self.assertRaisesMessage(ImproperlyConfigured, '.env'):
            obtener_motor_mysql()

    def test_utiliza_mysqldb_y_conserva_caracteres_de_la_contrasena(self):
        configuracion = {
            'ENGINE': 'django.db.backends.mysql', 'NAME': 'cowork_prueba',
            'USER': 'consulta', 'PASSWORD': 'p@ss:/#word',
            'HOST': '127.0.0.1', 'PORT': '3306',
            'OPTIONS': {'charset': 'utf8mb4', 'connect_timeout': 5},
        }
        with patch('cowork.database.settings.DATABASES', {'default': configuracion}):
            with patch('cowork.database._crear_motor_mysql') as crear:
                obtener_motor_mysql()
        url, timeout, comando = crear.call_args.args
        self.assertEqual(url.drivername, 'mysql+mysqldb')
        self.assertEqual(url.password, configuracion['PASSWORD'])
        self.assertEqual(url.database, 'cowork_prueba')
        self.assertEqual(url.query['charset'], 'utf8mb4')
        self.assertEqual(timeout, 5)
        self.assertEqual(comando, "SET sql_mode='STRICT_TRANS_TABLES'")

    def test_puerto_invalido_es_error_de_configuracion(self):
        for puerto in ('abc', '0', '65536'):
            with self.subTest(puerto=puerto):
                with patch('cowork.database.settings.DATABASES', {
                    'default': {'ENGINE': 'django.db.backends.mysql', 'PORT': puerto},
                }):
                    with self.assertRaises(ImproperlyConfigured):
                        obtener_motor_mysql()

    def test_la_sesion_se_cierra_incluso_si_la_consulta_falla(self):
        with patch('cowork.database.obtener_motor_mysql'), patch('cowork.database.Session') as clase:
            with self.assertRaises(ValueError):
                with sesion_mysql():
                    raise ValueError('Consulta interrumpida')
        clase.return_value.__exit__.assert_called_once()

    def test_mapeo_coincide_con_las_tablas_y_columnas_de_django(self):
        for modelo, modelo_sql in (
            (Sede, SedeSQL), (TipoEspacio, TipoEspacioSQL),
            (Usuario, UsuarioSQL), (Espacio, EspacioSQL), (Reserva, ReservaSQL),
        ):
            with self.subTest(modelo=modelo.__name__):
                self.assertEqual(modelo._meta.db_table, modelo_sql.__tablename__)
                self.assertEqual(
                    {campo.column for campo in modelo._meta.concrete_fields},
                    set(modelo_sql.__table__.columns.keys()),
                )


class ApiMySQLTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cuentas = get_user_model()
        cls.admin = cuentas.objects.create_superuser(
            'admin-api', 'admin-api@example.com', 'Clave-Prueba-123',
        )
        cls.miembro = cuentas.objects.create_user(
            'miembro-api', 'miembro-api@example.com', 'Clave-Prueba-123',
        )
        cls.perfil_admin = Usuario.desde_cuenta(cls.admin)
        Usuario.desde_cuenta(cls.miembro)
        Sede.objects.create(nombre='Sede solo en Django', direccion='Otra calle', ciudad='Valparaíso')

    def setUp(self):
        # Base SQLAlchemy aislada en memoria: prueba consultas ORM reales sin modificar MySQL local.
        self.motor = create_engine('sqlite://')
        Base.metadata.create_all(self.motor)
        self.addCleanup(self.motor.dispose)
        self.inicio = datetime(2026, 10, 9, 15, 0, tzinfo=timezone.utc)
        with Session(self.motor) as sesion:
            sede = SedeSQL(id=20, nombre='Sede MySQL', direccion='Calle 123', ciudad='Santiago', activa=True)
            tipo = TipoEspacioSQL(id=30, nombre='Sala', descripcion='Sala de reuniones')
            usuario = UsuarioSQL(
                id=40, cuenta_id=99, nombre='Ana', apellido='Pérez', correo='ana@example.com',
                rol='MIEMBRO', activo=True, fecha_registro=self.inicio,
            )
            espacio = EspacioSQL(
                id=50, sede=sede, tipo=tipo, nombre='Sala A', descripcion_publica='Con proyector',
                observaciones_privadas='Información interna', capacidad=8, estado='disponible',
            )
            reserva = ReservaSQL(
                id=60, usuario=usuario, espacio=espacio, inicio=self.inicio,
                fin=self.inicio + timedelta(hours=1), cantidad_personas=2,
                estado='pendiente', fecha_creacion=self.inicio,
                observaciones='', motivo_cancelacion='',
            )
            sesion.add_all([
                sede, tipo, usuario, espacio, reserva,
                SedeSQL(id=21, nombre='Segunda sede', direccion='Calle 456', ciudad='Santiago', activa=False),
            ])
            sesion.commit()

        @contextmanager
        def sesion_prueba():
            with Session(self.motor, autoflush=False) as sesion:
                yield sesion

        parche = patch('cowork.views.sesion_mysql', side_effect=sesion_prueba)
        self.consulta = parche.start()
        self.addCleanup(parche.stop)
        self.client.force_login(self.admin)

    def test_listado_consulta_la_segunda_base_y_devuelve_json(self):
        respuesta = self.client.get(reverse('api_mysql:sede-list'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'application/json')
        datos = respuesta.json()
        self.assertEqual(datos['count'], 2)
        self.assertEqual(datos['limit'], 100)
        self.assertEqual(datos['offset'], 0)
        self.assertEqual(datos['results'][0]['nombre'], 'Sede MySQL')
        self.assertIs(datos['results'][0]['activa'], True)
        self.assertNotIn('Sede solo en Django', respuesta.content.decode())

    def test_detalles_de_todos_los_recursos(self):
        for recurso, identificador in (
            ('sede', 20), ('tipo-espacio', 30), ('usuario', 40), ('espacio', 50), ('reserva', 60),
        ):
            with self.subTest(recurso=recurso):
                respuesta = self.client.get(reverse(f'api_mysql:{recurso}-detail', args=[identificador]))
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.json()['id'], identificador)

    def test_listados_de_todos_los_recursos(self):
        for recurso in ('tipo-espacio', 'usuario', 'espacio', 'reserva'):
            with self.subTest(recurso=recurso):
                respuesta = self.client.get(reverse(f'api_mysql:{recurso}-list'))
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.json()['count'], 1)
                self.assertEqual(len(respuesta.json()['results']), 1)

    def test_reserva_incluye_relaciones_y_fechas_utc_sin_consultas_adicionales(self):
        consultas = []

        def capturar(conexion, cursor, sentencia, parametros, contexto, muchos):
            consultas.append(sentencia)

        event.listen(self.motor, 'before_cursor_execute', capturar)
        respuesta = self.client.get(reverse('api_mysql:reserva-list'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(consultas), 2)  # Conteo y consulta con JOINs, sin N+1.
        datos = respuesta.json()['results'][0]
        self.assertEqual(datos['usuario']['correo'], 'ana@example.com')
        self.assertEqual(datos['espacio']['sede']['nombre'], 'Sede MySQL')
        self.assertEqual(datos['espacio']['tipo']['nombre'], 'Sala')
        self.assertEqual(datos['inicio'], '2026-10-09T15:00:00Z')
        self.assertEqual(datos['fin'], '2026-10-09T16:00:00Z')
        self.assertEqual(datos['usuario']['fecha_registro'], '2026-10-09T15:00:00Z')
        self.assertNotIn('cuenta_id', datos['usuario'])
        self.assertNotIn('password', datos['usuario'])
        self.assertNotIn('observaciones_privadas', datos['espacio'])

    def test_paginacion_es_estable_y_admite_paginas_vacias(self):
        respuesta = self.client.get(reverse('api_mysql:sede-list'), {'limit': 1, 'offset': 1})
        datos = respuesta.json()
        self.assertEqual(datos['count'], 2)
        self.assertEqual(datos['limit'], 1)
        self.assertEqual(datos['offset'], 1)
        self.assertEqual([sede['id'] for sede in datos['results']], [21])
        respuesta = self.client.get(reverse('api_mysql:sede-list'), {'offset': 100})
        self.assertEqual(respuesta.json()['results'], [])

    def test_parametros_invalidos_no_consultan_mysql(self):
        for parametros in ({'limit': 0}, {'limit': 201}, {'offset': -1}, {'limit': 'abc'}):
            with self.subTest(parametros=parametros):
                respuesta = self.client.get(reverse('api_mysql:sede-list'), parametros)
                self.assertEqual(respuesta.status_code, 400)
        self.consulta.assert_not_called()

    def test_registro_inexistente_devuelve_404_json(self):
        respuesta = self.client.get(reverse('api_mysql:sede-detail', args=[999]))
        self.assertEqual(respuesta.status_code, 404)
        self.assertIn('detail', respuesta.json())

    def test_anonimo_no_puede_consultar(self):
        self.client.logout()
        respuesta = self.client.get(reverse('api_mysql:sede-list'))
        self.assertEqual(respuesta.status_code, 403)
        self.assertIn('detail', respuesta.json())
        self.consulta.assert_not_called()

    def test_miembro_no_puede_consultar_ningun_recurso(self):
        self.client.force_login(self.miembro)
        for recurso in ('sede', 'tipo-espacio', 'usuario', 'espacio', 'reserva'):
            with self.subTest(recurso=recurso):
                self.assertEqual(self.client.get(reverse(f'api_mysql:{recurso}-list')).status_code, 403)
        self.consulta.assert_not_called()

    def test_administrador_desactivado_no_puede_consultar(self):
        Usuario.objects.filter(pk=self.perfil_admin.pk).update(activo=False)
        respuesta = self.client.get(reverse('api_mysql:sede-list'))
        self.assertEqual(respuesta.status_code, 403)
        self.consulta.assert_not_called()

    def test_api_no_admite_escrituras(self):
        for metodo in ('post', 'put', 'patch', 'delete'):
            with self.subTest(metodo=metodo):
                respuesta = getattr(self.client, metodo)(reverse('api_mysql:sede-list'))
                self.assertEqual(respuesta.status_code, 405)
        self.consulta.assert_not_called()

    def test_errores_de_configuracion_y_conexion_devuelven_503_sin_detalles(self):
        for error in (
            ImproperlyConfigured('PASSWORD=secreto'),
            OperationalError('SELECT dato_privado', {}, Exception('PASSWORD=secreto')),
        ):
            with self.subTest(error=type(error).__name__):
                self.consulta.side_effect = error
                with self.assertLogs('cowork.views', level='WARNING') as registro:
                    respuesta = self.client.get(reverse('api_mysql:sede-list'))
                self.assertEqual(respuesta.status_code, 503)
                self.assertIn('detail', respuesta.json())
                self.assertNotIn('secreto', respuesta.content.decode())
                self.assertNotIn('dato_privado', respuesta.content.decode())
                self.assertNotIn('secreto', ' '.join(registro.output))
