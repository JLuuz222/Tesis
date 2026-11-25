-- =====================================================================
-- TESIS2026 - Sistema de gestión de tareas interdepartamentales (Pintegral)
-- DER v3 - Script de creación de la base de datos (MySQL 8.4 LTS)
-- Probado en MySQL 8.4.2 y 8.0.46.
-- Incluye la migración 001 (legajo CHAR(5) y dominios de email).
--
-- Convenciones:
--   * Nombres de tablas y columnas en singular, minúscula y snake_case.
--   * Toda PK es "id_<tabla>" INT AUTO_INCREMENT.
--   * Toda FK se llama igual que la PK a la que apunta (o lleva un sufijo
--     que explica el rol: id_usuario_creador, id_usuario_destino, etc.).
--   * Motor InnoDB (soporta claves foráneas y transacciones).
--   * Juego de caracteres utf8mb4 (acentos, ñ y emojis sin problemas).
-- =====================================================================

-- Le avisa a MySQL que este archivo está en UTF-8. Sin esto, si el script
-- se ejecuta desde una consola que usa otra codificación, los acentos se
-- guardan mal ("Jefe de Ã¡rea" en vez de "Jefe de área").
SET NAMES utf8mb4;

DROP DATABASE IF EXISTS tesis2026;
CREATE DATABASE tesis2026
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
USE tesis2026;

-- ---------------------------------------------------------------------
-- 1. SEGURIDAD Y ORGANIZACIÓN
-- ---------------------------------------------------------------------

-- Roles del sistema: definen QUÉ puede hacer un usuario (permisos).
CREATE TABLE rol (
    id_rol        INT          NOT NULL AUTO_INCREMENT,
    nombre        VARCHAR(50)  NOT NULL,
    descripcion   VARCHAR(255) NULL,
    PRIMARY KEY (id_rol),
    UNIQUE KEY uq_rol_nombre (nombre)
) ENGINE=InnoDB;

-- Áreas de la empresa (Compras, Ventas, Stock...).
-- id_usuario_jefe se enlaza más abajo con ALTER TABLE porque usuario
-- todavía no existe (referencia circular usuario <-> departamento).
CREATE TABLE departamento (
    id_departamento   INT          NOT NULL AUTO_INCREMENT,
    nombre            VARCHAR(100) NOT NULL,
    codigo            VARCHAR(20)  NOT NULL,
    descripcion       VARCHAR(255) NULL,
    id_usuario_jefe   INT          NULL,
    email_contacto    VARCHAR(100) NULL,
    telefono_contacto VARCHAR(20)  NULL,
    activo            TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (id_departamento),
    UNIQUE KEY uq_departamento_nombre (nombre),
    UNIQUE KEY uq_departamento_codigo (codigo)
) ENGINE=InnoDB;

-- Puestos de trabajo: definen QUÉ HACE un usuario en la empresa
-- (Encargado de depósito, Operario de atención...). Los manuales se
-- publican por puesto.
CREATE TABLE puesto (
    id_puesto        INT          NOT NULL AUTO_INCREMENT,
    nombre           VARCHAR(100) NOT NULL,
    descripcion      VARCHAR(255) NULL,
    id_departamento  INT          NOT NULL,
    PRIMARY KEY (id_puesto),
    UNIQUE KEY uq_puesto_nombre_depto (nombre, id_departamento),
    CONSTRAINT fk_puesto_departamento FOREIGN KEY (id_departamento)
        REFERENCES departamento (id_departamento)
) ENGINE=InnoDB;

CREATE TABLE usuario (
    id_usuario        INT          NOT NULL AUTO_INCREMENT,
    nombre            VARCHAR(100) NOT NULL,
    apellido          VARCHAR(100) NOT NULL,
    email             VARCHAR(100) NOT NULL,
    password_hash     VARCHAR(255) NOT NULL,
    numero_legajo     CHAR(5)      NOT NULL,
    id_rol            INT          NOT NULL,
    id_departamento   INT          NOT NULL,
    id_puesto         INT          NULL,
    fecha_nacimiento  DATE         NULL,
    direccion         VARCHAR(255) NULL,
    telefono          VARCHAR(20)  NULL,
    fecha_ingreso     DATE         NULL,
    activo            TINYINT(1)   NOT NULL DEFAULT 1,
    ultimo_acceso     DATETIME     NULL,
    fecha_alta        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario),
    UNIQUE KEY uq_usuario_email (email),
    UNIQUE KEY uq_usuario_legajo (numero_legajo),
    -- Legajo: exactamente 5 dígitos ("00005") y distinto de "00000".
    CONSTRAINT ck_usuario_legajo CHECK (numero_legajo REGEXP '^[0-9]{5}$' AND numero_legajo <> '00000'),
    CONSTRAINT fk_usuario_rol FOREIGN KEY (id_rol)
        REFERENCES rol (id_rol),
    CONSTRAINT fk_usuario_departamento FOREIGN KEY (id_departamento)
        REFERENCES departamento (id_departamento),
    CONSTRAINT fk_usuario_puesto FOREIGN KEY (id_puesto)
        REFERENCES puesto (id_puesto)
) ENGINE=InnoDB;

-- Ahora que existe usuario, cerramos la referencia circular.
ALTER TABLE departamento
    ADD CONSTRAINT fk_departamento_jefe FOREIGN KEY (id_usuario_jefe)
        REFERENCES usuario (id_usuario);

-- ---------------------------------------------------------------------
-- 2. CATÁLOGOS (tablas de valores fijos)
-- ---------------------------------------------------------------------

CREATE TABLE estado_tarea (
    id_estado     INT          NOT NULL AUTO_INCREMENT,
    nombre        VARCHAR(50)  NOT NULL,
    descripcion   VARCHAR(255) NULL,
    color         VARCHAR(20)  NOT NULL,
    orden         INT          NOT NULL,
    es_final      TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (id_estado),
    UNIQUE KEY uq_estado_nombre (nombre)
) ENGINE=InnoDB;

CREATE TABLE prioridad (
    id_prioridad  INT          NOT NULL AUTO_INCREMENT,
    nombre        VARCHAR(20)  NOT NULL,
    nivel         INT          NOT NULL,
    color         VARCHAR(20)  NOT NULL,
    PRIMARY KEY (id_prioridad),
    UNIQUE KEY uq_prioridad_nombre (nombre),
    UNIQUE KEY uq_prioridad_nivel (nivel)
) ENGINE=InnoDB;

-- Parámetros configurables sin tocar código (umbral de carga, días
-- para archivar, horas de aviso antes del vencimiento...).
CREATE TABLE parametro (
    clave         VARCHAR(50)  NOT NULL,
    valor         VARCHAR(255) NOT NULL,
    descripcion   VARCHAR(255) NULL,
    PRIMARY KEY (clave)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. CALENDARIO (va antes de tarea porque una tarea puede nacer de una
--    reunión)
-- ---------------------------------------------------------------------

CREATE TABLE evento (
    id_evento                INT          NOT NULL AUTO_INCREMENT,
    titulo                   VARCHAR(100) NOT NULL,
    descripcion              VARCHAR(255) NULL,
    tipo                     ENUM('reunion','capacitacion','otro') NOT NULL DEFAULT 'reunion',
    fecha_inicio             DATETIME     NOT NULL,
    fecha_fin                DATETIME     NOT NULL,
    lugar                    VARCHAR(150) NULL,
    id_usuario_organizador   INT          NOT NULL,
    id_departamento_organizador INT       NOT NULL,
    fecha_creacion           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_evento),
    KEY ix_evento_fecha (fecha_inicio),
    CONSTRAINT ck_evento_fechas CHECK (fecha_fin > fecha_inicio),
    CONSTRAINT fk_evento_organizador FOREIGN KEY (id_usuario_organizador)
        REFERENCES usuario (id_usuario),
    CONSTRAINT fk_evento_departamento FOREIGN KEY (id_departamento_organizador)
        REFERENCES departamento (id_departamento)
) ENGINE=InnoDB;

CREATE TABLE evento_participante (
    id_evento             INT        NOT NULL,
    id_usuario            INT        NOT NULL,
    confirmacion          ENUM('pendiente','aceptada','rechazada') NOT NULL DEFAULT 'pendiente',
    recordatorio_enviado  TINYINT(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (id_evento, id_usuario),
    CONSTRAINT fk_participante_evento FOREIGN KEY (id_evento)
        REFERENCES evento (id_evento) ON DELETE CASCADE,
    CONSTRAINT fk_participante_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4. TAREAS (núcleo del sistema)
-- ---------------------------------------------------------------------

CREATE TABLE tarea (
    id_tarea            INT          NOT NULL AUTO_INCREMENT,
    titulo              VARCHAR(200) NOT NULL,
    descripcion         TEXT         NULL,
    id_prioridad        INT          NOT NULL,
    id_estado           INT          NOT NULL,
    id_departamento     INT          NOT NULL,
    id_usuario_creador  INT          NOT NULL,
    id_tarea_padre      INT          NULL,
    id_evento_origen    INT          NULL,
    fecha_creacion      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_vencimiento   DATETIME     NOT NULL,
    fecha_inicio        DATETIME     NULL,
    fecha_cierre        DATETIME     NULL,
    resultado           TEXT         NULL,
    archivada           TINYINT(1)   NOT NULL DEFAULT 0,
    fecha_archivado     DATETIME     NULL,
    PRIMARY KEY (id_tarea),
    KEY ix_tarea_vencimiento (fecha_vencimiento),
    KEY ix_tarea_archivada (archivada),
    CONSTRAINT fk_tarea_prioridad FOREIGN KEY (id_prioridad)
        REFERENCES prioridad (id_prioridad),
    CONSTRAINT fk_tarea_estado FOREIGN KEY (id_estado)
        REFERENCES estado_tarea (id_estado),
    CONSTRAINT fk_tarea_departamento FOREIGN KEY (id_departamento)
        REFERENCES departamento (id_departamento),
    CONSTRAINT fk_tarea_creador FOREIGN KEY (id_usuario_creador)
        REFERENCES usuario (id_usuario),
    CONSTRAINT fk_tarea_padre FOREIGN KEY (id_tarea_padre)
        REFERENCES tarea (id_tarea),
    CONSTRAINT fk_tarea_evento FOREIGN KEY (id_evento_origen)
        REFERENCES evento (id_evento)
) ENGINE=InnoDB;

-- Reemplaza a las tablas Asignaciones y usuario_tarea de la v2.
-- Una fila por cada vez que una tarea se asigna a alguien. La asignación
-- vigente es la que tiene activa = 1.
CREATE TABLE asignacion (
    id_asignacion         INT          NOT NULL AUTO_INCREMENT,
    id_tarea              INT          NOT NULL,
    id_usuario            INT          NOT NULL,
    id_usuario_asignador  INT          NULL,
    tipo                  ENUM('manual','automatica','delegacion') NOT NULL DEFAULT 'manual',
    fecha_asignacion      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin             DATETIME     NULL,
    activa                TINYINT(1)   NOT NULL DEFAULT 1,
    horas_dedicadas       DECIMAL(6,2) NOT NULL DEFAULT 0,
    PRIMARY KEY (id_asignacion),
    KEY ix_asignacion_usuario_activa (id_usuario, activa),
    CONSTRAINT fk_asignacion_tarea FOREIGN KEY (id_tarea)
        REFERENCES tarea (id_tarea),
    CONSTRAINT fk_asignacion_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario),
    CONSTRAINT fk_asignacion_asignador FOREIGN KEY (id_usuario_asignador)
        REFERENCES usuario (id_usuario)
) ENGINE=InnoDB;

-- HU21: el empleado pide delegar, el jefe de área aprueba o rechaza.
CREATE TABLE delegacion (
    id_delegacion         INT          NOT NULL AUTO_INCREMENT,
    id_tarea              INT          NOT NULL,
    id_usuario_origen     INT          NOT NULL,
    id_usuario_destino    INT          NOT NULL,
    id_usuario_aprobador  INT          NULL,
    motivo                VARCHAR(255) NOT NULL,
    estado                ENUM('pendiente','aprobada','rechazada') NOT NULL DEFAULT 'pendiente',
    fecha_solicitud       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_resolucion      DATETIME     NULL,
    PRIMARY KEY (id_delegacion),
    CONSTRAINT ck_delegacion_distintos CHECK (id_usuario_origen <> id_usuario_destino),
    CONSTRAINT fk_delegacion_tarea FOREIGN KEY (id_tarea)
        REFERENCES tarea (id_tarea),
    CONSTRAINT fk_delegacion_origen FOREIGN KEY (id_usuario_origen)
        REFERENCES usuario (id_usuario),
    CONSTRAINT fk_delegacion_destino FOREIGN KEY (id_usuario_destino)
        REFERENCES usuario (id_usuario),
    CONSTRAINT fk_delegacion_aprobador FOREIGN KEY (id_usuario_aprobador)
        REFERENCES usuario (id_usuario)
) ENGINE=InnoDB;

-- HU15: una tarea no puede empezar hasta que terminen sus predecesoras.
CREATE TABLE dependencia_tarea (
    id_tarea              INT NOT NULL,
    id_tarea_predecesora  INT NOT NULL,
    PRIMARY KEY (id_tarea, id_tarea_predecesora),
    CONSTRAINT ck_dependencia_distintas CHECK (id_tarea <> id_tarea_predecesora),
    CONSTRAINT fk_dependencia_tarea FOREIGN KEY (id_tarea)
        REFERENCES tarea (id_tarea) ON DELETE CASCADE,
    CONSTRAINT fk_dependencia_predecesora FOREIGN KEY (id_tarea_predecesora)
        REFERENCES tarea (id_tarea) ON DELETE CASCADE
) ENGINE=InnoDB;

-- HU22: etiquetas libres ("urgente", "en espera", "compras+marketing").
CREATE TABLE etiqueta (
    id_etiqueta         INT          NOT NULL AUTO_INCREMENT,
    nombre              VARCHAR(50)  NOT NULL,
    color               VARCHAR(20)  NOT NULL DEFAULT 'gris',
    id_usuario_creador  INT          NOT NULL,
    PRIMARY KEY (id_etiqueta),
    UNIQUE KEY uq_etiqueta_nombre (nombre),
    CONSTRAINT fk_etiqueta_creador FOREIGN KEY (id_usuario_creador)
        REFERENCES usuario (id_usuario)
) ENGINE=InnoDB;

CREATE TABLE tarea_etiqueta (
    id_tarea     INT NOT NULL,
    id_etiqueta  INT NOT NULL,
    PRIMARY KEY (id_tarea, id_etiqueta),
    CONSTRAINT fk_te_tarea FOREIGN KEY (id_tarea)
        REFERENCES tarea (id_tarea) ON DELETE CASCADE,
    CONSTRAINT fk_te_etiqueta FOREIGN KEY (id_etiqueta)
        REFERENCES etiqueta (id_etiqueta) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Historial de cambios de estado (HU03, HU11, Repo9).
CREATE TABLE historial_tarea (
    id_historial          INT          NOT NULL AUTO_INCREMENT,
    id_tarea              INT          NOT NULL,
    id_usuario            INT          NOT NULL,
    id_estado_anterior    INT          NULL,
    id_estado_nuevo       INT          NOT NULL,
    descripcion_cambio    VARCHAR(255) NULL,
    fecha_cambio          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_historial),
    KEY ix_historial_tarea_fecha (id_tarea, fecha_cambio),
    CONSTRAINT fk_historial_tarea FOREIGN KEY (id_tarea)
        REFERENCES tarea (id_tarea),
    CONSTRAINT fk_historial_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario),
    CONSTRAINT fk_historial_estado_ant FOREIGN KEY (id_estado_anterior)
        REFERENCES estado_tarea (id_estado),
    CONSTRAINT fk_historial_estado_nuevo FOREIGN KEY (id_estado_nuevo)
        REFERENCES estado_tarea (id_estado)
) ENGINE=InnoDB;

-- Comentarios y sugerencias sobre una tarea (HU03, HU23).
CREATE TABLE comentario (
    id_comentario  INT           NOT NULL AUTO_INCREMENT,
    id_tarea       INT           NOT NULL,
    id_usuario     INT           NOT NULL,
    tipo           ENUM('comentario','sugerencia','problema') NOT NULL DEFAULT 'comentario',
    texto          VARCHAR(1000) NOT NULL,
    fecha          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_comentario),
    KEY ix_comentario_tarea_fecha (id_tarea, fecha),
    CONSTRAINT fk_comentario_tarea FOREIGN KEY (id_tarea)
        REFERENCES tarea (id_tarea),
    CONSTRAINT fk_comentario_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 5. COMUNICACIÓN: soporte, alertas y notificaciones
-- ---------------------------------------------------------------------

-- HU09/HU10: un empleado pide ayuda a otra área. Si se acepta, se crea
-- una tarea para esa área (id_tarea_generada).
CREATE TABLE solicitud_soporte (
    id_solicitud              INT          NOT NULL AUTO_INCREMENT,
    id_usuario_solicitante    INT          NOT NULL,
    id_departamento_destino   INT          NOT NULL,
    id_usuario_responsable    INT          NULL,
    id_tarea_origen           INT          NULL,
    id_tarea_generada         INT          NULL,
    id_prioridad              INT          NOT NULL,
    tipo_soporte              VARCHAR(100) NOT NULL,
    descripcion               TEXT         NOT NULL,
    estado                    ENUM('pendiente','aceptada','rechazada','resuelta') NOT NULL DEFAULT 'pendiente',
    fecha_creacion            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_resolucion          DATETIME     NULL,
    PRIMARY KEY (id_solicitud),
    CONSTRAINT fk_soporte_solicitante FOREIGN KEY (id_usuario_solicitante)
        REFERENCES usuario (id_usuario),
    CONSTRAINT fk_soporte_departamento FOREIGN KEY (id_departamento_destino)
        REFERENCES departamento (id_departamento),
    CONSTRAINT fk_soporte_responsable FOREIGN KEY (id_usuario_responsable)
        REFERENCES usuario (id_usuario),
    CONSTRAINT fk_soporte_tarea_origen FOREIGN KEY (id_tarea_origen)
        REFERENCES tarea (id_tarea),
    CONSTRAINT fk_soporte_tarea_generada FOREIGN KEY (id_tarea_generada)
        REFERENCES tarea (id_tarea),
    CONSTRAINT fk_soporte_prioridad FOREIGN KEY (id_prioridad)
        REFERENCES prioridad (id_prioridad)
) ENGINE=InnoDB;

-- HU05/HU13: una alerta queda abierta hasta que alguien la atiende.
CREATE TABLE alerta (
    id_alerta               INT          NOT NULL AUTO_INCREMENT,
    id_tarea                INT          NOT NULL,
    id_usuario_destino      INT          NOT NULL,
    tipo                    ENUM('proxima_a_vencer','vencida','alta_prioridad','sin_actualizar') NOT NULL,
    mensaje                 VARCHAR(255) NOT NULL,
    fecha_generacion        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atendida                TINYINT(1)   NOT NULL DEFAULT 0,
    fecha_atencion          DATETIME     NULL,
    id_usuario_atencion     INT          NULL,
    PRIMARY KEY (id_alerta),
    KEY ix_alerta_destino_atendida (id_usuario_destino, atendida),
    CONSTRAINT fk_alerta_tarea FOREIGN KEY (id_tarea)
        REFERENCES tarea (id_tarea),
    CONSTRAINT fk_alerta_destino FOREIGN KEY (id_usuario_destino)
        REFERENCES usuario (id_usuario),
    CONSTRAINT fk_alerta_atencion FOREIGN KEY (id_usuario_atencion)
        REFERENCES usuario (id_usuario)
) ENGINE=InnoDB;

-- Bandeja de avisos de cada usuario (la "campanita").
CREATE TABLE notificacion (
    id_notificacion     INT          NOT NULL AUTO_INCREMENT,
    id_usuario_destino  INT          NOT NULL,
    id_usuario_emisor   INT          NULL,
    id_tarea            INT          NULL,
    tipo                ENUM('asignacion','vencimiento','retraso','alerta_critica','comentario',
                             'soporte','delegacion','manual','reunion','desbloqueo','prioridad') NOT NULL,
    mensaje             VARCHAR(255) NOT NULL,
    fecha_envio         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    leida               TINYINT(1)   NOT NULL DEFAULT 0,
    fecha_lectura       DATETIME     NULL,
    enviada_email       TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (id_notificacion),
    KEY ix_notificacion_destino_leida (id_usuario_destino, leida),
    CONSTRAINT fk_notificacion_destino FOREIGN KEY (id_usuario_destino)
        REFERENCES usuario (id_usuario),
    CONSTRAINT fk_notificacion_emisor FOREIGN KEY (id_usuario_emisor)
        REFERENCES usuario (id_usuario),
    CONSTRAINT fk_notificacion_tarea FOREIGN KEY (id_tarea)
        REFERENCES tarea (id_tarea)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 6. DOCUMENTOS Y MANUALES
--    Los archivos se guardan en disco; la base guarda la ruta.
-- ---------------------------------------------------------------------

-- Se llama manual_procedimiento y no "manual" porque MANUAL es palabra
-- reservada desde MySQL 8.4.
CREATE TABLE manual_procedimiento (
    id_manual           INT          NOT NULL AUTO_INCREMENT,
    titulo              VARCHAR(150) NOT NULL,
    tematica            VARCHAR(100) NULL,
    descripcion         VARCHAR(255) NULL,
    id_departamento     INT          NOT NULL,
    id_puesto           INT          NULL,
    version_actual      INT          NOT NULL DEFAULT 1,
    activo              TINYINT(1)   NOT NULL DEFAULT 1,
    id_usuario_creador  INT          NOT NULL,
    fecha_creacion      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_manual),
    CONSTRAINT fk_manual_departamento FOREIGN KEY (id_departamento)
        REFERENCES departamento (id_departamento),
    CONSTRAINT fk_manual_puesto FOREIGN KEY (id_puesto)
        REFERENCES puesto (id_puesto),
    CONSTRAINT fk_manual_creador FOREIGN KEY (id_usuario_creador)
        REFERENCES usuario (id_usuario)
) ENGINE=InnoDB;

-- HU07 criterio 2: cada actualización guarda una versión nueva.
CREATE TABLE manual_version (
    id_version          INT          NOT NULL AUTO_INCREMENT,
    id_manual           INT          NOT NULL,
    numero_version      INT          NOT NULL,
    nombre_archivo      VARCHAR(255) NOT NULL,
    ruta_archivo        VARCHAR(500) NOT NULL,
    tamanio_bytes       INT          NOT NULL,
    comentario_cambio   VARCHAR(255) NULL,
    id_usuario_carga    INT          NOT NULL,
    fecha_carga         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_version),
    UNIQUE KEY uq_manual_version (id_manual, numero_version),
    CONSTRAINT fk_version_manual FOREIGN KEY (id_manual)
        REFERENCES manual_procedimiento (id_manual),
    CONSTRAINT fk_version_usuario FOREIGN KEY (id_usuario_carga)
        REFERENCES usuario (id_usuario)
) ENGINE=InnoDB;

-- HU18: archivos adjuntos a una tarea (PDF, DOCX, XLSX; máx. 10 MB).
CREATE TABLE documento_tarea (
    id_documento        INT          NOT NULL AUTO_INCREMENT,
    id_tarea            INT          NOT NULL,
    nombre_original     VARCHAR(255) NOT NULL,
    ruta_archivo        VARCHAR(500) NOT NULL,
    tipo_mime           VARCHAR(100) NOT NULL,
    tamanio_bytes       INT          NOT NULL,
    id_usuario_carga    INT          NOT NULL,
    fecha_carga         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_documento),
    CONSTRAINT ck_documento_tamanio CHECK (tamanio_bytes <= 10485760),
    CONSTRAINT fk_documento_tarea FOREIGN KEY (id_tarea)
        REFERENCES tarea (id_tarea),
    CONSTRAINT fk_documento_usuario FOREIGN KEY (id_usuario_carga)
        REFERENCES usuario (id_usuario)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 7. REPORTES Y AUDITORÍA
-- ---------------------------------------------------------------------

-- Repo7 y Repo8: qué reportes se generaron/exportaron, quién y cuándo.
CREATE TABLE reporte_generado (
    id_reporte      INT          NOT NULL AUTO_INCREMENT,
    codigo_reporte  VARCHAR(10)  NOT NULL,
    id_usuario      INT          NOT NULL,
    formato         ENUM('pantalla','pdf','xlsx','csv') NOT NULL,
    parametros      JSON         NULL,
    fecha_generacion DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_reporte),
    CONSTRAINT fk_reporte_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario)
) ENGINE=InnoDB;

-- Registro de auditoría (req. no funcional): quién hizo qué y cuándo.
-- Sirve también para Repo1 (accesos), Repo2, Repo14 y Repo16 (consultas).
CREATE TABLE auditoria (
    id_auditoria  BIGINT       NOT NULL AUTO_INCREMENT,
    id_usuario    INT          NULL,
    accion        ENUM('login','logout','login_fallido','crear','modificar','eliminar',
                       'consultar','descargar','exportar') NOT NULL,
    entidad       VARCHAR(50)  NOT NULL,
    id_entidad    INT          NULL,
    detalle       VARCHAR(500) NULL,
    ip            VARCHAR(45)  NULL,
    fecha         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_auditoria),
    KEY ix_auditoria_usuario_fecha (id_usuario, fecha),
    KEY ix_auditoria_entidad (entidad, id_entidad),
    CONSTRAINT fk_auditoria_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario)
) ENGINE=InnoDB;

-- =====================================================================
-- DATOS SEMILLA (catálogos que el sistema necesita para arrancar)
-- =====================================================================

INSERT INTO rol (nombre, descripcion) VALUES
    ('Administrador', 'Gestiona usuarios, áreas y ve los reportes de toda la empresa'),
    ('Jefe de área',  'Crea, asigna y supervisa las tareas de su área'),
    ('Empleado',      'Ve y actualiza las tareas que tiene asignadas');

INSERT INTO estado_tarea (nombre, descripcion, color, orden, es_final) VALUES
    ('Pendiente',   'Creada, todavía no empezó',                 'gris',     1, 0),
    ('En progreso', 'El responsable está trabajando en ella',    'azul',     2, 0),
    ('Bloqueada',   'Espera que termine una tarea predecesora',  'naranja',  3, 0),
    ('Completada',  'Terminada por el responsable',              'verde',    4, 1),
    ('Cancelada',   'Se dio de baja antes de terminarse',        'rojo',     5, 1);

INSERT INTO prioridad (nombre, nivel, color) VALUES
    ('Baja',  1, 'verde'),
    ('Media', 2, 'amarillo'),
    ('Alta',  3, 'rojo');

INSERT INTO parametro (clave, valor, descripcion) VALUES
    ('horas_aviso_vencimiento', '24',  'HU05: horas antes del vencimiento para avisar'),
    ('dias_para_archivar',      '7',   'HU17: días desde que se completa hasta archivarla'),
    ('anios_retencion',         '2',   'Módulo 7: años que se conservan las tareas archivadas'),
    ('umbral_tareas_abiertas',  '10',  'HU20: tareas abiertas a partir de las cuales se marca sobrecarga'),
    ('horas_sin_actualizar',    '48',  'HU13: horas sin cambios para alertar una tarea crítica'),
    ('tamanio_max_archivo_mb',  '10',  'HU18: tamaño máximo de un adjunto'),
    ('dominios_email_permitidos',
     'gmail.com,gmail.com.ar,outlook.com,outlook.com.ar,hotmail.com,hotmail.com.ar,yahoo.com,yahoo.com.ar',
     'Dominios de email aceptados al crear usuarios, separados por coma');
