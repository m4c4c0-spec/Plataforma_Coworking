from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, transaction
from django.db.models.functions import Lower
from django.utils import timezone

from .fechas import fecha_utc


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
    updated_at = models.DateTimeField('fecha de actualización', auto_now=True)

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
        usuario, _ = cls.objects.get_or_create(cuenta=cuenta, defaults=cls._datos_cuenta(cuenta))
        return usuario

    @classmethod
    def _datos_cuenta(cls, cuenta):
        return {
            'nombre': cuenta.first_name or cuenta.get_username(),
            'apellido': cuenta.last_name, 'correo': cls._correo_disponible(cuenta),
            'rol': cls.Rol.ADMINISTRADOR if cuenta.is_superuser else cls.Rol.MIEMBRO,
            'activo': cuenta.is_active, 'fecha_registro': cuenta.date_joined,
        }

    @classmethod
    def _correo_disponible(cls, cuenta):
        correo = (cuenta.email or '').strip().lower()
        if correo and not cls.objects.filter(correo__iexact=correo).exists():
            return correo
        correo = f'usuario-{cuenta.pk}@example.invalid'
        sufijo = 0
        while cls.objects.filter(correo__iexact=correo).exists():
            sufijo += 1
            correo = f'usuario-{cuenta.pk}-{sufijo}@example.invalid'
        return correo

    def puedeRealizar(self, accion):
        if not self.activo or not self.cuenta.is_active:
            return False
        comunes = {
            'ver_espacios', 'ver_reservas', 'crear_reserva', 'editar_reserva',
            'cancelar_reserva', 'eliminar_reserva',
        }
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
        anterior = Usuario.objects.select_for_update().filter(pk=self.pk).first()
        if anterior is not None and self.pk == actor.pk and (
            not self.activo or self.rol != self.Rol.ADMINISTRADOR
        ):
            raise ValidationError('No puedes desactivar tu propia cuenta ni quitarte el rol de administrador.')
        self.full_clean()
        self.save()
        self._sincronizar_cuenta()
        EventoAuditoria.registrar_guardado(actor, self, anterior)

    def _sincronizar_cuenta(self):
        """La baja lógica también impide iniciar una nueva sesión de Django."""
        cuenta = self.cuenta
        cuenta.first_name, cuenta.last_name = self.nombre, self.apellido
        cuenta.email, cuenta.is_active = self.correo, self.activo
        cuenta.save(update_fields=['first_name', 'last_name', 'email', 'is_active'])

    def desactivar(self, actor):
        self._cambiar_activo(False, actor)

    def activar(self, actor):
        """Devuelve el acceso: guardar() también reactiva la cuenta de Django."""
        self._cambiar_activo(True, actor)

    @transaction.atomic
    def _cambiar_activo(self, activo, actor):
        actual = Usuario.objects.select_for_update().get(pk=self.pk)
        actual.activo = activo
        actual.guardar(actor)
        self.refresh_from_db()

    @transaction.atomic
    def eliminar(self, actor):
        """Borra el perfil y su cuenta si no tiene reservas ni acciones registradas."""
        actor = exigir_permiso(actor, 'gestionar_usuarios')
        actual = Usuario.objects.select_for_update().select_related('cuenta').get(pk=self.pk)
        if actual.pk == actor.pk:
            raise ValidationError('No puedes eliminar tu propia cuenta.')
        if actual.reservas.exists():
            raise ValidationError(
                'No se puede eliminar un usuario con reservas. Desactívalo para conservar su historial.'
            )
        if actual.eventos_auditoria.exists() or actual.cambios_reserva.exists():
            raise ValidationError(
                'No se puede eliminar un usuario con acciones registradas en la auditoría '
                'o en el historial de reservas. Desactívalo.'
            )
        EventoAuditoria.registrar_eliminacion(actor, actual)
        cuenta = actual.cuenta
        models.Model.delete(actual)
        cuenta.delete()

    def delete(self, *args, **kwargs):
        raise ValidationError('Utiliza eliminar(actor) para aplicar las reglas y registrar la auditoría.')


class Sede(models.Model):
    nombre = models.CharField(max_length=120)
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=120)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField('fecha de creación', default=timezone.now, editable=False)
    updated_at = models.DateTimeField('fecha de actualización', auto_now=True)

    class Meta:
        verbose_name = 'sede'
        verbose_name_plural = 'sedes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @transaction.atomic
    def guardar(self, actor):
        actor = exigir_permiso(actor, 'gestionar_espacios')
        anterior = type(self).objects.select_for_update().filter(pk=self.pk).first()
        self.full_clean()
        self.save()
        EventoAuditoria.registrar_guardado(actor, self, anterior)

    def desactivar(self, actor):
        """Los espacios de una sede inactiva dejan de aceptar reservas nuevas."""
        with transaction.atomic():
            actual = type(self).objects.select_for_update().get(pk=self.pk)
            actual.activa = False
            actual.guardar(actor)
            self.refresh_from_db()

    @transaction.atomic
    def eliminar(self, actor):
        """Solo se eliminan sedes sin espacios; la auditoría conserva sus valores."""
        actor = exigir_permiso(actor, 'gestionar_espacios')
        actual = type(self).objects.select_for_update().get(pk=self.pk)
        if actual.espacios.exists():
            raise ValidationError(
                'No se puede eliminar una sede con espacios. Desactívala o elimina primero sus espacios.'
            )
        EventoAuditoria.registrar_eliminacion(actor, actual)
        models.Model.delete(actual)

    def delete(self, *args, **kwargs):
        raise ValidationError('Utiliza eliminar(actor) para aplicar las reglas y registrar la auditoría.')


class TipoEspacio(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)
    created_at = models.DateTimeField('fecha de creación', default=timezone.now, editable=False)
    updated_at = models.DateTimeField('fecha de actualización', auto_now=True)

    class Meta:
        verbose_name = 'tipo de espacio'
        verbose_name_plural = 'tipos de espacio'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @transaction.atomic
    def guardar(self, actor):
        actor = exigir_permiso(actor, 'gestionar_espacios')
        anterior = type(self).objects.select_for_update().filter(pk=self.pk).first()
        self.full_clean()
        self.save()
        EventoAuditoria.registrar_guardado(actor, self, anterior)

    @transaction.atomic
    def eliminar(self, actor):
        """Solo se eliminan tipos sin espacios; la auditoría conserva sus valores."""
        actor = exigir_permiso(actor, 'gestionar_espacios')
        actual = type(self).objects.select_for_update().get(pk=self.pk)
        if actual.espacios.exists():
            raise ValidationError('No se puede eliminar un tipo con espacios asociados.')
        EventoAuditoria.registrar_eliminacion(actor, actual)
        actual.delete()


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
    created_at = models.DateTimeField('fecha de creación', default=timezone.now, editable=False)
    updated_at = models.DateTimeField('fecha de actualización', auto_now=True)

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
        try:
            inicio, fin = fecha_utc(inicio), fecha_utc(fin)
        except ValidationError:
            return False
        if fin <= inicio:
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
        if anterior is not None:
            self._validar_capacidad_reservas()
        self.save()
        EventoAuditoria.registrar_guardado(actor, self, anterior)

    def _validar_capacidad_reservas(self):
        if self.reservas.filter(
            estado__in=[Reserva.Estado.PENDIENTE, Reserva.Estado.CONFIRMADA],
            fin__gt=timezone.now(), cantidad_personas__gt=self.capacidad,
        ).exists():
            raise ValidationError({'capacidad': 'Existen reservas que superan esta capacidad.'})

    def cambiarEstado(self, nuevoEstado, actor):
        with transaction.atomic():
            actual = type(self).objects.select_for_update().get(pk=self.pk)
            actual.estado = nuevoEstado
            actual.guardar(actor)
            self.refresh_from_db()

    @transaction.atomic
    def eliminar(self, actor):
        """Solo se eliminan espacios sin reservas; la auditoría conserva sus valores."""
        actor = exigir_permiso(actor, 'gestionar_espacios')
        actual = type(self).objects.select_for_update().get(pk=self.pk)
        if actual.reservas.exists():
            raise ValidationError(
                'No se puede eliminar un espacio con reservas. Inactívalo para conservar su historial.'
            )
        EventoAuditoria.registrar_eliminacion(actor, actual)
        models.Model.delete(actual)

    def delete(self, *args, **kwargs):
        raise ValidationError('Utiliza eliminar(actor) para aplicar las reglas y registrar la auditoría.')


class Reserva(models.Model):
    """Reserva con transiciones explícitas, historial y baja por cancelación."""

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        CONFIRMADA = 'confirmada', 'Confirmada'
        CANCELADA = 'cancelada', 'Cancelada'
        FINALIZADA = 'finalizada', 'Finalizada'

    TRANSICIONES = {
        Estado.CONFIRMADA: ('confirmar_reserva', (Estado.PENDIENTE,)),
        Estado.CANCELADA: ('cancelar_reserva', (Estado.PENDIENTE, Estado.CONFIRMADA)),
        Estado.FINALIZADA: ('finalizar_reserva', (Estado.CONFIRMADA,)),
    }

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
    updated_at = models.DateTimeField('fecha de actualización', auto_now=True)
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
        try:
            return fecha_utc(self.fin) > fecha_utc(self.inicio)
        except ValidationError:
            return False

    def clean(self):
        super().clean()
        if not self.validarHorario():
            raise ValidationError({'fin': 'El fin debe ser posterior al inicio.'})
        self.inicio, self.fin = fecha_utc(self.inicio), fecha_utc(self.fin)
        if self.estado not in (self.Estado.PENDIENTE, self.Estado.CONFIRMADA):
            return
        self._validar_usuario_activo()
        if self.espacio_id:
            self._validar_espacio()

    def _validar_usuario_activo(self):
        if self.usuario_id and (not self.usuario.activo or not self.usuario.cuenta.is_active):
            raise ValidationError({'usuario': 'El usuario está inactivo.'})

    def _validar_espacio(self):
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
        self._validar_edicion(anterior)
        self.espacio = Espacio.objects.select_for_update().get(pk=self.espacio_id)
        self.usuario = Usuario.objects.select_for_update().get(pk=self.usuario_id)
        self.full_clean()
        self.save()
        if anterior is None:
            self._registrar_historial(actor, '', 'Creación de la reserva')
        EventoAuditoria.registrar_guardado(actor, self, anterior)

    def _validar_edicion(self, anterior):
        if anterior and anterior.estado != self.Estado.PENDIENTE:
            raise ValidationError('Solo se pueden editar reservas pendientes.')
        if self.estado != self.Estado.PENDIENTE or self.motivo_cancelacion:
            raise ValidationError('Utiliza las acciones de estado para cambiar la reserva.')
        if anterior and anterior.usuario_id != self.usuario_id:
            raise ValidationError('No se puede cambiar el titular de una reserva.')

    @transaction.atomic
    def _cambiar_estado(self, nuevo_estado, actor, motivo=''):
        actual = type(self).objects.select_for_update().get(pk=self.pk)
        accion, _ = self.TRANSICIONES[nuevo_estado]
        actor = actual._exigir_actor(actor, accion)
        motivo = self._normalizar_motivo(motivo)
        actual._validar_transicion(nuevo_estado, motivo)
        actual.espacio = Espacio.objects.select_for_update().get(pk=actual.espacio_id)
        anteriores, estado_anterior = valores_entidad(actual), actual.estado
        actual._guardar_estado(nuevo_estado, motivo)
        actual._registrar_historial(actor, estado_anterior, motivo)
        EventoAuditoria.registrar(actor, accion, actual, anteriores)
        self.estado, self.motivo_cancelacion = actual.estado, actual.motivo_cancelacion

    @staticmethod
    def _normalizar_motivo(motivo):
        if not isinstance(motivo, str):
            raise ValidationError({'motivo': 'El motivo debe ser un texto.'})
        return motivo.strip()

    def _validar_transicion(self, nuevo_estado, motivo):
        _, estados_permitidos = self.TRANSICIONES[nuevo_estado]
        if self.estado not in estados_permitidos:
            raise ValidationError('La transición de estado no está permitida.')
        if nuevo_estado == self.Estado.CANCELADA and not motivo:
            raise ValidationError({'motivo': 'Indica el motivo de cancelación.'})
        if nuevo_estado == self.Estado.FINALIZADA and self.fin > timezone.now():
            raise ValidationError('La reserva todavía no ha terminado.')

    def _guardar_estado(self, nuevo_estado, motivo):
        self.estado = nuevo_estado
        if nuevo_estado == self.Estado.CANCELADA:
            self.motivo_cancelacion = motivo
        self.full_clean()
        self.save(update_fields=['estado', 'motivo_cancelacion'])

    def _registrar_historial(self, actor, estado_anterior, motivo):
        HistorialEstadoReserva.objects.create(
            reserva=self, estado_anterior=estado_anterior,
            estado_nuevo=self.estado, responsable=actor, motivo=motivo,
        )

    def confirmar(self, actor):
        self._cambiar_estado(self.Estado.CONFIRMADA, actor)

    def cancelar(self, actor, motivo):
        self._cambiar_estado(self.Estado.CANCELADA, actor, motivo)

    def finalizar(self, actor):
        self._cambiar_estado(self.Estado.FINALIZADA, actor)

    @transaction.atomic
    def eliminar(self, actor):
        """Borra una reserva pendiente o cancelada junto con su historial."""
        actual = type(self).objects.select_for_update().get(pk=self.pk)
        actor = actual._exigir_actor(actor, 'eliminar_reserva')
        if actual.estado not in (self.Estado.PENDIENTE, self.Estado.CANCELADA):
            raise ValidationError(
                'Solo se pueden eliminar reservas pendientes o canceladas. Cancela primero una '
                'reserva confirmada; las finalizadas se conservan para los reportes.'
            )
        EventoAuditoria.registrar_eliminacion(actor, actual)
        actual.historial.all().delete()
        models.Model.delete(actual)

    def delete(self, *args, **kwargs):
        raise ValidationError('Utiliza eliminar(actor) para aplicar las reglas y registrar la auditoría.')


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
            actor=actor, accion=accion, tipo_entidad=entidad._meta.concrete_model._meta.model_name,
            id_entidad=entidad.pk, valores_anteriores=anteriores,
            valores_nuevos=valores_entidad(entidad),
        )

    @classmethod
    def registrar_eliminacion(cls, actor, entidad):
        """Conserva los valores del registro antes de borrarlo."""
        return cls.objects.create(
            actor=actor, accion='eliminar', tipo_entidad=entidad._meta.concrete_model._meta.model_name,
            id_entidad=entidad.pk, valores_anteriores=valores_entidad(entidad),
        )

    @classmethod
    def registrar_guardado(cls, actor, entidad, anterior):
        accion = 'actualizar' if anterior is not None else 'crear'
        anteriores = valores_entidad(anterior) if anterior is not None else {}
        return cls.registrar(actor, accion, entidad, anteriores)

    def consultarDetalle(self):
        return f'{self.accion}: {self.tipo_entidad} #{self.id_entidad} ({self.fecha:%Y-%m-%d %H:%M})'

    def __str__(self):
        return self.consultarDetalle()


class AdministradorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(rol=Usuario.Rol.ADMINISTRADOR)


class Administrador(Usuario):
    """Representa `admin` del diagrama sobre el perfil y la cuenta existentes."""

    objects = AdministradorManager()

    class Meta:
        proxy = True
        verbose_name = 'administrador'
        verbose_name_plural = 'administradores'

    @classmethod
    def desde_cuenta(cls, cuenta):
        perfil = Usuario.desde_cuenta(cuenta)
        administrador = cls.objects.filter(pk=perfil.pk).first()
        if administrador is None:
            raise PermissionDenied('La cuenta no tiene un perfil administrador.')
        return administrador

    def clean(self):
        super().clean()
        if self.rol != Usuario.Rol.ADMINISTRADOR:
            raise ValidationError({'rol': 'El perfil debe tener rol ADMINISTRADOR.'})

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.rol = Usuario.Rol.ADMINISTRADOR
        elif self.rol != Usuario.Rol.ADMINISTRADOR:
            raise ValidationError({'rol': 'Cambia el rol mediante el perfil Usuario.'})
        return super().save(*args, **kwargs)

    @transaction.atomic
    def guardar(self, actor):
        actor = exigir_permiso(actor, 'gestionar_usuarios')
        if self._state.adding:
            self.rol = Usuario.Rol.ADMINISTRADOR
        elif not Usuario.objects.select_for_update().filter(
            pk=self.pk, rol=Usuario.Rol.ADMINISTRADOR,
        ).exists():
            raise ValidationError('El perfil ya no es administrador. Recarga sus datos.')
        return super().guardar(actor)

    @transaction.atomic
    def gestion_horario(self, desde, hasta, *, reserva):
        """Reprograma una reserva pendiente mediante sus reglas de negocio."""
        from .reportes_dto import RangoFecha

        actor = exigir_permiso(self, 'ver_reportes')
        if not isinstance(reserva, Reserva) or reserva.pk is None:
            raise ValidationError('Indica una reserva guardada para cambiar su horario.')
        periodo = RangoFecha(desde, hasta)
        actual = Reserva.objects.select_for_update().get(pk=reserva.pk)
        actual.inicio, actual.fin = periodo.desde, periodo.hasta
        actual.guardar(actor)
        return actual

    @transaction.atomic
    def gestion_espacios(self, disponible, *, espacio):
        actor = exigir_permiso(self, 'gestionar_espacios')
        if type(disponible) is not bool or not isinstance(espacio, Espacio) or espacio.pk is None:
            raise ValidationError('Indica un espacio guardado y una disponibilidad booleana.')
        actual = Espacio.objects.select_for_update().get(pk=espacio.pk)
        estado = Espacio.Estado.DISPONIBLE if disponible else Espacio.Estado.INACTIVO
        actual.cambiarEstado(estado, actor)
        return actual.pk

    @property
    def reservas_administradas(self):
        """Relaciona administradores y reservas mediante el historial y la auditoría."""
        actor = exigir_permiso(self, 'ver_reportes')
        eventos = EventoAuditoria.objects.filter(
            actor=actor, tipo_entidad=Reserva._meta.model_name,
        ).values_list('id_entidad', flat=True)
        return Reserva.objects.filter(
            models.Q(historial__responsable=actor) | models.Q(pk__in=eventos),
        ).distinct()
