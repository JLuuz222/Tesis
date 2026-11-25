"""
Formularios web (Flask-WTF).

Cada clase describe los campos de un formulario y sus validaciones. Flask-WTF
además agrega automáticamente el campo oculto csrf_token, que protege contra
envíos falsificados desde otras páginas.

Las validaciones de acá son de FORMA (que el campo no esté vacío, que el
email tenga formato de email). Las reglas de NEGOCIO (que la clave sea la
correcta, que el usuario esté activo) están en la capa de negocio.
"""
from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length


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
