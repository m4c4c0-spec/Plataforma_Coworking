from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Espacio, Reserva, Usuario


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
