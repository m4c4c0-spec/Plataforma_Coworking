"""Perfiles de usuario, estados de reserva y registro de sus interacciones."""

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import PROTECT
from django.db.models.functions import Lower
from django.utils.timezone import now
from django.conf import settings
from django.db import migrations, models


def completar_datos(apps, schema_editor):
    alias = schema_editor.connection.alias
    app_cuenta, modelo_cuenta = settings.AUTH_USER_MODEL.split('.')
    Cuenta = apps.get_model(app_cuenta, modelo_cuenta)
    Usuario = apps.get_model('cowork', 'Usuario')
    Espacio = apps.get_model('cowork', 'Espacio')
    Reserva = apps.get_model('cowork', 'Reserva')
    Historial = apps.get_model('cowork', 'HistorialEstadoReserva')
    usados = set()
    reservados = {
        (cuenta.email or '').strip().lower()
        for cuenta in Cuenta.objects.using(alias).all()
    }
    for cuenta in Cuenta.objects.using(alias).order_by('pk'):
        correo = (cuenta.email or '').strip().lower()
        if not correo or correo in usados:
            correo = f'usuario-{cuenta.pk}@example.invalid'
            sufijo = 0
            while correo in reservados or correo in usados:
                sufijo += 1
                correo = f'usuario-{cuenta.pk}-{sufijo}@example.invalid'
        usados.add(correo)
        # Las claves originales permiten conservar las referencias de Reserva.
        Usuario.objects.using(alias).create(
            pk=cuenta.pk, cuenta_id=cuenta.pk,
            nombre=cuenta.first_name or cuenta.username, apellido=cuenta.last_name,
            correo=correo, activo=cuenta.is_active, fecha_registro=cuenta.date_joined,
            rol='ADMINISTRADOR' if cuenta.is_superuser else 'MIEMBRO',
        )
    Espacio.objects.using(alias).filter(activo=False).update(estado='inactivo')
    for reserva in Reserva.objects.using(alias).all():
        Historial.objects.using(alias).create(
            reserva_id=reserva.pk, estado_anterior='', estado_nuevo=reserva.estado,
            fecha_cambio=reserva.fecha_creacion,
            motivo='Estado conservado durante la migración; responsable original desconocido.',
        )


def restaurar_datos(apps, schema_editor):
    alias = schema_editor.connection.alias
    Usuario = apps.get_model('cowork', 'Usuario')
    Reserva = apps.get_model('cowork', 'Reserva')
    Espacio = apps.get_model('cowork', 'Espacio')
    # Una reserva pendiente no existía en el esquema anterior.
    Reserva.objects.using(alias).filter(estado='pendiente').update(estado='confirmada')
    cuentas = dict(Usuario.objects.using(alias).values_list('pk', 'cuenta_id'))
    for reserva in Reserva.objects.using(alias).all():
        Reserva.objects.using(alias).filter(pk=reserva.pk).update(
            usuario_id=cuentas[reserva.usuario_id],
        )
    Espacio.objects.using(alias).exclude(estado='disponible').update(activo=False)


class Migration(migrations.Migration):
    # Reconoce instalaciones que ya aplicaron el nombre anterior.
    replaces = [('cowork', '0004_modelos_diagrama')]

    dependencies = [
        ('cowork', '0003_renombrar_campos_diagrama'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150)),
                ('apellido', models.CharField(blank=True, max_length=150)),
                ('correo', models.EmailField(max_length=254, unique=True)),
                ('rol', models.CharField(choices=[('MIEMBRO', 'Miembro'), ('ADMINISTRADOR', 'Administrador')], default='MIEMBRO', max_length=20)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_registro', models.DateTimeField(default=now, editable=False)),
                ('cuenta', models.OneToOneField(on_delete=PROTECT, related_name='perfil_cowork', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['apellido', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='HistorialEstadoReserva',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_anterior', models.CharField(blank=True, choices=[('pendiente', 'Pendiente'), ('confirmada', 'Confirmada'), ('cancelada', 'Cancelada'), ('finalizada', 'Finalizada')], max_length=20)),
                ('estado_nuevo', models.CharField(choices=[('pendiente', 'Pendiente'), ('confirmada', 'Confirmada'), ('cancelada', 'Cancelada'), ('finalizada', 'Finalizada')], max_length=20)),
                ('fecha_cambio', models.DateTimeField(default=now, editable=False)),
                ('motivo', models.TextField(blank=True)),
                ('reserva', models.ForeignKey(on_delete=PROTECT, related_name='historial', to='cowork.reserva')),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=PROTECT, related_name='cambios_reserva', to='cowork.usuario')),
            ],
            options={
                'verbose_name_plural': 'historiales de estado de reservas',
                'ordering': ['fecha_cambio', 'pk'],
            },
        ),
        migrations.CreateModel(
            name='EventoAuditoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(default=now, editable=False)),
                ('accion', models.CharField(max_length=80)),
                ('tipo_entidad', models.CharField(max_length=80)),
                ('id_entidad', models.PositiveBigIntegerField()),
                ('valores_anteriores', models.JSONField(blank=True, default=dict, encoder=DjangoJSONEncoder)),
                ('valores_nuevos', models.JSONField(blank=True, default=dict, encoder=DjangoJSONEncoder)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=PROTECT, related_name='eventos_auditoria', to='cowork.usuario')),
            ],
            options={
                'verbose_name_plural': 'eventos de auditoría',
                'ordering': ['-fecha', '-pk'],
            },
        ),
        migrations.AddField(
            model_name='espacio',
            name='estado',
            field=models.CharField(choices=[('disponible', 'Disponible'), ('mantenimiento', 'En mantenimiento'), ('inactivo', 'Inactivo')], default='disponible', max_length=20),
        ),
        migrations.AddField(
            model_name='espacio',
            name='observaciones_privadas',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='reserva',
            name='motivo_cancelacion',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='reserva',
            name='cantidad_personas',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='reserva',
            name='estado',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('confirmada', 'Confirmada'), ('cancelada', 'Cancelada'), ('finalizada', 'Finalizada')], default='pendiente', max_length=20),
        ),
        migrations.AddConstraint(
            model_name='espacio',
            constraint=models.CheckConstraint(condition=models.Q(('estado__in', ['disponible', 'mantenimiento', 'inactivo'])), name='espacio_estado_valido'),
        ),
        migrations.RunPython(completar_datos, restaurar_datos),
        migrations.RemoveField(
            model_name='espacio',
            name='activo',
        ),
        migrations.AlterField(
            model_name='reserva',
            name='usuario',
            field=models.ForeignKey(on_delete=PROTECT, related_name='reservas', to='cowork.usuario'),
        ),
        migrations.AddIndex(
            model_name='reserva',
            index=models.Index(fields=['espacio', 'estado', 'inicio', 'fin'], name='reserva_disponibilidad_idx'),
        ),
        migrations.AddConstraint(
            model_name='reserva',
            constraint=models.CheckConstraint(condition=models.Q(('estado__in', ['pendiente', 'confirmada', 'cancelada', 'finalizada'])), name='reserva_estado_valido'),
        ),
        migrations.AddConstraint(
            model_name='usuario',
            constraint=models.UniqueConstraint(Lower('correo'), name='usuario_correo_sin_mayusculas'),
        ),
        migrations.AddConstraint(
            model_name='usuario',
            constraint=models.CheckConstraint(condition=models.Q(('rol__in', ['MIEMBRO', 'ADMINISTRADOR'])), name='usuario_rol_valido'),
        ),
    ]
