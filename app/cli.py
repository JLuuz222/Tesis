"""
Comandos de consola propios del sistema.

Se ejecutan desde la terminal, con el entorno virtual activo:

    flask --app run crear-admin

--app run le indica a Flask que la aplicación está en run.py.

Ojo en Windows: en Git Bash la contraseña oculta no se puede escribir (la
terminal no le pasa el teclado a Python). Usar la terminal de VS Code, CMD o
PowerShell, o en Git Bash anteponer winpty:  winpty flask --app run crear-admin
"""
import click
from flask import Flask
from sqlalchemy.exc import OperationalError

from app.business import auth_service, parametro_service, validaciones_usuario
from app.business.validaciones_usuario import ErrorDeValidacion


def _con_validacion(funcion):
    """Adapta una regla de negocio para usarla en click.prompt(value_proc=...).

    click llama a value_proc con lo que escribió el usuario. Si value_proc
    lanza click.BadParameter, click muestra el mensaje y VUELVE A PREGUNTAR,
    en vez de cortar el comando. Así cada dato se corrige en el momento.
    """
    def procesar(valor):
        try:
            return funcion(valor)
        except ErrorDeValidacion as error:
            raise click.BadParameter(str(error))
    return procesar


def _obligatorio(valor: str) -> str:
    valor = valor.strip()
    if not valor:
        raise ErrorDeValidacion("Este dato es obligatorio.")
    return valor


def registrar_comandos(app: Flask) -> None:

    # @app.cli.command crea un comando nuevo para "flask". click es la
    # librería que usa Flask para los comandos: pide datos y muestra mensajes.
    @app.cli.command("crear-admin")
    def crear_admin():
        """Crea el primer usuario Administrador."""
        try:
            dominios = parametro_service.dominios_email_permitidos()
        except OperationalError as error:
            # OperationalError: MySQL no responde o rechazó el usuario/clave.
            raise click.ClickException(
                "No se pudo conectar a MySQL. Revisá el .env y que el servicio esté "
                f"corriendo.\nDetalle: {error.orig}")

        def email_valido(valor: str) -> str:
            email = validaciones_usuario.normalizar_email(valor, dominios)
            if not auth_service.email_disponible(email):
                raise ErrorDeValidacion(f"Ya existe un usuario con el email {email}.")
            return email

        def legajo_valido(valor: str) -> str:
            legajo = validaciones_usuario.normalizar_legajo(valor)
            if not auth_service.legajo_disponible(legajo):
                raise ErrorDeValidacion(f"Ya existe un usuario con el legajo {legajo}.")
            return legajo

        click.echo("Alta de usuario Administrador")
        nombre = click.prompt("Nombre", value_proc=_con_validacion(_obligatorio))
        apellido = click.prompt("Apellido", value_proc=_con_validacion(_obligatorio))
        email = click.prompt("Email", value_proc=_con_validacion(email_valido))
        legajo = click.prompt("Número de legajo (hasta 5 dígitos)",
                              value_proc=_con_validacion(legajo_valido))
        click.echo(f"  Se guardará como {legajo}.")
        departamento = click.prompt("Departamento", default="Gerencia",
                                    value_proc=_con_validacion(_obligatorio))

        click.echo("La contraseña debe tener 8 caracteres o más, con mayúscula, minúscula, "
                   "número y carácter especial, y no contener tu nombre ni tu legajo.")
        click.echo("Al escribirla no se ve nada en pantalla: es normal.")
        # hide_input: no muestra lo que se escribe.
        # confirmation_prompt: la pide dos veces para evitar errores de tipeo.
        # La regla se controla con la primera; después se pide la confirmación.
        clave = click.prompt(
            "Contraseña", hide_input=True, confirmation_prompt="Repetí la contraseña",
            value_proc=_con_validacion(
                lambda valor: validaciones_usuario.validar_clave(valor, nombre, apellido, legajo)),
        )

        try:
            usuario = auth_service.crear_administrador(
                nombre, apellido, email, legajo, clave, departamento)
        except ErrorDeValidacion as error:
            # ClickException muestra el mensaje y termina con código de error.
            raise click.ClickException(str(error))
        click.echo(f"Listo: {usuario.nombre_completo} ({usuario.email}, legajo "
                   f"{usuario.numero_legajo}) ya puede iniciar sesión.")
