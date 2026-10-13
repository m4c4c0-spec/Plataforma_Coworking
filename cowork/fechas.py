from datetime import UTC, date, datetime, time

from django.core.exceptions import ValidationError
from django.utils import timezone


def fecha_con_hora(valor):
    if isinstance(valor, datetime):
        return timezone.make_aware(valor) if timezone.is_naive(valor) else valor
    if isinstance(valor, date):
        return timezone.make_aware(datetime.combine(valor, time.min))
    raise ValidationError('El período debe contener fechas válidas.')


def fecha_utc(valor):
    return fecha_con_hora(valor).astimezone(UTC)


def horas_entre(desde, hasta):
    return (fecha_utc(hasta) - fecha_utc(desde)).total_seconds() / 3600


def hora_local_sin_zona(valor):
    return timezone.localtime(fecha_con_hora(valor)).replace(tzinfo=None)
