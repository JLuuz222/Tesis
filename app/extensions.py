"""
Extensiones de Flask compartidas por toda la aplicación.

Se crean acá "vacías" (sin app) y se conectan dentro de create_app() con
db.init_app(app). Si las creáramos dentro de create_app, cada archivo que
necesite "db" tendría que importar app/__init__.py, y eso genera importaciones
circulares (A importa B y B importa A).
"""
from flask_sqlalchemy import SQLAlchemy

# "db" es el punto de acceso a la base: db.session para consultas y
# transacciones, db.Model como clase base de los modelos.
db = SQLAlchemy()
