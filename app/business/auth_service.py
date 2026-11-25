"""
Lógica de autenticación: contraseñas, inicio de sesión y alta del primer
administrador.

Las rutas (capa de presentación) no comparan contraseñas ni escriben en la
base: le piden todo a este service.
"""
from datetime import datetime

from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from app.business import auditoria_service, parametro_service, roles, validaciones_usuario
# Se reexporta para que quien use auth_service pueda capturar el error.
from app.business.validaciones_usuario import ErrorDeValidacion  # noqa: F401
from app.data.models import Departamento, Rol, Usuario
from app.extensions import db

# --- Contraseñas --------------------------------------------------------------

def generar_hash(clave: str) -> str:
    """Convierte la contraseña en un hash.

    Un hash es una transformación de un solo sentido: de la contraseña se
    obtiene el hash, pero del hash no se puede volver a la contraseña.
    generate_password_hash usa el algoritmo scrypt y le agrega una "sal"
    aleatoria, así dos usuarios con la misma contraseña tienen hashes
    distintos. Si alguien roba la base, no ve las contraseñas.
    """
    return generate_password_hash(clave)


def verificar_clave(usuario: Usuario, clave: str) -> bool:
    """Calcula el hash de la clave ingresada y lo compara con el guardado."""
    return check_password_hash(usuario.password_hash, clave)


# --- Inicio de sesión ---------------------------------------------------------

def autenticar(email: str, clave: str, ip: str | None) -> Usuario | None:
    """Devuelve el usuario si el email y la clave son correctos, o None.

    Registra cada intento en auditoria (Repo1: reporte de accesos) y, si
    entra, actualiza ultimo_acceso.
    """
    email = email.strip().lower()
    usuario = db.session.scalar(select(Usuario).where(Usuario.email == email))

    if usuario is None or not verificar_clave(usuario, clave):
        auditoria_service.registrar(
            "login_fallido", "usuario",
            id_usuario=usuario.id_usuario if usuario else None,
            detalle=f"Intento con el email {email}", ip=ip,
        )
        db.session.commit()
        return None

    if not usuario.activo:
        auditoria_service.registrar(
            "login_fallido", "usuario", id_usuario=usuario.id_usuario,
            id_entidad=usuario.id_usuario, detalle="Usuario inactivo", ip=ip,
        )
        db.session.commit()
        return None

    usuario.ultimo_acceso = datetime.now()
    auditoria_service.registrar(
        "login", "usuario", id_usuario=usuario.id_usuario,
        id_entidad=usuario.id_usuario, ip=ip,
    )
    db.session.commit()
    return usuario


def registrar_logout(usuario: Usuario, ip: str | None) -> None:
    auditoria_service.registrar(
        "logout", "usuario", id_usuario=usuario.id_usuario,
        id_entidad=usuario.id_usuario, ip=ip,
    )
    db.session.commit()


def obtener_usuario_por_id(id_usuario: int) -> Usuario | None:
    # db.session.get busca por clave primaria (SELECT ... WHERE id_usuario = ?).
    return db.session.get(Usuario, id_usuario)


# --- Alta del primer administrador -------------------------------------------

def email_disponible(email: str) -> bool:
    return db.session.scalar(select(Usuario).where(Usuario.email == email)) is None


def legajo_disponible(legajo: str) -> bool:
    return db.session.scalar(select(Usuario).where(Usuario.numero_legajo == legajo)) is None


def crear_administrador(nombre: str, apellido: str, email: str, legajo: str,
                        clave: str, nombre_departamento: str) -> Usuario:
    """Crea un usuario con rol Administrador.

    Si el departamento no existe, lo crea. Lo usa el comando
    "flask --app run crear-admin", porque sin un primer usuario nadie puede
    iniciar sesión para dar de alta a los demás.

    Vuelve a aplicar TODAS las reglas aunque quien llama ya las haya
    controlado: la capa de negocio no confía en que la presentación validó.
    """
    nombre, apellido = nombre.strip(), apellido.strip()
    nombre_departamento = nombre_departamento.strip()
    if not nombre or not apellido:
        raise ErrorDeValidacion("El nombre y el apellido son obligatorios.")
    if not nombre_departamento:
        raise ErrorDeValidacion("El departamento es obligatorio.")

    email = validaciones_usuario.normalizar_email(
        email, parametro_service.dominios_email_permitidos())
    legajo = validaciones_usuario.normalizar_legajo(legajo)
    validaciones_usuario.validar_clave(clave, nombre, apellido, legajo)

    if not email_disponible(email):
        raise ErrorDeValidacion(f"Ya existe un usuario con el email {email}.")
    if not legajo_disponible(legajo):
        raise ErrorDeValidacion(f"Ya existe un usuario con el legajo {legajo}.")

    rol_admin = db.session.scalar(select(Rol).where(Rol.nombre == roles.ADMINISTRADOR))
    if rol_admin is None:
        raise ErrorDeValidacion("No está el rol Administrador. ¿Se ejecutó database/der_v3.sql?")

    departamento = db.session.scalar(
        select(Departamento).where(Departamento.nombre == nombre_departamento)
    )
    if departamento is None:
        # El código se arma con las 3 primeras letras: "Gerencia" -> "GER".
        departamento = Departamento(nombre=nombre_departamento,
                                    codigo=nombre_departamento[:3].upper())
        db.session.add(departamento)

    usuario = Usuario(
        nombre=nombre, apellido=apellido, email=email,
        password_hash=generar_hash(clave), numero_legajo=legajo,
        rol=rol_admin, departamento=departamento,
    )
    db.session.add(usuario)
    # flush() manda los INSERT a MySQL sin cerrar la transacción, para que
    # usuario.id_usuario ya tenga su número y lo podamos usar en la auditoría.
    db.session.flush()
    auditoria_service.registrar("crear", "usuario", id_entidad=usuario.id_usuario,
                                detalle="Alta del administrador desde la consola")
    # commit() confirma todo junto: departamento, usuario y auditoría. Si
    # algo falla antes de esta línea, no se guarda nada.
    db.session.commit()
    return usuario
