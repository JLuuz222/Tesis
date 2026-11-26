"""
Paquete principal de la aplicación.

Usamos el patrón "application factory": en vez de crear la app como una
variable global, la crea una función (create_app). Ventajas:
  * se puede crear una app con otra configuración (por ejemplo, para pruebas);
  * se evitan las importaciones circulares entre archivos;
  * es la forma recomendada por la documentación de Flask.
"""
from flask import Flask

from config import Config
from app.extensions import csrf, db, login_manager


def create_app(config_class: type = Config) -> Flask:
    # template_folder indica dónde están los HTML. Por defecto Flask los busca
    # en app/templates; nosotros los tenemos en la capa de presentación.
    app = Flask(__name__, template_folder="presentation/templates")
    app.config.from_object(config_class)

    # Conecta las extensiones con esta app concreta.
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Importamos los modelos para que SQLAlchemy conozca las tablas.
    from app.data import models  # noqa: F401

    # Flask-Login guarda en la cookie solo el id del usuario. En cada pedido
    # llama a esta función para convertir ese id en el objeto Usuario
    # (current_user).
    from app.business.auth_service import obtener_usuario_por_id

    @login_manager.user_loader
    def cargar_usuario(id_usuario: str):
        return obtener_usuario_por_id(int(id_usuario))

    # Registramos los blueprints (grupos de rutas) de la capa de presentación.
    from app.presentation.routes.areas import areas_bp
    from app.presentation.routes.auth import auth_bp
    from app.presentation.routes.errores import errores_bp
    from app.presentation.routes.main import main_bp
    from app.presentation.routes.usuarios import usuarios_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(errores_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(areas_bp)

    # Hace disponibles las constantes de roles en todas las plantillas:
    # {% if current_user.tiene_rol(roles.ADMINISTRADOR) %}
    from app.business import permisos, roles
    app.jinja_env.globals["roles"] = roles
    app.jinja_env.globals["permisos"] = permisos

    # Comandos de consola (flask --app run crear-admin).
    from app.cli import registrar_comandos
    registrar_comandos(app)

    return app
