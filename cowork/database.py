"""Conexión de SQLAlchemy a la base principal de MySQL/MariaDB."""

from contextlib import contextmanager
from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session


@lru_cache(maxsize=1)
def _crear_motor_mysql(url, connect_timeout, init_command):
    try:
        return create_engine(
            url,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={
                'connect_timeout': connect_timeout,
                'init_command': init_command,
            },
        )
    except ImportError as error:
        raise ImproperlyConfigured(
            'Instala requirements.txt para utilizar mysqlclient.'
        ) from error


def obtener_motor_mysql():
    # Reutiliza la conexión principal de Django; no duplica credenciales.
    configuracion = settings.DATABASES.get('default')
    if not configuracion:
        raise ImproperlyConfigured('Configura la base principal MySQL/MariaDB en .env.')
    if configuracion['ENGINE'] != 'django.db.backends.mysql':
        raise ImproperlyConfigured('La base principal debe utilizar MySQL/MariaDB.')
    try:
        puerto = int(configuracion.get('PORT') or 3306)
    except (TypeError, ValueError) as error:
        raise ImproperlyConfigured('MYSQL_PORT debe ser un número entero.') from error
    if not 1 <= puerto <= 65535:
        raise ImproperlyConfigured('MYSQL_PORT debe estar entre 1 y 65535.')
    opciones = configuracion.get('OPTIONS', {})
    # URL.create conserva contraseñas con @, :, / o # sin concatenarlas en una URL.
    url = URL.create(
        'mysql+mysqldb',
        username=configuracion['USER'],
        password=configuracion.get('PASSWORD', ''),
        host=configuracion.get('HOST') or '127.0.0.1',
        port=puerto,
        database=configuracion['NAME'],
        query={'charset': opciones.get('charset', 'utf8mb4')},
    )
    return _crear_motor_mysql(
        url,
        opciones.get('connect_timeout', 5),
        opciones.get('init_command', "SET sql_mode='STRICT_TRANS_TABLES'"),
    )


@contextmanager
def sesion_mysql():
    """Una sesión por consulta; cierra y revierte la transacción al salir."""
    with Session(obtener_motor_mysql(), autoflush=False) as sesion:
        yield sesion
