from datetime import timedelta

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Espacio, Reserva, Sede, TipoEspacio, Usuario
from .reportes_dto import Formato, TipoReporte
from .services import ServicioReportes


class FormularioBootstrap:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs['class'] = 'form-check-input'
            else:
                campo.widget.attrs['class'] = 'form-select' if isinstance(campo.widget, forms.Select) else 'form-control'


class UsuarioForm(FormularioBootstrap, forms.ModelForm):
    nombre_usuario = forms.CharField(
        max_length=150, label='Nombre de acceso',
        validators=get_user_model()._meta.get_field('username').validators,
    )
    password = forms.CharField(
        label='Contraseña', widget=forms.PasswordInput, required=False,
        help_text='Obligatoria al crear. Deja vacío al editar para conservar la contraseña.',
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'correo', 'rol']

    def __init__(self, *args, actor, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['nombre_usuario'].initial = self.instance.cuenta.get_username()
            self.fields['nombre_usuario'].disabled = True

    def clean_nombre_usuario(self):
        nombre = self.cleaned_data['nombre_usuario']
        if not self.instance.pk and get_user_model().objects.filter(username=nombre).exists():
            raise ValidationError('Ya existe una cuenta con este nombre de acceso.')
        return nombre

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.instance.pk and not password:
            raise ValidationError('Indica una contraseña para la nueva cuenta.')
        if password:
            cuenta = self.instance.cuenta if self.instance.pk else get_user_model()(
                username=self.cleaned_data.get('nombre_usuario', ''),
                email=self.cleaned_data.get('correo', ''),
                first_name=self.cleaned_data.get('nombre', ''),
                last_name=self.cleaned_data.get('apellido', ''),
            )
            password_validation.validate_password(password, cuenta)
        return password

    @transaction.atomic
    def save(self, commit=True):
        if not commit:
            raise ValueError('El usuario y su cuenta deben guardarse juntos.')
        usuario = super().save(commit=False)
        if not usuario.pk:
            usuario.cuenta = get_user_model().objects.create_user(
                username=self.cleaned_data['nombre_usuario'],
                password=self.cleaned_data['password'],
            )
        elif self.cleaned_data['password']:
            usuario.cuenta.set_password(self.cleaned_data['password'])
            usuario.cuenta.save(update_fields=['password'])
        usuario.guardar(self.actor)
        return usuario


class SedeForm(FormularioBootstrap, forms.ModelForm):
    class Meta:
        model = Sede
        fields = ['nombre', 'direccion', 'ciudad', 'activa']


class TipoEspacioForm(FormularioBootstrap, forms.ModelForm):
    class Meta:
        model = TipoEspacio
        fields = ['nombre', 'descripcion']
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 3})}


class EspacioForm(FormularioBootstrap, forms.ModelForm):
    class Meta:
        model = Espacio
        fields = [
            'sede', 'tipo', 'nombre', 'capacidad', 'estado',
            'descripcion_publica', 'observaciones_privadas',
        ]
        widgets = {
            'descripcion_publica': forms.Textarea(attrs={'rows': 3}),
            'observaciones_privadas': forms.Textarea(attrs={'rows': 3}),
        }


class ReservaForm(FormularioBootstrap, forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['usuario', 'espacio', 'inicio', 'fin', 'cantidad_personas', 'observaciones']
        widgets = {
            'inicio': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
            'fin': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['espacio'].queryset = Espacio.objects.filter(
            estado=Espacio.Estado.DISPONIBLE, sede__activa=True,
        ).select_related('sede', 'tipo')
        self.fields['usuario'].queryset = Usuario.objects.filter(activo=True, cuenta__is_active=True)
        if self.instance.pk:
            self.fields['usuario'].initial = self.instance.usuario_id
            self.fields['usuario'].disabled = True
        elif actor.rol != Usuario.Rol.ADMINISTRADOR:
            self.instance.usuario = actor
            self.fields['usuario'].initial = actor.pk
            self.fields['usuario'].disabled = True


class CancelacionForm(FormularioBootstrap, forms.Form):
    motivo = forms.CharField(label='Motivo de cancelación', widget=forms.Textarea(attrs={'rows': 3}))


class ReporteForm(FormularioBootstrap, forms.Form):
    """Valida los parámetros de un reporte; la pantalla y la API comparten esta lógica."""

    MAXIMO_DIAS = 366

    tipo = forms.ChoiceField(label='Reporte', choices=[
        (TipoReporte.RESERVAS.value, 'Detalle de reservas'),
        (TipoReporte.DIARIO.value, 'Uso diario por espacio'),
    ])
    formato = forms.ChoiceField(choices=[(Formato.PDF.value, 'PDF'), (Formato.EXCEL.value, 'Excel (xlsx)')])
    desde = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    hasta = forms.DateField(
        label='Hasta (incluido)', required=False, widget=forms.DateInput(attrs={'type': 'date'}),
    )
    usuario = forms.ModelChoiceField(
        Usuario.objects.all(), required=False, empty_label='Todos',
        help_text='Solo para el detalle de reservas.',
    )
    espacio = forms.ModelChoiceField(
        Espacio.objects.select_related('sede'), required=False, empty_label='Todos',
        help_text='Solo para el detalle de reservas.',
    )
    estado = forms.ChoiceField(
        choices=[('', 'Todos')] + Reserva.Estado.choices, required=False,
        help_text='Solo para el detalle de reservas.',
    )

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get('desde'), datos.get('hasta')
        if desde and hasta and hasta < desde:
            self.add_error('hasta', 'La fecha final no puede ser anterior a la inicial.')
        elif datos.get('tipo') == TipoReporte.DIARIO.value:
            if not desde or not hasta:
                self.add_error(None, 'El reporte diario requiere las fechas desde y hasta.')
            elif (hasta - desde).days >= self.MAXIMO_DIAS:
                self.add_error('hasta', f'El reporte diario admite hasta {self.MAXIMO_DIAS} días.')
        return datos

    def generar(self, actor):
        datos = self.cleaned_data
        filtros = {'desde': datos['desde'], 'hasta': None}
        if datos['hasta']:
            # La fecha final se incluye completa: el período termina al iniciar el día siguiente.
            filtros['hasta'] = datos['hasta'] + timedelta(days=1)
        if datos['tipo'] == TipoReporte.RESERVAS.value:
            filtros.update(
                usuario_id=datos['usuario'].pk if datos['usuario'] else None,
                espacio_id=datos['espacio'].pk if datos['espacio'] else None,
                estado=datos['estado'] or None,
            )
        return ServicioReportes.generarDocumento(datos['tipo'], datos['formato'], actor, **filtros)
