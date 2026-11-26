"""
Rutas de gestión de usuarios (paso 0.3).

Las ven el Administrador (todos los usuarios) y el Jefe de área (solo los
empleados de su área). Los permisos finos los controla la capa de negocio:
si un service lanza SinPermiso, errores.py responde con la página 403.
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.business import roles, usuario_service
from app.business.usuario_service import DatosUsuario
from app.business.validaciones_usuario import ErrorDeValidacion
from app.presentation.decorators import rol_requerido
from app.presentation.forms import UsuarioForm

# url_prefix: todas las rutas de este archivo empiezan con /usuarios.
usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def _cargar_opciones(form: UsuarioForm) -> None:
    """Llena los desplegables según lo que el usuario actual puede asignar."""
    form.id_rol.choices = [(r.id_rol, r.nombre) for r in usuario_service.roles_asignables(current_user)]
    form.id_departamento.choices = [
        (d.id_departamento, d.nombre) for d in usuario_service.departamentos_asignables(current_user)]
    form.id_puesto.choices = [(0, "(sin puesto)")] + [
        (p.id_puesto, f"{p.departamento.nombre} · {p.nombre}")
        for p in usuario_service.puestos_asignables(current_user)]


def _datos_del_form(form: UsuarioForm) -> DatosUsuario:
    """Pasa los datos del formulario al objeto que entiende la capa de negocio."""
    return DatosUsuario(
        nombre=form.nombre.data, apellido=form.apellido.data, email=form.email.data,
        legajo=form.legajo.data, id_rol=form.id_rol.data,
        id_departamento=form.id_departamento.data, id_puesto=form.id_puesto.data or None,
        fecha_nacimiento=form.fecha_nacimiento.data, fecha_ingreso=form.fecha_ingreso.data,
        telefono=form.telefono.data, direccion=form.direccion.data,
    )


@usuarios_bp.route("/")
@login_required
@rol_requerido(roles.ADMINISTRADOR, roles.JEFE_DE_AREA)
def lista():
    # request.args son los parámetros de la URL: /usuarios/?area=2&estado=todos
    id_area = request.args.get("area", type=int)
    estado = request.args.get("estado", "activos")
    usuarios = usuario_service.listar(current_user, id_area, estado)
    areas = usuario_service.departamentos_asignables(current_user)
    return render_template("usuarios/lista.html", usuarios=usuarios, areas=areas,
                           id_area=id_area, estado=estado)


@usuarios_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido(roles.ADMINISTRADOR, roles.JEFE_DE_AREA)
def nuevo():
    form = UsuarioForm()
    _cargar_opciones(form)
    if request.method == "GET":
        # Valores iniciales: rol Empleado y el área de quien carga.
        empleado = next((v for v, t in form.id_rol.choices if t == roles.EMPLEADO), None)
        form.id_rol.data = empleado
        form.id_departamento.data = current_user.id_departamento

    if form.validate_on_submit():
        try:
            usuario, clave = usuario_service.crear(current_user, _datos_del_form(form),
                                                   request.remote_addr)
        except ErrorDeValidacion as error:
            flash(str(error), "danger")
        else:
            # No redirigimos: la clave temporal se muestra una sola vez en esta
            # respuesta y no se guarda en ningún lado (ni en la cookie).
            return render_template("usuarios/clave_temporal.html", usuario=usuario, clave=clave,
                                   accion="creado")
    return render_template("usuarios/form.html", form=form, usuario=None)


@usuarios_bp.route("/<int:id_usuario>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido(roles.ADMINISTRADOR, roles.JEFE_DE_AREA)
def editar(id_usuario: int):
    usuario = usuario_service.obtener_para_gestionar(current_user, id_usuario) or abort(404)
    # obj=usuario llena el formulario con los datos actuales en el GET.
    form = UsuarioForm(obj=usuario)
    _cargar_opciones(form)
    if request.method == "GET":
        form.legajo.data = usuario.numero_legajo
        form.id_puesto.data = usuario.id_puesto or 0

    if form.validate_on_submit():
        try:
            usuario_service.actualizar(current_user, usuario, _datos_del_form(form),
                                       request.remote_addr)
        except ErrorDeValidacion as error:
            flash(str(error), "danger")
        else:
            flash(f"Se guardaron los cambios de {usuario.nombre_completo}.", "success")
            return redirect(url_for("usuarios.lista"))
    return render_template("usuarios/form.html", form=form, usuario=usuario)


@usuarios_bp.route("/<int:id_usuario>/estado", methods=["POST"])
@login_required
@rol_requerido(roles.ADMINISTRADOR, roles.JEFE_DE_AREA)
def cambiar_estado(id_usuario: int):
    usuario = usuario_service.obtener_para_gestionar(current_user, id_usuario) or abort(404)
    activar = request.form.get("activo") == "1"
    try:
        usuario_service.cambiar_estado(current_user, usuario, activar, request.remote_addr)
    except ErrorDeValidacion as error:
        flash(str(error), "danger")
    else:
        flash(f"{usuario.nombre_completo} quedó {'activo' if activar else 'dado de baja'}.", "success")
    return redirect(url_for("usuarios.lista"))


@usuarios_bp.route("/<int:id_usuario>/restablecer-clave", methods=["POST"])
@login_required
@rol_requerido(roles.ADMINISTRADOR, roles.JEFE_DE_AREA)
def restablecer_clave(id_usuario: int):
    usuario = usuario_service.obtener_para_gestionar(current_user, id_usuario) or abort(404)
    try:
        clave = usuario_service.restablecer_clave(current_user, usuario, request.remote_addr)
    except ErrorDeValidacion as error:
        flash(str(error), "danger")
        return redirect(url_for("usuarios.lista"))
    return render_template("usuarios/clave_temporal.html", usuario=usuario, clave=clave,
                           accion="restablecido")
