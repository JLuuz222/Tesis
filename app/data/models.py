"""
Modelos de datos (capa de acceso a datos).

Cada clase representa una tabla de la base tesis2026 y cada atributo, una
columna. SQLAlchemy traduce entre objetos de Python y filas de MySQL:

    Rol.query.all()   ->   SELECT * FROM rol;

La base la crea el script database/der_v3.sql, así que acá solo describimos
las tablas que ya existen. Los nombres (__tablename__ y columnas) tienen que
coincidir exactamente con el script.

En el paso 0.1 solo está Rol, para probar la conexión. En el paso 0.2 se
agregan departamento, puesto y usuario.
"""
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
