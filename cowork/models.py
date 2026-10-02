from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.db.models.functions import Lower
from django.utils import timezone


def exigir_permiso(actor, accion):
    if not isinstance(actor, Usuario):
        raise PermissionDenied('No tienes permiso para realizar esta acción.')
    vigente = Usuario.objects.select_related('cuenta').filter(pk=actor.pk).first()
    if vigente is None or not vigente.puedeRealizar(accion):
        raise PermissionDenied('No tienes permiso para realizar esta acción.')
    return vigente


def valores_entidad(entidad):
    """Captura campos de negocio sin incluir credenciales de autenticación."""
    return {
        campo.attname: getattr(entidad, campo.attname)
        for campo in entidad._meta.concrete_fields
    }


class Usuario(models.Model):
    """Perfil de negocio asociado a la cuenta de autenticación de Django."""

    class Rol(models.TextChoices):
        MIEMBRO = 'MIEMBRO', 'Miembro'
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'

    cuenta = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='perfil_cowork',
    )
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150, blank=True)
    correo = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.MIEMBRO)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ['apellido', 'nombre']
        constraints = [
            models.UniqueConstraint(Lower('correo'), name='usuario_correo_sin_mayusculas'),
            models.CheckConstraint(
                condition=models.Q(rol__in=['MIEMBRO', 'ADMINISTRADOR']),
                name='usuario_rol_valido',
            ),
        ]

    def __str__(self):
        return f'{self.nombre} {self.apellido}'.strip() or self.correo

    @classmethod
    def desde_cuenta(cls, cuenta):
        """Permite ingresar con cuentas previas, incluido createsuperuser."""
        usuario = cls.objects.filter(cuenta=cuenta).first()
        if usuario is not None:
            return usuario
        correo = (cuenta.email or '').strip().lower()
        if not correo or cls.objects.filter(correo__iexact=correo).exists():
            correo = f'usuario-{cuenta.pk}@example.invalid'
            sufijo = 0
            while cls.objects.filter(correo__iexact=correo).exists():
                sufijo += 1
                correo = f'usuario-{cuenta.pk}-{sufijo}@example.invalid'
        usuario, _ = cls.objects.get_or_create(cuenta=cuenta, defaults={
            'nombre': cuenta.first_name or cuenta.get_username(),
            'apellido': cuenta.last_name, 'correo': correo,
            'rol': cls.Rol.ADMINISTRADOR if cuenta.is_superuser else cls.Rol.MIEMBRO,
            'activo': cuenta.is_active, 'fecha_registro': cuenta.date_joined,
        })
        return usuario

    def puedeRealizar(self, accion):
        if not self.activo or not self.cuenta.is_active:
            return False
        comunes = {'ver_espacios', 'ver_reservas', 'crear_reserva', 'editar_reserva', 'cancelar_reserva'}
        administrativas = {
            'gestionar_usuarios', 'gestionar_espacios', 'confirmar_reserva',
            'finalizar_reserva', 'ver_reportes', 'ver_auditoria',
        }
        return accion in comunes or (
            self.rol == self.Rol.ADMINISTRADOR and accion in administrativas
        )

    def clean(self):
        super().clean()
        self.correo = self.correo.strip().lower()

    @transaction.atomic
    def guardar(self, actor):
        actor = exigir_permiso(actor, 'gestionar_usuarios')
        anterior = type(self).objects.select_for_update().filter(pk=self.pk).first()
        valores_anteriores = valores_entidad(anterior) if anterior else {}
        self.full_clean()
        self.save()
        # La baja lógica también impide iniciar una nueva sesión de Django.
        cuenta = self.cuenta
        cuenta.first_name, cuenta.last_name = self.nombre, self.apellido
        cuenta.email, cuenta.is_active = self.correo, self.activo
        cuenta.save(update_fields=['first_name', 'last_name', 'email', 'is_active'])
        EventoAuditoria.registrar(
            actor, 'actualizar' if anterior else 'crear', self, valores_anteriores,
        )

    def desactivar(self, actor):
        self.activo = False
        self.guardar(actor)

    def delete(self, *args, **kwargs):
        raise ValidationError('Los usuarios se desactivan; no se eliminan.')


class Sede(models.Model):
    nombre = models.CharField(max_length=120)
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=120)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'sede'
        verbose_name_plural = 'sedes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class TipoEspacio(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'tipo de espacio'
        verbose_name_plural = 'tipos de espacio'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Espacio(models.Model):
    """Unidad reservable de una sede. La disponibilidad depende del horario."""

    class Estado(models.TextChoices):
        DISPONIBLE = 'disponible', 'Disponible'
        MANTENIMIENTO = 'mantenimiento', 'En mantenimiento'
        INACTIVO = 'inactivo', 'Inactivo'

    sede = models.ForeignKey(
        Sede,
        on_delete=models.PROTECT,
        related_name='espacios',
    )
    tipo = models.ForeignKey(
        TipoEspacio,
        on_delete=models.PROTECT,
        related_name='espacios',
    )
    nombre = models.CharField(max_length=120)
    descripcion_publica = models.TextField(blank=True)
    observaciones_privadas = models.TextField(blank=True)
    capacidad = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.DISPONIBLE)

    class Meta:
        verbose_name = 'espacio'
        verbose_name_plural = 'espacios'
        ordering = ['sede', 'nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['sede', 'nombre'],
                name='espacio_nombre_unico_por_sede',
            ),
            models.CheckConstraint(
                condition=models.Q(capacidad__gte=1),
                name='espacio_capacidad_minima',
            ),
            models.CheckConstraint(
                condition=models.Q(estado__in=['disponible', 'mantenimiento', 'inactivo']),
                name='espacio_estado_valido',
            ),
        ]

    def __str__(self):
        return f'{self.nombre} ({self.sede})'

    def estaDisponible(self, inicio, fin, excluir_reserva=None):
        if not inicio or not fin or fin <= inicio:
            return False
        if self.estado != self.Estado.DISPONIBLE or not self.sede.activa:
            return False
        reservas = self.reservas.filter(
            estado__in=[Reserva.Estado.PENDIENTE, Reserva.Estado.CONFIRMADA],
            inicio__lt=fin, fin__gt=inicio,
        )
        if excluir_reserva is not None:
            reservas = reservas.exclude(pk=excluir_reserva)
        return not reservas.exists()

    @transaction.atomic
    def guardar(self, actor):
        actor = exigir_permiso(actor, 'gestionar_espacios')
        anterior = type(self).objects.select_for_update().filter(pk=self.pk).first()
        self.full_clean()
        if anterior and self.reservas.filter(
            estado__in=[Reserva.Estado.PENDIENTE, Reserva.Estado.CONFIRMADA],
            fin__gt=timezone.now(), cantidad_personas__gt=self.capacidad,
        ).exists():
            raise ValidationError({'capacidad': 'Existen reservas que superan esta capacidad.'})
        self.save()
        EventoAuditoria.registrar(
            actor, 'actualizar' if anterior else 'crear', self,
            valores_entidad(anterior) if anterior else {},
        )

    def cambiarEstado(self, nuevoEstado, actor):
        self.estado = nuevoEstado
        self.guardar(actor)

    def delete(self, *args, **kwargs):
        raise ValidationError('Los espacios se inactivan; no se eliminan.')


class Reserva(models.Model):
    """Reserva con transiciones explícitas, historial y baja por cancelación."""

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        CONFIRMADA = 'confirmada', 'Confirmada'
        CANCELADA = 'cancelada', 'Cancelada'
        FINALIZADA = 'finalizada', 'Finalizada'

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='reservas',
    )
    espacio = models.ForeignKey(
        Espacio,
        on_delete=models.PROTECT,
        related_name='reservas',
    )
    inicio = models.DateTimeField()
    fin = models.DateTimeField()
    cantidad_personas = models.PositiveIntegerField(default=1)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)
    motivo_cancelacion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'reserva'
        verbose_name_plural = 'reservas'
        ordering = ['-inicio']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fin__gt=models.F('inicio')),
                name='reserva_fin_posterior_al_inicio',
            ),
            models.CheckConstraint(
                condition=models.Q(cantidad_personas__gte=1),
                name='reserva_cantidad_personas_minima',
            ),
            models.CheckConstraint(
                condition=models.Q(estado__in=['pendiente', 'confirmada', 'cancelada', 'finalizada']),
                name='reserva_estado_valido',
            ),
        ]
        indexes = [models.Index(fields=['espacio', 'estado', 'inicio', 'fin'], name='reserva_disponibilidad_idx')]

    def __str__(self):
        return f'{self.espacio.nombre} · {self.inicio:%Y-%m-%d %H:%M}'

    def validarHorario(self):
        return bool(self.inicio and self.fin and self.fin > self.inicio)

    def clean(self):
        super().clean()
        if not self.validarHorario():
            raise ValidationError({'fin': 'El fin debe ser posterior al inicio.'})
        if self.estado in [self.Estado.PENDIENTE, self.Estado.CONFIRMADA]:
            if self.usuario_id and not self.usuario.activo:
                raise ValidationError({'usuario': 'El usuario está inactivo.'})
            if self.espacio_id:
                if self.cantidad_personas is not None and self.cantidad_personas > self.espacio.capacidad:
                    raise ValidationError({'cantidad_personas': 'La cantidad supera la capacidad del espacio.'})
                if not self.espacio.estaDisponible(self.inicio, self.fin, self.pk):
                    raise ValidationError({'espacio': 'El espacio no está disponible en ese horario.'})

    def _exigir_actor(self, actor, accion):
        actor = exigir_permiso(actor, accion)
        if actor.rol != Usuario.Rol.ADMINISTRADOR and actor.pk != self.usuario_id:
            raise PermissionDenied('Solo puedes gestionar tus propias reservas.')
        return actor

    @transaction.atomic
    def guardar(self, actor):
        """Crea o edita una reserva pendiente y vuelve a validar bajo bloqueo."""
        actor = self._exigir_actor(actor, 'editar_reserva' if self.pk else 'crear_reserva')
        anterior = type(self).objects.select_for_update().filter(pk=self.pk).first()
        if anterior and anterior.estado != self.Estado.PENDIENTE:
            raise ValidationError('Solo se pueden editar reservas pendientes.')
        if self.estado != self.Estado.PENDIENTE or self.motivo_cancelacion:
            raise ValidationError('Utiliza las acciones de estado para cambiar la reserva.')
        if anterior and anterior.usuario_id != self.usuario_id:
            raise ValidationError('No se puede cambiar el titular de una reserva.')
        self.espacio = Espacio.objects.select_for_update().get(pk=self.espacio_id)
        self.usuario = Usuario.objects.select_for_update().get(pk=self.usuario_id)
        self.full_clean()
        self.save()
        if anterior is None:
            HistorialEstadoReserva.objects.create(
                reserva=self, estado_anterior='', estado_nuevo=self.estado, responsable=actor,
                motivo='Creación de la reserva',
            )
        EventoAuditoria.registrar(
            actor, 'actualizar' if anterior else 'crear', self,
            valores_entidad(anterior) if anterior else {},
        )

    @transaction.atomic
    def _cambiar_estado(self, nuevo_estado, actor, motivo=''):
        acciones = {
            self.Estado.CONFIRMADA: 'confirmar_reserva',
            self.Estado.CANCELADA: 'cancelar_reserva',
            self.Estado.FINALIZADA: 'finalizar_reserva',
        }
        actual = type(self).objects.select_for_update().get(pk=self.pk)
        actor = actual._exigir_actor(actor, acciones[nuevo_estado])
        permitidos = {
            self.Estado.CONFIRMADA: [self.Estado.PENDIENTE],
            self.Estado.CANCELADA: [self.Estado.PENDIENTE, self.Estado.CONFIRMADA],
            self.Estado.FINALIZADA: [self.Estado.CONFIRMADA],
        }
        if actual.estado not in permitidos[nuevo_estado]:
            raise ValidationError('La transición de estado no está permitida.')
        if nuevo_estado == self.Estado.CANCELADA and not motivo.strip():
            raise ValidationError({'motivo': 'Indica el motivo de cancelación.'})
        if nuevo_estado == self.Estado.FINALIZADA and actual.fin > timezone.now():
            raise ValidationError('La reserva todavía no ha terminado.')
        actual.espacio = Espacio.objects.select_for_update().get(pk=actual.espacio_id)
        anteriores = valores_entidad(actual)
        estado_anterior = actual.estado
        actual.estado = nuevo_estado
        if nuevo_estado == self.Estado.CANCELADA:
            actual.motivo_cancelacion = motivo.strip()
        actual.full_clean()
        actual.save(update_fields=['estado', 'motivo_cancelacion'])
        HistorialEstadoReserva.objects.create(
            reserva=actual, estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado, responsable=actor, motivo=motivo.strip(),
        )
        EventoAuditoria.registrar(actor, acciones[nuevo_estado], actual, anteriores)
        self.estado, self.motivo_cancelacion = actual.estado, actual.motivo_cancelacion

    def confirmar(self, actor):
        self._cambiar_estado(self.Estado.CONFIRMADA, actor)

    def cancelar(self, actor, motivo):
        self._cambiar_estado(self.Estado.CANCELADA, actor, motivo)

    def finalizar(self, actor):
        self._cambiar_estado(self.Estado.FINALIZADA, actor)

    def delete(self, *args, **kwargs):
        raise ValidationError('Las reservas se cancelan; no se eliminan.')


class HistorialEstadoReserva(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.PROTECT, related_name='historial')
    responsable = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, null=True, blank=True,
        related_name='cambios_reserva',
    )
    estado_anterior = models.CharField(max_length=20, choices=Reserva.Estado.choices, blank=True)
    estado_nuevo = models.CharField(max_length=20, choices=Reserva.Estado.choices)
    fecha_cambio = models.DateTimeField(default=timezone.now, editable=False)
    motivo = models.TextField(blank=True)

    class Meta:
        ordering = ['fecha_cambio', 'pk']
        verbose_name_plural = 'historiales de estado de reservas'

    def consultarDetalle(self):
        anterior = self.get_estado_anterior_display() or 'Sin estado'
        return f'{anterior} / {self.get_estado_nuevo_display()}: {self.motivo}'

    def __str__(self):
        return self.consultarDetalle()


class EventoAuditoria(models.Model):
    actor = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, null=True, blank=True,
        related_name='eventos_auditoria',
    )
    fecha = models.DateTimeField(default=timezone.now, editable=False)
    accion = models.CharField(max_length=80)
    tipo_entidad = models.CharField(max_length=80)
    id_entidad = models.PositiveBigIntegerField()
    valores_anteriores = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True)
    valores_nuevos = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True)

    class Meta:
        ordering = ['-fecha', '-pk']
        verbose_name_plural = 'eventos de auditoría'

    @classmethod
    def registrar(cls, actor, accion, entidad, anteriores):
        return cls.objects.create(
            actor=actor, accion=accion, tipo_entidad=entidad._meta.model_name,
            id_entidad=entidad.pk, valores_anteriores=anteriores,
            valores_nuevos=valores_entidad(entidad),
        )

    def consultarDetalle(self):
        return f'{self.accion}: {self.tipo_entidad} #{self.id_entidad} ({self.fecha:%Y-%m-%d %H:%M})'

    def __str__(self):
        return self.consultarDetalle()
