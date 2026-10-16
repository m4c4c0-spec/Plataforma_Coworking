from django.urls import reverse

from cowork.models import Usuario
from .test_gestion import DatosCoworkTests


class AdministradorAdminTests(DatosCoworkTests):
    def setUp(self):
        super().setUp()
        cuenta = self.admin.cuenta
        cuenta.is_staff = cuenta.is_superuser = True
        cuenta.save(update_fields=['is_staff', 'is_superuser'])
        self.client.force_login(cuenta)

    def test_lista_solo_los_perfiles_administradores(self):
        lista = self.client.get(reverse('admin:cowork_administrador_changelist'))
        self.assertContains(lista, 'admin@example.com')
        self.assertNotContains(lista, 'miembro@example.com')

    def test_es_de_solo_consulta(self):
        self.assertEqual(self.client.get(reverse('admin:cowork_administrador_add')).status_code, 403)
        detalle = self.client.get(reverse('admin:cowork_administrador_change', args=[self.admin.pk]))
        self.assertContains(detalle, 'admin@example.com')
        self.assertNotContains(detalle, 'name="_save"')
        eliminar = reverse('admin:cowork_administrador_delete', args=[self.admin.pk])
        self.assertEqual(self.client.post(eliminar, {'post': 'yes'}).status_code, 403)
        self.assertTrue(Usuario.objects.filter(pk=self.admin.pk).exists())
