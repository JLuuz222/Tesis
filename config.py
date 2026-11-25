"""
Configuración de la aplicación.

Toda la configuración se lee de variables de entorno, que a su vez se cargan
del archivo .env. Así:
  * la contraseña de la base no queda escrita en el código ni en Git;
  * cada integrante usa sus propios datos sin tocar este archivo;
  * en el servidor se cambian los valores sin cambiar el código.
"""
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Lee el archivo .env (si existe) y carga cada línea CLAVE=valor como variable
# de entorno. Después se leen con os.getenv("CLAVE").
load_dotenv()


def _armar_url_base_de_datos() -> str:
    """Arma la URL de conexión que entiende SQLAlchemy.

    Formato:  mysql+pymysql://usuario:contraseña@host:puerto/base
      * "mysql"   -> el motor de base de datos.
      * "pymysql" -> el driver de Python que se usa para hablar con MySQL.
    quote_plus() escapa caracteres especiales de la contraseña (@, #, /, etc.)
    que si no romperían la URL.
    """
    usuario = os.getenv("DB_USER", "tesis_app")
    contrasenia = quote_plus(os.getenv("DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "127.0.0.1")
    puerto = os.getenv("DB_PORT", "3306")
    base = os.getenv("DB_NAME", "tesis2026")
    return f"mysql+pymysql://{usuario}:{contrasenia}@{host}:{puerto}/{base}?charset=utf8mb4"


class Config:
    """Valores que Flask y sus extensiones leen al arrancar.

    Flask toma automáticamente los atributos EN MAYÚSCULAS de esta clase
    cuando hacemos app.config.from_object(Config).
    """

    # Firma las cookies de sesión: si alguien modifica su cookie a mano,
    # Flask lo detecta porque la firma no coincide.
    SECRET_KEY = os.getenv("SECRET_KEY", "solo-para-desarrollo-cambiar")

    SQLALCHEMY_DATABASE_URI = _armar_url_base_de_datos()

    # Desactiva un sistema de eventos de Flask-SQLAlchemy que no usamos y
    # consume memoria.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cookies de sesión:
    #   HTTPONLY: JavaScript no puede leer la cookie (si alguien inyecta un
    #             script en una página, no puede robar la sesión).
    #   SAMESITE "Lax": el navegador no manda la cookie en formularios que
    #             vienen desde otro sitio.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Cuánto dura "Mantener la sesión iniciada" (en segundos): 7 días.
    REMEMBER_COOKIE_DURATION = 7 * 24 * 60 * 60

    SQLALCHEMY_ENGINE_OPTIONS = {
        # Antes de usar una conexión guardada, verifica que siga viva.
        # MySQL corta las conexiones inactivas después de un rato; sin esto
        # aparece el error "MySQL server has gone away".
        "pool_pre_ping": True,
    }
