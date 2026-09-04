from cowork import views
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

# Django usa esta función cuando ninguna ruta coincide. No es un endpoint adicional.
handler404 = views.error_404

urlpatterns = [
    path(settings.ADMIN_URL_PATH, admin.site.urls),
    path('', include('cowork.urls')),
]
