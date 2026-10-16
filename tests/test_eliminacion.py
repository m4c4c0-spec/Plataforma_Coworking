from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from rest_framework.test import APIClient

from cowork.models import Espacio, EventoAuditoria, HistorialEstadoReserva, Reserva, Sede, Usuario
from .test_gestion import DatosCoworkTests


class EliminacionModelosTests(DatosCoworkTests):
    def test_sede_solo_se_elimina_sin_espacios(self):
        with self.assertRaisesMessage(ValidationError, 'sede con espacios'):
            self.sede.eliminar(self.admin)
        sede = Sede.objects.create(nombre='Temporal', direccion='Calle 2', ciudad='Talca')
        sede.eliminar(self.admin)
        self.assertFalse(Sede.objects.filter(pk=sede.pk).exists())
        evento = EventoAuditoria.objects.get(accion='eliminar')
        self.assertEqual((evento.tipo_entidad, evento.id_entidad), ('sede', sede.pk))
        self.assertEqual(evento.valores_anteriores['ciudad'], 'Talca')
        self.assertEqual(evento.actor, self.admin)

    def test_espacio_solo_se_elimina_sin_reservas(self):
        reserva = self.nueva_reserva()
        with self.assertRaisesMessage(ValidationError, 'espacio con reservas'):
            self.espacio.eliminar(self.admin)
        reserva.eliminar(self.miembro)
        self.espacio.eliminar(self.admin)
        self.assertFalse(Espacio.objects.filter(pk=self.espacio.pk).exists())

    def test_usuario_sin_actividad_se_elimina_con_su_cuenta(self):
        cuenta_id = self.otro.cuenta_id
        self.otro.eliminar(self.admin)
        self.assertFalse(Usuario.objects.filter(pk=self.otro.pk).exists())
        self.assertFalse(get_user_model().objects.filter(pk=cuenta_id).exists())
        self.assertEqual(EventoAuditoria.objects.get(accion='eliminar').valores_anteriores['correo'], 'otro@example.com')

    def test_usuario_con_reservas_o_acciones_se_conserva(self):
        self.nueva_reserva()
        with self.assertRaisesMessage(ValidationError, 'usuario con reservas'):
            self.miembro.eliminar(self.admin)
        # Un administrador que registró acciones conserva su perfil en la auditoría.
        segundo = self.crear_usuario('segundo', Usuario.Rol.ADMINISTRADOR)
        Sede(nombre='Norte', direccion='Av. 1', ciudad='Arica').guardar(segundo)
        with self.assertRaisesMessage(ValidationError, 'acciones registradas'):
            segundo.eliminar(self.admin)
        with self.assertRaisesMessage(ValidationError, 'propia cuenta'):
            self.admin.eliminar(self.admin)

    def test_reserva_pendiente_o_cancelada_se_elimina_con_su_historial(self):
        pendiente = self.nueva_reserva()
        pendiente.eliminar(self.miembro)
        self.assertFalse(Reserva.objects.filter(pk=pendiente.pk).exists())
        self.assertFalse(HistorialEstadoReserva.objects.filter(reserva_id=pendiente.pk).exists())
        cancelada = self.nueva_reserva()
        cancelada.cancelar(self.miembro, 'Cambio de planes')
        cancelada.eliminar(self.admin)
        self.assertFalse(Reserva.objects.exists())
        self.assertEqual(EventoAuditoria.objects.filter(accion='eliminar', tipo_entidad='reserva').count(), 2)

    def test_reserva_confirmada_o_finalizada_no_se_elimina(self):
        reserva = self.nueva_reserva()
        reserva.confirmar(self.admin)
        with self.assertRaisesMessage(ValidationError, 'pendientes o canceladas'):
            reserva.eliminar(self.admin)
        with patch('cowork.models.timezone.now', return_value=self.fin + timedelta(minutes=1)):
            reserva.finalizar(self.admin)
        with self.assertRaises(ValidationError):
            reserva.eliminar(self.admin)
        self.assertTrue(Reserva.objects.filter(pk=reserva.pk).exists())

    def test_permisos_de_eliminacion(self):
        reserva = self.nueva_reserva()
        for accion in (
            lambda: self.sede.eliminar(self.miembro),
            lambda: self.espacio.eliminar(self.miembro),
            lambda: self.tipo.eliminar(self.miembro),
            lambda: self.otro.eliminar(self.miembro),
            lambda: reserva.eliminar(self.otro),
        ):
            with self.subTest(accion=accion), self.assertRaises(PermissionDenied):
                accion()
        self.assertTrue(Reserva.objects.filter(pk=reserva.pk).exists())
        self.assertFalse(EventoAuditoria.objects.filter(accion='eliminar').exists())

    def test_delete_directo_sigue_bloqueado(self):
        for objeto in (self.sede, self.espacio, self.miembro, self.nueva_reserva()):
            with self.subTest(objeto=objeto), self.assertRaisesMessage(ValidationError, 'eliminar(actor)'):
                objeto.delete()


class EliminacionApiTests(DatosCoworkTests):
    def setUp(self):
        self.client = APIClient(HTTP_HOST='localhost')

    def test_miembro_elimina_su_reserva_pendiente(self):
        propia = self.nueva_reserva()
        ajena = self.nueva_reserva(usuario=self.otro, inicio=self.fin, fin=self.fin + timedelta(hours=1))
        self.client.force_login(self.miembro.cuenta)
        self.assertEqual(self.client.delete(reverse('api:reserva-detail', args=[ajena.pk])).status_code, 404)
        self.assertEqual(self.client.delete(reverse('api:reserva-detail', args=[propia.pk])).status_code, 204)
        self.assertEqual(list(Reserva.objects.values_list('pk', flat=True)), [ajena.pk])

    def test_miembro_no_elimina_recursos_administrativos(self):
        self.client.force_login(self.miembro.cuenta)
        for nombre, pk in (
            ('sede', self.sede.pk), ('tipo-espacio', self.tipo.pk),
            ('espacio', self.espacio.pk), ('usuario', self.otro.pk),
        ):
            with self.subTest(nombre=nombre):
                self.assertEqual(self.client.delete(reverse(f'api:{nombre}-detail', args=[pk])).status_code, 403)

    def test_reserva_confirmada_devuelve_400(self):
        reserva = self.nueva_reserva()
        reserva.confirmar(self.admin)
        self.client.force_login(self.admin.cuenta)
        respuesta = self.client.delete(reverse('api:reserva-detail', args=[reserva.pk]))
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('pendientes o canceladas', respuesta.data['non_field_errors'][0])


class EliminacionPantallasTests(DatosCoworkTests):
    def test_confirmacion_y_eliminacion_de_un_espacio(self):
        self.client.force_login(self.admin.cuenta)
        url = reverse('espacio_eliminar', args=[self.espacio.pk])
        self.assertContains(self.client.get(url), 'Eliminar espacio')
        self.assertContains(self.client.get(reverse('espacios')), url)
        self.assertRedirects(self.client.post(url), reverse('espacios'))
        self.assertFalse(Espacio.objects.filter(pk=self.espacio.pk).exists())

    def test_error_de_negocio_se_muestra_como_mensaje(self):
        self.client.force_login(self.admin.cuenta)
        respuesta = self.client.post(reverse('sede_eliminar', args=[self.sede.pk]), follow=True)
        self.assertContains(respuesta, 'No se puede eliminar una sede con espacios.')
        self.assertTrue(Sede.objects.filter(pk=self.sede.pk).exists())

    def test_botones_solo_aparecen_cuando_se_puede_eliminar(self):
        self.nueva_reserva()
        self.client.force_login(self.admin.cuenta)
        self.assertNotContains(self.client.get(reverse('sedes')), reverse('sede_eliminar', args=[self.sede.pk]))
        self.assertNotContains(self.client.get(reverse('espacios')), reverse('espacio_eliminar', args=[self.espacio.pk]))
        usuarios = self.client.get(reverse('usuarios'))
        self.assertContains(usuarios, reverse('usuario_eliminar', args=[self.otro.pk]))
        self.assertNotContains(usuarios, reverse('usuario_eliminar', args=[self.miembro.pk]))
        self.assertNotContains(usuarios, reverse('usuario_eliminar', args=[self.admin.pk]))

    def test_miembro_elimina_su_reserva_desde_el_detalle(self):
        reserva = self.nueva_reserva()
        self.client.force_login(self.miembro.cuenta)
        url = reverse('reserva_eliminar', args=[reserva.pk])
        self.assertContains(self.client.get(reverse('reserva_detalle', args=[reserva.pk])), url)
        self.assertRedirects(self.client.post(url), reverse('reservas'))
        self.assertFalse(Reserva.objects.exists())
        for ruta, pk in (('usuario_eliminar', self.otro.pk), ('espacio_eliminar', self.espacio.pk), ('sede_eliminar', self.sede.pk)):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(ruta, args=[pk])).status_code, 403)

    def test_reserva_confirmada_vuelve_al_detalle_con_el_error(self):
        reserva = self.nueva_reserva()
        reserva.confirmar(self.admin)
        self.client.force_login(self.admin.cuenta)
        respuesta = self.client.post(reverse('reserva_eliminar', args=[reserva.pk]), follow=True)
        self.assertRedirects(respuesta, reverse('reserva_detalle', args=[reserva.pk]))
        self.assertContains(respuesta, 'Solo se pueden eliminar reservas pendientes o canceladas.')
        self.assertNotContains(respuesta, reverse('reserva_eliminar', args=[reserva.pk]))
