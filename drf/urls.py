from cowork import views
from django.conf import settings
from django.contrib import admin
from django.urls import path

# Django invokes this handler when no URL pattern matches. It is not a public route.
handler404 = views.error_404

urlpatterns = [
    path(settings.ADMIN_URL_PATH, admin.site.urls),
    path('', views.bienvenida, name='bienvenida'),
    path('', views.inicio, name='inicio')
]

