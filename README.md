# Plataforma_Coworking
Esta sera una futura plataforma de trabajo compartido para digitalizar los datos y tener una consistencia de cada uno 

# Istalacion para windows 11/10
Para comprobar la instalación de Python:

  ```powershell
  py --version
  ```

  ## Instalación en Windows

  Abra PowerShell o CMD en la carpeta que contiene `manage.py`.

  ### 1. Crear el entorno virtual

  ```powershell
  py -m venv .venv
  ```

  ### 2. Instalar las dependencias

  ```powershell
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  ```

  ### 3. Preparar la base de datos

  ```powershell
  .\.venv\Scripts\python.exe manage.py migrate
  ```

  ### 4. Iniciar la aplicación

  ```powershell
  .\.venv\Scripts\python.exe manage.py runserver --insecure
  ```

  La opción `--insecure` permite cargar los archivos estáticos manteniendo `DEBUG=False`, lo que permite
  mostrar la página 404 personalizada.

  ## Comprobar la aplicación

  Abra las siguientes direcciones:

  - Bienvenida: <http://127.0.0.1:8000/>
  - Bienvenida alternativa: <http://127.0.0.1:8000/bienvenida/>
  - Prueba del error 404: <http://127.0.0.1:8000/prueba-404/>

  Para detener el servidor, presione `Ctrl+C` en la terminal.
