from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError

from cowork.models import Administrador, Espacio, EventoAuditoria, Reserva, Usuario
from cowork.reportes_dto import RangoFecha
from cowork.services import ServicioReportes
from .test_gestion import DatosCoworkTests


class ConsistenciaModelosTests(DatosCoworkTests):
    def test_desde_cuenta_no_asciende_una_cuenta_comun_sin_perfil(self):
        cuenta = get_user_model().objects.create_user(username='cuenta_comun')
        with self.assertRaises(PermissionDenied):
            Administrador.desde_cuenta(cuenta)
        perfil = Usuario.objects.get(cuenta=cuenta)
        self.assertEqual(perfil.rol, Usuario.Rol.MIEMBRO)
        self.assertFalse(perfil.puedeRealizar('gestionar_usuarios'))

    def test_desde_cuenta_no_duplica_un_perfil_miembro(self):
        with self.assertRaises(PermissionDenied):
            Administrador.desde_cuenta(self.miembro.cuenta)
        self.miembro.refresh_from_db()
        self.assertEqual(self.miembro.rol, Usuario.Rol.MIEMBRO)
        self.assertEqual(Usuario.objects.filter(cuenta=self.miembro.cuenta).count(), 1)

    def test_desde_cuenta_administrativa_conserva_identidad(self):
        proxy = Administrador.desde_cuenta(self.admin.cuenta)
        self.assertEqual(proxy.pk, self.admin.pk)
        self.assertEqual(proxy.cuenta_id, self.admin.cuenta_id)

    def test_desde_cuenta_superusuario_crea_el_perfil_administrativo(self):
        cuenta = get_user_model().objects.create_superuser(username='super_consistencia')
        proxy = Administrador.desde_cuenta(cuenta)
        self.assertEqual(proxy.rol, Usuario.Rol.ADMINISTRADOR)
        self.assertEqual(Usuario.objects.filter(cuenta=cuenta).count(), 1)

    def test_proxy_desactualizado_no_restaura_el_rol_perdido(self):
        proxy = Administrador.objects.get(pk=self.admin.pk)
        self.otro.rol = Usuario.Rol.ADMINISTRADOR
        self.otro.save(update_fields=['rol'])
        Usuario.objects.filter(pk=self.admin.pk).update(rol=Usuario.Rol.MIEMBRO)
        proxy.nombre = 'Edición de una copia antigua'
        with self.assertRaises(ValidationError):
            proxy.guardar(self.otro)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.rol, Usuario.Rol.MIEMBRO)
        self.assertFalse(EventoAuditoria.objects.exists())

    def test_auditoria_del_proxy_utiliza_la_entidad_concreta(self):
        proxy = Administrador.objects.get(pk=self.admin.pk)
        proxy.nombre = 'Nombre actualizado'
        proxy.guardar(self.admin)
        evento = EventoAuditoria.objects.get()
        self.assertEqual(evento.accion, 'actualizar')
        self.assertEqual(evento.tipo_entidad, 'usuario')
        self.assertEqual(evento.valores_anteriores['nombre'], self.admin.nombre)
        self.assertEqual(evento.valores_nuevos['nombre'], 'Nombre actualizado')

    def test_baja_de_copia_anterior_conserva_ediciones_recientes(self):
        copia = Usuario.objects.get(pk=self.miembro.pk)
        self.miembro.nombre = 'Nombre nuevo'
        self.miembro.correo = 'correo_nuevo@example.com'
        self.miembro.guardar(self.admin)
        copia.desactivar(self.admin)
        self.miembro.refresh_from_db()
        self.assertEqual(self.miembro.nombre, 'Nombre nuevo')
        self.assertEqual(self.miembro.correo, 'correo_nuevo@example.com')
        self.assertFalse(self.miembro.activo)
        self.assertFalse(self.miembro.cuenta.is_active)
        evento = EventoAuditoria.objects.first()
        self.assertEqual(evento.valores_anteriores['correo'], 'correo_nuevo@example.com')
        self.assertEqual(evento.valores_nuevos['correo'], 'correo_nuevo@example.com')

    def test_baja_de_proxy_conserva_el_rol_cambiado_por_otro_administrador(self):
        copia = Administrador.objects.get(pk=self.admin.pk)
        self.otro.rol = Usuario.Rol.ADMINISTRADOR
        self.otro.save(update_fields=['rol'])
        Usuario.objects.filter(pk=self.admin.pk).update(rol=Usuario.Rol.MIEMBRO)
        copia.desactivar(self.otro)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.rol, Usuario.Rol.MIEMBRO)
        self.assertFalse(self.admin.activo)
        self.assertEqual(EventoAuditoria.objects.get().tipo_entidad, 'usuario')

    def test_estado_de_copia_anterior_conserva_nombre_y_capacidad(self):
        copia = Espacio.objects.get(pk=self.espacio.pk)
        self.espacio.nombre = 'Sala renovada'
        self.espacio.capacidad = 10
        self.espacio.guardar(self.admin)
        copia.cambiarEstado(Espacio.Estado.INACTIVO, self.admin)
        self.espacio.refresh_from_db()
        self.assertEqual(self.espacio.nombre, 'Sala renovada')
        self.assertEqual(self.espacio.capacidad, 10)
        self.assertEqual(self.espacio.estado, Espacio.Estado.INACTIVO)
        evento = EventoAuditoria.objects.first()
        self.assertEqual(evento.valores_anteriores['capacidad'], 10)
        self.assertEqual(evento.valores_nuevos['capacidad'], 10)

    def test_cuenta_de_acceso_inactiva_no_puede_ser_titular(self):
        self.miembro.cuenta.is_active = False
        self.miembro.cuenta.save(update_fields=['is_active'])
        reserva = Reserva(usuario=self.miembro, espacio=self.espacio, inicio=self.inicio, fin=self.fin)
        with self.assertRaises(ValidationError):
            reserva.guardar(self.admin)
        self.assertFalse(Reserva.objects.exists())
        self.assertFalse(EventoAuditoria.objects.exists())

    def test_confirmacion_revalida_la_actividad_de_la_cuenta(self):
        reserva = self.nueva_reserva()
        self.miembro.cuenta.is_active = False
        self.miembro.cuenta.save(update_fields=['is_active'])
        with self.assertRaises(ValidationError):
            reserva.confirmar(self.admin)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, Reserva.Estado.PENDIENTE)
        self.assertEqual(reserva.historial.count(), 1)
        reserva.cancelar(self.admin, 'Cuenta desactivada')
        self.assertEqual(reserva.estado, Reserva.Estado.CANCELADA)

    def test_cancelacion_con_motivo_no_textual_falla_sin_modificar_la_reserva(self):
        reserva = self.nueva_reserva()
        with self.assertRaises(ValidationError):
            reserva.cancelar(self.miembro, None)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, Reserva.Estado.PENDIENTE)
        self.assertEqual(reserva.historial.count(), 1)


class CambioHorarioModelosTests(DatosCoworkTests):
    @staticmethod
    def hora(minuto, repeticion):
        return datetime(2026, 4, 4, 23, minuto, tzinfo=ZoneInfo('America/Santiago'), fold=repeticion)

    def test_intervalo_valido_cuyo_fin_parece_anterior_en_hora_local(self):
        inicio, fin = self.hora(45, 0), self.hora(15, 1)
        self.assertTrue(self.espacio.estaDisponible(inicio, fin))
        reserva = self.nueva_reserva(inicio=inicio, fin=fin)
        reserva.refresh_from_db()
        self.assertTrue(reserva.validarHorario())
        self.assertEqual(reserva.inicio, inicio.astimezone(UTC))
        self.assertEqual(reserva.fin, fin.astimezone(UTC))
        self.assertFalse(self.espacio.estaDisponible(inicio, fin))

    def test_uso_global_y_diario_coinciden_durante_la_hora_repetida(self):
        inicio, fin = self.hora(15, 0), self.hora(45, 1)
        reserva = self.nueva_reserva(inicio=inicio, fin=fin)
        reserva.confirmar(self.admin)
        uso = ServicioReportes.calcularUsoEspacios(inicio, fin, self.admin)
        diario = ServicioReportes.resumirReservasDiarias(RangoFecha(inicio, fin), self.admin)
        self.assertEqual(uso[self.espacio.pk]['horas'], 1.5)
        self.assertEqual(sum(fila.horas for fila in diario), 1.5)

    def test_todos_los_reportes_aceptan_el_intervalo_de_la_hora_repetida(self):
        inicio, fin = self.hora(45, 0), self.hora(15, 1)
        reserva = self.nueva_reserva(inicio=inicio, fin=fin)
        reservas = ServicioReportes.buscarReservas({'desde': inicio, 'hasta': fin}, self.admin)
        self.assertEqual(list(reservas), [reserva])
        self.assertEqual(ServicioReportes.resumirActividad(inicio, fin, self.admin)['total'], 0)
        self.assertEqual(ServicioReportes.analizarUsuarios(inicio, fin, self.admin)['con_reservas'], 1)
