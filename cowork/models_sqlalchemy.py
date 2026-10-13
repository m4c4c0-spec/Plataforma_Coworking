"""Mapeo de las tablas de negocio existentes; las migraciones las gestiona Django."""

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class FechaUTC(TypeDecorator):
    """Django guarda sus DateTimeField como fechas UTC sin zona en MySQL."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=timezone.utc) if value is not None else None


class Base(DeclarativeBase):
    pass


class SedeSQL(Base):
    __tablename__ = 'cowork_sede'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    direccion: Mapped[str] = mapped_column(String(255))
    ciudad: Mapped[str] = mapped_column(String(120))
    activa: Mapped[bool] = mapped_column(Boolean)


class TipoEspacioSQL(Base):
    __tablename__ = 'cowork_tipoespacio'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    descripcion: Mapped[str] = mapped_column(Text)


class UsuarioSQL(Base):
    __tablename__ = 'cowork_usuario'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    cuenta_id: Mapped[int] = mapped_column(BigInteger)
    nombre: Mapped[str] = mapped_column(String(150))
    apellido: Mapped[str] = mapped_column(String(150))
    correo: Mapped[str] = mapped_column(String(254))
    rol: Mapped[str] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean)
    fecha_registro: Mapped[datetime] = mapped_column(FechaUTC)


class EspacioSQL(Base):
    __tablename__ = 'cowork_espacio'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey('cowork_sede.id'))
    tipo_id: Mapped[int] = mapped_column(ForeignKey('cowork_tipoespacio.id'))
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion_publica: Mapped[str] = mapped_column(Text)
    observaciones_privadas: Mapped[str] = mapped_column(Text)
    capacidad: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20))
    sede: Mapped[SedeSQL] = relationship(lazy='raise')
    tipo: Mapped[TipoEspacioSQL] = relationship(lazy='raise')


class ReservaSQL(Base):
    __tablename__ = 'cowork_reserva'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey('cowork_usuario.id'))
    espacio_id: Mapped[int] = mapped_column(ForeignKey('cowork_espacio.id'))
    inicio: Mapped[datetime] = mapped_column(FechaUTC)
    fin: Mapped[datetime] = mapped_column(FechaUTC)
    cantidad_personas: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20))
    fecha_creacion: Mapped[datetime] = mapped_column(FechaUTC)
    observaciones: Mapped[str] = mapped_column(Text)
    motivo_cancelacion: Mapped[str] = mapped_column(Text)
    usuario: Mapped[UsuarioSQL] = relationship(lazy='raise')
    espacio: Mapped[EspacioSQL] = relationship(lazy='raise')
