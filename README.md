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
4. **Crear el primer administrador** (una sola vez por base):
   ```
   flask --app run crear-admin
   ```
   Pide nombre, apellido, email, legajo, departamento y contraseña.
   **En Git Bash** la contraseña oculta no se puede escribir: usar la terminal
   de VS Code, CMD o PowerShell, o anteponer `winpty`
   (`winpty flask --app run crear-admin`).
5. **Levantar el sistema.**
   ```
   python run.py
   ```
   Abrir http://127.0.0.1:5000 e iniciar sesión con el administrador.
   En "Estado del sistema" se ve la conexión a MySQL y los 3 roles.

## Cambios en la base (migraciones)

Una base creada con una versión anterior de `der_v3.sql` se actualiza
ejecutando, en orden y como root, los scripts de `database/migraciones/`.
Una base nueva creada con el `der_v3.sql` actual no los necesita.

| Script | Qué cambia |
|---|---|
| `001_legajo_y_dominios_email.sql` | Legajo de 5 dígitos con ceros (`CHAR(5)`) y dominios de email permitidos |

## Reglas de negocio de usuarios

Están en `app/business/validaciones_usuario.py`:

- **Email:** solo dominios permitidos. La lista está en la tabla `parametro`
  (`dominios_email_permitidos`), así se puede ampliar sin tocar el código.
- **Legajo:** solo números, de 1 a 5 dígitos; se guarda con ceros (`5` → `00005`).
- **Contraseña:** mínimo 8 caracteres, con mayúscula, minúscula, número y
  carácter especial; no puede contener el nombre, el apellido ni el legajo.

## Roles

| Rol | Qué puede hacer |
|---|---|
| Administrador | Gestiona usuarios y áreas; ve el estado del sistema y todos los reportes |
| Jefe de área | Crea, asigna y supervisa las tareas de su área |
| Empleado | Ve y actualiza las tareas que tiene asignadas |
