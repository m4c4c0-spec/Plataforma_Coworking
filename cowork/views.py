from django.shortcuts import render


def bienvenida(request):
    "Renderiza la pagina publica de bienvenida."
    return render(request, 'bienvenida.html')


def error_404(request, exception):
    "Devuelve el error generico sin exponer detalles de la excepcion."
    return render(request, '404.html', status=404)

def inicio(request): 
    "renderiza la pagina de inicio para ver las caracteristicas de la app"
    return render(request, 'inicio.html')