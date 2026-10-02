# Plataforma Coworking

Plataforma de trabajo compartido orientada a organizar espacios, reservas y comunidad de una manera clara y sencilla.

## Requisitos

- Python instalado.
- Git instalado.
- Windows 10 u 11.

Para comprobar que Python está disponible:

```powershell
py --version
```

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

### 4. Preparar la base de datos

```powershell
python manage.py migrate
```

El archivo `db.sqlite3` se crea localmente y está excluido del repositorio mediante `.gitignore`.

### 5. Iniciar la aplicación

```powershell
python manage.py runserver
```

Abre la aplicación en <http://127.0.0.1:8000/>.

## Rutas disponibles

| URL | Vista | Plantilla | Resultado |
| --- | --- | --- | --- |
| `/` | `bienvenida` | `cowork/bienvenida.html` | Página de bienvenida |
| `/inicio/` | `inicio` | `cowork/inicio.html` | Página principal |
| Cualquier URL inexistente | `error_404` | `cowork/404.html` | Error HTTP 404 personalizado |

El botón **Entrar a la plataforma** utiliza el nombre de la ruta `inicio` para navegar desde la bienvenida hasta `/inicio/`.

## Modelos y CRUD de coworking

El modelo de negocio incluye `Usuario`, `Espacio`, `Reserva`, `HistorialEstadoReserva` y `EventoAuditoria`. `ServicioReportes` es un servicio de consultas en `cowork/services.py`, no una tabla. Se conservan los catálogos `Sede` y `TipoEspacio`: cada espacio pertenece a una sede y a un tipo. También se mantiene `cantidad_personas` para validar la capacidad de las reservas.

Los identificadores del diagrama corresponden al campo `id` automático de Django, disponible como `pk`. Las operaciones del diagrama conservan sus nombres, por ejemplo `puedeRealizar`, `estaDisponible`, `confirmar` y `consultarDetalle`.

### Preparar el primer acceso

Después de actualizar los archivos, ejecuta desde la carpeta que contiene `manage.py`:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Si ya tienes una cuenta de superusuario, puedes utilizarla. Su perfil `Usuario` se crea con rol `ADMINISTRADOR` al acceder por primera vez al CRUD. La autenticación utiliza la cuenta existente de Django mediante una relación uno a uno; no se cambia `AUTH_USER_MODEL` ni se reemplazan sus tablas.

1. Entra en `/gestion-interna/` con el superusuario y crea al menos una sede y un tipo de espacio. Si configuraste `DJANGO_ADMIN_URL_PATH`, utiliza esa ruta administrativa.
2. Entra en `/ingresar/` con el nombre de acceso y la contraseña del superusuario.
3. Crea espacios desde `/espacios/nuevo/` y usuarios desde `/usuarios/nuevo/`.
4. Los miembros pueden ingresar con las credenciales asignadas y crear reservas desde `/reservas/nueva/`.

El formulario de usuario crea también su cuenta de acceso. Las contraseñas se almacenan con el mecanismo de Django y no se incluyen en la auditoría. Al editar un usuario, una contraseña vacía conserva la contraseña actual.

### Pantallas disponibles

| URL | Función | Acceso |
| --- | --- | --- |
| `/ingresar/` | Inicio de sesión | Público |
| `/salir/` | Cierre de sesión mediante POST | Autenticado |
| `/usuarios/` | Listado de usuarios | Administrador |
| `/usuarios/nuevo/` | Crear usuario y cuenta | Administrador |
| `/usuarios/<id>/editar/` | Editar datos y rol | Administrador |
| `/usuarios/<id>/desactivar/` | Confirmar la baja lógica | Administrador |
| `/espacios/` | Consultar espacios | Miembro o administrador |
| `/espacios/nuevo/` | Crear espacio | Administrador |
| `/espacios/<id>/editar/` | Editar espacio y estado | Administrador |
| `/espacios/<id>/desactivar/` | Confirmar la inactivación | Administrador |
| `/reservas/` | Listar reservas | Miembro: propias; administrador: todas |
| `/reservas/nueva/` | Crear una reserva pendiente | Miembro o administrador |
| `/reservas/<id>/` | Detalle e historial | Titular o administrador |
| `/reservas/<id>/editar/` | Editar una reserva pendiente | Titular o administrador |
| `/reservas/<id>/cancelar/` | Cancelar indicando un motivo | Titular o administrador |
| `/reservas/<id>/confirmar/` | Confirmar mediante POST | Administrador |
| `/reservas/<id>/finalizar/` | Finalizar mediante POST | Administrador |

Las pantallas incluyen protección CSRF. Los formularios de baja muestran una confirmación; solo POST modifica datos. El miembro no puede cambiar el titular de su reserva ni acceder a reservas ajenas. Las observaciones privadas del espacio se muestran únicamente al administrador.

### Reglas del negocio

- Roles: `MIEMBRO` y `ADMINISTRADOR`. El correo es único sin distinguir mayúsculas de minúsculas.
- Un espacio puede estar `disponible`, en `mantenimiento` o `inactivo`. Su sede debe estar activa para admitir reservas.
- Una reserva nueva queda `pendiente`. El administrador puede confirmarla. El titular o el administrador pueden cancelar reservas pendientes o confirmadas; el motivo es obligatorio. El administrador puede finalizar una reserva confirmada después de su hora de fin.
- El fin debe ser posterior al inicio. La cantidad de personas debe ser positiva y no superar la capacidad del espacio.
- Las reservas pendientes y confirmadas bloquean su intervalo. Una reserva que termina exactamente cuando empieza otra no se solapa. Las reservas canceladas y finalizadas no bloquean disponibilidad.
- Cada reserva creada por el CRUD incluye un estado inicial en el historial. Cada transición agrega el estado anterior, el nuevo, la fecha, el responsable y el motivo.
- Usuarios y espacios utilizan baja lógica. Las reservas se cancelan y sus registros se conservan. Desactivar un usuario también impide su acceso mediante la cuenta de Django; sus reservas existentes se conservan.
- `guardar(actor)` en los modelos aplica validaciones, permisos y auditoría dentro de una transacción. Para cambiar el estado de una reserva, utiliza `confirmar`, `cancelar` o `finalizar`. No uses `save()` o `QuerySet.update()` para ejecutar operaciones de negocio: esas operaciones de Django no aplican el flujo completo.

SQLite utiliza transacciones `IMMEDIATE` para serializar las escrituras antes de comprobar la disponibilidad. Los métodos vuelven a validar al guardar, aunque el formulario ya haya pasado su validación.

En Django Admin, los catálogos Sede y TipoEspacio se pueden gestionar. Usuario, Espacio, Reserva, HistorialEstadoReserva y EventoAuditoria se registran para consulta; sus cambios se realizan mediante el CRUD para aplicar las reglas y la auditoría.

### Migraciones y datos existentes

Las migraciones nuevas renombran `Espacio.descripcion` a `descripcion_publica` y `Reserva.creada_en` a `fecha_creacion`, conservando sus valores. Los espacios antiguos con `activo=False` quedan `inactivos`. Las reservas existentes conservan sus identificadores, sus estados y sus referencias, y reciben un registro inicial del historial con responsable desconocido.

Las cuentas existentes reciben un perfil de usuario. Si una cuenta carece de correo o comparte el mismo correo con otra, su perfil recibe un correo temporal único terminado en `@example.invalid`; el administrador debe corregirlo. El correo de la cuenta original se conserva durante la migración.

Al revertir al esquema anterior, las reservas vuelven a referenciar cuentas Django. Las reservas pendientes pasan a confirmadas porque el esquema anterior no incluía el estado pendiente. Revertir elimina las tablas nuevas de perfiles, historial y auditoría; conserva primero una copia de la base de datos si necesitas esos registros.

### Servicio de reportes

`ServicioReportes.buscarReservas(filtros, actor)` acepta `usuario_id`, `espacio_id`, `estado`, `desde` y `hasta`. Los miembros siempre reciben únicamente sus propias reservas. Los filtros de fechas incluyen reservas que se cruzan con el período.

Los métodos `calcularUsoEspacios`, `resumirActividad` y `analizarUsuarios` requieren un administrador y un período con fin posterior al inicio. El uso de espacios suma horas confirmadas o finalizadas, recortadas al período solicitado. Los reportes están disponibles desde Python; esta primera entrega no incluye una pantalla de reportes ni una API REST.

### Pruebas

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Las pruebas cubren el acceso por rol, la privacidad de reservas y espacios, el CRUD, CSRF, correo único, capacidad, solapamientos, transiciones, historial, auditoría y conservación de datos al migrar y revertir.

## Flujo de una petición

```text
URL solicitada
    ↓
drf/urls.py recibe la petición e incluye las rutas de cowork
    ↓
cowork/urls.py busca una coincidencia
    ↓
cowork/views.py ejecuta la vista asociada
    ↓
render() carga una plantilla desde cowork/templates/cowork/, que extiende cowork/base.html
    ↓
Django devuelve una respuesta HTTP al navegador
```

Si ninguna ruta coincide, Django utiliza `handler404`, ejecuta la vista `error_404` y devuelve `cowork/404.html` con estado HTTP 404.

## Organización de las rutas

`drf/urls.py` es el enrutador principal del proyecto. Mantiene la ruta administrativa, el controlador global del error 404 y utiliza `include()` para delegar las rutas públicas a la aplicación.

`cowork/urls.py` contiene las rutas propias de `cowork`: la bienvenida y el inicio. De esta manera, el núcleo decide a qué aplicación enviar la petición y cada aplicación administra sus propios endpoints.

## Dependencias

Las dependencias utilizadas están registradas en `requirements.txt`:

- **Django:** framework principal que recibe las peticiones y relaciona rutas, vistas y plantillas.
- **asgiref:** dependencia de Django que proporciona compatibilidad con ASGI y ejecución asíncrona.
- **sqlparse:** dependencia utilizada por Django para analizar y dar formato a instrucciones SQL.
- **Bootstrap 5.3:** se carga desde jsDelivr en `cowork/base.html` y aporta la grilla responsive y utilidades de interfaz.

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
- `db.sqlite3`: contiene la base de datos local.
- `.env`: puede contener variables privadas.
- `__pycache__/` y `*.pyc`: archivos temporales generados por Python.

## Detener el servidor

Presiona `Ctrl+C` en la terminal donde se está ejecutando Django.
