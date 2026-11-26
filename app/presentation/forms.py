"""
Formularios web (Flask-WTF).

Cada clase describe los campos de un formulario y sus validaciones. Flask-WTF
además agrega automáticamente el campo oculto csrf_token, que protege contra
envíos falsificados desde otras páginas.

Las validaciones de acá son de FORMA (que el campo no esté vacío, que el
email tenga formato de email). Las reglas de NEGOCIO (que la clave sea la
correcta, que el legajo no se repita, quién puede asignar qué rol) están en
la capa de negocio.
"""
from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateField, EmailField, PasswordField, SelectField, StringField,
                     SubmitField, TextAreaField)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


def _sin_espacios(valor: str | None) -> str | None:
    """Saca los espacios del principio y del final (típico al copiar y pegar)."""
    return valor.strip() if valor else valor


class LoginForm(FlaskForm):
    email = EmailField(
        "Email",
        # filters se aplica ANTES de validar: si no, " juan@x.com" fallaría
        # la validación de formato por el espacio.
        filters=[_sin_espacios],
        validators=[DataRequired("Ingresá tu email."),
                    Email("El email no tiene un formato válido."),
                    Length(max=100)],
    )
    clave = PasswordField("Contraseña", validators=[DataRequired("Ingresá tu contraseña.")])
    recordarme = BooleanField("Mantener la sesión iniciada")
    enviar = SubmitField("Ingresar")


class CambiarClaveForm(FlaskForm):
    clave_actual = PasswordField("Contraseña actual",
                                 validators=[DataRequired("Ingresá tu contraseña actual.")])
    clave_nueva = PasswordField("Contraseña nueva",
                                validators=[DataRequired("Ingresá la contraseña nueva.")])
    # EqualTo compara con otro campo del mismo formulario.
    confirmacion = PasswordField("Repetí la contraseña nueva", validators=[
        DataRequired("Repetí la contraseña nueva."),
        EqualTo("clave_nueva", "Las dos contraseñas nuevas no coinciden.")])
    enviar = SubmitField("Cambiar contraseña")


class UsuarioForm(FlaskForm):
    """Alta y edición de usuarios.

    Las opciones de rol, área y puesto no están fijas: la ruta las carga
    según quién está usando el formulario (un Jefe de área solo ve su área
    y el rol Empleado).
    """
    nombre = StringField("Nombre", filters=[_sin_espacios],
                         validators=[DataRequired("Ingresá el nombre."), Length(max=100)])
    apellido = StringField("Apellido", filters=[_sin_espacios],
                           validators=[DataRequired("Ingresá el apellido."), Length(max=100)])
    email = EmailField("Email", filters=[_sin_espacios],
                       validators=[DataRequired("Ingresá el email."), Length(max=100)])
    legajo = StringField("Número de legajo", filters=[_sin_espacios],
                         validators=[DataRequired("Ingresá el legajo."), Length(max=5)],
                         description="Hasta 5 dígitos. Se guarda con ceros: 5 → 00005.")
    # coerce=int: el navegador manda texto ("3"); coerce lo convierte a número.
    id_rol = SelectField("Rol", coerce=int)
    id_departamento = SelectField("Área", coerce=int)
    # 0 = sin puesto (un SelectField con coerce=int no admite None).
    id_puesto = SelectField("Puesto", coerce=int, description="Tiene que ser del área elegida.")
    fecha_nacimiento = DateField("Fecha de nacimiento", validators=[Optional()])
    fecha_ingreso = DateField("Fecha de ingreso", validators=[Optional()])
    telefono = StringField("Teléfono", filters=[_sin_espacios], validators=[Length(max=20)])
    direccion = StringField("Dirección", filters=[_sin_espacios], validators=[Length(max=255)])
    enviar = SubmitField("Guardar")


class AreaForm(FlaskForm):
    nombre = StringField("Nombre", filters=[_sin_espacios],
                         validators=[DataRequired("Ingresá el nombre."), Length(max=100)])
    codigo = StringField("Código", filters=[_sin_espacios],
                         validators=[DataRequired("Ingresá el código."), Length(max=20)],
                         description="Corto, por ejemplo COM para Compras.")
    descripcion = TextAreaField("Descripción", filters=[_sin_espacios],
                                validators=[Length(max=255)])
    email_contacto = StringField("Email de contacto", filters=[_sin_espacios],
                                 validators=[Length(max=100)])
    telefono_contacto = StringField("Teléfono de contacto", filters=[_sin_espacios],
                                    validators=[Length(max=20)])
    # Solo se muestra al editar. 0 = sin jefe.
    id_usuario_jefe = SelectField("Jefe del área", coerce=int, validate_choice=False)
    enviar = SubmitField("Guardar")


class PuestoForm(FlaskForm):
    nombre = StringField("Nombre del puesto", filters=[_sin_espacios],
                         validators=[DataRequired("Ingresá el nombre del puesto."),
                                     Length(max=100)])
    descripcion = StringField("Descripción", filters=[_sin_espacios], validators=[Length(max=255)])
    enviar = SubmitField("Guardar")
