# Plataforma Coworking

  Plataforma de trabajo compartido orientada a organizar espacios, reservas y comunidad de una manera clara y sencilla.

  ## Requisitos

  - Python instalado.
  - Git instalado.
  - Sistema operativo Windows 10 u 11.

  Para comprobar la instalación de Python:

  ```powershell
  py --version

  ## Instalación en Windows

  Abra PowerShell en la carpeta que contiene manage.py.

  ### 1. Crear el ambiente virtual

  py -m venv .venv

  ### 2. Activar el ambiente virtual

  .\.venv\Scripts\Activate.ps1

  Cuando esté activado, debería aparecer (.venv) al comienzo de la línea de comandos.

  ### 3. Instalar las dependencias

  python -m pip install -r requirements.txt

  ### 4. Preparar la base de datos

  python manage.py migrate

  La base de datos db.sqlite3 se crea localmente y está excluida del repositorio mediante .gitignore.

  ### 5. Iniciar la aplicación

  python manage.py runserver

  El servidor estará disponible normalmente en:

  http://127.0.0.1:8000/ (http://127.0.0.1:8000/)

  ## Flujo principal

  /                  → vista bienvenida → bienvenida.html
  /inicio/           → vista inicio → inicio.html
  Ruta inexistente   → handler404 → 404.html

  ## Dependencias

  Las dependencias utilizadas están registradas en requirements.txt:

  - Django: framework principal utilizado para desarrollar la aplicación.
  - asgiref: dependencia utilizada por Django para compatibilidad ASGI.
  - sqlparse: dependencia utilizada por Django para procesar instrucciones SQL.

  ## Detener el servidor

  Presione Ctrl+C en la terminal donde se está ejecutando Django.