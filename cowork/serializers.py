"""Representaciones JSON explícitas de los objetos consultados con SQLAlchemy."""

from datetime import timezone

from rest_framework import serializers


class SedeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(read_only=True)
    direccion = serializers.CharField(read_only=True)
    ciudad = serializers.CharField(read_only=True)
    activa = serializers.BooleanField(read_only=True)


class TipoEspacioSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(read_only=True)
    descripcion = serializers.CharField(read_only=True)


class UsuarioSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(read_only=True)
    apellido = serializers.CharField(read_only=True)
    correo = serializers.EmailField(read_only=True)
    rol = serializers.CharField(read_only=True)
    activo = serializers.BooleanField(read_only=True)
    fecha_registro = serializers.DateTimeField(read_only=True, default_timezone=timezone.utc)


class EspacioSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(read_only=True)
    descripcion_publica = serializers.CharField(read_only=True)
    capacidad = serializers.IntegerField(read_only=True)
    estado = serializers.CharField(read_only=True)
    sede = SedeSerializer(read_only=True)
    tipo = TipoEspacioSerializer(read_only=True)


class ReservaSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    usuario = UsuarioSerializer(read_only=True)
    espacio = EspacioSerializer(read_only=True)
    inicio = serializers.DateTimeField(read_only=True, default_timezone=timezone.utc)
    fin = serializers.DateTimeField(read_only=True, default_timezone=timezone.utc)
    cantidad_personas = serializers.IntegerField(read_only=True)
    estado = serializers.CharField(read_only=True)
    fecha_creacion = serializers.DateTimeField(read_only=True, default_timezone=timezone.utc)
    observaciones = serializers.CharField(read_only=True)
    motivo_cancelacion = serializers.CharField(read_only=True)


class PaginacionSerializer(serializers.Serializer):
    limit = serializers.IntegerField(default=100, min_value=1, max_value=200)
    offset = serializers.IntegerField(default=0, min_value=0)
