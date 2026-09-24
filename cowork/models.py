from django.conf import settings
from django.db import models


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
    """Unidad concreta que se reserva completa: sala, oficina o puesto.

    Pertenece a una sede y a un tipo. El nombre se repite entre sedes,
    pero no dentro de la misma. ``activo`` indica si está habilitado;
    la disponibilidad de un horario no se guarda aquí: se calcula con
    las reservas. La sede y el tipo no se pueden borrar mientras tengan
    espacios.
    """

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
    descripcion = models.TextField(blank=True)
    capacidad = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

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
        ]

    def __str__(self):
        return f'{self.nombre} ({self.sede})'


class Reserva(models.Model):
    """Intervalo en el que un usuario usa un espacio.

    Nace confirmada. El fin tiene que ser posterior al inicio y la
    cantidad de personas es al menos 1. Estas reglas viven en la base.
    Que la cantidad no supere la capacidad, que el espacio y la sede
    estén activos y que no se solape con otra reserva confirmada son
    reglas entre entidades: se resuelven aparte, no en esta fila.
    Cancelar o finalizar conserva el registro. El usuario y el espacio
    no se pueden borrar mientras tengan reservas.
    """

    class Estado(models.TextChoices):
        CONFIRMADA = 'confirmada', 'Confirmada'
        CANCELADA = 'cancelada', 'Cancelada'
        FINALIZADA = 'finalizada', 'Finalizada'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
    cantidad_personas = models.PositiveIntegerField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.CONFIRMADA,
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)

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
        ]

    def __str__(self):
        return f'{self.espacio.nombre} · {self.inicio:%Y-%m-%d %H:%M}'
