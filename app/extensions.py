"""
Extensiones de Flask compartidas por toda la aplicación.

Se crean acá "vacías" (sin app) y se conectan dentro de create_app() con
init_app(app). Si las creáramos dentro de create_app, cada archivo que
las necesite tendría que importar app/__init__.py, y eso genera importaciones
circulares (A importa B y B importa A).
"""
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

# "db" es el punto de acceso a la base: db.session para consultas y
# transacciones, db.Model como clase base de los modelos.
db = SQLAlchemy()

# Maneja la sesión del usuario: recuerda quién entró y protege las páginas.
login_manager = LoginManager()
# Si alguien sin sesión entra a una página protegida, lo manda a esta ruta.
login_manager.login_view = "auth.login"
login_manager.login_message = "Iniciá sesión para continuar."
login_manager.login_message_category = "warning"

# Protección CSRF: cada formulario lleva un código oculto que el servidor
# verifica. Así otra página web no puede enviar formularios "en nombre" de
# un usuario que tiene la sesión abierta.
csrf = CSRFProtect()
