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
from app.extensions import db


def create_app(config_class: type = Config) -> Flask:
    # template_folder indica dónde están los HTML. Por defecto Flask los busca
    # en app/templates; nosotros los tenemos en la capa de presentación.
    app = Flask(__name__, template_folder="presentation/templates")
    app.config.from_object(config_class)

    # Conecta las extensiones con esta app concreta.
    db.init_app(app)

    # Importamos los modelos para que SQLAlchemy conozca las tablas.
    from app.data import models  # noqa: F401

    # Registramos los blueprints (grupos de rutas) de la capa de presentación.
    from app.presentation.routes.main import main_bp
    app.register_blueprint(main_bp)

    return app
