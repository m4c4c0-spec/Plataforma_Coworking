import logging

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied, ValidationError
from django.db import IntegrityError
from django.db.models import Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.http import content_disposition_header
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import APIException, NotFound
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from .database import sesion_mysql
from .forms import (
    CancelacionForm, EspacioForm, ReporteForm, ReservaForm, SedeForm, TipoEspacioForm, UsuarioForm,
)
from .models import Espacio, Sede, TipoEspacio, Usuario, exigir_permiso
from .models_sqlalchemy import EspacioSQL, ReservaSQL, SedeSQL, TipoEspacioSQL, UsuarioSQL
from .serializers import (
    EspacioSerializer, PaginacionSerializer, ReservaSerializer,
    SedeSerializer, TipoEspacioSerializer, UsuarioSerializer,
)
from .serializers_gestion import (
    CancelacionSerializer, EspacioGestionSerializer, ReservaGestionSerializer,
    SedeGestionSerializer, TipoEspacioGestionSerializer, UsuarioGestionSerializer,
)
from .services import ServicioReportes

logger = logging.getLogger(__name__)


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


def respuesta_archivo(contenido, nombre, tipo_contenido):
    return HttpResponse(contenido, content_type=tipo_contenido, headers={
        'Content-Disposition': content_disposition_header(True, nombre),
    })


# Pantallas HTML: páginas públicas, autenticación y gestión por recurso.


class HTMLViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]
    renderer_classes = [TemplateHTMLRenderer]

    def perform_content_negotiation(self, request, force=False):
        # Las pantallas conservan su respuesta HTML para cualquier Accept.
        return super().perform_content_negotiation(request, force=True)

    def handle_exception(self, exc):
        if isinstance(exc, Http404):
            return render(self.request, 'cowork/404.html', status=404)
        return super().handle_exception(exc)


class PaginaViewSet(HTMLViewSet):
    def bienvenida(self, request):
        """Renderiza la página pública de bienvenida."""
        return render(request, 'cowork/bienvenida.html')

    def inicio(self, request):
        """Renderiza la página que presenta las características de la aplicación."""
        return render(request, 'cowork/inicio.html')


class Error404ViewSet(HTMLViewSet):
    authentication_classes = []

    def retrieve(self, request, exception=None):
        """Devuelve un error 404 sin exponer detalles de la excepción."""
        return render(request, 'cowork/404.html', status=404)


class AutenticacionViewSet(HTMLViewSet):
    """Agrupa el acceso y conserva las protecciones de autenticación de Django."""

    def ingresar(self, request):
        return auth_views.LoginView.as_view(template_name='cowork/ingresar.html')(request._request)

    def salir(self, request):
        return auth_views.LogoutView.as_view()(request._request)


class PantallaGestionViewSet(HTMLViewSet):
    permission_classes = [IsAuthenticated]
    permiso_lectura = 'ver_espacios'
    permisos_acciones = {}

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        permiso = self.permisos_acciones.get(self.action, self.permiso_lectura)
        request.actor = exigir_permiso(Usuario.desde_cuenta(request.user), permiso)

    def contexto_gestion(self, request, **extra):
        return {'actor': request.actor, 'es_admin': request.actor.rol == Usuario.Rol.ADMINISTRADOR, **extra}


class UsuarioPantallaViewSet(PantallaGestionViewSet):
    permiso_lectura = 'gestionar_usuarios'

    def list(self, request):
        return render(request, 'cowork/usuarios.html', self.contexto_gestion(
            request, usuarios=Usuario.objects.select_related('cuenta'),
        ))

    def crear(self, request):
        return self._formulario(request)

    def editar(self, request, pk=None):
        return self._formulario(request, pk)

    def _formulario(self, request, pk=None):
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
        return render(request, 'cowork/formulario.html', self.contexto_gestion(
            request, form=form, titulo='Editar usuario' if pk else 'Crear usuario', volver='usuarios',
        ))

    def desactivar(self, request, pk=None):
        usuario = get_object_or_404(Usuario, pk=pk)
        if request.method == 'POST':
            usuario.desactivar(request.actor)
            messages.success(request, 'Usuario desactivado. Sus reservas y registros se conservan.')
            return redirect('usuarios')
        return render(request, 'cowork/confirmar_accion.html', self.contexto_gestion(
            request, titulo='Desactivar usuario', objeto=usuario, volver='usuarios',
            descripcion='El usuario pierde acceso. Sus reservas e historial se conservan.',
        ))


class EspacioPantallaViewSet(PantallaGestionViewSet):
    permisos_acciones = {
        'crear': 'gestionar_espacios', 'editar': 'gestionar_espacios',
        'desactivar': 'gestionar_espacios',
    }

    def list(self, request):
        registros = Espacio.objects.select_related('sede', 'tipo')
        if request.actor.rol != Usuario.Rol.ADMINISTRADOR:
            registros = registros.filter(estado=Espacio.Estado.DISPONIBLE, sede__activa=True)
        return render(request, 'cowork/espacios.html', self.contexto_gestion(request, espacios=registros))

    def crear(self, request):
        return self._formulario(request)

    def editar(self, request, pk=None):
        return self._formulario(request, pk)

    def _formulario(self, request, pk=None):
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
        return render(request, 'cowork/formulario.html', self.contexto_gestion(
            request, form=form, titulo='Editar espacio' if pk else 'Crear espacio', volver='espacios',
        ))

    def desactivar(self, request, pk=None):
        espacio = get_object_or_404(Espacio, pk=pk)
        if request.method == 'POST':
            espacio.cambiarEstado(Espacio.Estado.INACTIVO, request.actor)
            messages.success(request, 'Espacio inactivado. Las reservas existentes se conservan.')
            return redirect('espacios')
        return render(request, 'cowork/confirmar_accion.html', self.contexto_gestion(
            request, titulo='Inactivar espacio', objeto=espacio, volver='espacios',
            descripcion='El espacio deja de aceptar reservas. Las reservas existentes se conservan.',
        ))


class SedePantallaViewSet(PantallaGestionViewSet):
    permiso_lectura = 'gestionar_espacios'

    def list(self, request):
        return render(request, 'cowork/sedes.html', self.contexto_gestion(request, sedes=Sede.objects.all()))

    def crear(self, request):
        return self._formulario(request)

    def editar(self, request, pk=None):
        return self._formulario(request, pk)

    def _formulario(self, request, pk=None):
        sede = get_object_or_404(Sede, pk=pk) if pk else None
        form = SedeForm(request.POST if request.method == 'POST' else None, instance=sede)
        if request.method == 'POST' and form.is_valid():
            try:
                form.save(commit=False).guardar(request.actor)
            except (ValidationError, IntegrityError) as error:
                agregar_errores(form, error)
            else:
                messages.success(request, 'Sede guardada.')
                return redirect('sedes')
        return render(request, 'cowork/formulario.html', self.contexto_gestion(
            request, form=form, titulo='Editar sede' if pk else 'Crear sede', volver='sedes',
        ))

    def desactivar(self, request, pk=None):
        sede = get_object_or_404(Sede, pk=pk)
        if request.method == 'POST':
            sede.desactivar(request.actor)
            messages.success(request, 'Sede desactivada. Sus espacios y reservas se conservan.')
            return redirect('sedes')
        return render(request, 'cowork/confirmar_accion.html', self.contexto_gestion(
            request, titulo='Desactivar sede', objeto=sede, volver='sedes',
            descripcion='Sus espacios dejan de aceptar reservas nuevas. Las reservas existentes se conservan.',
        ))


class TipoEspacioPantallaViewSet(PantallaGestionViewSet):
    permiso_lectura = 'gestionar_espacios'

    def list(self, request):
        return render(request, 'cowork/tipos_espacio.html', self.contexto_gestion(
            request, tipos=TipoEspacio.objects.annotate(total_espacios=Count('espacios')),
        ))

    def crear(self, request):
        return self._formulario(request)

    def editar(self, request, pk=None):
        return self._formulario(request, pk)

    def _formulario(self, request, pk=None):
        tipo = get_object_or_404(TipoEspacio, pk=pk) if pk else None
        form = TipoEspacioForm(request.POST if request.method == 'POST' else None, instance=tipo)
        if request.method == 'POST' and form.is_valid():
            try:
                form.save(commit=False).guardar(request.actor)
            except (ValidationError, IntegrityError) as error:
                agregar_errores(form, error)
            else:
                messages.success(request, 'Tipo de espacio guardado.')
                return redirect('tipos_espacio')
        return render(request, 'cowork/formulario.html', self.contexto_gestion(
            request, form=form, titulo='Editar tipo de espacio' if pk else 'Crear tipo de espacio',
            volver='tipos_espacio',
        ))

    def eliminar(self, request, pk=None):
        tipo = get_object_or_404(TipoEspacio, pk=pk)
        if request.method == 'POST':
            try:
                tipo.eliminar(request.actor)
            except ValidationError as error:
                messages.error(request, ' '.join(error.messages))
            else:
                messages.success(request, 'Tipo de espacio eliminado.')
            return redirect('tipos_espacio')
        return render(request, 'cowork/confirmar_accion.html', self.contexto_gestion(
            request, titulo='Eliminar tipo de espacio', objeto=tipo, volver='tipos_espacio',
            descripcion='Solo se pueden eliminar tipos sin espacios asociados. La auditoría conserva sus datos.',
        ))


class ReservaPantallaViewSet(PantallaGestionViewSet):
    permiso_lectura = 'ver_reservas'
    permisos_acciones = {
        'crear': 'crear_reserva', 'editar': 'editar_reserva',
        'cancelar': 'cancelar_reserva', 'confirmar': 'confirmar_reserva',
        'finalizar': 'finalizar_reserva',
    }

    def list(self, request):
        return render(request, 'cowork/reservas.html', self.contexto_gestion(
            request, reservas=ServicioReportes.buscarReservas({}, request.actor),
        ))

    def retrieve(self, request, pk=None):
        reserva = get_object_or_404(ServicioReportes.buscarReservas({}, request.actor), pk=pk)
        return render(request, 'cowork/reserva_detalle.html', self.contexto_gestion(
            request, reserva=reserva, historial=reserva.historial.select_related('responsable'),
        ))

    def crear(self, request):
        return self._formulario(request)

    def editar(self, request, pk=None):
        return self._formulario(request, pk)

    def _formulario(self, request, pk=None):
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
        return render(request, 'cowork/formulario.html', self.contexto_gestion(
            request, form=form, titulo='Editar reserva' if pk else 'Crear reserva', volver='reservas',
        ))

    def cancelar(self, request, pk=None):
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
        return render(request, 'cowork/formulario.html', self.contexto_gestion(
            request, form=form, titulo='Cancelar reserva', volver='reservas',
        ))

    def confirmar(self, request, pk=None):
        reserva = get_object_or_404(ServicioReportes.buscarReservas({}, request.actor), pk=pk)
        try:
            reserva.confirmar(request.actor)
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
        else:
            messages.success(request, 'Reserva confirmada.')
        return redirect('reserva_detalle', pk=pk)

    def finalizar(self, request, pk=None):
        reserva = get_object_or_404(ServicioReportes.buscarReservas({}, request.actor), pk=pk)
        try:
            reserva.finalizar(request.actor)
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
        else:
            messages.success(request, 'Reserva finalizada.')
        return redirect('reserva_detalle', pk=pk)


class ReportePantallaViewSet(PantallaGestionViewSet):
    permiso_lectura = 'ver_reportes'

    def generar(self, request):
        # GET: generar un reporte no modifica datos, por lo que no requiere CSRF.
        form = ReporteForm(request.query_params or None)
        if form.is_valid():
            try:
                return respuesta_archivo(*form.generar(request.actor))
            except ValidationError as error:
                agregar_errores(form, error)
        return render(request, 'cowork/reportes.html', self.contexto_gestion(request, form=form))


# API de gestión de la base principal.


class PermisoGestion(BasePermission):
    message = 'No tienes permiso para realizar esta acción.'

    def has_permission(self, request, view):
        request.actor = Usuario.desde_cuenta(request.user)
        permiso = view.permisos_acciones.get(view.action, view.permiso_lectura)
        return request.actor.puedeRealizar(permiso)


class GestionViewSet(viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated, PermisoGestion]
    renderer_classes = [JSONRenderer]
    # DefaultRouter genera <int:pk>, igual que las rutas de las pantallas.
    lookup_value_converter = 'int'
    permiso_lectura = 'ver_espacios'
    permisos_acciones = {}

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            errores = exc.message_dict if hasattr(exc, 'message_dict') else {'non_field_errors': exc.messages}
            errores = {'non_field_errors' if campo == '__all__' else campo: valor for campo, valor in errores.items()}
            exc = serializers.ValidationError(errores)
        elif isinstance(exc, IntegrityError):
            exc = serializers.ValidationError({
                'non_field_errors': ['No se pudo guardar: existe un registro con esos datos.'],
            })
        return super().handle_exception(exc)


class LecturaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GestionViewSet):
    pass


class GuardadoViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, LecturaViewSet):
    """Crear y editar; las bajas se realizan mediante acciones del dominio."""


CATALOGO_ACCIONES = {
    accion: 'gestionar_espacios'
    for accion in ('create', 'update', 'partial_update', 'desactivar', 'destroy')
}


class SedeViewSet(GuardadoViewSet):
    queryset = Sede.objects.all()
    serializer_class = SedeGestionSerializer
    permisos_acciones = CATALOGO_ACCIONES

    def get_queryset(self):
        registros = super().get_queryset()
        if self.request.actor.rol != Usuario.Rol.ADMINISTRADOR:
            registros = registros.filter(activa=True)
        return registros

    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        sede = self.get_object()
        sede.desactivar(request.actor)
        return Response(self.get_serializer(sede).data)


class TipoEspacioViewSet(mixins.DestroyModelMixin, GuardadoViewSet):
    queryset = TipoEspacio.objects.all()
    serializer_class = TipoEspacioGestionSerializer
    permisos_acciones = CATALOGO_ACCIONES

    def perform_destroy(self, instance):
        instance.eliminar(self.request.actor)


class UsuarioViewSet(GuardadoViewSet):
    queryset = Usuario.objects.select_related('cuenta')
    serializer_class = UsuarioGestionSerializer
    permiso_lectura = 'gestionar_usuarios'

    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        usuario = self.get_object()
        usuario.desactivar(request.actor)
        return Response(self.get_serializer(usuario).data)


class EspacioViewSet(GuardadoViewSet):
    queryset = Espacio.objects.select_related('sede', 'tipo')
    serializer_class = EspacioGestionSerializer
    permisos_acciones = {
        'create': 'gestionar_espacios', 'update': 'gestionar_espacios',
        'partial_update': 'gestionar_espacios', 'desactivar': 'gestionar_espacios',
    }

    def get_queryset(self):
        registros = super().get_queryset()
        if self.request.actor.rol != Usuario.Rol.ADMINISTRADOR:
            registros = registros.filter(estado=Espacio.Estado.DISPONIBLE, sede__activa=True)
        return registros

    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        espacio = self.get_object()
        espacio.cambiarEstado(Espacio.Estado.INACTIVO, request.actor)
        return Response(self.get_serializer(espacio).data)


class ReservaViewSet(GuardadoViewSet):
    serializer_class = ReservaGestionSerializer
    permiso_lectura = 'ver_reservas'
    permisos_acciones = {
        'create': 'crear_reserva', 'update': 'editar_reserva',
        'partial_update': 'editar_reserva', 'cancelar': 'cancelar_reserva',
        'confirmar': 'confirmar_reserva', 'finalizar': 'finalizar_reserva',
    }

    def get_queryset(self):
        return ServicioReportes.buscarReservas({}, self.request.actor)

    @action(detail=True, methods=['post'], serializer_class=CancelacionSerializer)
    def cancelar(self, request, pk=None):
        reserva = self.get_object()
        parametros = self.get_serializer(data=request.data)
        parametros.is_valid(raise_exception=True)
        reserva.cancelar(request.actor, parametros.validated_data['motivo'])
        return Response(ReservaGestionSerializer(reserva, context=self.get_serializer_context()).data)

    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        reserva = self.get_object()
        reserva.confirmar(request.actor)
        return Response(self.get_serializer(reserva).data)

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        reserva = self.get_object()
        reserva.finalizar(request.actor)
        return Response(self.get_serializer(reserva).data)


class ReporteViewSet(GestionViewSet):
    """GET /api/reportes/?tipo=...&formato=... descarga un PDF o un Excel."""

    permiso_lectura = 'ver_reportes'

    def list(self, request):
        form = ReporteForm(request.query_params)
        if not form.is_valid():
            raise serializers.ValidationError({
                'non_field_errors' if campo == '__all__' else campo: list(mensajes)
                for campo, mensajes in form.errors.items()
            })
        return respuesta_archivo(*form.generar(request.actor))


# API de consulta a la base MySQL mediante SQLAlchemy.


class EsAdministradorCowork(BasePermission):
    message = 'Solo los administradores activos pueden consultar la base MySQL.'

    def has_permission(self, request, view):
        actor = Usuario.desde_cuenta(request.user)
        return actor.puedeRealizar('ver_reportes')


class MySQLNoDisponible(APIException):
    status_code = 503
    default_detail = 'MySQL no está disponible. Revisa la configuración, el servicio y las migraciones.'
    default_code = 'mysql_no_disponible'


class ConsultaMySQLViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated, EsAdministradorCowork]
    renderer_classes = [JSONRenderer]
    http_method_names = ['get', 'head', 'options']
    lookup_value_converter = 'int'
    modelo = None
    serializer_class = None
    relaciones = ()

    def list(self, request):
        return self._consultar(request)

    def retrieve(self, request, pk=None):
        return self._consultar(request, pk)

    def _consultar(self, request, pk=None):
        parametros = PaginacionSerializer(data=request.query_params)
        parametros.is_valid(raise_exception=True)
        try:
            with sesion_mysql() as sesion:
                consulta = select(self.modelo).options(*self.relaciones)
                if pk is not None:
                    objeto = sesion.scalar(consulta.where(self.modelo.id == pk))
                    if objeto is None:
                        raise NotFound('No se encontró el registro en MySQL.')
                    return Response(self.serializer_class(objeto).data)
                limite = parametros.validated_data['limit']
                offset = parametros.validated_data['offset']
                total = sesion.scalar(select(func.count()).select_from(self.modelo))
                objetos = sesion.scalars(
                    consulta.order_by(self.modelo.id).limit(limite).offset(offset)
                ).all()
                return Response({
                    'count': total, 'limit': limite, 'offset': offset,
                    'results': self.serializer_class(objetos, many=True).data,
                })
        except (ImproperlyConfigured, SQLAlchemyError) as error:
            # Las excepciones del driver pueden contener SQL y credenciales.
            logger.warning('Consulta MySQL fallida (%s).', type(error).__name__)
            raise MySQLNoDisponible() from error


class SedeMySQLViewSet(ConsultaMySQLViewSet):
    modelo = SedeSQL
    serializer_class = SedeSerializer


class TipoEspacioMySQLViewSet(ConsultaMySQLViewSet):
    modelo = TipoEspacioSQL
    serializer_class = TipoEspacioSerializer


class UsuarioMySQLViewSet(ConsultaMySQLViewSet):
    modelo = UsuarioSQL
    serializer_class = UsuarioSerializer


class EspacioMySQLViewSet(ConsultaMySQLViewSet):
    modelo = EspacioSQL
    serializer_class = EspacioSerializer
    relaciones = (joinedload(EspacioSQL.sede), joinedload(EspacioSQL.tipo))


class ReservaMySQLViewSet(ConsultaMySQLViewSet):
    modelo = ReservaSQL
    serializer_class = ReservaSerializer
    relaciones = (
        joinedload(ReservaSQL.usuario),
        joinedload(ReservaSQL.espacio).joinedload(EspacioSQL.sede),
        joinedload(ReservaSQL.espacio).joinedload(EspacioSQL.tipo),
    )
