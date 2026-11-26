"""
Gestión de usuarios desde la web (paso 0.3): alta, edición, baja/alta,
restablecer contraseña y cambio de la propia contraseña.

Cada función recibe el "actor" (el usuario que hace la acción, current_user)
para controlar sus permisos y dejarlo registrado en la auditoría.
"""
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select

from app.business import (auditoria_service, auth_service, parametro_service, permisos, roles,
                          validaciones_usuario as v)
from app.business.permisos import SinPermiso
from app.business.validaciones_usuario import ErrorDeValidacion
from app.data.models import Departamento, Puesto, Rol, Usuario
from app.extensions import db


@dataclass
class DatosUsuario:
    """Los datos que llegan del formulario, ya separados de WTForms.

    Así el service no depende de cómo es la pantalla: lo mismo serviría
    para una importación desde Excel o una API.
    """
    nombre: str
    apellido: str
    email: str
    legajo: str
    id_rol: int
    id_departamento: int
    id_puesto: int | None = None
    fecha_nacimiento: date | None = None
    direccion: str | None = None
    telefono: str | None = None
    fecha_ingreso: date | None = None


# --- Consultas ----------------------------------------------------------------

def listar(actor, id_departamento: int | None = None, estado: str = "activos") -> list[Usuario]:
    """Usuarios que el actor puede ver, ordenados por apellido.

    El Jefe de área solo ve a los de su área, aunque pida otra.
    estado: "activos", "inactivos" o "todos".
    """
    consulta = select(Usuario).order_by(Usuario.apellido, Usuario.nombre)
    if actor.tiene_rol(roles.JEFE_DE_AREA):
        id_departamento = actor.id_departamento
    if id_departamento:
        consulta = consulta.where(Usuario.id_departamento == id_departamento)
    if estado == "activos":
        consulta = consulta.where(Usuario.activo.is_(True))
    elif estado == "inactivos":
        consulta = consulta.where(Usuario.activo.is_(False))
    return list(db.session.scalars(consulta))


def obtener_para_gestionar(actor, id_usuario: int) -> Usuario | None:
    """Devuelve el usuario si el actor puede gestionarlo; si no, SinPermiso."""
    usuario = db.session.get(Usuario, id_usuario)
    if usuario is None:
        return None
    permisos.exigir(permisos.puede_gestionar_a(actor, usuario))
    return usuario


def roles_asignables(actor) -> list[Rol]:
    """El Administrador asigna cualquier rol; el Jefe de área, solo Empleado."""
    consulta = select(Rol).order_by(Rol.id_rol)
    if not actor.tiene_rol(roles.ADMINISTRADOR):
        consulta = consulta.where(Rol.nombre == roles.EMPLEADO)
    return list(db.session.scalars(consulta))


def departamentos_asignables(actor) -> list[Departamento]:
    """El Administrador elige entre las áreas activas; el Jefe, solo la suya."""
    if not actor.tiene_rol(roles.ADMINISTRADOR):
        return [actor.departamento]
    return list(db.session.scalars(
        select(Departamento).where(Departamento.activo.is_(True)).order_by(Departamento.nombre)))


def puestos_asignables(actor) -> list[Puesto]:
    consulta = select(Puesto).join(Puesto.departamento).order_by(Departamento.nombre, Puesto.nombre)
    if not actor.tiene_rol(roles.ADMINISTRADOR):
        consulta = consulta.where(Puesto.id_departamento == actor.id_departamento)
    return list(db.session.scalars(consulta))


# --- Validación común de alta y edición ---------------------------------------

def _validar(actor, datos: DatosUsuario, usuario_existente: Usuario | None = None) -> dict:
    """Aplica todas las reglas y devuelve los valores limpios, listos para guardar."""
    limpio = {
        "nombre": v.texto_obligatorio(datos.nombre, "El nombre", 100),
        "apellido": v.texto_obligatorio(datos.apellido, "El apellido", 100),
        "email": v.normalizar_email(datos.email, parametro_service.dominios_email_permitidos()),
        "numero_legajo": v.normalizar_legajo(datos.legajo),
        "fecha_nacimiento": v.validar_fecha_nacimiento(datos.fecha_nacimiento),
        "direccion": v.texto_opcional(datos.direccion, "La dirección", 255),
        "telefono": v.texto_opcional(datos.telefono, "El teléfono", 20),
        "fecha_ingreso": datos.fecha_ingreso,
    }

    # Email y legajo únicos. En una edición, el propio usuario no cuenta.
    id_propio = usuario_existente.id_usuario if usuario_existente else None
    for columna, valor, texto in ((Usuario.email, limpio["email"], "el email"),
                                  (Usuario.numero_legajo, limpio["numero_legajo"], "el legajo")):
        otro = db.session.scalar(select(Usuario).where(columna == valor))
        if otro and otro.id_usuario != id_propio:
            raise ErrorDeValidacion(f"Ya existe un usuario con {texto} {valor}.")

    # Rol, área y puesto: tienen que estar entre los que el actor puede asignar.
    rol = db.session.get(Rol, datos.id_rol)
    permisos.exigir(rol is not None and rol in roles_asignables(actor))
    departamento = db.session.get(Departamento, datos.id_departamento)
    permisos.exigir(departamento is not None and departamento in departamentos_asignables(actor))
    puesto = None
    if datos.id_puesto:
        puesto = db.session.get(Puesto, datos.id_puesto)
        if puesto is None or puesto.id_departamento != departamento.id_departamento:
            raise ErrorDeValidacion(f"El puesto elegido no pertenece al área {departamento.nombre}.")

    limpio.update(rol=rol, departamento=departamento, puesto=puesto)
    return limpio


def _quedaria_sin_administradores(usuario: Usuario, nuevo_rol: Rol | None = None,
                                  se_desactiva: bool = False) -> bool:
    """True si el cambio dejaría al sistema sin ningún Administrador activo.

    Sin administradores nadie podría crear áreas ni usuarios.
    """
    if usuario.rol.nombre != roles.ADMINISTRADOR or not usuario.activo:
        return False
    deja_de_ser_admin = se_desactiva or (nuevo_rol is not None and nuevo_rol.nombre != roles.ADMINISTRADOR)
    if not deja_de_ser_admin:
        return False
    admins_activos = db.session.scalar(
        select(func.count()).select_from(Usuario).join(Usuario.rol)
        .where(Rol.nombre == roles.ADMINISTRADOR, Usuario.activo.is_(True)))
    return admins_activos <= 1


def _quitar_jefatura(usuario: Usuario) -> None:
    """Si el usuario es jefe de alguna área, esa área queda sin jefe.

    Pasa cuando se lo cambia de área o se lo da de baja: no puede seguir
    figurando como jefe de un área a la que ya no pertenece.
    """
    for area in db.session.scalars(
            select(Departamento).where(Departamento.id_usuario_jefe == usuario.id_usuario)):
        area.id_usuario_jefe = None


# --- Alta y edición -------------------------------------------------------------

def crear(actor, datos: DatosUsuario, ip: str | None = None) -> tuple[Usuario, str]:
    """Crea el usuario con una contraseña temporal.

    Devuelve (usuario, clave_temporal). La clave se muestra UNA sola vez en
    pantalla para que quien lo creó se la pase al empleado; en la base queda
    solo su hash, como siempre.
    """
    permisos.exigir(permisos.puede_gestionar_usuarios(actor))
    limpio = _validar(actor, datos)
    clave = v.generar_clave_temporal(limpio["nombre"], limpio["apellido"], limpio["numero_legajo"])

    usuario = Usuario(**limpio, password_hash=auth_service.generar_hash(clave),
                      debe_cambiar_clave=True)
    db.session.add(usuario)
    db.session.flush()
    auditoria_service.registrar(
        "crear", "usuario", id_usuario=actor.id_usuario, id_entidad=usuario.id_usuario,
        detalle=f"Alta de {usuario.nombre_completo} ({usuario.email}) como {usuario.rol.nombre}",
        ip=ip)
    db.session.commit()
    return usuario, clave


def actualizar(actor, usuario: Usuario, datos: DatosUsuario, ip: str | None = None) -> Usuario:
    permisos.exigir(permisos.puede_gestionar_a(actor, usuario))
    limpio = _validar(actor, datos, usuario_existente=usuario)

    if usuario.id_usuario == actor.id_usuario and limpio["rol"].id_rol != usuario.id_rol:
        raise ErrorDeValidacion("No podés cambiar tu propio rol.")
    if _quedaria_sin_administradores(usuario, nuevo_rol=limpio["rol"]):
        raise ErrorDeValidacion("Es el único Administrador activo: no se le puede cambiar el rol.")

    if limpio["departamento"].id_departamento != usuario.id_departamento:
        _quitar_jefatura(usuario)

    # Arma un resumen de lo que cambió, para la auditoría.
    cambios = [campo for campo, valor in limpio.items() if getattr(usuario, campo) != valor]
    for campo, valor in limpio.items():
        setattr(usuario, campo, valor)
    auditoria_service.registrar(
        "modificar", "usuario", id_usuario=actor.id_usuario, id_entidad=usuario.id_usuario,
        detalle="Cambió: " + (", ".join(cambios) if cambios else "nada"), ip=ip)
    db.session.commit()
    return usuario


def cambiar_estado(actor, usuario: Usuario, activo: bool, ip: str | None = None) -> None:
    """Baja o alta LÓGICA: el usuario no se borra, se marca activo = 0.

    No se borra porque sus tareas, comentarios y auditoría lo siguen
    nombrando; borrarlo dejaría ese historial sin dueño.
    """
    permisos.exigir(permisos.puede_gestionar_a(actor, usuario))
    if not activo and usuario.id_usuario == actor.id_usuario:
        raise ErrorDeValidacion("No podés darte de baja a vos mismo.")
    if not activo and _quedaria_sin_administradores(usuario, se_desactiva=True):
        raise ErrorDeValidacion("Es el único Administrador activo: no se lo puede dar de baja.")
    if activo and not usuario.departamento.activo:
        raise ErrorDeValidacion(
            f"El área {usuario.departamento.nombre} está dada de baja: reactivala primero.")

    usuario.activo = activo
    if not activo:
        _quitar_jefatura(usuario)
    auditoria_service.registrar(
        "modificar", "usuario", id_usuario=actor.id_usuario, id_entidad=usuario.id_usuario,
        detalle="Alta del usuario" if activo else "Baja del usuario", ip=ip)
    db.session.commit()


def restablecer_clave(actor, usuario: Usuario, ip: str | None = None) -> str:
    """Le da una contraseña temporal nueva y lo obliga a cambiarla al entrar."""
    permisos.exigir(permisos.puede_gestionar_a(actor, usuario))
    if usuario.id_usuario == actor.id_usuario:
        raise ErrorDeValidacion("Para tu propia contraseña usá \"Cambiar contraseña\".")
    clave = v.generar_clave_temporal(usuario.nombre, usuario.apellido, usuario.numero_legajo)
    usuario.password_hash = auth_service.generar_hash(clave)
    usuario.debe_cambiar_clave = True
    auditoria_service.registrar(
        "modificar", "usuario", id_usuario=actor.id_usuario, id_entidad=usuario.id_usuario,
        detalle="Contraseña restablecida", ip=ip)
    db.session.commit()
    return clave


# --- La propia contraseña -----------------------------------------------------

def cambiar_mi_clave(usuario: Usuario, clave_actual: str, clave_nueva: str,
                     ip: str | None = None) -> None:
    if not auth_service.verificar_clave(usuario, clave_actual):
        raise ErrorDeValidacion("La contraseña actual no es correcta.")
    if clave_nueva == clave_actual:
        raise ErrorDeValidacion("La contraseña nueva tiene que ser distinta de la actual.")
    v.validar_clave(clave_nueva, usuario.nombre, usuario.apellido, usuario.numero_legajo)

    usuario.password_hash = auth_service.generar_hash(clave_nueva)
    usuario.debe_cambiar_clave = False
    auditoria_service.registrar(
        "modificar", "usuario", id_usuario=usuario.id_usuario, id_entidad=usuario.id_usuario,
        detalle="Cambio de contraseña propia", ip=ip)
    db.session.commit()

