from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from cowork.models import Espacio, EventoAuditoria, Reserva, Usuario
from .test_gestion import DatosCoworkTests


class GestionViewSetTests(DatosCoworkTests):
    def setUp(self):
        self.client = APIClient(HTTP_HOST='localhost')
        self.client.force_login(self.miembro.cuenta)

    def datos_reserva(self, **cambios):
        return {
            'espacio': self.espacio.pk, 'inicio': self.inicio.isoformat(),
            'fin': self.fin.isoformat(), 'cantidad_personas': 2, **cambios,
        }

    def datos_usuario(self, **cambios):
        return {
            'nombre_usuario': 'nueva-cuenta', 'password': 'Clave-Nueva-891!',
            'nombre': 'Ana', 'apellido': 'Pérez', 'correo': 'ana@example.com',
            'rol': Usuario.Rol.MIEMBRO, **cambios,
        }

    def test_crear_y_editar_reserva_guarda_historial_y_auditoria(self):
        respuesta = self.client.post(reverse('api:reserva-list'), self.datos_reserva(), format='json')
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        reserva = Reserva.objects.get(pk=respuesta.data['id'])
        self.assertEqual(reserva.usuario, self.miembro)
        self.assertEqual(reserva.estado, Reserva.Estado.PENDIENTE)
        self.assertEqual(reserva.historial.get().responsable, self.miembro)
        self.assertTrue(respuesta.data['inicio'].endswith('Z'))
        url = reverse('api:reserva-detail', args=[reserva.pk])
        respuesta = self.client.patch(url, {'cantidad_personas': 3}, format='json')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        evento = EventoAuditoria.objects.get(accion='actualizar')
        self.assertEqual(evento.valores_anteriores['cantidad_personas'], 2)
        self.assertEqual(evento.valores_nuevos['cantidad_personas'], 3)
        respuesta = self.client.put(url, self.datos_reserva(observaciones='Con proyector'), format='json')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        reserva.refresh_from_db()
        self.assertEqual(reserva.observaciones, 'Con proyector')

    def test_errores_de_horario_y_capacidad_no_guardan(self):
        for cambios, campo in (
            ({'fin': self.inicio.isoformat()}, 'fin'),
            ({'cantidad_personas': 5}, 'cantidad_personas'),
            ({'cantidad_personas': 0}, 'cantidad_personas'),
            ({'espacio': 99999}, 'espacio'),
        ):
            with self.subTest(cambios=cambios):
                respuesta = self.client.post(reverse('api:reserva-list'), self.datos_reserva(**cambios), format='json')
                self.assertEqual(respuesta.status_code, 400, respuesta.data)
                self.assertIn(campo, respuesta.data)
        self.assertFalse(Reserva.objects.exists())
        self.assertFalse(EventoAuditoria.objects.exists())

    def test_solapamiento_no_crea_una_segunda_reserva(self):
        self.nueva_reserva()
        respuesta = self.client.post(reverse('api:reserva-list'), self.datos_reserva(), format='json')
        self.assertEqual(respuesta.status_code, 400, respuesta.data)
        self.assertIn('espacio', respuesta.data)
        self.assertEqual(Reserva.objects.count(), 1)
        self.assertEqual(EventoAuditoria.objects.count(), 1)

    def test_miembro_no_puede_crear_para_otro_titular(self):
        respuesta = self.client.post(
            reverse('api:reserva-list'), self.datos_reserva(usuario=self.otro.pk), format='json',
        )
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(Reserva.objects.exists())

    def test_reservas_ajenas_no_aparecen_y_no_se_pueden_modificar(self):
        reserva = self.nueva_reserva(usuario=self.otro)
        self.assertEqual(self.client.get(reverse('api:reserva-list')).data, [])
        detalle = reverse('api:reserva-detail', args=[reserva.pk])
        self.assertEqual(self.client.get(detalle).status_code, 404)
        self.assertEqual(self.client.patch(detalle, {'observaciones': 'Cambio'}, format='json').status_code, 404)
        respuesta = self.client.post(
            reverse('api:reserva-cancelar', args=[reserva.pk]), {'motivo': 'Cambio'}, format='json',
        )
        self.assertEqual(respuesta.status_code, 404)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, Reserva.Estado.PENDIENTE)

    def test_administrador_crea_para_un_miembro_y_no_puede_cambiar_titular(self):
        self.client.force_login(self.admin.cuenta)
        respuesta = self.client.post(
            reverse('api:reserva-list'), self.datos_reserva(usuario=self.otro.pk), format='json',
        )
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        reserva = Reserva.objects.get(pk=respuesta.data['id'])
        respuesta = self.client.patch(
            reverse('api:reserva-detail', args=[reserva.pk]), {'usuario': self.miembro.pk}, format='json',
        )
        self.assertEqual(respuesta.status_code, 400)
        reserva.refresh_from_db()
        self.assertEqual(reserva.usuario, self.otro)

    def test_estado_se_modifica_mediante_acciones(self):
        respuesta = self.client.post(
            reverse('api:reserva-list'), self.datos_reserva(estado='confirmada'), format='json',
        )
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(respuesta.data['estado'], Reserva.Estado.PENDIENTE)

    def test_confirmar_y_finalizar_conserva_historial_y_auditoria(self):
        reserva = self.nueva_reserva(inicio=timezone.now() - timedelta(hours=2), fin=timezone.now() - timedelta(hours=1))
        self.client.force_login(self.admin.cuenta)
        for accion, estado in (('confirmar', Reserva.Estado.CONFIRMADA), ('finalizar', Reserva.Estado.FINALIZADA)):
            respuesta = self.client.post(reverse(f'api:reserva-{accion}', args=[reserva.pk]), format='json')
            self.assertEqual(respuesta.status_code, 200, respuesta.data)
            self.assertEqual(respuesta.data['estado'], estado)
        reserva.refresh_from_db()
        self.assertEqual(reserva.historial.count(), 3)
        self.assertEqual(EventoAuditoria.objects.count(), 3)

    def test_reserva_confirmada_no_se_edita_ni_finaliza_antes_del_fin(self):
        reserva = self.nueva_reserva()
        reserva.confirmar(self.admin)
        self.client.force_login(self.admin.cuenta)
        respuesta = self.client.patch(
            reverse('api:reserva-detail', args=[reserva.pk]), {'cantidad_personas': 3}, format='json',
        )
        self.assertEqual(respuesta.status_code, 400)
        respuesta = self.client.post(reverse('api:reserva-finalizar', args=[reserva.pk]), format='json')
        self.assertEqual(respuesta.status_code, 400)
        reserva.refresh_from_db()
        self.assertEqual(reserva.cantidad_personas, 2)
        self.assertEqual(reserva.estado, Reserva.Estado.CONFIRMADA)

    def test_cancelar_exige_motivo_y_conserva_la_reserva(self):
        reserva = self.nueva_reserva()
        url = reverse('api:reserva-cancelar', args=[reserva.pk])
        self.assertEqual(self.client.post(url, {'motivo': '  '}, format='json').status_code, 400)
        respuesta = self.client.post(url, {'motivo': 'Cambio de planes'}, format='json')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, Reserva.Estado.CANCELADA)
        self.assertEqual(reserva.motivo_cancelacion, 'Cambio de planes')
        self.assertEqual(reserva.historial.count(), 2)

    def test_miembro_no_puede_ejecutar_operaciones_administrativas(self):
        reserva = self.nueva_reserva()
        for url in (
            reverse('api:usuario-list'), reverse('api:espacio-list'),
            reverse('api:usuario-desactivar', args=[self.otro.pk]),
            reverse('api:espacio-desactivar', args=[self.espacio.pk]),
            reverse('api:reserva-confirmar', args=[reserva.pk]),
            reverse('api:reserva-finalizar', args=[reserva.pk]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {}, format='json').status_code, 403)

    def test_anonimo_e_inactivo_no_pueden_guardar(self):
        self.client.logout()
        self.assertEqual(self.client.post(reverse('api:reserva-list'), self.datos_reserva(), format='json').status_code, 403)
        self.client.force_login(self.miembro.cuenta)
        Usuario.objects.filter(pk=self.miembro.pk).update(activo=False)
        self.assertEqual(self.client.post(reverse('api:reserva-list'), self.datos_reserva(), format='json').status_code, 403)
        self.assertFalse(Reserva.objects.exists())

    def test_crear_y_editar_usuario_sin_exponer_password(self):
        self.client.force_login(self.admin.cuenta)
        respuesta = self.client.post(reverse('api:usuario-list'), self.datos_usuario(), format='json')
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        usuario = Usuario.objects.select_related('cuenta').get(pk=respuesta.data['id'])
        self.assertTrue(usuario.cuenta.check_password('Clave-Nueva-891!'))
        self.assertEqual(usuario.cuenta.email, 'ana@example.com')
        self.assertNotIn('password', respuesta.data)
        self.assertNotIn('cuenta', respuesta.data)
        self.assertNotIn('nombre_usuario', respuesta.data)
        respuesta = self.client.patch(
            reverse('api:usuario-detail', args=[usuario.pk]), {'nombre': 'Ana María'}, format='json',
        )
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        usuario.refresh_from_db()
        usuario.cuenta.refresh_from_db()
        self.assertEqual(usuario.cuenta.first_name, 'Ana María')
        self.assertTrue(usuario.cuenta.check_password('Clave-Nueva-891!'))
        self.assertEqual(EventoAuditoria.objects.count(), 2)

    def test_usuario_exige_cuenta_y_password_valida(self):
        self.client.force_login(self.admin.cuenta)
        for cambios, campo in (({'password': ''}, 'password'), ({'password': '123'}, 'password'), ({'nombre_usuario': ''}, 'nombre_usuario')):
            with self.subTest(cambios=cambios):
                respuesta = self.client.post(reverse('api:usuario-list'), self.datos_usuario(**cambios), format='json')
                self.assertEqual(respuesta.status_code, 400, respuesta.data)
                self.assertIn(campo, respuesta.data)
        self.assertFalse(get_user_model().objects.filter(username='nueva-cuenta').exists())
        self.assertFalse(Usuario.objects.filter(correo='ana@example.com').exists())

    def test_fallo_al_guardar_usuario_revierte_la_cuenta(self):
        self.client.force_login(self.admin.cuenta)
        with patch('cowork.models.Usuario.guardar', side_effect=IntegrityError('password=secreto')):
            respuesta = self.client.post(reverse('api:usuario-list'), self.datos_usuario(), format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertNotIn('secreto', str(respuesta.data))
        self.assertFalse(get_user_model().objects.filter(username='nueva-cuenta').exists())

    def test_desactivar_usuario_sincroniza_la_cuenta_y_conserva_registros(self):
        self.nueva_reserva()
        self.client.force_login(self.admin.cuenta)
        respuesta = self.client.post(reverse('api:usuario-desactivar', args=[self.miembro.pk]), format='json')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.miembro.refresh_from_db()
        self.miembro.cuenta.refresh_from_db()
        self.assertFalse(self.miembro.activo)
        self.assertFalse(self.miembro.cuenta.is_active)
        self.assertEqual(Reserva.objects.count(), 1)

    def test_crear_editar_y_desactivar_espacio_aplica_las_reglas(self):
        self.client.force_login(self.admin.cuenta)
        respuesta = self.client.post(reverse('api:espacio-list'), {
            'nombre': 'Sala nueva', 'sede': self.sede.pk, 'tipo': self.tipo.pk, 'capacidad': 6,
        }, format='json')
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        espacio = Espacio.objects.get(pk=respuesta.data['id'])
        respuesta = self.client.patch(reverse('api:espacio-detail', args=[espacio.pk]), {'capacidad': 0}, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.nueva_reserva(espacio=espacio, cantidad_personas=5)
        respuesta = self.client.patch(reverse('api:espacio-detail', args=[espacio.pk]), {'capacidad': 4}, format='json')
        self.assertEqual(respuesta.status_code, 400)
        respuesta = self.client.post(reverse('api:espacio-desactivar', args=[espacio.pk]), format='json')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        espacio.refresh_from_db()
        self.assertEqual(espacio.estado, Espacio.Estado.INACTIVO)
        self.assertEqual(espacio.capacidad, 6)
        self.assertEqual(Reserva.objects.count(), 1)

    def test_miembro_ve_espacios_disponibles_sin_observaciones_privadas(self):
        respuesta = self.client.get(reverse('api:espacio-detail', args=[self.espacio.pk]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn('observaciones_privadas', respuesta.data)
        Espacio.objects.filter(pk=self.espacio.pk).update(estado=Espacio.Estado.INACTIVO)
        self.assertEqual(self.client.get(reverse('api:espacio-list')).data, [])
        self.assertEqual(self.client.get(reverse('api:espacio-detail', args=[self.espacio.pk])).status_code, 404)

    def test_catalogos_permiten_consultar_sedes_y_tipos(self):
        for recurso in ('sede', 'tipo-espacio'):
            with self.subTest(recurso=recurso):
                respuesta = self.client.get(reverse(f'api:{recurso}-list'))
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(len(respuesta.data), 1)

    def test_delete_no_elimina_datos_de_negocio(self):
        reserva = self.nueva_reserva()
        self.client.force_login(self.admin.cuenta)
        for recurso, pk in (('usuario', self.miembro.pk), ('espacio', self.espacio.pk), ('reserva', reserva.pk)):
            with self.subTest(recurso=recurso):
                self.assertEqual(self.client.delete(reverse(f'api:{recurso}-detail', args=[pk])).status_code, 405)
        self.assertTrue(Usuario.objects.filter(pk=self.miembro.pk).exists())
        self.assertTrue(Espacio.objects.filter(pk=self.espacio.pk).exists())
        self.assertTrue(Reserva.objects.filter(pk=reserva.pk).exists())

    def test_autenticacion_de_sesion_exige_csrf_al_guardar(self):
        cliente = APIClient(enforce_csrf_checks=True, HTTP_HOST='localhost')
        cliente.force_login(self.miembro.cuenta)
        url = reverse('api:reserva-list')
        self.assertEqual(cliente.post(url, self.datos_reserva(), format='json').status_code, 403)
        cliente.get(reverse('reservas'))
        token = cliente.cookies['csrftoken'].value
        respuesta = cliente.post(url, self.datos_reserva(), format='json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
