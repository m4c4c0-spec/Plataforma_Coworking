# Plataforma_Coworking
Esta sera una futura plataforma de trabajo compartido para digitalizar los datos y tener una consistencia de cada uno 

La explicacion completa del flujo, archivo por archivo, esta disponible en
[`DOCUMENTACION_TECNICA.md`](DOCUMENTACION_TECNICA.md).

## Alcance

Este repositorio es un prototipo academico. La pagina 404, los permisos del
administrador y las pruebas automatizadas forman parte de la implementacion. Las
referencias a HTTPS, MFA, VPN o infraestructura cloud son recomendaciones teoricas
para un posible despliegue futuro, no requisitos para ejecutar el proyecto.

## Pagina 404 y configuracion segura

Django muestra automaticamente `templates/404.html` cuando una URL no coincide con
ninguna ruta. No se debe crear una ruta `/404/`: el manejador global `handler404` se
encarga de responder con el estado HTTP correcto.

La configuracion usa `DEBUG=False` por defecto para no revelar rutas, variables ni
detalles internos. Para trabajar localmente con la pagina tecnica de Django:

```bash
DJANGO_DEBUG=True .venv/bin/python manage.py runserver
```

En un despliegue futuro se deberian definir estas variables con valores reales:

```bash
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS=cowork.ejemplo.cl,www.cowork.ejemplo.cl
export DJANGO_SECRET_KEY='una-clave-larga-aleatoria-y-privada'
export DJANGO_ADMIN_URL_PATH='ruta-administrativa-larga-y-privada'
```

No se debe usar `*` en `DJANGO_ALLOWED_HOSTS`. El proxy de produccion tambien debe
forzar HTTPS antes de habilitar HSTS y cookies `Secure`.

## Proteccion cross-site del administrador

El administrador hereda la proteccion CSRF de Django, valida el encabezado `Origin`
en operaciones inseguras y rechaza origenes no confiables. Ademas, las cabeceras CSP
y `X-Frame-Options: DENY` impiden cargar el admin dentro de un iframe, enviar sus
formularios a otro origen o ejecutar scripts externos.

La ruta convencional `/admin/` no esta publicada. El administrador se monta en el
valor de `DJANGO_ADMIN_URL_PATH`; si no se define, en desarrollo se usa
`/gestion-interna/`. La ruta privada reduce escaneos automaticos, pero no reemplaza
la autenticacion: Django solo permite entrar a usuarios activos con permiso de staff.

Para crear el primer administrador desde la terminal:

```bash
.venv/bin/python manage.py createsuperuser
```

Fuera del alcance academico, un despliegue real tambien deberia limitar el panel por
IP o VPN desde nginx, el firewall o el proveedor cloud. Esa restriccion no debe
basarse en `X-Forwarded-For` sin configurar previamente proxies de confianza.
