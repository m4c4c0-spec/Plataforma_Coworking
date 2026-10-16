"""Serializers de la API de gestión de la base principal.

Las fechas se leen y se muestran en TIME_ZONE (hora de Chile), igual que en las pantallas.
"""

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .forms import UsuarioForm
from .models import Espacio, EventoAuditoria, HistorialEstadoReserva, Reserva, Sede, TipoEspacio, Usuario


class GuardarModelSerializer(serializers.ModelSerializer):
    """Conserva las reglas, transacciones y auditoría de guardar(actor)."""

    def create(self, validated_data):
        instancia = self.Meta.model(**validated_data)
        instancia.guardar(self.context['request'].actor)
        return instancia

    def update(self, instance, validated_data):
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        instance.guardar(self.context['request'].actor)
        return instance


class UsuarioGestionSerializer(serializers.ModelSerializer):
    nombre_usuario = serializers.CharField(max_length=150, write_only=True, required=False)
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, trim_whitespace=False,
        style={'input_type': 'password'},
    )

    class Meta:
        model = Usuario
        fields = [
            'id', 'nombre', 'apellido', 'correo', 'rol', 'activo',
            'fecha_registro', 'nombre_usuario', 'password',
        ]
        read_only_fields = ['id', 'activo', 'fecha_registro']

    def validate(self, attrs):
        # El formulario ya valida la cuenta, la contraseña y el perfil juntos.
        datos = dict(attrs)
        if self.instance is not None:
            nombre_usuario = self.instance.cuenta.get_username()
            if datos.get('nombre_usuario', nombre_usuario) != nombre_usuario:
                raise serializers.ValidationError({'nombre_usuario': 'No se puede cambiar el nombre de acceso.'})
            datos['nombre_usuario'] = nombre_usuario
            for campo in UsuarioForm.Meta.fields:
                datos.setdefault(campo, getattr(self.instance, campo))
        self.formulario = UsuarioForm(
            data=datos, instance=self.instance, actor=self.context['request'].actor,
        )
        if not self.formulario.is_valid():
            errores = {
                'non_field_errors' if campo == '__all__' else campo: list(mensajes)
                for campo, mensajes in self.formulario.errors.items()
            }
            raise serializers.ValidationError(errores)
        return attrs

    def create(self, validated_data):
        return self.formulario.save()

    def update(self, instance, validated_data):
        return self.formulario.save()


class SedeGestionSerializer(GuardarModelSerializer):
    class Meta:
        model = Sede
        fields = ['id', 'nombre', 'direccion', 'ciudad', 'activa']
        read_only_fields = ['id']


class TipoEspacioGestionSerializer(GuardarModelSerializer):
    class Meta:
        model = TipoEspacio
        fields = ['id', 'nombre', 'descripcion']
        read_only_fields = ['id']


class EspacioGestionSerializer(GuardarModelSerializer):
    capacidad = serializers.IntegerField(min_value=1)

    class Meta:
        model = Espacio
        fields = [
            'id', 'sede', 'tipo', 'nombre', 'capacidad', 'estado',
            'descripcion_publica', 'observaciones_privadas',
        ]
        read_only_fields = ['id']

    def get_fields(self):
        campos = super().get_fields()
        if self.context['request'].actor.rol != Usuario.Rol.ADMINISTRADOR:
            campos.pop('observaciones_privadas')
        return campos


class ReservaGestionSerializer(GuardarModelSerializer):
    # En la API navegable se escribe el ID: una lista desplegable mostraría a todos los usuarios.
    usuario = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(), required=False, style={'base_template': 'input.html'},
    )
    cantidad_personas = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        model = Reserva
        fields = [
            'id', 'usuario', 'espacio', 'inicio', 'fin', 'cantidad_personas',
            'estado', 'fecha_creacion', 'observaciones', 'motivo_cancelacion',
        ]
        read_only_fields = ['id', 'estado', 'fecha_creacion', 'motivo_cancelacion']

    def validate(self, attrs):
        actor = self.context['request'].actor
        if actor.rol != Usuario.Rol.ADMINISTRADOR:
            if 'usuario' in attrs and attrs['usuario'].pk != actor.pk:
                raise PermissionDenied('Solo puedes gestionar tus propias reservas.')
            if self.instance is None:
                attrs['usuario'] = actor
        elif self.instance is None and 'usuario' not in attrs:
            raise serializers.ValidationError({'usuario': 'Indica el titular de la reserva.'})
        return attrs


class CancelacionSerializer(serializers.Serializer):
    motivo = serializers.CharField()


# El historial y la auditoría son registros: la API solo los consulta.


class HistorialEstadoReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialEstadoReserva
        fields = ['id', 'reserva', 'estado_anterior', 'estado_nuevo', 'responsable', 'fecha_cambio', 'motivo']
        read_only_fields = fields


class EventoAuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoAuditoria
        fields = [
            'id', 'actor', 'fecha', 'accion', 'tipo_entidad', 'id_entidad',
            'valores_anteriores', 'valores_nuevos',
        ]
        read_only_fields = fields
