-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Servidor: mariadb:3306
-- Tiempo de generación: 16-10-2026 a las 16:36:19
-- Versión del servidor: 11.4.13-MariaDB-ubu2404
-- Versión de PHP: 8.3.35

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `plataforma_coworking_local`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auth_group`
--

CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL,
  `name` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auth_group_permissions`
--

CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auth_permission`
--

CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `auth_permission`
--

INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can view log entry', 1, 'view_logentry'),
(5, 'Can add permission', 3, 'add_permission'),
(6, 'Can change permission', 3, 'change_permission'),
(7, 'Can delete permission', 3, 'delete_permission'),
(8, 'Can view permission', 3, 'view_permission'),
(9, 'Can add group', 2, 'add_group'),
(10, 'Can change group', 2, 'change_group'),
(11, 'Can delete group', 2, 'delete_group'),
(12, 'Can view group', 2, 'view_group'),
(13, 'Can add user', 4, 'add_user'),
(14, 'Can change user', 4, 'change_user'),
(15, 'Can delete user', 4, 'delete_user'),
(16, 'Can view user', 4, 'view_user'),
(17, 'Can add content type', 5, 'add_contenttype'),
(18, 'Can change content type', 5, 'change_contenttype'),
(19, 'Can delete content type', 5, 'delete_contenttype'),
(20, 'Can view content type', 5, 'view_contenttype'),
(21, 'Can add session', 6, 'add_session'),
(22, 'Can change session', 6, 'change_session'),
(23, 'Can delete session', 6, 'delete_session'),
(24, 'Can view session', 6, 'view_session'),
(25, 'Can add sede', 12, 'add_sede'),
(26, 'Can change sede', 12, 'change_sede'),
(27, 'Can delete sede', 12, 'delete_sede'),
(28, 'Can view sede', 12, 'view_sede'),
(29, 'Can add tipo de espacio', 13, 'add_tipoespacio'),
(30, 'Can change tipo de espacio', 13, 'change_tipoespacio'),
(31, 'Can delete tipo de espacio', 13, 'delete_tipoespacio'),
(32, 'Can view tipo de espacio', 13, 'view_tipoespacio'),
(33, 'Can add espacio', 8, 'add_espacio'),
(34, 'Can change espacio', 8, 'change_espacio'),
(35, 'Can delete espacio', 8, 'delete_espacio'),
(36, 'Can view espacio', 8, 'view_espacio'),
(37, 'Can add reserva', 11, 'add_reserva'),
(38, 'Can change reserva', 11, 'change_reserva'),
(39, 'Can delete reserva', 11, 'delete_reserva'),
(40, 'Can view reserva', 11, 'view_reserva'),
(41, 'Can add usuario', 14, 'add_usuario'),
(42, 'Can change usuario', 14, 'change_usuario'),
(43, 'Can delete usuario', 14, 'delete_usuario'),
(44, 'Can view usuario', 14, 'view_usuario'),
(45, 'Can add historial estado reserva', 10, 'add_historialestadoreserva'),
(46, 'Can change historial estado reserva', 10, 'change_historialestadoreserva'),
(47, 'Can delete historial estado reserva', 10, 'delete_historialestadoreserva'),
(48, 'Can view historial estado reserva', 10, 'view_historialestadoreserva'),
(49, 'Can add evento auditoria', 9, 'add_eventoauditoria'),
(50, 'Can change evento auditoria', 9, 'change_eventoauditoria'),
(51, 'Can delete evento auditoria', 9, 'delete_eventoauditoria'),
(52, 'Can view evento auditoria', 9, 'view_eventoauditoria'),
(53, 'Can add administrador', 7, 'add_administrador'),
(54, 'Can change administrador', 7, 'change_administrador'),
(55, 'Can delete administrador', 7, 'delete_administrador'),
(56, 'Can view administrador', 7, 'view_administrador');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auth_user`
--

CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `auth_user`
--

INSERT INTO `auth_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`) VALUES
(101, 'pbkdf2_sha256$1500000$e8oAzwXBBS2bIj2a3uheL4$YqR/wnXyDzMCrq23SWOeZv9nhIv/3/GP/b0etAEdwXM=', '2026-10-13 21:38:51.959038', 1, 'admin_demo', 'Valentina', 'Rojas', 'admin.demo@example.com', 1, 1, '2026-08-01 13:00:00.000000'),
(102, 'pbkdf2_sha256$1500000$e8oAzwXBBS2bIj2a3uheL4$YqR/wnXyDzMCrq23SWOeZv9nhIv/3/GP/b0etAEdwXM=', '2026-10-13 20:46:38.548560', 0, 'ana_demo', 'Ana', 'Muñoz', 'ana.demo@example.com', 0, 1, '2026-08-05 14:00:00.000000'),
(103, 'pbkdf2_sha256$1500000$e8oAzwXBBS2bIj2a3uheL4$YqR/wnXyDzMCrq23SWOeZv9nhIv/3/GP/b0etAEdwXM=', NULL, 0, 'bruno_demo', 'Bruno', 'Soto', 'bruno.demo@example.com', 0, 1, '2026-08-10 15:00:00.000000'),
(104, 'pbkdf2_sha256$1500000$e8oAzwXBBS2bIj2a3uheL4$YqR/wnXyDzMCrq23SWOeZv9nhIv/3/GP/b0etAEdwXM=', NULL, 0, 'carla_demo', 'Carla', 'Fuentes', 'carla.demo@example.com', 0, 1, '2026-08-15 16:00:00.000000'),
(105, 'pbkdf2_sha256$1500000$e8oAzwXBBS2bIj2a3uheL4$YqR/wnXyDzMCrq23SWOeZv9nhIv/3/GP/b0etAEdwXM=', NULL, 0, 'diego_demo', 'Diego', 'Contreras', 'diego.demo@example.com', 0, 0, '2026-08-20 17:00:00.000000');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auth_user_groups`
--

CREATE TABLE `auth_user_groups` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auth_user_user_permissions`
--

CREATE TABLE `auth_user_user_permissions` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cowork_espacio`
--

CREATE TABLE `cowork_espacio` (
  `id` bigint(20) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `descripcion_publica` longtext NOT NULL,
  `capacidad` int(10) UNSIGNED NOT NULL CHECK (`capacidad` >= 0),
  `sede_id` bigint(20) NOT NULL,
  `tipo_id` bigint(20) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `observaciones_privadas` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL
) ;

--
-- Volcado de datos para la tabla `cowork_espacio`
--

INSERT INTO `cowork_espacio` (`id`, `nombre`, `descripcion_publica`, `capacidad`, `sede_id`, `tipo_id`, `estado`, `observaciones_privadas`, `created_at`, `updated_at`) VALUES
(101, 'Sala Andes', 'Sala con pantalla de 65\" y videoconferencia.', 8, 1, 4, 'disponible', 'Control remoto en recepción.', '2026-10-15 18:26:47.456009', '2026-10-15 18:26:47.511393'),
(102, 'Sala Pacífico', 'Sala pequeña para reuniones rápidas.', 4, 1, 4, 'disponible', '', '2026-10-15 18:26:47.456009', '2026-10-15 18:26:47.511393'),
(103, 'Oficina 201', 'Oficina privada con ventana y pizarra.', 5, 2, 3, 'disponible', 'Llave en conserjería, piso 2.', '2026-10-15 18:26:47.456009', '2026-10-15 18:26:47.511393'),
(104, 'Zona abierta A', 'Área de escritorios compartidos con casilleros.', 20, 2, 1, 'disponible', '', '2026-10-15 18:26:47.456009', '2026-10-15 18:26:47.511393'),
(105, 'Cabina 1', 'Cabina insonorizada para llamadas.', 1, 1, 5, 'disponible', '', '2026-10-15 18:26:47.456009', '2026-10-15 18:26:47.511393'),
(106, 'Auditorio Costa', 'Espacio para talleres con proyector y sonido.', 40, 3, 6, 'disponible', 'Solicitar técnico con 48 h de anticipación.', '2026-10-15 18:26:47.456009', '2026-10-15 18:26:47.511393'),
(107, 'Escritorio 12', 'Escritorio fijo junto a la ventana.', 1, 3, 2, 'mantenimiento', 'Cambio de silla pendiente.', '2026-10-15 18:26:47.456009', '2026-10-15 18:26:47.511393'),
(108, 'Sala Biobío', 'Sala de reuniones de la sede Concepción.', 6, 4, 4, 'inactivo', 'Fuera de servicio por remodelación.', '2026-10-15 18:26:47.456009', '2026-10-15 18:26:47.511393');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cowork_eventoauditoria`
--

CREATE TABLE `cowork_eventoauditoria` (
  `id` bigint(20) NOT NULL,
  `fecha` datetime(6) NOT NULL,
  `accion` varchar(80) NOT NULL,
  `tipo_entidad` varchar(80) NOT NULL,
  `id_entidad` bigint(20) UNSIGNED NOT NULL CHECK (`id_entidad` >= 0),
  `valores_anteriores` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`valores_anteriores`)),
  `valores_nuevos` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`valores_nuevos`)),
  `actor_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `cowork_eventoauditoria`
--

INSERT INTO `cowork_eventoauditoria` (`id`, `fecha`, `accion`, `tipo_entidad`, `id_entidad`, `valores_anteriores`, `valores_nuevos`, `actor_id`) VALUES
(1, '2026-10-16 16:33:58.940711', 'crear', 'reserva', 113, '{}', '{\"id\": 113, \"usuario_id\": 104, \"espacio_id\": 101, \"inicio\": \"2026-10-16T17:33:00Z\", \"fin\": \"2026-10-16T19:33:00Z\", \"cantidad_personas\": 1, \"estado\": \"pendiente\", \"fecha_creacion\": \"2026-10-16T16:33:58.935Z\", \"updated_at\": \"2026-10-16T16:33:58.935Z\", \"observaciones\": \"\", \"motivo_cancelacion\": \"\"}', 101),
(2, '2026-10-16 16:34:01.995099', 'confirmar_reserva', 'reserva', 113, '{\"id\": 113, \"usuario_id\": 104, \"espacio_id\": 101, \"inicio\": \"2026-10-16T17:33:00Z\", \"fin\": \"2026-10-16T19:33:00Z\", \"cantidad_personas\": 1, \"estado\": \"pendiente\", \"fecha_creacion\": \"2026-10-16T16:33:58.935Z\", \"updated_at\": \"2026-10-16T16:33:58.935Z\", \"observaciones\": \"\", \"motivo_cancelacion\": \"\"}', '{\"id\": 113, \"usuario_id\": 104, \"espacio_id\": 101, \"inicio\": \"2026-10-16T17:33:00Z\", \"fin\": \"2026-10-16T19:33:00Z\", \"cantidad_personas\": 1, \"estado\": \"confirmada\", \"fecha_creacion\": \"2026-10-16T16:33:58.935Z\", \"updated_at\": \"2026-10-16T16:33:58.935Z\", \"observaciones\": \"\", \"motivo_cancelacion\": \"\"}', 101);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cowork_historialestadoreserva`
--

CREATE TABLE `cowork_historialestadoreserva` (
  `id` bigint(20) NOT NULL,
  `estado_anterior` varchar(20) NOT NULL,
  `estado_nuevo` varchar(20) NOT NULL,
  `fecha_cambio` datetime(6) NOT NULL,
  `motivo` longtext NOT NULL,
  `reserva_id` bigint(20) NOT NULL,
  `responsable_id` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `cowork_historialestadoreserva`
--

INSERT INTO `cowork_historialestadoreserva` (`id`, `estado_anterior`, `estado_nuevo`, `fecha_cambio`, `motivo`, `reserva_id`, `responsable_id`) VALUES
(101, '', 'pendiente', '2026-10-10 13:00:00.000000', 'Creación de la reserva', 101, 102),
(102, '', 'pendiente', '2026-10-10 14:00:00.000000', 'Creación de la reserva', 102, 103),
(103, 'pendiente', 'confirmada', '2026-10-11 12:00:00.000000', '', 102, 101),
(104, '', 'pendiente', '2026-10-09 18:00:00.000000', 'Creación de la reserva', 103, 104),
(105, 'pendiente', 'confirmada', '2026-10-10 12:30:00.000000', '', 103, 101),
(106, '', 'pendiente', '2026-10-08 15:00:00.000000', 'Creación de la reserva', 104, 102),
(107, 'pendiente', 'cancelada', '2026-10-09 11:00:00.000000', 'La llamada se reprogramó.', 104, 102),
(108, '', 'pendiente', '2026-10-12 19:00:00.000000', 'Creación de la reserva', 105, 103),
(109, '', 'pendiente', '2026-10-12 20:00:00.000000', 'Creación de la reserva', 106, 104),
(110, '', 'pendiente', '2026-10-11 13:00:00.000000', 'Creación de la reserva', 107, 102),
(111, 'pendiente', 'confirmada', '2026-10-11 15:00:00.000000', '', 107, 101),
(112, '', 'pendiente', '2026-09-25 13:00:00.000000', 'Creación de la reserva', 108, 102),
(113, 'pendiente', 'confirmada', '2026-09-26 12:00:00.000000', '', 108, 101),
(114, 'confirmada', 'finalizada', '2026-10-01 15:30:00.000000', '', 108, 101),
(115, '', 'pendiente', '2026-09-30 12:00:00.000000', 'Creación de la reserva', 109, 103),
(116, 'pendiente', 'confirmada', '2026-09-30 14:00:00.000000', '', 109, 101),
(117, 'confirmada', 'finalizada', '2026-10-05 21:30:00.000000', '', 109, 101),
(118, '', 'pendiente', '2026-10-01 13:00:00.000000', 'Creación de la reserva', 110, 104),
(119, 'pendiente', 'confirmada', '2026-10-02 12:00:00.000000', '', 110, 101),
(120, 'confirmada', 'cancelada', '2026-10-06 21:00:00.000000', 'Corte de energía programado en la sede.', 110, 101),
(121, '', 'pendiente', '2026-09-10 13:00:00.000000', 'Creación de la reserva', 111, 105),
(122, 'pendiente', 'confirmada', '2026-09-10 15:00:00.000000', '', 111, 101),
(123, 'confirmada', 'finalizada', '2026-09-15 14:30:00.000000', '', 111, 101),
(124, '', 'pendiente', '2026-10-02 18:00:00.000000', 'Creación de la reserva', 112, 103),
(125, 'pendiente', 'confirmada', '2026-10-03 12:00:00.000000', '', 112, 101),
(126, 'confirmada', 'finalizada', '2026-10-08 16:15:00.000000', '', 112, 101),
(127, '', 'pendiente', '2026-10-16 16:33:58.936936', 'Creación de la reserva', 113, 101),
(128, 'pendiente', 'confirmada', '2026-10-16 16:34:01.993656', '', 113, 101);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cowork_reserva`
--

CREATE TABLE `cowork_reserva` (
  `id` bigint(20) NOT NULL,
  `inicio` datetime(6) NOT NULL,
  `fin` datetime(6) NOT NULL,
  `cantidad_personas` int(10) UNSIGNED NOT NULL CHECK (`cantidad_personas` >= 0),
  `estado` varchar(20) NOT NULL,
  `fecha_creacion` datetime(6) NOT NULL,
  `observaciones` longtext NOT NULL,
  `espacio_id` bigint(20) NOT NULL,
  `usuario_id` bigint(20) NOT NULL,
  `motivo_cancelacion` longtext NOT NULL,
  `updated_at` datetime(6) NOT NULL
) ;

--
-- Volcado de datos para la tabla `cowork_reserva`
--

INSERT INTO `cowork_reserva` (`id`, `inicio`, `fin`, `cantidad_personas`, `estado`, `fecha_creacion`, `observaciones`, `espacio_id`, `usuario_id`, `motivo_cancelacion`, `updated_at`) VALUES
(101, '2026-11-03 12:00:00.000000', '2026-11-03 14:00:00.000000', 6, 'pendiente', '2026-10-10 13:00:00.000000', 'Reunión de planificación.', 101, 102, '', '2026-10-15 18:26:47.571753'),
(102, '2026-11-03 14:00:00.000000', '2026-11-03 15:00:00.000000', 4, 'confirmada', '2026-10-10 14:00:00.000000', '', 101, 103, '', '2026-10-15 18:26:47.571753'),
(103, '2026-11-05 13:00:00.000000', '2026-11-05 20:00:00.000000', 3, 'confirmada', '2026-10-09 18:00:00.000000', 'Jornada de trabajo del equipo.', 103, 104, '', '2026-10-15 18:26:47.571753'),
(104, '2026-11-04 18:00:00.000000', '2026-11-04 18:30:00.000000', 1, 'cancelada', '2026-10-08 15:00:00.000000', '', 105, 102, 'La llamada se reprogramó.', '2026-10-15 18:26:47.571753'),
(105, '2026-11-20 21:00:00.000000', '2026-11-21 00:00:00.000000', 30, 'pendiente', '2026-10-12 19:00:00.000000', 'Taller de emprendimiento.', 106, 103, '', '2026-10-15 18:26:47.571753'),
(106, '2026-11-10 12:00:00.000000', '2026-11-10 13:00:00.000000', 2, 'pendiente', '2026-10-12 20:00:00.000000', '', 102, 104, '', '2026-10-15 18:26:47.571753'),
(107, '2026-10-15 12:00:00.000000', '2026-10-15 16:00:00.000000', 1, 'confirmada', '2026-10-11 13:00:00.000000', '', 104, 102, '', '2026-10-15 18:26:47.571753'),
(108, '2026-10-01 12:00:00.000000', '2026-10-01 15:00:00.000000', 5, 'finalizada', '2026-09-25 13:00:00.000000', 'Presentación a clientes.', 101, 102, '', '2026-10-15 18:26:47.571753'),
(109, '2026-10-05 11:00:00.000000', '2026-10-05 21:00:00.000000', 1, 'finalizada', '2026-09-30 12:00:00.000000', '', 104, 103, '', '2026-10-15 18:26:47.571753'),
(110, '2026-10-07 17:00:00.000000', '2026-10-07 19:00:00.000000', 2, 'cancelada', '2026-10-01 13:00:00.000000', '', 103, 104, 'Corte de energía programado en la sede.', '2026-10-15 18:26:47.571753'),
(111, '2026-09-15 13:00:00.000000', '2026-09-15 14:00:00.000000', 2, 'finalizada', '2026-09-10 13:00:00.000000', '', 102, 105, '', '2026-10-15 18:26:47.571753'),
(112, '2026-10-08 12:00:00.000000', '2026-10-08 16:00:00.000000', 4, 'finalizada', '2026-10-02 18:00:00.000000', '', 103, 103, '', '2026-10-15 18:26:47.571753'),
(113, '2026-10-16 17:33:00.000000', '2026-10-16 19:33:00.000000', 1, 'confirmada', '2026-10-16 16:33:58.935428', '', 101, 104, '', '2026-10-16 16:33:58.935456');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cowork_sede`
--

CREATE TABLE `cowork_sede` (
  `id` bigint(20) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `direccion` varchar(255) NOT NULL,
  `ciudad` varchar(120) NOT NULL,
  `activa` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `cowork_sede`
--

INSERT INTO `cowork_sede` (`id`, `nombre`, `direccion`, `ciudad`, `activa`, `created_at`, `updated_at`) VALUES
(1, 'Sede Centro', 'Av. Libertador Bernardo O\'Higgins 1234', 'Santiago', 1, '2026-10-15 18:26:47.626761', '2026-10-15 18:26:47.683836'),
(2, 'Sede Providencia', 'Av. Providencia 2150', 'Providencia', 1, '2026-10-15 18:26:47.626761', '2026-10-15 18:26:47.683836'),
(3, 'Sede Viña del Mar', 'Av. Libertad 1050', 'Viña del Mar', 1, '2026-10-15 18:26:47.626761', '2026-10-15 18:26:47.683836'),
(4, 'Sede Concepción', 'Calle Barros Arana 800', 'Concepción', 1, '2026-10-15 18:26:47.626761', '2026-10-15 18:26:47.683836');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cowork_tipoespacio`
--

CREATE TABLE `cowork_tipoespacio` (
  `id` bigint(20) NOT NULL,
  `nombre` varchar(80) NOT NULL,
  `descripcion` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `cowork_tipoespacio`
--

INSERT INTO `cowork_tipoespacio` (`id`, `nombre`, `descripcion`, `created_at`, `updated_at`) VALUES
(1, 'Escritorio compartido', 'Puesto de trabajo libre en un área abierta, sin ubicación asignada.', '2026-10-15 18:26:47.735296', '2026-10-15 18:26:47.786873'),
(2, 'Escritorio fijo', 'Puesto de trabajo asignado en un área abierta.', '2026-10-15 18:26:47.735296', '2026-10-15 18:26:47.786873'),
(3, 'Oficina privada', 'Oficina cerrada para equipos pequeños.', '2026-10-15 18:26:47.735296', '2026-10-15 18:26:47.786873'),
(4, 'Sala de reuniones', 'Sala cerrada con mesa, pantalla y videoconferencia.', '2026-10-15 18:26:47.735296', '2026-10-15 18:26:47.786873'),
(5, 'Cabina telefónica', 'Cabina individual para llamadas y videollamadas.', '2026-10-15 18:26:47.735296', '2026-10-15 18:26:47.786873'),
(6, 'Sala de eventos', 'Espacio amplio para talleres, charlas y presentaciones.', '2026-10-15 18:26:47.735296', '2026-10-15 18:26:47.786873');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cowork_usuario`
--

CREATE TABLE `cowork_usuario` (
  `id` bigint(20) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `apellido` varchar(150) NOT NULL,
  `correo` varchar(254) NOT NULL,
  `rol` varchar(20) NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `fecha_registro` datetime(6) NOT NULL,
  `cuenta_id` int(11) NOT NULL,
  `updated_at` datetime(6) NOT NULL
) ;

--
-- Volcado de datos para la tabla `cowork_usuario`
--

INSERT INTO `cowork_usuario` (`id`, `nombre`, `apellido`, `correo`, `rol`, `activo`, `fecha_registro`, `cuenta_id`, `updated_at`) VALUES
(101, 'Valentina', 'Rojas', 'admin.demo@example.com', 'ADMINISTRADOR', 1, '2026-08-01 13:00:00.000000', 101, '2026-10-15 18:26:47.850892'),
(102, 'Ana', 'Muñoz', 'ana.demo@example.com', 'MIEMBRO', 1, '2026-08-05 14:00:00.000000', 102, '2026-10-15 18:26:47.850892'),
(103, 'Bruno', 'Soto', 'bruno.demo@example.com', 'MIEMBRO', 1, '2026-08-10 15:00:00.000000', 103, '2026-10-15 18:26:47.850892'),
(104, 'Carla', 'Fuentes', 'carla.demo@example.com', 'MIEMBRO', 1, '2026-08-15 16:00:00.000000', 104, '2026-10-15 18:26:47.850892'),
(105, 'Diego', 'Contreras', 'diego.demo@example.com', 'MIEMBRO', 0, '2026-08-20 17:00:00.000000', 105, '2026-10-15 18:26:47.850892');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `django_admin_log`
--

CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) UNSIGNED NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `django_content_type`
--

CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `django_content_type`
--

INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
(1, 'admin', 'logentry'),
(2, 'auth', 'group'),
(3, 'auth', 'permission'),
(4, 'auth', 'user'),
(5, 'contenttypes', 'contenttype'),
(7, 'cowork', 'administrador'),
(8, 'cowork', 'espacio'),
(9, 'cowork', 'eventoauditoria'),
(10, 'cowork', 'historialestadoreserva'),
(11, 'cowork', 'reserva'),
(12, 'cowork', 'sede'),
(13, 'cowork', 'tipoespacio'),
(14, 'cowork', 'usuario'),
(6, 'sessions', 'session');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `django_migrations`
--

CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `django_migrations`
--

INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES
(1, 'contenttypes', '0001_initial', '2026-10-13 16:32:39.199195'),
(2, 'auth', '0001_initial', '2026-10-13 16:32:40.099537'),
(3, 'admin', '0001_initial', '2026-10-13 16:32:40.285956'),
(4, 'admin', '0002_logentry_remove_auto_add', '2026-10-13 16:32:40.299989'),
(5, 'admin', '0003_logentry_add_action_flag_choices', '2026-10-13 16:32:40.310657'),
(6, 'contenttypes', '0002_remove_content_type_name', '2026-10-13 16:32:40.442622'),
(7, 'auth', '0002_alter_permission_name_max_length', '2026-10-13 16:32:40.530031'),
(8, 'auth', '0003_alter_user_email_max_length', '2026-10-13 16:32:40.591768'),
(9, 'auth', '0004_alter_user_username_opts', '2026-10-13 16:32:40.608258'),
(10, 'auth', '0005_alter_user_last_login_null', '2026-10-13 16:32:40.688996'),
(11, 'auth', '0006_require_contenttypes_0002', '2026-10-13 16:32:40.694846'),
(12, 'auth', '0007_alter_validators_add_error_messages', '2026-10-13 16:32:40.709653'),
(13, 'auth', '0008_alter_user_username_max_length', '2026-10-13 16:32:40.762367'),
(14, 'auth', '0009_alter_user_last_name_max_length', '2026-10-13 16:32:40.827226'),
(15, 'auth', '0010_alter_group_name_max_length', '2026-10-13 16:32:40.892333'),
(16, 'auth', '0011_update_proxy_permissions', '2026-10-13 16:32:40.909545'),
(17, 'auth', '0012_alter_user_first_name_max_length', '2026-10-13 16:32:40.966096'),
(18, 'cowork', '0001_sede_y_tipo_espacio', '2026-10-13 16:32:41.024600'),
(19, 'cowork', '0002_espacio_y_reserva', '2026-10-13 16:32:41.708523'),
(20, 'cowork', '0003_renombrar_campos_diagrama', '2026-10-13 16:32:41.839460'),
(21, 'cowork', '0004_modelos_diagrama', '2026-10-13 16:32:43.151884'),
(22, 'cowork', '0004_interaccion_del_usuario', '2026-10-13 16:32:43.156876'),
(23, 'cowork', '0005_administrador_diagrama', '2026-10-13 16:32:43.164916'),
(24, 'sessions', '0001_initial', '2026-10-13 16:32:43.251346'),
(26, 'cowork', '0006_fechas_creacion_actualizacion', '2026-10-15 18:26:47.903499');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `django_session`
--

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `django_session`
--

INSERT INTO `django_session` (`session_key`, `session_data`, `expire_date`) VALUES
('ebrfg9f4hf8rnet4awjn66fx9g86fkh8', '.eJxVjEEOwiAQAP-yZ0PoIrD06L1vIAsstmrapLQn499Nkx70OjOZN0TetzHuTdY4Feih0wiXX5o4P2U-VHnwfF9UXuZtnZI6EnXapoalyOt2tn-DkdsIPQg6dDWheNQ2S5CKXC2SGH0l7jR5nYIlj2K9E1MdmxRMLY4644kJPl8hTTe8:1xGjOQ:0-05Qc543mTRENHsBWxIZcTv3HDef1PDRWDuWYKrp68', '2026-10-27 20:46:38.554701'),
('pybd1ojl5smke14vxgboskdtfsg417le', '.eJxVjEEOwiAQAP-yZ0NgEdj26L1vaJay2KqBpLQn499Nkx70OjOZN4y8b_O4N1nHJUEPRhu4_NLI01PKodKDy72qqZZtXaI6EnXapoaa5HU727_BzG2GHgQ9-hxRAmo3SScZOTsksfpKbDQFHTtHAcUFLzZ7trGzOXkyNhATfL4gtDe7:1xGkCx:DVqxzTm2Pf8hAKPE0vJWjfVP2y6eWsI4rbQdgiHrHlE', '2026-10-27 21:38:51.964577');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `auth_group`
--
ALTER TABLE `auth_group`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indices de la tabla `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  ADD KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`);

--
-- Indices de la tabla `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`);

--
-- Indices de la tabla `auth_user`
--
ALTER TABLE `auth_user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indices de la tabla `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  ADD KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`);

--
-- Indices de la tabla `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  ADD KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`);

--
-- Indices de la tabla `cowork_espacio`
--
ALTER TABLE `cowork_espacio`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `espacio_nombre_unico_por_sede` (`sede_id`,`nombre`),
  ADD KEY `cowork_espacio_tipo_id_908c32ea_fk_cowork_tipoespacio_id` (`tipo_id`);

--
-- Indices de la tabla `cowork_eventoauditoria`
--
ALTER TABLE `cowork_eventoauditoria`
  ADD PRIMARY KEY (`id`),
  ADD KEY `cowork_eventoauditoria_actor_id_69e243bb_fk_cowork_usuario_id` (`actor_id`);

--
-- Indices de la tabla `cowork_historialestadoreserva`
--
ALTER TABLE `cowork_historialestadoreserva`
  ADD PRIMARY KEY (`id`),
  ADD KEY `cowork_historialesta_reserva_id_e6edce92_fk_cowork_re` (`reserva_id`),
  ADD KEY `cowork_historialesta_responsable_id_f7a50143_fk_cowork_us` (`responsable_id`);

--
-- Indices de la tabla `cowork_reserva`
--
ALTER TABLE `cowork_reserva`
  ADD PRIMARY KEY (`id`),
  ADD KEY `cowork_reserva_usuario_id_357bac53_fk_cowork_usuario_id` (`usuario_id`),
  ADD KEY `reserva_disponibilidad_idx` (`espacio_id`,`estado`,`inicio`,`fin`);

--
-- Indices de la tabla `cowork_sede`
--
ALTER TABLE `cowork_sede`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `cowork_tipoespacio`
--
ALTER TABLE `cowork_tipoespacio`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nombre` (`nombre`);

--
-- Indices de la tabla `cowork_usuario`
--
ALTER TABLE `cowork_usuario`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `correo` (`correo`),
  ADD UNIQUE KEY `cuenta_id` (`cuenta_id`);

--
-- Indices de la tabla `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  ADD KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`);

--
-- Indices de la tabla `django_content_type`
--
ALTER TABLE `django_content_type`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`);

--
-- Indices de la tabla `django_migrations`
--
ALTER TABLE `django_migrations`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `django_session`
--
ALTER TABLE `django_session`
  ADD PRIMARY KEY (`session_key`),
  ADD KEY `django_session_expire_date_a5c62663` (`expire_date`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `auth_group`
--
ALTER TABLE `auth_group`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `auth_permission`
--
ALTER TABLE `auth_permission`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=57;

--
-- AUTO_INCREMENT de la tabla `auth_user`
--
ALTER TABLE `auth_user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=106;

--
-- AUTO_INCREMENT de la tabla `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `cowork_espacio`
--
ALTER TABLE `cowork_espacio`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `cowork_eventoauditoria`
--
ALTER TABLE `cowork_eventoauditoria`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `cowork_historialestadoreserva`
--
ALTER TABLE `cowork_historialestadoreserva`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=129;

--
-- AUTO_INCREMENT de la tabla `cowork_reserva`
--
ALTER TABLE `cowork_reserva`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `cowork_sede`
--
ALTER TABLE `cowork_sede`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `cowork_tipoespacio`
--
ALTER TABLE `cowork_tipoespacio`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `cowork_usuario`
--
ALTER TABLE `cowork_usuario`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `django_admin_log`
--
ALTER TABLE `django_admin_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `django_content_type`
--
ALTER TABLE `django_content_type`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `django_migrations`
--
ALTER TABLE `django_migrations`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=27;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `auth_group_permissions`
--
ALTER TABLE `auth_group_permissions`
  ADD CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

--
-- Filtros para la tabla `auth_permission`
--
ALTER TABLE `auth_permission`
  ADD CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);

--
-- Filtros para la tabla `auth_user_groups`
--
ALTER TABLE `auth_user_groups`
  ADD CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  ADD CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Filtros para la tabla `auth_user_user_permissions`
--
ALTER TABLE `auth_user_user_permissions`
  ADD CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  ADD CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

--
-- Filtros para la tabla `cowork_espacio`
--
ALTER TABLE `cowork_espacio`
  ADD CONSTRAINT `cowork_espacio_sede_id_2d813e98_fk_cowork_sede_id` FOREIGN KEY (`sede_id`) REFERENCES `cowork_sede` (`id`),
  ADD CONSTRAINT `cowork_espacio_tipo_id_908c32ea_fk_cowork_tipoespacio_id` FOREIGN KEY (`tipo_id`) REFERENCES `cowork_tipoespacio` (`id`);

--
-- Filtros para la tabla `cowork_eventoauditoria`
--
ALTER TABLE `cowork_eventoauditoria`
  ADD CONSTRAINT `cowork_eventoauditoria_actor_id_69e243bb_fk_cowork_usuario_id` FOREIGN KEY (`actor_id`) REFERENCES `cowork_usuario` (`id`);

--
-- Filtros para la tabla `cowork_historialestadoreserva`
--
ALTER TABLE `cowork_historialestadoreserva`
  ADD CONSTRAINT `cowork_historialesta_reserva_id_e6edce92_fk_cowork_re` FOREIGN KEY (`reserva_id`) REFERENCES `cowork_reserva` (`id`),
  ADD CONSTRAINT `cowork_historialesta_responsable_id_f7a50143_fk_cowork_us` FOREIGN KEY (`responsable_id`) REFERENCES `cowork_usuario` (`id`);

--
-- Filtros para la tabla `cowork_reserva`
--
ALTER TABLE `cowork_reserva`
  ADD CONSTRAINT `cowork_reserva_espacio_id_bda80dc7_fk_cowork_espacio_id` FOREIGN KEY (`espacio_id`) REFERENCES `cowork_espacio` (`id`),
  ADD CONSTRAINT `cowork_reserva_usuario_id_357bac53_fk_cowork_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `cowork_usuario` (`id`);

--
-- Filtros para la tabla `cowork_usuario`
--
ALTER TABLE `cowork_usuario`
  ADD CONSTRAINT `cowork_usuario_cuenta_id_bbc569e7_fk_auth_user_id` FOREIGN KEY (`cuenta_id`) REFERENCES `auth_user` (`id`);

--
-- Filtros para la tabla `django_admin_log`
--
ALTER TABLE `django_admin_log`
  ADD CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  ADD CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
