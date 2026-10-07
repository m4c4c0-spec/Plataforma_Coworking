from django.contrib.staticfiles.management.commands.runserver import Command as StaticRunserver


class Command(StaticRunserver):
    """Sirve los estáticos locales sin desactivar las páginas de error personalizadas."""

    def add_arguments(self, parser):
        super().add_arguments(parser)
        # Solo afecta al servidor de desarrollo; --nostatic sigue disponible.
        parser.set_defaults(insecure_serving=True)
