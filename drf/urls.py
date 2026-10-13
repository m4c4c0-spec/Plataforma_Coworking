from cowork import views
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

# Django invoca este ViewSet con la excepción cuando ninguna ruta coincide.
handler404 = views.Error404ViewSet.as_view({
    metodo: 'retrieve' for metodo in views.Error404ViewSet.http_method_names
})

urlpatterns = [
    path(settings.ADMIN_URL_PATH, admin.site.urls),
    path('', include('cowork.urls')),
]
