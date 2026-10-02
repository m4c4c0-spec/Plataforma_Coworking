from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Espacio, EventoAuditoria, Reserva, Sede, TipoEspacio, Usuario
from .services import ServicioReportes


class DatosCoworkTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = cls.crear_usuario('admin', Usuario.Rol.ADMINISTRADOR)
        cls.miembro = cls.crear_usuario('miembro')
        cls.otro = cls.crear_usuario('otro')
        cls.sede = Sede.objects.create(nombre='Centro', direccion='Calle 100', ciudad='Santiago')
        cls.tipo = TipoEspacio.objects.create(nombre='Sala')
        cls.espacio = Espacio.objects.create(
            sede=cls.sede, tipo=cls.tipo, nombre='Sala 1', capacidad=4,
            descripcion_publica='Sala luminosa', observaciones_privadas='Clave interna de mantenimiento',
        )
        cls.inicio = timezone.now() + timedelta(days=2)
        cls.fin = cls.inicio + timedelta(hours=2)

    @staticmethod
    def crear_usuario(nombre, rol=Usuario.Rol.MIEMBRO):
        cuenta = get_user_model().objects.create_user(username=nombre, password='ClaveSegura-739!')
        return Usuario.objects.create(
            cuenta=cuenta, nombre=nombre, correo=f'{nombre}@example.com', rol=rol,
        )

    def setUp(self):
        self.client.defaults['HTTP_HOST'] = 'localhost'

    def nueva_reserva(self, **cambios):
        datos = {
            'usuario': self.miembro, 'espacio': self.espacio,
            'inicio': self.inicio, 'fin': self.fin, 'cantidad_personas': 2,
        }
        datos.update(cambios)
        reserva = Reserva(**datos)
        reserva.guardar(datos['usuario'])
        return reserva

    def datos_formulario_reserva(self, **cambios):
        datos = {
            'usuario': self.miembro.pk, 'espacio': self.espacio.pk,
            'inicio': timezone.localtime(self.inicio).strftime('%Y-%m-%dT%H:%M'),
            'fin': timezone.localtime(self.fin).strftime('%Y-%m-%dT%H:%M'),
            'cantidad_personas': 2, 'observaciones': '',
        }
        datos.update(cambios)
        return datos


class ReglasReservaTests(DatosCoworkTests):
    def test_creacion_guarda_historial_y_auditoria(self):
        reserva = self.nueva_reserva()
        self.assertEqual(reserva.estado, Reserva.Estado.PENDIENTE)
        cambio = reserva.historial.get()
        self.assertEqual(cambio.estado_anterior, '')
        self.assertEqual(cambio.estado_nuevo, Reserva.Estado.PENDIENTE)
        self.assertEqual(cambio.responsable, self.miembro)
        evento = EventoAuditoria.objects.get()
        self.assertEqual(evento.valores_anteriores, {})
        self.assertEqual(evento.valores_nuevos['usuario_id'], self.miembro.pk)
        self.assertIsInstance(evento.valores_nuevos['inicio'], str)

    def test_fin_anterior_o_igual_no_guarda_registros(self):
        for fin in [self.inicio, self.inicio - timedelta(minutes=1)]:
            with self.subTest(fin=fin), self.assertRaises(ValidationError):
                self.nueva_reserva(fin=fin)
        self.assertFalse(Reserva.objects.exists())
        self.assertFalse(EventoAuditoria.objects.exists())

    def test_capacidad_y_cantidad_positiva(self):
        for cantidad in [0, 5]:
            with self.subTest(cantidad=cantidad), self.assertRaises(ValidationError):
                self.nueva_reserva(cantidad_personas=cantidad)

    def test_solapamiento_incluye_pendientes_y_confirmadas(self):
        primera = self.nueva_reserva()
        for estado in [Reserva.Estado.PENDIENTE, Reserva.Estado.CONFIRMADA]:
            if estado == Reserva.Estado.CONFIRMADA:
                primera.confirmar(self.admin)
            with self.subTest(estado=estado), self.assertRaises(ValidationError):
                self.nueva_reserva(usuario=self.otro, inicio=self.inicio + timedelta(minutes=10))
        self.assertEqual(Reserva.objects.count(), 1)

    def test_intervalos_adyacentes_no_se_solapan(self):
        self.nueva_reserva()
        self.nueva_reserva(inicio=self.fin, fin=self.fin + timedelta(hours=1))
        self.assertEqual(Reserva.objects.count(), 2)

    def test_cancelar_libera_horario_y_conserva_historial(self):
        reserva = self.nueva_reserva()
        reserva.cancelar(self.miembro, 'Cambio de planes')
        self.nueva_reserva(usuario=self.otro)
        reserva.refresh_from_db()
        self.assertEqual(reserva.motivo_cancelacion, 'Cambio de planes')
        self.assertEqual(reserva.historial.count(), 2)
        self.assertEqual(Reserva.objects.count(), 2)

    def test_usuarios_espacios_y_sedes_inactivos(self):
        self.miembro.activo = False
        self.miembro.save()
        with self.assertRaises(PermissionDenied):
            self.nueva_reserva()
        self.miembro.activo = True
        self.miembro.save()
        self.espacio.estado = Espacio.Estado.MANTENIMIENTO
        self.espacio.save()
        with self.assertRaises(ValidationError):
            self.nueva_reserva()
        self.espacio.estado = Espacio.Estado.DISPONIBLE
        self.espacio.save()
        self.sede.activa = False
        self.sede.save()
        with self.assertRaises(ValidationError):
            self.nueva_reserva()

    def test_miembro_no_gestiona_reservas_ajenas_ni_confirma(self):
        reserva = self.nueva_reserva()
        with self.assertRaises(PermissionDenied):
            reserva.cancelar(self.otro, 'Intento ajeno')
        with self.assertRaises(PermissionDenied):
            reserva.confirmar(self.miembro)
        self.assertEqual(reserva.historial.count(), 1)

    def test_transiciones_y_finalizacion_solo_tras_fin(self):
        reserva = self.nueva_reserva()
        with self.assertRaises(ValidationError):
            reserva.finalizar(self.admin)
        reserva.confirmar(self.admin)
        with self.assertRaises(ValidationError):
            reserva.finalizar(self.admin)
        with patch('cowork.models.timezone.now', return_value=self.fin + timedelta(minutes=1)):
            reserva.finalizar(self.admin)
        self.assertEqual(reserva.estado, Reserva.Estado.FINALIZADA)
        with self.assertRaises(ValidationError):
            reserva.cancelar(self.admin, 'Ya finalizada')
        self.assertEqual(reserva.historial.count(), 3)

    def test_cancelacion_exige_motivo_y_rechaza_copia_desactualizada(self):
        reserva = self.nueva_reserva()
        copia = Reserva.objects.get(pk=reserva.pk)
        with self.assertRaises(ValidationError):
            reserva.cancelar(self.miembro, '   ')
        reserva.cancelar(self.miembro, 'Motivo válido')
        with self.assertRaises(ValidationError):
            copia.cancelar(self.miembro, 'Segundo intento')
        self.assertEqual(reserva.historial.count(), 2)

    def test_edicion_pendiente_y_auditoria_de_valores(self):
        reserva = self.nueva_reserva()
        reserva.cantidad_personas = 3
        reserva.guardar(self.miembro)
        evento = EventoAuditoria.objects.filter(accion='actualizar').get()
        self.assertEqual(evento.valores_anteriores['cantidad_personas'], 2)
        self.assertEqual(evento.valores_nuevos['cantidad_personas'], 3)
        self.assertEqual(reserva.historial.count(), 1)
        reserva.confirmar(self.admin)
        with self.assertRaises(ValidationError):
            reserva.guardar(self.admin)

    def test_no_cambia_titular_ni_estado_desde_edicion(self):
        reserva = self.nueva_reserva()
        reserva.usuario = self.otro
        with self.assertRaises(ValidationError):
            reserva.guardar(self.admin)
        reserva.usuario = self.miembro
        reserva.estado = Reserva.Estado.CONFIRMADA
        with self.assertRaises(ValidationError):
            reserva.guardar(self.admin)

    def test_fallo_auditoria_revierte_reserva_e_historial(self):
        with patch.object(EventoAuditoria, 'registrar', side_effect=RuntimeError('Fallo de escritura')):
            with self.assertRaises(RuntimeError):
                self.nueva_reserva()
        self.assertFalse(Reserva.objects.exists())
        self.assertFalse(self.miembro.cambios_reserva.exists())

    def test_base_rechaza_intervalo_invalido_incluso_sin_validacion_python(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Reserva.objects.create(
                usuario=self.miembro, espacio=self.espacio,
                inicio=self.inicio, fin=self.inicio, cantidad_personas=1,
            )


class UsuariosEspaciosReportesTests(DatosCoworkTests):
    def test_correo_unico_sin_distinguir_mayusculas(self):
        self.miembro.correo = 'Miembro@EXAMPLE.COM'
        self.miembro.guardar(self.admin)
        self.assertEqual(self.miembro.correo, 'miembro@example.com')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.filter(pk=self.otro.pk).update(correo='MIEMBRO@example.com')

    def test_baja_logica_conserva_reservas_y_desactiva_cuenta(self):
        reserva = self.nueva_reserva()
        self.miembro.desactivar(self.admin)
        self.miembro.cuenta.refresh_from_db()
        self.assertFalse(self.miembro.cuenta.is_active)
        self.assertTrue(Reserva.objects.filter(pk=reserva.pk).exists())
        with self.assertRaises(ValidationError):
            self.miembro.delete()

    def test_permisos_del_diagrama(self):
        self.assertTrue(self.miembro.puedeRealizar('crear_reserva'))
        self.assertFalse(self.miembro.puedeRealizar('gestionar_usuarios'))
        self.assertTrue(self.admin.puedeRealizar('gestionar_espacios'))
        self.assertFalse(self.admin.puedeRealizar('accion_inexistente'))

    def test_permiso_usa_rol_persistido_y_no_acepta_escalada_en_memoria(self):
        self.miembro.rol = Usuario.Rol.ADMINISTRADOR
        with self.assertRaises(PermissionDenied):
            self.miembro.guardar(self.miembro)
        ajena = self.nueva_reserva(usuario=self.otro)
        with self.assertRaises(PermissionDenied):
            ajena.cancelar(self.miembro, 'Rol falsificado')
        self.assertFalse(ServicioReportes.buscarReservas({}, self.miembro).exists())

    def test_administrador_puede_desactivarse_con_la_misma_instancia(self):
        self.admin.desactivar(self.admin)
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.activo)
        self.assertFalse(self.admin.cuenta.is_active)

    def test_baja_espacio_y_limite_capacidad(self):
        reserva = self.nueva_reserva()
        self.espacio.capacidad = 1
        with self.assertRaises(ValidationError):
            self.espacio.guardar(self.admin)
        self.espacio.refresh_from_db()
        self.espacio.cambiarEstado(Espacio.Estado.INACTIVO, self.admin)
        self.assertTrue(Reserva.objects.filter(pk=reserva.pk).exists())
        self.assertFalse(self.espacio.estaDisponible(self.fin, self.fin + timedelta(hours=1)))

    def test_busqueda_aplica_propiedad_y_rechaza_filtros_arbitrarios(self):
        self.nueva_reserva()
        ajena = self.nueva_reserva(usuario=self.otro, inicio=self.fin, fin=self.fin + timedelta(hours=1))
        self.assertEqual(ServicioReportes.buscarReservas({}, self.miembro).count(), 1)
        self.assertEqual(ServicioReportes.buscarReservas({'usuario_id': ajena.usuario_id}, self.miembro).count(), 0)
        with self.assertRaises(ValidationError):
            ServicioReportes.buscarReservas({'usuario__cuenta__password': 'dato'}, self.admin)

    def test_uso_recorta_horas_al_periodo_y_excluye_pendientes(self):
        reserva = self.nueva_reserva()
        reserva.confirmar(self.admin)
        self.nueva_reserva(inicio=self.fin, fin=self.fin + timedelta(hours=1))
        uso = ServicioReportes.calcularUsoEspacios(
            self.inicio + timedelta(minutes=30), self.fin + timedelta(minutes=30), self.admin,
        )
        self.assertEqual(uso[self.espacio.pk]['horas'], 1.5)
        self.assertEqual(uso[self.espacio.pk]['reservas'], 1)

    def test_reportes_exigen_admin_y_periodo_valido(self):
        for metodo in [ServicioReportes.calcularUsoEspacios, ServicioReportes.resumirActividad, ServicioReportes.analizarUsuarios]:
            with self.subTest(metodo=metodo.__name__), self.assertRaises(PermissionDenied):
                metodo(self.inicio, self.fin, self.miembro)
            with self.subTest(metodo=metodo.__name__), self.assertRaises(ValidationError):
                metodo(self.fin, self.inicio, self.admin)

    def test_analisis_usuarios_no_duplica_usuarios_con_varias_reservas(self):
        self.nueva_reserva()
        self.nueva_reserva(inicio=self.fin, fin=self.fin + timedelta(hours=1))
        analisis = ServicioReportes.analizarUsuarios(self.inicio, self.fin + timedelta(hours=2), self.admin)
        self.assertEqual(analisis['total'], 3)
        self.assertEqual(analisis['activos'], 3)
        self.assertEqual(analisis['con_reservas'], 1)
        actividad = ServicioReportes.resumirActividad(timezone.now() - timedelta(minutes=1), self.fin, self.admin)
        self.assertEqual(actividad['por_accion'], {'crear': 2})


class PantallasCrudTests(DatosCoworkTests):
    def test_crud_exige_login_y_login_funciona(self):
        response = self.client.get(reverse('reservas'))
        self.assertRedirects(response, '/ingresar/?next=/reservas/')
        response = self.client.post(reverse('login'), {'username': 'miembro', 'password': 'ClaveSegura-739!'})
        self.assertRedirects(response, reverse('reservas'))

    def test_miembro_no_accede_gestion_administrativa(self):
        self.client.force_login(self.miembro.cuenta)
        for ruta in ['usuarios', 'usuario_crear', 'espacio_crear']:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(ruta)).status_code, 403)

    def test_lista_y_detalle_ocultan_reservas_ajenas(self):
        propia = self.nueva_reserva()
        ajena = self.nueva_reserva(usuario=self.otro, inicio=self.fin, fin=self.fin + timedelta(hours=1))
        self.client.force_login(self.miembro.cuenta)
        response = self.client.get(reverse('reservas'))
        self.assertContains(response, reverse('reserva_detalle', args=[propia.pk]))
        self.assertNotContains(response, reverse('reserva_detalle', args=[ajena.pk]))
        for ruta in ['reserva_detalle', 'reserva_editar', 'reserva_cancelar']:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(ruta, args=[ajena.pk])).status_code, 404)

    def test_miembro_no_ve_observaciones_privadas(self):
        self.client.force_login(self.miembro.cuenta)
        response = self.client.get(reverse('espacios'))
        self.assertContains(response, 'Sala luminosa')
        self.assertNotContains(response, 'Clave interna de mantenimiento')

    def test_creacion_ignora_titular_y_estado_falsificados(self):
        self.client.force_login(self.miembro.cuenta)
        response = self.client.post(reverse('reserva_crear'), self.datos_formulario_reserva(
            usuario=self.otro.pk, estado='confirmada', motivo_cancelacion='Forzado',
        ))
        reserva = Reserva.objects.get()
        self.assertRedirects(response, reverse('reserva_detalle', args=[reserva.pk]))
        self.assertEqual(reserva.usuario, self.miembro)
        self.assertEqual(reserva.estado, Reserva.Estado.PENDIENTE)
        self.assertEqual(reserva.motivo_cancelacion, '')

    def test_formulario_rechaza_solapamiento_y_muestra_error(self):
        self.nueva_reserva()
        self.client.force_login(self.miembro.cuenta)
        response = self.client.post(reverse('reserva_crear'), self.datos_formulario_reserva())
        self.assertContains(response, 'El espacio no está disponible en ese horario.')
        self.assertEqual(Reserva.objects.count(), 1)

    def test_editar_y_cancelar_reserva_por_formulario(self):
        reserva = self.nueva_reserva()
        self.client.force_login(self.miembro.cuenta)
        response = self.client.post(reverse('reserva_editar', args=[reserva.pk]), self.datos_formulario_reserva(cantidad_personas=3))
        self.assertEqual(response.status_code, 302)
        reserva.refresh_from_db()
        self.assertEqual(reserva.cantidad_personas, 3)
        response = self.client.post(reverse('reserva_cancelar', args=[reserva.pk]), {'motivo': 'Cambio de jornada'})
        self.assertEqual(response.status_code, 302)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, Reserva.Estado.CANCELADA)
        self.assertEqual(reserva.historial.count(), 2)

    def test_confirmar_y_finalizar_requieren_post_y_admin(self):
        reserva = self.nueva_reserva()
        self.client.force_login(self.admin.cuenta)
        for ruta in ['reserva_confirmar', 'reserva_finalizar']:
            self.assertEqual(self.client.get(reverse(ruta, args=[reserva.pk])).status_code, 405)
        self.client.force_login(self.miembro.cuenta)
        self.assertEqual(self.client.post(reverse('reserva_confirmar', args=[reserva.pk])).status_code, 403)
        self.client.force_login(self.admin.cuenta)
        self.client.post(reverse('reserva_confirmar', args=[reserva.pk]))
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, Reserva.Estado.CONFIRMADA)
        response = self.client.post(reverse('reserva_finalizar', args=[reserva.pk]), follow=True)
        self.assertContains(response, 'La reserva todavía no ha terminado.')

    def test_admin_crea_usuario_y_cuenta_con_password_cifrado(self):
        self.client.force_login(self.admin.cuenta)
        response = self.client.post(reverse('usuario_crear'), {
            'nombre': 'Nueva', 'apellido': 'Persona', 'correo': 'NUEVA@example.com',
            'rol': 'MIEMBRO', 'nombre_usuario': 'nueva', 'password': 'UnaClave-8546!',
        })
        self.assertRedirects(response, reverse('usuarios'))
        usuario = Usuario.objects.get(correo='nueva@example.com')
        self.assertTrue(usuario.cuenta.check_password('UnaClave-8546!'))
        self.assertNotIn('password', EventoAuditoria.objects.get().valores_nuevos)
        response = self.client.post(reverse('usuario_editar', args=[usuario.pk]), {
            'nombre': 'Nombre cambiado', 'apellido': 'Persona', 'correo': 'nueva@example.com',
            'rol': 'MIEMBRO', 'nombre_usuario': 'falsificado', 'password': '',
        })
        self.assertRedirects(response, reverse('usuarios'))
        usuario.refresh_from_db()
        self.assertEqual(usuario.cuenta.username, 'nueva')
        self.assertEqual(usuario.cuenta.first_name, 'Nombre cambiado')

    def test_admin_crea_edita_e_inactiva_espacio(self):
        self.client.force_login(self.admin.cuenta)
        datos = {
            'nombre': 'Sala 2', 'sede': self.sede.pk, 'tipo': self.tipo.pk,
            'capacidad': 6, 'estado': 'disponible',
            'descripcion_publica': 'Sala nueva', 'observaciones_privadas': 'Interno',
        }
        self.assertRedirects(self.client.post(reverse('espacio_crear'), datos), reverse('espacios'))
        espacio = Espacio.objects.get(nombre='Sala 2')
        datos['nombre'] = 'Sala renovada'
        self.assertRedirects(self.client.post(reverse('espacio_editar', args=[espacio.pk]), datos), reverse('espacios'))
        self.client.get(reverse('espacio_desactivar', args=[espacio.pk]))
        espacio.refresh_from_db()
        self.assertEqual(espacio.estado, Espacio.Estado.DISPONIBLE)
        self.client.post(reverse('espacio_desactivar', args=[espacio.pk]))
        espacio.refresh_from_db()
        self.assertEqual(espacio.estado, Espacio.Estado.INACTIVO)

    def test_desactivar_usuario_por_post_cierra_acceso_existente(self):
        self.client.force_login(self.admin.cuenta)
        url = reverse('usuario_desactivar', args=[self.miembro.pk])
        self.client.get(url)
        self.miembro.refresh_from_db()
        self.assertTrue(self.miembro.activo)
        self.assertRedirects(self.client.post(url), reverse('usuarios'))
        self.client.force_login(self.miembro.cuenta)
        self.assertEqual(self.client.get(reverse('reservas')).status_code, 302)

    def test_creacion_requiere_token_csrf(self):
        cliente = Client(enforce_csrf_checks=True, HTTP_HOST='localhost')
        cliente.force_login(self.miembro.cuenta)
        datos = self.datos_formulario_reserva()
        self.assertEqual(cliente.post(reverse('reserva_crear'), datos).status_code, 403)
        cliente.get(reverse('reserva_crear'))
        datos['csrfmiddlewaretoken'] = cliente.cookies['csrftoken'].value
        self.assertEqual(cliente.post(reverse('reserva_crear'), datos).status_code, 302)

    def test_superusuario_nuevo_obtiene_perfil_administrador_al_ingresar(self):
        cuenta = get_user_model().objects.create_superuser(username='super', email='super@example.com', password='ClaveSegura-739!')
        self.client.force_login(cuenta)
        self.assertEqual(self.client.get(reverse('usuarios')).status_code, 200)
        self.assertEqual(Usuario.objects.get(cuenta=cuenta).rol, Usuario.Rol.ADMINISTRADOR)
