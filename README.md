# Plataforma Coworking

Plataforma de trabajo compartido orientada a organizar espacios, reservas y comunidad de una manera clara y sencilla.

## Requisitos

- Python 3.12 o superior (compatible con Django 6.1).
- Git.
- Fedora Linux o Windows 10/11.
- Un servidor **MySQL 8.4+ o MariaDB 10.11+**. Es la base de datos principal del
  proyecto: sin él la aplicación no inicia. Ver [Base de datos MySQL/MariaDB](#base-de-datos-mysqlmariadb).

Para comprobar que Python está disponible:

```powershell
py --version
```

## Base de datos MySQL/MariaDB

Todas las pantallas, la autenticación, el CRUD, las APIs y Django Admin usan una
sola base MySQL/MariaDB (conexión `default`). MySQL y MariaDB comparten el backend
`django.db.backends.mysql` de Django; el controlador es `mysqlclient`, incluido en
`requirements.txt`. Las credenciales se leen desde `.env`
(ver [Datos sensibles y archivo .env](#datos-sensibles-y-archivo-env)).

Elige una de estas formas de levantar el servidor.

### Opción A (recomendada): contenedor con Podman o Docker

`compose.yaml` levanta MariaDB 11.4 LTS sin instalar el servidor en el sistema.
Toma la base, el usuario, la contraseña y el puerto de `.env`, crea la base con
`utf8mb4_unicode_ci`, concede al usuario permisos sobre la base de pruebas
(`db/init/01-permisos-pruebas.sh`) y guarda los datos en un volumen. Solo escucha
en `127.0.0.1`.

- **Fedora:** Podman viene instalado. Instala el proveedor de compose una vez con
  `sudo dnf install podman-compose`.
- **Windows 10/11:** instala Podman Desktop o Docker Desktop (ambos usan WSL2).
  Con Docker, reemplaza `podman compose` por `docker compose`.

Con `.env` completo, desde la raíz del proyecto (compose lee `.env` automáticamente):

```bash
podman compose up -d    # crear o iniciar
podman compose ps       # estado (healthy cuando está lista)
podman compose stop     # detener conservando los datos
podman compose down -v  # eliminar contenedor y datos
```

La base y el usuario se crean solos la primera vez. Si hay otro MySQL/MariaDB
usando el puerto 3306, detenlo o cambia `PORT` en `.env`.

#### Administración visual con phpMyAdmin

`compose.yaml` también levanta **phpMyAdmin** en <http://127.0.0.1:8081/>. Ingresa
con `USER` y `PASSWORD` de `.env` para ver las tablas (`cowork_sede`,
`cowork_espacio`, `cowork_reserva`, etc.), sus registros y su estructura, ejecutar
consultas SQL o exportar la base. Si el puerto 8081 está ocupado, define
`PHPMYADMIN_PORT` en `.env`.

Úsalo principalmente para **consultar**. Los cambios hechos directamente en las
tablas no pasan por `guardar(actor)`: no validan capacidad ni solapamientos, no
registran historial ni auditoría y pueden dejar datos inconsistentes. Para crear,
editar o dar de baja registros, utiliza las pantallas o la API de la aplicación.
Con un servidor instalado (opción B) puedes usar en su lugar HeidiSQL, MySQL
Workbench, DBeaver o el phpMyAdmin de WampServer.

### Opción B: servidor instalado en el equipo

Sirve MariaDB o MySQL instalado como servicio: en Fedora `sudo dnf install mariadb-server`
y `sudo systemctl start mariadb`; en Windows el instalador oficial de MariaDB 11.4 LTS
o MySQL 8.4 LTS, o WampServer. **XAMPP no sirve**: incluye MariaDB 10.4, más antigua
de lo que exige Django 6.1. Para comprobar la versión ejecuta `SELECT VERSION();`.

Abre la consola SQL como administrador (`sudo mariadb`, `mysql -u root -p`, HeidiSQL
o phpMyAdmin) y crea la base y un usuario exclusivo. Usa los mismos valores que
pondrás en `.env` y reemplaza la contraseña del ejemplo:

```sql
CREATE DATABASE plataforma_coworking_local
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'coworking_local'@'127.0.0.1'
    IDENTIFIED BY 'REEMPLAZA_CON_TU_CONTRASENA';
GRANT ALL PRIVILEGES ON plataforma_coworking_local.*
    TO 'coworking_local'@'127.0.0.1';
-- Base temporal que crea y elimina `python manage.py test`.
GRANT ALL PRIVILEGES ON test_plataforma_coworking_local.*
    TO 'coworking_local'@'127.0.0.1';
EXIT;
```

Ejecuta la creación solo en la primera instalación. El usuario de la aplicación
tiene permisos solamente sobre su base y la base de pruebas.

### Comprobar la conexión

Con el ambiente virtual activado y `.env` completo:

```bash
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Conexión MySQL/MariaDB correcta')"
```

MariaDB no admite el índice funcional de `Lower('correo')`; la advertencia
`models.W044` está silenciada en `drf/settings.py`. El campo `correo` sigue siendo
único y, con la collation `utf8mb4_unicode_ci`, compara sin distinguir mayúsculas
de minúsculas. En MySQL 8.4 el índice funcional sí se crea.

Referencias: [bases de datos de Django](https://docs.djangoproject.com/en/6.1/ref/databases/)
e [instalación de mysqlclient](https://github.com/PyMySQL/mysqlclient#install).

## Instalación y sesión de trabajo en Fedora Linux

Instala Python, Git y las herramientas para compilar `mysqlclient`:

```bash
sudo dnf install python3 python3-pip git gcc python3-devel mariadb-connector-c-devel pkgconf-pkg-config
python3 --version
```

En Bash, entra en la raíz del proyecto (la carpeta que contiene `manage.py`):

```bash
cd /ruta/al/Plataforma_Coworking
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp -n .env.example .env
chmod 600 .env
```

Completa `SECRET_KEY` y `PASSWORD` en `.env` (ver
[Datos sensibles y archivo .env](#datos-sensibles-y-archivo-env)), levanta la base
(ver [Base de datos MySQL/MariaDB](#base-de-datos-mysqlmariadb)) y crea las tablas:

```bash
env -u USER podman compose up -d
env -u USER python manage.py migrate
env -u USER python manage.py loaddata sedes tipos_espacio
env -u USER python manage.py createsuperuser
```

En Linux, `env -u USER` evita que la variable `USER` del sistema reemplace la de
`.env` (ver [Datos sensibles y archivo .env](#datos-sensibles-y-archivo-env)).

Si `.venv` ya existe y fue creado en este equipo con una versión compatible de Python, omite su creación. Un ambiente virtual de Windows no se puede reutilizar en Linux.

Para iniciar cada nueva sesión de desarrollo:

```bash
cd /ruta/al/Plataforma_Coworking
env -u USER podman compose up -d
source .venv/bin/activate
env -u USER python manage.py runserver
```

Abre <http://127.0.0.1:8000/>. El proyecto mantiene `DEBUG=False` y su comando `runserver` sirve los archivos estáticos durante el desarrollo. Bootstrap está incluido en el repositorio, por lo que el diseño funciona sin conexión a un CDN. `DEBUG` se lee desde `.env` y vale `False` si no lo defines.

Detén el servidor con `Ctrl+C` y cierra la sesión del ambiente con:

```bash
deactivate
```

Para comprobar la página 404 personalizada, visita <http://127.0.0.1:8000/ruta-inexistente/>. Si el servidor estaba abierto antes de actualizar el proyecto, reinícialo con `Ctrl+C` y `python manage.py runserver`, y recarga el navegador con `Ctrl+Shift+R`.

El servicio de archivos estáticos de `runserver` es solo para desarrollo y puede desactivarse con `--nostatic`. En producción, los archivos estáticos deben servirse mediante la infraestructura del despliegue.

## Instalación en Windows

Abre PowerShell y entra en la carpeta raíz del proyecto, es decir, la carpeta que contiene `manage.py`, `requirements.txt`, `drf` y `cowork`:

```powershell
cd ruta\ruta2\ruta3\Plataforma_Coworking
```

No debes entrar en la carpeta `cowork`, porque esa es solamente la aplicación interna del proyecto.

### 1. Crear el ambiente virtual

```powershell
py -m venv .venv
```

### 2. Activar el ambiente virtual

```powershell
.\.venv\Scripts\Activate.ps1
```

Cuando esté activado, aparecerá `(.venv)` al comienzo de la línea de comandos.

Si PowerShell impide ejecutar el script de activación, habilítalo solamente durante esa sesión:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar las dependencias

```powershell
python -m pip install -r requirements.txt
```

En Windows, pip descarga `mysqlclient` ya compilado: la versión 2.3.0 publica
paquetes para Python 3.12, 3.13 y 3.14 de 64 bits. No necesitas instalar un compilador.

### 4. Crear el archivo de ambiente

```powershell
Copy-Item .env.example .env
```

Completa `SECRET_KEY` y `PASSWORD` en `.env` (ver [Datos sensibles y archivo .env](#datos-sensibles-y-archivo-env)).

### 5. Levantar la base de datos y crear las tablas

Inicia MySQL/MariaDB con la opción A o B de [Base de datos MySQL/MariaDB](#base-de-datos-mysqlmariadb)
y luego ejecuta:

```powershell
python manage.py migrate
python manage.py loaddata sedes tipos_espacio
python manage.py createsuperuser
```

### 6. Iniciar la aplicación

```powershell
python manage.py runserver
```

Abre la aplicación en <http://127.0.0.1:8000/>.

## Datos iniciales (fixtures)

La carpeta `cowork/fixtures/` contiene los catálogos precargados en formato JSON,
un archivo por modelo:

| Archivo | Modelo | Registros |
| --- | --- | --- |
| `sedes.json` | `cowork.sede` | Sede Centro (Santiago), Sede Providencia, Sede Viña del Mar y Sede Concepción, todas activas |
| `tipos_espacio.json` | `cowork.tipoespacio` | Escritorio compartido, Escritorio fijo, Oficina privada, Sala de reuniones, Cabina telefónica y Sala de eventos |

Cárgalos después de `migrate`:

```bash
python manage.py loaddata sedes tipos_espacio
```

Cada registro tiene un `pk` fijo: cargar los archivos de nuevo no duplica datos,
pero **sobrescribe** la sede o el tipo con ese mismo `pk`, incluidos los cambios
hechos desde el CRUD. Ejecútalo solo en una base nueva. `loaddata` guarda los
registros directamente, sin pasar por `guardar(actor)`, por lo que la carga no
genera eventos de auditoría.

### Datos de demostración (opcional)

Para probar el flujo completo sin crear registros a mano, hay tres fixtures más
con usuarios, espacios y reservas de ejemplo:

```bash
python manage.py loaddata sedes tipos_espacio usuarios_demo espacios_demo reservas_demo
```

| Archivo | Contenido |
| --- | --- |
| `usuarios_demo.json` | 5 cuentas de Django con su perfil `Usuario` |
| `espacios_demo.json` | 8 espacios en las 4 sedes: disponibles, uno en mantenimiento y uno inactivo |
| `reservas_demo.json` | 12 reservas en los 4 estados, con su historial de estados |

Todas las cuentas usan la contraseña **`Coworking-Demo-2026`** (guardada cifrada en el JSON):

| Usuario | Rol | Para probar |
| --- | --- | --- |
| `admin_demo` | Administrador (también entra en Django Admin) | Confirmar, finalizar, gestionar catálogos y descargar reportes |
| `ana_demo` | Miembro | Ver, crear, editar y cancelar sus reservas |
| `bruno_demo` | Miembro | Reservas pendientes y confirmadas propias |
| `carla_demo` | Miembro | Reservas pendientes, confirmadas y canceladas propias |
| `diego_demo` | Miembro inactivo | El ingreso es rechazado; sus reservas se conservan |

Recorrido sugerido:

1. Ingresa como `ana_demo`: en `/reservas/` ves solo tus 4 reservas y en
   `/espacios/` no aparecen los espacios en mantenimiento ni inactivos.
2. Crea una reserva en la Sala Andes el 3 de noviembre de 2026 entre las 10:00
   y las 11:00: se rechaza porque se solapa con reservas existentes.
3. Ingresa como `admin_demo`, abre una reserva pendiente y confírmala; el
   detalle muestra el historial con el responsable de cada cambio.
4. En `/reportes/` descarga el uso diario del 1 al 8 de octubre de 2026: incluye
   las reservas finalizadas de esas fechas.

Las fechas de las reservas son fijas: las vigentes están entre octubre y
noviembre de 2026 y las finalizadas entre septiembre y octubre de 2026. Los
registros usan identificadores desde 101, para no sobrescribir cuentas creadas
con `createsuperuser`. `loaddata` no genera eventos de auditoría; las acciones
que realices después en la aplicación sí los registran. **Usa estos datos solo
en bases de desarrollo o de prueba**: las contraseñas de demostración son públicas.

Los usuarios, espacios y reservas reales no se incluyen en los fixtures base:
los usuarios necesitan una cuenta de Django con contraseña (`createsuperuser` o
el CRUD) y los espacios se crean desde `/espacios/nuevo/` usando estas sedes y tipos.

## Datos sensibles y archivo .env

La `SECRET_KEY` de Django y las credenciales de la base de datos no están en el
código. `drf/settings.py` las lee con **python-decouple** (`from decouple import config`)
desde el archivo `.env` de la raíz del proyecto, junto a `manage.py`. Django lo
carga automáticamente en Linux y Windows; no necesitas exportar variables en la terminal.

`.env` está excluido de Git. `.env.example` es la plantilla versionada con todas
las variables. Para generar una clave secreta, con el ambiente activado:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia el resultado en `.env` entre comillas simples, sin espacios alrededor del `=`:

```text
SECRET_KEY='clave_generada'
```

| Variable | Obligatoria | Uso |
| --- | --- | --- |
| `SECRET_KEY` | Sí | Clave criptográfica de Django. |
| `DEBUG` | No | `False` por defecto; mantiene la página 404 personalizada. |
| `NAME`, `USER` | Sí | Base y usuario de la aplicación (los mismos nombres de la guía). |
| `PASSWORD` | Sí | Contraseña del usuario de la aplicación. |
| `HOST`, `PORT` | No | Servidor MySQL/MariaDB; por defecto `127.0.0.1:3306`. |

Si falta una variable obligatoria, Django se detiene indicando su nombre. Una
variable definida en la terminal tiene prioridad sobre el valor de `.env`.

**Linux y macOS:** el sistema ya define `USER` con el usuario de la sesión, y por
esa prioridad Django lo usaría en lugar del de `.env` (la conexión falla con
*Access denied for user '<tu usuario>'*). Ejecuta los comandos de Django y de
compose con `env -u USER`, por ejemplo `env -u USER python manage.py runserver`
o `env -u USER podman compose up -d`. En Windows no hace falta, porque el sistema
usa `USERNAME` y no `USER`.

## Consultar MySQL con SQLAlchemy y convertir los datos a JSON

La API utiliza **SQLAlchemy** para consultar las tablas de negocio de MySQL,
**mysqlclient** para abrir la conexión y los **serializers de Django REST Framework**
para convertir los objetos obtenidos en datos JSON. SQLAlchemy utiliza el dialecto
`mysql+mysqldb`, que corresponde al paquete `mysqlclient`.

Las tablas son las mismas que crean las migraciones de Django (`cowork_sede`,
`cowork_tipoespacio`, `cowork_usuario`, `cowork_espacio` y `cowork_reserva`).
SQLAlchemy mapea esas tablas sin crear un esquema adicional y lee los mismos datos
que guardan las pantallas y la API de gestión.

Inicia sesión en `/ingresar/` con una cuenta administradora de la plataforma y
abre cualquiera de estos endpoints en el mismo navegador:

| Colección | Detalle por ID |
| --- | --- |
| `/api/mysql/sedes/` | `/api/mysql/sedes/1/` |
| `/api/mysql/tipos-espacio/` | `/api/mysql/tipos-espacio/1/` |
| `/api/mysql/usuarios/` | `/api/mysql/usuarios/1/` |
| `/api/mysql/espacios/` | `/api/mysql/espacios/1/` |
| `/api/mysql/reservas/` | `/api/mysql/reservas/1/` |

La API admite consultas de lectura y requiere un administrador activo. Los serializers
exponen campos explícitos: no incluyen contraseñas, la cuenta de autenticación
ni las observaciones privadas del espacio. Las reservas incluyen su usuario,
espacio, sede y tipo; las fechas se representan en ISO 8601 con zona UTC (`Z`).

Los listados devuelven `count`, `limit`, `offset` y `results`. Por ejemplo,
`/api/mysql/sedes/?limit=10&offset=0` puede devolver:

```json
{
  "count": 1,
  "limit": 10,
  "offset": 0,
  "results": [
    {
      "id": 1,
      "nombre": "Sede Centro",
      "direccion": "Calle 123",
      "ciudad": "Santiago",
      "activa": true
    }
  ]
}
```

El límite predeterminado es 100, el máximo 200 y `offset` debe ser no negativo.
Una tabla vacía devuelve `results: []`; un ID inexistente devuelve HTTP 404.
Los parámetros inválidos devuelven HTTP 400 y la falta de permisos HTTP 403.
Si falta el driver, el servicio no responde o las tablas
no están preparadas, la API devuelve HTTP 503 sin publicar detalles de la conexión.

También puedes consultar y serializar desde el shell de Django:

```python
import json
from sqlalchemy import select
from cowork.database import sesion_mysql
from cowork.models_sqlalchemy import SedeSQL
from cowork.serializers_mysql import SedeSerializer

with sesion_mysql() as sesion:
    sedes = sesion.scalars(select(SedeSQL).order_by(SedeSQL.id).limit(100)).all()
    datos = SedeSerializer(sedes, many=True).data

print(json.dumps(datos, ensure_ascii=False, indent=2))
```

La sesión se cierra después de cada consulta y las relaciones se cargan con JOINs
para evitar una consulta adicional por registro. La configuración se reutiliza
desde `DATABASES['default']`; no necesitas definir otra URL ni duplicar credenciales.

Para ejecutar las pruebas, que utilizan una base SQLAlchemy aislada en memoria y no modifican MySQL local:

```bash
python manage.py test tests.test_api_mysql --noinput
```

Archivos principales: `cowork/database.py`, `cowork/models_sqlalchemy.py`,
`cowork/serializers_mysql.py`, `cowork/views.py` y `cowork/urls.py`.

Los ViewSets de consulta están en `cowork/views.py`. Se registran en el router
`enrutador_mysql` (`DefaultRouter`) de `cowork/urls.py` y se incluyen bajo
`/api/mysql/`, con los nombres `api_mysql:sede-list`, `api_mysql:sede-detail`, etc.
`/api/mysql/` muestra la raíz de la API con el enlace de cada colección.

Referencias: [SQLAlchemy con mysqlclient](https://docs.sqlalchemy.org/en/20/dialects/mysql.html#module-sqlalchemy.dialects.mysql.mysqldb)
y [serializers de Django REST Framework](https://www.django-rest-framework.org/api-guide/serializers/).

## Guardar mediante ViewSets y DefaultRouter

Los ViewSets de gestión también están en **`cowork/views.py`**, dentro de la
aplicación. Heredan de `viewsets.ModelViewSet` (con `queryset` y `serializer_class`,
como en la guía) junto con `ReglasGestion`, que agrega la autenticación, los
permisos por acción y el borrado mediante `eliminar(actor)`. Sus serializers están
en `cowork/serializer.py`. `cowork/urls.py` los registra en un `routers.DefaultRouter`
(`enrutador.register(r'sedes', views.SedeViewSet, basename='sede')`, etc.) y
incluye sus rutas bajo `/cowork/` (por ejemplo `/cowork/sedes/`), como indica la guía. El router genera las rutas de los métodos que
implementa cada ViewSet y de sus acciones `@action` (activar, desactivar,
confirmar, cancelar y finalizar). `/cowork/` muestra la raíz de la API con el enlace de cada
recurso. Los identificadores usan el conversor `int`, igual que las pantallas.
Utilizan la base principal MySQL/MariaDB, la misma de las pantallas de gestión y
de la API de consulta `/api/mysql/`.

| Recurso | Listar y crear | Consultar, editar y eliminar | Acciones POST por ID |
| --- | --- | --- | --- |
| Sedes | `/cowork/sedes/` | `/cowork/sedes/1/` | `/cowork/sedes/1/desactivar/` |
| Tipos de espacio | `/cowork/tipos-espacio/` | `/cowork/tipos-espacio/1/` | |
| Usuarios | `/cowork/usuarios/` | `/cowork/usuarios/1/` | `/cowork/usuarios/1/desactivar/`, `/cowork/usuarios/1/activar/` |
| Espacios | `/cowork/espacios/` | `/cowork/espacios/1/` | `/cowork/espacios/1/desactivar/` |
| Reservas | `/cowork/reservas/` | `/cowork/reservas/1/` | `/cowork/reservas/1/confirmar/`, `/cowork/reservas/1/cancelar/`, `/cowork/reservas/1/finalizar/` |
| Historial de reservas (solo consulta) | `/cowork/historial-reservas/` | `/cowork/historial-reservas/1/` | |
| Eventos de auditoría (solo consulta) | `/cowork/eventos-auditoria/` | `/cowork/eventos-auditoria/1/` | |

Usa `GET` para consultar, `POST` sobre la colección para crear, `PUT` o `PATCH`
sobre el detalle para editar y `DELETE` sobre el detalle para eliminar. Crear
devuelve HTTP 201; editar y ejecutar acciones devuelven HTTP 200 y eliminar
devuelve HTTP 204. Los administradores gestionan los catálogos y los miembros
solo consultan las sedes activas y los tipos.

El historial y la auditoría son registros que escriben las propias operaciones,
por eso sus ViewSets heredan de `viewsets.ReadOnlyModelViewSet`: solo permiten
`GET` y cualquier otro método responde HTTP 405. El historial lo consultan el
administrador (todo) y el miembro (solo el de sus reservas); la auditoría
requiere el permiso `ver_auditoria`, que solo tiene el administrador.

#### Eliminación protegida

`DELETE` borra el registro de la base solo si no rompe datos relacionados; en
caso contrario devuelve HTTP 400 con el motivo y la alternativa:

| Recurso | Se elimina cuando | Si no se puede |
| --- | --- | --- |
| Sede | No tiene espacios | Desactivarla (`desactivar/`) o eliminar antes sus espacios |
| Tipo de espacio | No tiene espacios | Mantenerlo |
| Espacio | No tiene reservas | Inactivarlo (`desactivar/`) para conservar su historial |
| Usuario | No tiene reservas ni acciones en la auditoría o el historial, y no es quien elimina | Desactivarlo (`desactivar/`) |
| Reserva | Está `pendiente` o `cancelada` | Cancelar primero una confirmada; las finalizadas se conservan para los reportes |

Eliminar un usuario borra también su cuenta de acceso de Django. Eliminar una
reserva borra también su historial de estados. Cada eliminación registra un
evento `eliminar` en la auditoría con los valores que tenía el registro. El
titular puede eliminar sus propias reservas; el resto requiere un administrador.

Los administradores activos gestionan usuarios y espacios, y confirman o
finalizan reservas. Los miembros activos pueden consultar espacios disponibles
y crear, editar o cancelar sus propias reservas. Cada guardado utiliza los
métodos del modelo para aplicar permisos, validaciones, historial y auditoría.
Los errores de validación devuelven HTTP 400 con los campos correspondientes.

Después de iniciar sesión en `/ingresar/`, un miembro puede enviar este JSON a
`POST /cowork/reservas/`, usando el ID de un espacio existente y un horario libre:

```json
{
  "espacio": 1,
  "inicio": "2026-10-12T15:00:00Z",
  "fin": "2026-10-12T16:00:00Z",
  "cantidad_personas": 2,
  "observaciones": "Necesito proyector"
}
```

La API asigna al miembro como titular. Para crear como administrador, incluye
`usuario` con el ID del titular. `estado`, `fecha_creacion` y `motivo_cancelacion`
son campos de lectura; los cambios de estado se realizan mediante las acciones.
Para cancelar, envía `{"motivo": "Cambio de planes"}` a la ruta de cancelación.

Crear usuarios requiere `nombre_usuario`, `password`, `nombre` y `correo`;
`apellido` y `rol` son opcionales. Al editar, omite `password` para conservar la
contraseña. La API reutiliza `UsuarioForm` para validar y guardar la cuenta junto
al perfil. Las contraseñas nunca se incluyen en las respuestas.

Las peticiones usan autenticación de sesión. Para `POST`, `PUT` y `PATCH`, envía
la cookie de sesión y el encabezado `X-CSRFToken` con el valor de la cookie
`csrftoken`, obtenida al abrir una pantalla de gestión. Los listados devuelven
una lista JSON; los detalles y guardados devuelven un objeto, con las relaciones
de gestión representadas por sus IDs. Las observaciones privadas de los espacios
solo se muestran a administradores.

Los nombres de las rutas, generados por el router a partir del `basename`, siguen
el formato `api:usuario-list`, `api:usuario-detail`, `api:espacio-desactivar` o
`api:reserva-confirmar`.
Para validar las rutas de ambas APIs y los flujos de guardado con bases aisladas:

```bash
python manage.py test tests.test_viewsets tests.test_api_mysql --noinput
```

Archivos principales: `cowork/views.py`, `cowork/serializer.py`,
`cowork/urls.py` y `drf/urls.py`.
Referencia: [ViewSets de Django REST Framework](https://www.django-rest-framework.org/api-guide/viewsets/).

## Rutas disponibles

| URL | Vista | Plantilla | Resultado |
| --- | --- | --- | --- |
| `/` | `bienvenida` | `cowork/bienvenida.html` | Página de bienvenida |
| `/inicio/` | `inicio` | `cowork/inicio.html` | Página principal |
| `/admin/` | `admin.site.urls` | Django Admin | CRUD de los modelos con las mismas reglas y auditoría |
| Cualquier URL inexistente | `Error404ViewSet.retrieve` | `cowork/404.html` | Error HTTP 404 personalizado |

El botón **Entrar a la plataforma** utiliza el nombre de la ruta `inicio` para navegar desde la bienvenida hasta `/inicio/`.

Las páginas `bienvenida` e `inicio` son funciones, como en la guía; el resto de
las vistas HTTP propias de la aplicación están agrupadas en ViewSets dentro de
`cowork/views.py`. `SedePantallaViewSet`, `TipoEspacioPantallaViewSet`,
`UsuarioPantallaViewSet`, `EspacioPantallaViewSet`, `ReservaPantallaViewSet` y
`ReportePantallaViewSet` reúnen los listados, formularios y acciones de las
pantallas HTML.

Las APIs JSON (`/cowork/` y `/api/mysql/`) usan `DefaultRouter`. Las pantallas HTML
declaran sus rutas con `path()`, porque sus URLs (`nuevo/`, `editar/`, `desactivar/`)
y sus nombres (`usuario_crear`, `espacio_editar`, etc.) son los que usan las
plantillas y las redirecciones; un router genera otro formato de URLs pensado
para APIs. Cada ruta indica el método HTTP y la acción del ViewSet mediante
`as_view()` y los identificadores utilizan el conversor `<int:pk>`.

Los listados y detalles permiten `GET` y `HEAD`. Crear, editar, cancelar y
desactivar permiten `GET` para mostrar el formulario y `POST` para guardarlo;
confirmar y finalizar requieren `POST`. `AutenticacionViewSet` agrupa `/ingresar/`
y `/salir/`, reutilizando las vistas de Django para conservar la sesión, la
protección CSRF y la validación de las redirecciones. Las pantallas protegidas
siguen enviando al formulario de acceso a quienes no han iniciado sesión.

## Modelos y CRUD de coworking

El modelo de negocio incluye `Usuario`, `Espacio`, `Reserva`, `HistorialEstadoReserva` y `EventoAuditoria`. `ServicioReportes` es un servicio de consultas en `cowork/services.py`, no una tabla. Se conservan los catálogos `Sede` y `TipoEspacio`: cada espacio pertenece a una sede y a un tipo. También se mantiene `cantidad_personas` para validar la capacidad de las reservas.

Los identificadores del diagrama corresponden al campo `id` automático de Django, disponible como `pk`. Las operaciones del diagrama conservan sus nombres, por ejemplo `puedeRealizar`, `estaDisponible`, `confirmar` y `consultarDetalle`.

### Preparar el primer acceso

Después de actualizar los archivos, ejecuta desde la carpeta que contiene `manage.py`:

```powershell
python manage.py migrate
python manage.py loaddata sedes tipos_espacio
python manage.py createsuperuser
python manage.py runserver
```

Si ya tienes una cuenta de superusuario, puedes utilizarla. Su perfil `Usuario` se crea con rol `ADMINISTRADOR` al acceder por primera vez al CRUD. La autenticación utiliza la cuenta existente de Django mediante una relación uno a uno; no se cambia `AUTH_USER_MODEL` ni se reemplazan sus tablas.

1. Entra en `/ingresar/` con el nombre de acceso y la contraseña del superusuario.
2. Si cargaste los [datos iniciales](#datos-iniciales-fixtures), ya tienes sedes y tipos de espacio. Si no, crea al menos una sede en `/sedes/nueva/` y un tipo en `/tipos-espacio/nuevo/`.
3. Crea espacios desde `/espacios/nuevo/` y usuarios desde `/usuarios/nuevo/`.
4. Los miembros pueden ingresar con las credenciales asignadas y crear reservas desde `/reservas/nueva/`.

El formulario de usuario crea también su cuenta de acceso. Las contraseñas se almacenan con el mecanismo de Django y no se incluyen en la auditoría. Al editar un usuario, una contraseña vacía conserva la contraseña actual.

### Pantallas disponibles

| URL | Función | Acceso |
| --- | --- | --- |
| `/ingresar/` | Inicio de sesión | Público |
| `/salir/` | Cierre de sesión mediante POST | Autenticado |
| `/sedes/` | Listado de sedes | Administrador |
| `/sedes/nueva/` | Crear sede | Administrador |
| `/sedes/<id>/editar/` | Editar sede | Administrador |
| `/sedes/<id>/desactivar/` | Confirmar la desactivación | Administrador |
| `/sedes/<id>/eliminar/` | Eliminar una sede sin espacios | Administrador |
| `/tipos-espacio/` | Listado de tipos de espacio | Administrador |
| `/tipos-espacio/nuevo/` | Crear tipo | Administrador |
| `/tipos-espacio/<id>/editar/` | Editar tipo | Administrador |
| `/tipos-espacio/<id>/eliminar/` | Eliminar un tipo sin espacios | Administrador |
| `/usuarios/` | Listado de usuarios | Administrador |
| `/usuarios/nuevo/` | Crear usuario y cuenta | Administrador |
| `/usuarios/<id>/editar/` | Editar datos y rol | Administrador |
| `/usuarios/<id>/desactivar/` | Confirmar la baja lógica | Administrador |
| `/usuarios/<id>/activar/` | Confirmar la reactivación de un usuario inactivo | Administrador |
| `/usuarios/<id>/eliminar/` | Eliminar un usuario sin actividad | Administrador |
| `/espacios/` | Consultar espacios | Miembro o administrador |
| `/espacios/nuevo/` | Crear espacio | Administrador |
| `/espacios/<id>/editar/` | Editar espacio y estado | Administrador |
| `/espacios/<id>/desactivar/` | Confirmar la inactivación | Administrador |
| `/espacios/<id>/eliminar/` | Eliminar un espacio sin reservas | Administrador |
| `/reservas/` | Listar reservas | Miembro: propias; administrador: todas |
| `/reservas/nueva/` | Crear una reserva pendiente | Miembro o administrador |
| `/reservas/<id>/` | Detalle e historial | Titular o administrador |
| `/reservas/<id>/editar/` | Editar una reserva pendiente | Titular o administrador |
| `/reservas/<id>/cancelar/` | Cancelar indicando un motivo | Titular o administrador |
| `/reservas/<id>/confirmar/` | Confirmar mediante POST | Administrador |
| `/reservas/<id>/finalizar/` | Finalizar mediante POST | Administrador |
| `/reservas/<id>/eliminar/` | Eliminar una reserva pendiente o cancelada | Titular o administrador |
| `/reportes/` | Descargar reportes en PDF o Excel | Administrador |

Las pantallas incluyen protección CSRF. Los formularios de baja y de eliminación muestran una confirmación; solo POST modifica datos. El botón **Eliminar** aparece solo cuando el registro se puede eliminar; si otra acción lo impide entre tanto, la pantalla muestra el motivo. El miembro no puede cambiar el titular de su reserva ni acceder a reservas ajenas. Las observaciones privadas del espacio se muestran únicamente al administrador.

### Reglas del negocio

- Roles: `MIEMBRO` y `ADMINISTRADOR`. El correo es único sin distinguir mayúsculas de minúsculas.
- Un espacio puede estar `disponible`, en `mantenimiento` o `inactivo`. Su sede debe estar activa para admitir reservas.
- Una reserva nueva queda `pendiente`. El administrador puede confirmarla. El titular o el administrador pueden cancelar reservas pendientes o confirmadas; el motivo es obligatorio. El administrador puede finalizar una reserva confirmada después de su hora de fin.
- El fin debe ser posterior al inicio. La cantidad de personas debe ser positiva y no superar la capacidad del espacio.
- Las reservas pendientes y confirmadas bloquean su intervalo. Una reserva que termina exactamente cuando empieza otra no se solapa. Las reservas canceladas y finalizadas no bloquean disponibilidad.
- Cada reserva creada por el CRUD incluye un estado inicial en el historial. Cada transición agrega el estado anterior, el nuevo, la fecha, el responsable y el motivo.
- Desactivar una sede hace que sus espacios dejen de aceptar reservas nuevas; las existentes se conservan. Desactivar un usuario también impide su acceso mediante la cuenta de Django; sus reservas se conservan. Activarlo le devuelve el acceso con su misma contraseña.
- La eliminación física está protegida (ver [Eliminación protegida](#eliminación-protegida)): sedes y tipos sin espacios, espacios sin reservas, usuarios sin actividad y reservas pendientes o canceladas. Para registros con historial se utiliza la baja lógica (desactivar o cancelar).
- Elimina siempre con `eliminar(actor)`, que valida, aplica permisos y audita. Llamar directamente a `delete()` en sedes, espacios, usuarios o reservas lanza un error.
- `guardar(actor)` en los modelos aplica validaciones, permisos y auditoría dentro de una transacción. Para cambiar el estado de una reserva, utiliza `confirmar`, `cancelar` o `finalizar`. No uses `save()` o `QuerySet.update()` para ejecutar operaciones de negocio: esas operaciones de Django no aplican el flujo completo.

Antes de comprobar la disponibilidad, `guardar` bloquea la fila del espacio con `SELECT ... FOR UPDATE` en MySQL/MariaDB, de modo que dos reservas simultáneas del mismo espacio se validan una después de la otra. Los métodos vuelven a validar al guardar, aunque el formulario ya haya pasado su validación.

En Django Admin todos los modelos están registrados. Sedes, tipos de espacio, espacios, usuarios y reservas se crean, editan y eliminan mediante `guardar(actor)` y `eliminar(actor)`, con las mismas reglas, permisos y auditoría que las pantallas. El historial, la auditoría y la lista de administradores (modelo proxy `Administrador`) son de solo consulta; un administrador se crea o cambia de rol desde Usuarios.

### Migraciones y datos existentes

La migración `0004_interaccion_del_usuario` crea los perfiles, el historial de reservas y los eventos de auditoría con sus relaciones incluidas. Reemplaza a `0004_modelos_diagrama`: Django reconoce las bases que ya aplicaron ese nombre, sin volver a crear tablas ni requerir borrar la base de datos. El modelo de auditoría mantiene el nombre `EventoAuditoria`.

Las migraciones nuevas renombran `Espacio.descripcion` a `descripcion_publica` y `Reserva.creada_en` a `fecha_creacion`, conservando sus valores. Los espacios antiguos con `activo=False` quedan `inactivos`. Las reservas existentes conservan sus identificadores, sus estados y sus referencias, y reciben un registro inicial del historial con responsable desconocido.

Las cuentas existentes reciben un perfil de usuario. Si una cuenta carece de correo o comparte el mismo correo con otra, su perfil recibe un correo temporal único terminado en `@example.invalid`; el administrador debe corregirlo. El correo de la cuenta original se conserva durante la migración.

Al revertir al esquema anterior, las reservas vuelven a referenciar cuentas Django; la clave foránea se recrea después de convertir los identificadores, porque MySQL la valida de inmediato. Las reservas pendientes pasan a confirmadas porque el esquema anterior no incluía el estado pendiente. Revertir elimina las tablas nuevas de perfiles, historial y auditoría; conserva primero una copia de la base de datos si necesitas esos registros.

### Servicio de reportes

`ServicioReportes.buscarReservas(filtros, actor)` acepta `usuario_id`, `espacio_id`, `estado`, `desde` y `hasta`. Los miembros siempre reciben únicamente sus propias reservas. Los filtros de fechas incluyen reservas que se cruzan con el período.

Los métodos `calcularUsoEspacios`, `resumirActividad` y `analizarUsuarios` requieren un administrador y un período con fin posterior al inicio. El uso de espacios suma horas confirmadas o finalizadas, recortadas al período solicitado.

### Descargar reportes en PDF o Excel

Los administradores descargan reportes desde la pantalla `/reportes/` (enlace
**Reportes** del menú) o desde la API `GET /cowork/reportes/`. Ambas validan los
parámetros con `ReporteForm` y generan el archivo con `ServicioReportes.generarDocumento`.

| Parámetro | Valores | Uso |
| --- | --- | --- |
| `tipo` | `reservas` o `diario` | Detalle de reservas, o uso diario (reservas y horas) por espacio. |
| `formato` | `pdf` o `xlsx` | Documento PDF o libro Excel. |
| `desde`, `hasta` | Fecha `AAAA-MM-DD` | Período; `hasta` incluye el día completo. Obligatorio para `diario` (máximo 366 días). |
| `usuario`, `espacio` | ID | Opcional, solo para `reservas`. |
| `estado` | `pendiente`, `confirmada`, `cancelada` o `finalizada` | Opcional, solo para `reservas`. |

Por ejemplo, con la sesión iniciada como administrador:

```text
/cowork/reportes/?tipo=diario&formato=xlsx&desde=2026-10-01&hasta=2026-10-31
```

La respuesta es el archivo adjunto (`reporte-diario.xlsx` o `reporte-reservas.pdf`).
Los parámetros inválidos devuelven HTTP 400 con los errores por campo y los
miembros reciben HTTP 403. Las horas se muestran en la zona horaria del proyecto.

### Pruebas

Todas las pruebas están en la carpeta `tests/` de la raíz del proyecto, separadas
de `cowork/` y `drf/`. Los archivos se agrupan por tema: configuración, páginas
y catálogos, gestión, modelos, migraciones, reportes, API MySQL y ViewSets.

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Las pruebas se ejecutan sobre MySQL/MariaDB: Django crea la base temporal
`test_<NAME>` y la elimina al terminar, sin tocar los datos de la base
principal. El usuario de `.env` necesita permisos sobre esa base (el contenedor
los concede solo; con un servidor instalado, ver el `GRANT` de la opción B).

Puedes ejecutar la carpeta completa con `python manage.py test tests` o un solo
módulo, por ejemplo `python manage.py test tests.test_gestion`.

Las pruebas cubren el acceso por rol, la privacidad de reservas y espacios, el CRUD, CSRF, correo único, capacidad, solapamientos, transiciones, historial, auditoría y conservación de datos al migrar y revertir.

## Flujo de una petición

```text
URL solicitada
    ↓
drf/urls.py recibe la petición e incluye las rutas de cowork
    ↓
cowork/urls.py busca una coincidencia
    ↓
cowork/views.py ejecuta la acción del ViewSet asociado
    ↓
render() carga una plantilla desde cowork/templates/cowork/, que extiende cowork/base.html
    ↓
Django devuelve una respuesta HTTP al navegador
```

Si ninguna ruta coincide, Django utiliza `handler404`, ejecuta `Error404ViewSet.retrieve` y devuelve `cowork/404.html` con estado HTTP 404.

## Organización de las rutas

`drf/urls.py` es el enrutador principal del proyecto. Mantiene la ruta administrativa, el controlador global del error 404 y utiliza `include()` para delegar las rutas públicas a la aplicación.

`cowork/urls.py` concentra todas las rutas de la aplicación: páginas públicas, autenticación, gestión HTML y las APIs JSON. Las pantallas se declaran con `path()`; las APIs se registran en dos `DefaultRouter` (`enrutador` y `enrutador_mysql`), incluidos con los namespaces `api` y `api_mysql`. `drf/urls.py` incluye únicamente este archivo para las rutas de cowork, además de la ruta administrativa y el controlador global del error 404.

## Dependencias

Las dependencias utilizadas están registradas en `requirements.txt`:

- **Django:** framework principal que recibe las peticiones y relaciona rutas, vistas y plantillas.
- **asgiref:** dependencia de Django que proporciona compatibilidad con ASGI y ejecución asíncrona.
- **sqlparse:** dependencia utilizada por Django para analizar y dar formato a instrucciones SQL.
- **mysqlclient:** controlador recomendado por Django para conectarse a MySQL/MariaDB.
- **SQLAlchemy:** ORM utilizado por la API de consulta `/api/mysql/`.
- **tzdata:** base de zonas horarias de Python; necesaria en Windows, que no la incluye en el sistema.
- **openpyxl y reportlab:** generan los reportes en Excel y PDF.
- **djangorestframework:** serializers y ViewSets de las APIs JSON.
- **python-decouple:** lee la `SECRET_KEY` y las credenciales de la base de datos desde `.env`.
- **Bootstrap 5.3.3:** se carga desde `cowork/static/cowork/vendor/bootstrap/` en `cowork/base.html` y aporta la grilla responsive y utilidades de interfaz. Se incluye su licencia MIT y los archivos oficiales CSS y JavaScript.

## Frontend y sistema visual

El frontend utiliza **plantillas Django + Bootstrap 5.3 + CSS propio**. Esta combinación es la más adecuada para la etapa actual porque no requiere Node.js, un compilador ni comandos adicionales: basta con iniciar Django para trabajar en las vistas.

- `cowork/templates/cowork/base.html`: estructura compartida y carga de Bootstrap/CSS.
- `cowork/templates/cowork/bienvenida.html`: portada y presentación de la propuesta de valor.
- `cowork/templates/cowork/inicio.html`: vista general de la plataforma.
- `cowork/templates/cowork/404.html`: página de error consistente con la marca.
- `cowork/static/cowork/css/styles.css`: colores, tipografía, componentes y reglas responsive.

Se recomienda mantener esta base hasta que la aplicación necesite una interfaz altamente interactiva. **Tailwind CSS** sería útil si el equipo adoptara Node.js y un flujo de compilación; **React o Vue** solo se justificarían si el producto evolucionara hacia una aplicación con mucho estado en el navegador. Para las vistas renderizadas por Django, Bootstrap más CSS propio ofrece menor complejidad y mantenimiento directo.

## Archivos excluidos de Git

- `.venv/`: contiene el ambiente virtual local.
- `.env`: contiene la `SECRET_KEY` y las credenciales de la base de datos. Se versiona solo `.env.example`.
- `__pycache__/` y `*.pyc`: archivos temporales generados por Python.

## Detener el servidor

Presiona `Ctrl+C` en la terminal donde se está ejecutando Django.
