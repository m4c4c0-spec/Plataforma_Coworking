from django.shortcuts import render


def bienvenida(request):
    """Renderiza la página pública de bienvenida."""
    return render(request, 'bienvenida.html')


def error_404(request, exception):
    """Devuelve un error 404 sin exponer detalles de la excepción."""
    return render(request, '404.html', status=404)


def inicio(request):
    """Renderiza la página que presenta las características de la aplicación."""
    return render(request, 'inicio.html')
