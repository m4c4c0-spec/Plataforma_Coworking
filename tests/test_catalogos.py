from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from rest_framework.test import APIClient

from cowork.models import Espacio, EventoAuditoria, Reserva, Sede, TipoEspacio
from .test_gestion import DatosCoworkTests


class CatalogosModeloTests(DatosCoworkTests):
    def test_guardar_sede_registra_auditoria(self):
        sede = Sede(nombre='Norte', direccion='Av. 1', ciudad='Santiago')
        sede.guardar(self.admin)
        sede.ciudad = 'Valparaíso'
        sede.guardar(self.admin)
        eventos = EventoAuditoria.objects.filter(tipo_entidad='sede', id_entidad=sede.pk)
        self.assertEqual(sorted(eventos.values_list('accion', flat=True)), ['actualizar', 'crear'])
        self.assertEqual(eventos.get(accion='actualizar').valores_anteriores['ciudad'], 'Santiago')

    def test_miembro_no_gestiona_catalogos(self):
        with self.assertRaises(PermissionDenied):
            Sede(nombre='Norte', direccion='Av. 1', ciudad='Santiago').guardar(self.miembro)
        with self.assertRaises(PermissionDenied):
            TipoEspacio(nombre='Oficina').guardar(self.miembro)
        with self.assertRaises(PermissionDenied):
            self.sede.desactivar(self.miembro)
        self.assertFalse(Sede.objects.filter(nombre='Norte').exists())

    def test_sede_inactiva_bloquea_reservas_nuevas(self):
        self.sede.desactivar(self.admin)
        self.assertFalse(self.sede.activa)
        self.assertFalse(self.espacio.estaDisponible(self.inicio, self.fin))
        with self.assertRaises(ValidationError):
            self.nueva_reserva()
        with self.assertRaises(ValidationError):
            self.sede.delete()

    def test_tipo_con_espacios_no_se_elimina(self):
        with self.assertRaises(ValidationError):
            self.tipo.eliminar(self.admin)
        self.assertTrue(TipoEspacio.objects.filter(pk=self.tipo.pk).exists())

    def test_eliminar_tipo_sin_espacios_conserva_auditoria(self):
        tipo = TipoEspacio(nombre='Cabina')
        tipo.guardar(self.admin)
        pk = tipo.pk
        tipo.eliminar(self.admin)
        self.assertFalse(TipoEspacio.objects.filter(pk=pk).exists())
        evento = EventoAuditoria.objects.get(accion='eliminar')
        self.assertEqual(evento.id_entidad, pk)
        self.assertEqual(evento.valores_anteriores['nombre'], 'Cabina')
        self.assertEqual(evento.valores_nuevos, {})


class CatalogosPantallaTests(DatosCoworkTests):
    def test_miembro_no_accede(self):
        self.client.force_login(self.miembro.cuenta)
        for ruta in ['sedes', 'sede_crear', 'tipos_espacio', 'tipo_espacio_crear']:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(reverse(ruta)).status_code, 403)

    def test_admin_crea_edita_y_desactiva_sede(self):
        self.client.force_login(self.admin.cuenta)
        response = self.client.post(reverse('sede_crear'), {
            'nombre': 'Norte', 'direccion': 'Av. 1', 'ciudad': 'Santiago', 'activa': 'on',
        })
        self.assertRedirects(response, reverse('sedes'))
        sede = Sede.objects.get(nombre='Norte')
        self.assertContains(self.client.get(reverse('sedes')), 'Norte')
        response = self.client.post(reverse('sede_editar', args=[sede.pk]), {
            'nombre': 'Norte', 'direccion': 'Av. 2', 'ciudad': 'Santiago', 'activa': 'on',
        })
        self.assertRedirects(response, reverse('sedes'))
        sede.refresh_from_db()
        self.assertEqual(sede.direccion, 'Av. 2')
        self.assertEqual(self.client.get(reverse('sede_desactivar', args=[sede.pk])).status_code, 200)
        self.client.post(reverse('sede_desactivar', args=[sede.pk]))
        sede.refresh_from_db()
        self.assertFalse(sede.activa)

    def test_admin_gestiona_tipos(self):
        self.client.force_login(self.admin.cuenta)
        response = self.client.post(reverse('tipo_espacio_crear'), {'nombre': 'Cabina', 'descripcion': ''})
        self.assertRedirects(response, reverse('tipos_espacio'))
        tipo = TipoEspacio.objects.get(nombre='Cabina')
        response = self.client.post(reverse('tipo_espacio_crear'), {'nombre': 'Cabina', 'descripcion': ''})
        self.assertContains(response, 'Ya existe')
        self.client.post(reverse('tipo_espacio_eliminar', args=[self.tipo.pk]))
        self.assertTrue(TipoEspacio.objects.filter(pk=self.tipo.pk).exists())
        self.client.post(reverse('tipo_espacio_eliminar', args=[tipo.pk]))
        self.assertFalse(TipoEspacio.objects.filter(pk=tipo.pk).exists())


class CatalogosApiTests(DatosCoworkTests):
    def setUp(self):
        self.client = APIClient(HTTP_HOST='localhost')
        self.client.force_login(self.admin.cuenta)

    def test_crud_de_sede(self):
        respuesta = self.client.post(reverse('api:sede-list'), {
            'nombre': 'Norte', 'direccion': 'Av. 1', 'ciudad': 'Santiago',
        }, format='json')
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        url = reverse('api:sede-detail', args=[respuesta.data['id']])
        respuesta = self.client.patch(url, {'ciudad': 'Concepción'}, format='json')
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data['ciudad'], 'Concepción')
        respuesta = self.client.post(reverse('api:sede-desactivar', args=[respuesta.data['id']]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.data['activa'])
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertTrue(EventoAuditoria.objects.filter(accion='eliminar', tipo_entidad='sede').exists())

    def test_crud_de_tipo(self):
        respuesta = self.client.post(reverse('api:tipo-espacio-list'), {'nombre': 'Cabina'}, format='json')
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        url = reverse('api:tipo-espacio-detail', args=[respuesta.data['id']])
        self.assertEqual(self.client.put(url, {'nombre': 'Cabina telefónica'}, format='json').status_code, 200)
        respuesta = self.client.delete(reverse('api:tipo-espacio-detail', args=[self.tipo.pk]))
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_miembro_solo_lee_sedes_activas(self):
        inactiva = Sede.objects.create(nombre='Cerrada', direccion='X', ciudad='Y', activa=False)
        self.client.force_login(self.miembro.cuenta)
        respuesta = self.client.get(reverse('api:sede-list'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn(inactiva.pk, [sede['id'] for sede in respuesta.data])
        respuesta = self.client.post(reverse('api:sede-list'), {
            'nombre': 'Norte', 'direccion': 'Av. 1', 'ciudad': 'Santiago',
        }, format='json')
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(self.client.delete(reverse('api:tipo-espacio-detail', args=[self.tipo.pk])).status_code, 403)
        self.assertEqual(Espacio.objects.count(), 1)
        self.assertFalse(Reserva.objects.exists())
