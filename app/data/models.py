"""
Modelos de datos (capa de acceso a datos).

Cada clase representa una tabla de la base tesis2026 y cada atributo, una
columna. SQLAlchemy traduce entre objetos de Python y filas de MySQL:

    db.session.scalars(select(Rol)).all()   ->   SELECT * FROM rol;

La base la crea el script database/der_v3.sql, así que acá solo describimos
las tablas que ya existen. Los nombres (__tablename__ y columnas) tienen que
coincidir exactamente con el script.

Paso 0.1: Rol.
Paso 0.2: Departamento, Puesto, Usuario, Auditoria y Parametro.
"""
from datetime import date, datetime

from flask_login import UserMixin
from sqlalchemy import ForeignKey, func

from app.extensions import db


class Rol(db.Model):
    __tablename__ = "rol"

    # Mapped / mapped_column es la sintaxis de SQLAlchemy 2.0. El tipo entre
    # corchetes es el tipo de Python; SQLAlchemy lo usa para validar y para
    # que el editor sepa qué hay en cada atributo.
    id_rol: db.Mapped[int] = db.mapped_column(primary_key=True)
    nombre: db.Mapped[str] = db.mapped_column(db.String(50), unique=True)
    # "str | None" significa que la columna admite NULL en la base.
    descripcion: db.Mapped[str | None] = db.mapped_column(db.String(255))

    def __repr__(self) -> str:
        # Cómo se muestra el objeto al imprimirlo; útil para depurar.
        return f"<Rol {self.id_rol}: {self.nombre}>"


class Departamento(db.Model):
    __tablename__ = "departamento"

    id_departamento: db.Mapped[int] = db.mapped_column(primary_key=True)
    nombre: db.Mapped[str] = db.mapped_column(db.String(100), unique=True)
    codigo: db.Mapped[str] = db.mapped_column(db.String(20), unique=True)
    descripcion: db.Mapped[str | None] = db.mapped_column(db.String(255))
    # ForeignKey indica que la columna apunta a otra tabla (clave foránea).
    id_usuario_jefe: db.Mapped[int | None] = db.mapped_column(ForeignKey("usuario.id_usuario"))
    email_contacto: db.Mapped[str | None] = db.mapped_column(db.String(100))
    telefono_contacto: db.Mapped[str | None] = db.mapped_column(db.String(20))
    activo: db.Mapped[bool] = db.mapped_column(default=True)

    # relationship() no es una columna: es un "atajo" para navegar entre
    # objetos. departamento.jefe devuelve el objeto Usuario del jefe, sin
    # escribir el JOIN a mano. foreign_keys aclara qué columna usar, porque
    # entre usuario y departamento hay dos caminos (el jefe y el área de
    # cada usuario).
    jefe: db.Mapped["Usuario | None"] = db.relationship(foreign_keys=[id_usuario_jefe])

    def __repr__(self) -> str:
        return f"<Departamento {self.codigo}: {self.nombre}>"


class Puesto(db.Model):
    __tablename__ = "puesto"

    id_puesto: db.Mapped[int] = db.mapped_column(primary_key=True)
    nombre: db.Mapped[str] = db.mapped_column(db.String(100))
    descripcion: db.Mapped[str | None] = db.mapped_column(db.String(255))
    id_departamento: db.Mapped[int] = db.mapped_column(ForeignKey("departamento.id_departamento"))

    departamento: db.Mapped["Departamento"] = db.relationship()

    def __repr__(self) -> str:
        return f"<Puesto {self.nombre}>"


class Usuario(UserMixin, db.Model):
    """Persona que usa el sistema.

    Hereda de UserMixin (Flask-Login), que le agrega lo que Flask-Login
    necesita: is_authenticated, get_id(), etc.
    """

    __tablename__ = "usuario"

    id_usuario: db.Mapped[int] = db.mapped_column(primary_key=True)
    nombre: db.Mapped[str] = db.mapped_column(db.String(100))
    apellido: db.Mapped[str] = db.mapped_column(db.String(100))
    email: db.Mapped[str] = db.mapped_column(db.String(100), unique=True)
    # Nunca la contraseña real: solo su hash (ver business/auth_service.py).
    password_hash: db.Mapped[str] = db.mapped_column(db.String(255))
    # Texto de 5 dígitos ("00005"), no número: un INT no guarda los ceros
    # a la izquierda. La base controla el formato con un CHECK.
    numero_legajo: db.Mapped[str] = db.mapped_column(db.CHAR(5), unique=True)
    id_rol: db.Mapped[int] = db.mapped_column(ForeignKey("rol.id_rol"))
    id_departamento: db.Mapped[int] = db.mapped_column(ForeignKey("departamento.id_departamento"))
    id_puesto: db.Mapped[int | None] = db.mapped_column(ForeignKey("puesto.id_puesto"))
    fecha_nacimiento: db.Mapped[date | None] = db.mapped_column(db.Date)
    direccion: db.Mapped[str | None] = db.mapped_column(db.String(255))
    telefono: db.Mapped[str | None] = db.mapped_column(db.String(20))
    fecha_ingreso: db.Mapped[date | None] = db.mapped_column(db.Date)
    activo: db.Mapped[bool] = db.mapped_column(default=True)
    ultimo_acceso: db.Mapped[datetime | None]
    # server_default=func.now(): si no mandamos valor, lo completa MySQL.
    fecha_alta: db.Mapped[datetime] = db.mapped_column(server_default=func.now())

    # lazy="joined": trae el rol en la misma consulta que el usuario. Lo
    # usamos en cada página (para los permisos), así nos ahorramos una
    # consulta extra cada vez.
    rol: db.Mapped["Rol"] = db.relationship(lazy="joined")
    departamento: db.Mapped["Departamento"] = db.relationship(foreign_keys=[id_departamento])
    puesto: db.Mapped["Puesto | None"] = db.relationship()

    # --- Lo que Flask-Login necesita ---------------------------------------

    def get_id(self) -> str:
        # Flask-Login guarda este valor en la cookie de sesión. UserMixin
        # busca un atributo "id", y nuestra PK se llama id_usuario.
        return str(self.id_usuario)

    @property
    def is_active(self) -> bool:
        # Un usuario dado de baja (activo = 0) no puede iniciar sesión, y si
        # ya tenía la sesión abierta, Flask-Login la deja de aceptar.
        return bool(self.activo)

    # --- Ayudas para las plantillas y los permisos ------------------------

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    def tiene_rol(self, *nombres_rol: str) -> bool:
        return self.rol.nombre in nombres_rol

    def __repr__(self) -> str:
        return f"<Usuario {self.email}>"


class Parametro(db.Model):
    """Valores configurables del sistema (clave -> valor)."""

    __tablename__ = "parametro"

    clave: db.Mapped[str] = db.mapped_column(db.String(50), primary_key=True)
    valor: db.Mapped[str] = db.mapped_column(db.String(255))
    descripcion: db.Mapped[str | None] = db.mapped_column(db.String(255))


class Auditoria(db.Model):
    """Registro de quién hizo qué y cuándo (requerimiento no funcional)."""

    __tablename__ = "auditoria"

    id_auditoria: db.Mapped[int] = db.mapped_column(db.BigInteger, primary_key=True)
    id_usuario: db.Mapped[int | None] = db.mapped_column(ForeignKey("usuario.id_usuario"))
    accion: db.Mapped[str] = db.mapped_column(db.String(20))
    entidad: db.Mapped[str] = db.mapped_column(db.String(50))
    id_entidad: db.Mapped[int | None]
    detalle: db.Mapped[str | None] = db.mapped_column(db.String(500))
    ip: db.Mapped[str | None] = db.mapped_column(db.String(45))
    fecha: db.Mapped[datetime] = db.mapped_column(server_default=func.now())
