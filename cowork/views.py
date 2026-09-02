from django.shortcuts import render


def bienvenida(request):
    "Renderiza la pagina publica de bienvenida."
    return render(request, 'bienvenida.html')


def error_404(request, exception):
    "Devuelve el error generico sin exponer detalles de la excepcion."
    return render(request, '404.html', status=404)
