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
cd ruta\donde\clonaste\Plataforma_Coworking
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
| `/` | `bienvenida` | `bienvenida.html` | Página de bienvenida |
| `/inicio/` | `inicio` | `inicio.html` | Página principal |
| Cualquier URL inexistente | `error_404` | `404.html` | Error HTTP 404 personalizado |

El botón **Entrar a la plataforma** utiliza el nombre de la ruta `inicio` para navegar desde la bienvenida hasta `/inicio/`.

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
render() carga una plantilla desde cowork/templates/
    ↓
Django devuelve una respuesta HTTP al navegador
```

Si ninguna ruta coincide, Django utiliza `handler404`, ejecuta la vista `error_404` y devuelve `404.html` con estado HTTP 404.

## Organización de las rutas

`drf/urls.py` es el enrutador principal del proyecto. Mantiene la ruta administrativa, el controlador global del error 404 y utiliza `include()` para delegar las rutas públicas a la aplicación.

`cowork/urls.py` contiene las rutas propias de `cowork`: la bienvenida y el inicio. De esta manera, el núcleo decide a qué aplicación enviar la petición y cada aplicación administra sus propios endpoints.

## Dependencias

Las dependencias utilizadas están registradas en `requirements.txt`:

- **Django:** framework principal que recibe las peticiones y relaciona rutas, vistas y plantillas.
- **asgiref:** dependencia de Django que proporciona compatibilidad con ASGI y ejecución asíncrona.
- **sqlparse:** dependencia utilizada por Django para analizar y dar formato a instrucciones SQL.

## Archivos excluidos de Git

- `.venv/`: contiene el ambiente virtual local.
- `db.sqlite3`: contiene la base de datos local.
- `.env`: puede contener variables privadas.
- `__pycache__/` y `*.pyc`: archivos temporales generados por Python.

## Detener el servidor

Presiona `Ctrl+C` en la terminal donde se está ejecutando Django.
