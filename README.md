# TESIS2026 · Sistema de gestión de tareas (Pintegral)

Aplicación web para asignar y seguir tareas entre las áreas de Pintegral.
Trabajo final de Analista Universitario en Sistemas Informáticos (UNC · ESCMB).
Autores: Josefina Mansilla, Lautaro Quevedo y Gabriel Zamora.

Stack: Python 3.13 · Flask · SQLAlchemy · MySQL 8.4 LTS · Bootstrap 5.

## Estructura (Arquitectura N-Layers V3)

```
Tesis/
├── app/
│   ├── presentation/     Capa de presentación: rutas y plantillas HTML
│   │   ├── routes/
│   │   └── templates/
│   ├── business/         Capa de lógica de negocio (services)
│   ├── data/             Capa de acceso a datos (modelos SQLAlchemy)
│   ├── integrations/     Servicios externos (email, calendarios)
│   ├── extensions.py     Extensiones compartidas (db)
│   └── __init__.py       create_app(): arma la aplicación
├── database/             Scripts SQL de la base
├── config.py             Configuración leída del .env
├── run.py                Punto de entrada
└── requirements.txt      Dependencias de Python
```

## Puesta en marcha (Windows)

Requisitos: Python 3.13 y MySQL 8.4 con la base `tesis2026` creada con
`database/der_v3.sql`.

1. **Usuario de MySQL para la app.** Abrir `database/crear_usuario_app.sql` en
   Workbench, cambiar `CAMBIAR_ESTA_CLAVE` por una clave propia y ejecutarlo.
2. **Entorno virtual.** En una terminal, dentro de la carpeta del proyecto:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Con Git Bash, la activación es `source .venv/Scripts/activate`.
3. **Configuración.** Copiar `.env.example` como `.env` y completar
   `SECRET_KEY` y `DB_PASSWORD`.
4. **Levantar el sistema.**
   ```
   python run.py
   ```
   Abrir http://127.0.0.1:5000 . Si conecta, la página muestra los 3 roles.
