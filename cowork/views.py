from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import CancelacionForm, EspacioForm, ReservaForm, UsuarioForm
from .models import Espacio, Usuario, exigir_permiso
from .services import ServicioReportes


def bienvenida(request):
    """Renderiza la página pública de bienvenida."""
    return render(request, 'cowork/bienvenida.html')


def error_404(request, exception):
    """Devuelve un error 404 sin exponer detalles de la excepción."""
    return render(request, 'cowork/404.html', status=404)


def inicio(request):
    """Renderiza la página que presenta las características de la aplicación."""
    return render(request, 'cowork/inicio.html')


def con_actor(accion):
    """Resuelve el perfil en cada petición y aplica permisos antes de la vista."""
    def decorar(vista):
        @login_required
        @wraps(vista)
        def protegida(request, *args, **kwargs):
            request.actor = Usuario.desde_cuenta(request.user)
            request.actor = exigir_permiso(request.actor, accion)
            return vista(request, *args, **kwargs)
        return protegida
    return decorar


def contexto_gestion(request, **extra):
    return {'actor': request.actor, 'es_admin': request.actor.rol == Usuario.Rol.ADMINISTRADOR, **extra}


def agregar_errores(form, error):
    if isinstance(error, IntegrityError):
        form.add_error(None, 'No se pudo guardar: existe un registro con esos datos. Revisa el formulario.')
    elif hasattr(error, 'message_dict'):
        for campo, errores in error.message_dict.items():
            for mensaje in errores:
                form.add_error(campo if campo in form.fields else None, mensaje)
    else:
        for mensaje in error.messages:
            form.add_error(None, mensaje)


@con_actor('gestionar_usuarios')
def usuarios(request):
    return render(request, 'cowork/usuarios.html', contexto_gestion(
        request, usuarios=Usuario.objects.select_related('cuenta'),
    ))


@con_actor('gestionar_usuarios')
@require_http_methods(['GET', 'POST'])
def usuario_formulario(request, pk=None):
    usuario = get_object_or_404(Usuario, pk=pk) if pk else None
    form = UsuarioForm(request.POST if request.method == 'POST' else None, instance=usuario, actor=request.actor)
    if request.method == 'POST' and form.is_valid():
        try:
            form.save()
        except (ValidationError, IntegrityError) as error:
            agregar_errores(form, error)
        else:
            messages.success(request, 'Usuario guardado.')
            return redirect('usuarios')
    return render(request, 'cowork/formulario.html', contexto_gestion(
        request, form=form, titulo='Editar usuario' if pk else 'Crear usuario', volver='usuarios',
    ))


@con_actor('gestionar_usuarios')
@require_http_methods(['GET', 'POST'])
def usuario_desactivar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        usuario.desactivar(request.actor)
        messages.success(request, 'Usuario desactivado. Sus reservas y registros se conservan.')
        return redirect('usuarios')
    return render(request, 'cowork/confirmar_accion.html', contexto_gestion(
        request, titulo='Desactivar usuario', objeto=usuario, volver='usuarios',
        descripcion='El usuario pierde acceso. Sus reservas e historial se conservan.',
    ))


@con_actor('ver_espacios')
def espacios(request):
    registros = Espacio.objects.select_related('sede', 'tipo')
    if request.actor.rol != Usuario.Rol.ADMINISTRADOR:
        registros = registros.filter(estado=Espacio.Estado.DISPONIBLE, sede__activa=True)
    return render(request, 'cowork/espacios.html', contexto_gestion(request, espacios=registros))


@con_actor('gestionar_espacios')
@require_http_methods(['GET', 'POST'])
def espacio_formulario(request, pk=None):
    espacio = get_object_or_404(Espacio, pk=pk) if pk else None
    form = EspacioForm(request.POST if request.method == 'POST' else None, instance=espacio)
    if request.method == 'POST' and form.is_valid():
        try:
            espacio = form.save(commit=False)
            espacio.guardar(request.actor)
        except (ValidationError, IntegrityError) as error:
            agregar_errores(form, error)
        else:
            messages.success(request, 'Espacio guardado.')
            return redirect('espacios')
    return render(request, 'cowork/formulario.html', contexto_gestion(
        request, form=form, titulo='Editar espacio' if pk else 'Crear espacio', volver='espacios',
    ))


@con_actor('gestionar_espacios')
@require_http_methods(['GET', 'POST'])
def espacio_desactivar(request, pk):
    espacio = get_object_or_404(Espacio, pk=pk)
    if request.method == 'POST':
        espacio.cambiarEstado(Espacio.Estado.INACTIVO, request.actor)
        messages.success(request, 'Espacio inactivado. Las reservas existentes se conservan.')
        return redirect('espacios')
    return render(request, 'cowork/confirmar_accion.html', contexto_gestion(
        request, titulo='Inactivar espacio', objeto=espacio, volver='espacios',
        descripcion='El espacio deja de aceptar reservas. Las reservas existentes se conservan.',
    ))


@con_actor('ver_reservas')
def reservas(request):
    return render(request, 'cowork/reservas.html', contexto_gestion(
        request, reservas=ServicioReportes.buscarReservas({}, request.actor),
    ))


@con_actor('ver_reservas')
def reserva_detalle(request, pk):
    reserva = get_object_or_404(ServicioReportes.buscarReservas({}, request.actor), pk=pk)
    return render(request, 'cowork/reserva_detalle.html', contexto_gestion(
        request, reserva=reserva, historial=reserva.historial.select_related('responsable'),
    ))


@con_actor('crear_reserva')
@require_http_methods(['GET', 'POST'])
def reserva_formulario(request, pk=None):
    reserva = get_object_or_404(ServicioReportes.buscarReservas({}, request.actor), pk=pk) if pk else None
    if reserva and reserva.estado != reserva.Estado.PENDIENTE:
        raise PermissionDenied('Solo se pueden editar reservas pendientes.')
    form = ReservaForm(request.POST if request.method == 'POST' else None, instance=reserva, actor=request.actor)
    if request.method == 'POST' and form.is_valid():
        try:
            reserva = form.save(commit=False)
            reserva.guardar(request.actor)
        except (ValidationError, IntegrityError) as error:
            agregar_errores(form, error)
        else:
            messages.success(request, 'Reserva guardada. Queda pendiente de confirmación.')
            return redirect('reserva_detalle', pk=reserva.pk)
    return render(request, 'cowork/formulario.html', contexto_gestion(
        request, form=form, titulo='Editar reserva' if pk else 'Crear reserva', volver='reservas',
    ))


@con_actor('cancelar_reserva')
@require_http_methods(['GET', 'POST'])
def reserva_cancelar(request, pk):
    reserva = get_object_or_404(ServicioReportes.buscarReservas({}, request.actor), pk=pk)
    form = CancelacionForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            reserva.cancelar(request.actor, form.cleaned_data['motivo'])
        except ValidationError as error:
            agregar_errores(form, error)
        else:
            messages.success(request, 'Reserva cancelada.')
            return redirect('reserva_detalle', pk=pk)
    return render(request, 'cowork/formulario.html', contexto_gestion(
        request, form=form, titulo='Cancelar reserva', volver='reservas',
    ))


@con_actor('confirmar_reserva')
@require_POST
def reserva_confirmar(request, pk):
    reserva = get_object_or_404(ServicioReportes.buscarReservas({}, request.actor), pk=pk)
    try:
        reserva.confirmar(request.actor)
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    else:
        messages.success(request, 'Reserva confirmada.')
    return redirect('reserva_detalle', pk=pk)


@con_actor('finalizar_reserva')
@require_POST
def reserva_finalizar(request, pk):
    reserva = get_object_or_404(ServicioReportes.buscarReservas({}, request.actor), pk=pk)
    try:
        reserva.finalizar(request.actor)
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    else:
        messages.success(request, 'Reserva finalizada.')
    return redirect('reserva_detalle', pk=pk)
