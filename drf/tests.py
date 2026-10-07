from django.core.management import get_commands, load_command_class
from django.test import Client, RequestFactory, SimpleTestCase, override_settings

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


@override_settings(DEBUG=False)
class RunserverDisenoTests(SimpleTestCase):
    def setUp(self):
        command = load_command_class(get_commands()['runserver'], 'runserver')
        parser = command.create_parser('manage.py', 'runserver')
        self.options = vars(parser.parse_args([]))
        self.command = command
        self.handler = command.get_handler(**self.options)

    def solicitar(self, path, handler=None):
        request = RequestFactory().get(path, HTTP_HOST='localhost')
        result = {}

        def start_response(status, headers):
            result.update(status=int(status.split()[0]), headers=dict(headers))

        response = (handler or self.handler)(request.environ, start_response)
        try:
            result['body'] = b''.join(response)
        finally:
            response.close()
        return result

    def test_css_y_javascript_se_sirven_con_debug_false(self):
        assets = {
            '/static/cowork/css/styles.css': (b'--brand-ink', 'text/css'),
            '/static/cowork/vendor/bootstrap/css/bootstrap.min.css': (b'.row{', 'text/css'),
            '/static/cowork/vendor/bootstrap/js/bootstrap.bundle.min.js': (b'Bootstrap v5.3.3', 'javascript'),
            '/static/admin/css/base.css': (b'body', 'text/css'),
        }
        for path, (content, mime) in assets.items():
            with self.subTest(path=path):
                response = self.solicitar(path)
                self.assertEqual(response['status'], 200)
                self.assertIn(mime, response['headers']['Content-Type'])
                self.assertIn(content, response['body'])

    def test_ruta_inexistente_muestra_404_personalizado_con_estilos(self):
        response = self.solicitar('/ruta-inexistente/')
        self.assertEqual(response['status'], 404)
        self.assertIn('Esta página no está disponible.'.encode(), response['body'])
        self.assertIn(b'/static/cowork/css/styles.css', response['body'])
        self.assertNotIn(b'Traceback', response['body'])

    def test_nostatic_desactiva_el_servicio_de_estaticos(self):
        self.options['use_static_handler'] = False
        handler = self.command.get_handler(**self.options)
        response = self.solicitar('/static/cowork/css/styles.css', handler)
        self.assertEqual(response['status'], 404)
