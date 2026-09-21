from django.test import Client, SimpleTestCase, override_settings

import drf.settings as project_settings


class TestClientHostTests(SimpleTestCase):
    """El Client de Django envía Host: testserver, que no está en ALLOWED_HOSTS."""

    @override_settings(
        DEBUG=False,
        ALLOWED_HOSTS=['localhost', '127.0.0.1', '[::1]'],
    )
    def test_get_raiz_con_host_testserver_responde_400(self):
        response = Client().get('/')

        self.assertEqual(response.status_code, 400)

    @override_settings(DEBUG=False)
    def test_get_raiz_con_host_permitido_responde_200(self):
        response = Client().get('/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)

    def test_allowed_hosts_de_produccion_no_incluye_testserver(self):
        self.assertNotIn('testserver', project_settings.ALLOWED_HOSTS)

    def test_localhost_esta_permitido_para_el_client_de_pruebas(self):
        self.assertIn('localhost', project_settings.ALLOWED_HOSTS)
