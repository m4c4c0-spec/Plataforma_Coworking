from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('cowork', '0002_espacio_y_reserva')]

    operations = [
        migrations.RenameField('espacio', 'descripcion', 'descripcion_publica'),
        migrations.RenameField('reserva', 'creada_en', 'fecha_creacion'),
    ]
