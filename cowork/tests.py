from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.urls import reverse


class HostPermitidoTests(SimpleTestCase):
    """DEBUG=False rechaza Host: testserver; las pruebas usan un host de ALLOWED_HOSTS."""

    def setUp(self):
        super().setUp()
        self.client.defaults['HTTP_HOST'] = 'localhost'


class PaginasPublicasTests(HostPermitidoTests):
    def test_bienvenida_extiende_la_plantilla_base(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cowork/base.html')
        self.assertTemplateUsed(response, 'cowork/bienvenida.html')
        self.assertContains(response, 'Un espacio para trabajar mejor.')
        self.assertContains(response, reverse('inicio'))
        self.assertContains(response, 'bootstrap.min.css')
        self.assertContains(response, 'btn btn-primary')

    def test_inicio_extiende_la_plantilla_base(self):
        response = self.client.get('/inicio/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cowork/base.html')
        self.assertTemplateUsed(response, 'cowork/inicio.html')
        self.assertContains(response, 'Todo lo necesario, en un solo lugar.')
        self.assertContains(response, reverse('bienvenida'))
        self.assertContains(response, 'navbar')
        self.assertContains(response, 'row g-3')

    def test_nombres_de_ruta_publicos(self):
        self.assertEqual(reverse('bienvenida'), '/')
        self.assertEqual(reverse('inicio'), '/inicio/')


class Error404Tests(HostPermitidoTests):
    @override_settings(DEBUG=False)
    def test_url_inexistente_usa_plantilla_personalizada(self):
        response = self.client.get('/ruta-que-no-existe/')

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'cowork/base.html')
        self.assertTemplateUsed(response, 'cowork/404.html')
        self.assertContains(response, 'Esta página no está disponible.', status_code=404)
        self.assertContains(response, reverse('bienvenida'), status_code=404)
        self.assertContains(response, 'bootstrap.min.css', status_code=404)
        self.assertNotContains(response, 'DisallowedHost', status_code=404)
        self.assertNotContains(response, 'Traceback', status_code=404)


class ArquitecturaDePlantillasTests(SimpleTestCase):
    templates_dir = Path(settings.BASE_DIR) / 'cowork' / 'templates' / 'cowork'
    paginas = ('bienvenida.html', 'inicio.html', '404.html')

    def test_existe_base_html_en_el_namespace_de_la_app(self):
        self.assertTrue((self.templates_dir / 'base.html').is_file())

    def test_plantillas_estan_en_templates_cowork(self):
        for nombre in self.paginas:
            self.assertTrue((self.templates_dir / nombre).is_file())

    def test_paginas_extienden_base_sin_duplicar_css(self):
        base = (self.templates_dir / 'base.html').read_text(encoding='utf-8')
        self.assertIn('bootstrap.min.css', base)
        self.assertIn('bootstrap.bundle.min.js', base)
        self.assertIn('{% block content %}', base)

        for nombre in self.paginas:
            html = (self.templates_dir / nombre).read_text(encoding='utf-8')
            self.assertIn('{% extends "cowork/base.html" %}', html)
            self.assertNotIn('<style>', html)
            self.assertNotIn('<!DOCTYPE html>', html)


class PoliticaCspTests(HostPermitidoTests):
    def test_csp_permite_bootstrap_desde_jsdelivr(self):
        response = self.client.get('/')
        csp = response.headers['Content-Security-Policy']

        self.assertIn("script-src 'self' https://cdn.jsdelivr.net", csp)
        self.assertIn('https://cdn.jsdelivr.net', csp)
        self.assertIn("'unsafe-inline'", csp)
        self.assertContains(response, 'rel="stylesheet"')
