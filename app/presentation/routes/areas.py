"""
Rutas de gestión de áreas y puestos (paso 0.3). Solo para el Administrador.
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.business import area_service, roles
from app.business.area_service import DatosArea
from app.business.validaciones_usuario import ErrorDeValidacion
from app.data.models import Departamento, Puesto
from app.extensions import db
from app.presentation.decorators import rol_requerido
from app.presentation.forms import AreaForm, PuestoForm

areas_bp = Blueprint("areas", __name__, url_prefix="/areas")


def _area_o_404(id_area: int) -> Departamento:
    return db.session.get(Departamento, id_area) or abort(404)


def _datos_del_form(form: AreaForm) -> DatosArea:
    return DatosArea(
        nombre=form.nombre.data, codigo=form.codigo.data, descripcion=form.descripcion.data,
        email_contacto=form.email_contacto.data, telefono_contacto=form.telefono_contacto.data,
        id_usuario_jefe=form.id_usuario_jefe.data or None,
    )


@areas_bp.route("/")
@login_required
@rol_requerido(roles.ADMINISTRADOR)
def lista():
    return render_template("areas/lista.html", filas=area_service.listar_con_totales())


@areas_bp.route("/nueva", methods=["GET", "POST"])
@login_required
@rol_requerido(roles.ADMINISTRADOR)
def nueva():
    form = AreaForm()
    form.id_usuario_jefe.choices = [(0, "(sin jefe)")]
    if form.validate_on_submit():
        try:
            area = area_service.crear_area(current_user, _datos_del_form(form), request.remote_addr)
        except ErrorDeValidacion as error:
            flash(str(error), "danger")
        else:
            flash(f"Se creó el área {area.nombre}. Ahora podés cargarle puestos.", "success")
            return redirect(url_for("areas.puestos", id_area=area.id_departamento))
    return render_template("areas/form.html", form=form, area=None)


@areas_bp.route("/<int:id_area>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido(roles.ADMINISTRADOR)
def editar(id_area: int):
    area = _area_o_404(id_area)
    form = AreaForm(obj=area)
    form.id_usuario_jefe.choices = [(0, "(sin jefe)")] + [
        (u.id_usuario, u.nombre_completo) for u in area_service.candidatos_a_jefe(area)]
    if request.method == "GET":
        form.id_usuario_jefe.data = area.id_usuario_jefe or 0

    if form.validate_on_submit():
        try:
            area_service.actualizar_area(current_user, area, _datos_del_form(form),
                                         request.remote_addr)
        except ErrorDeValidacion as error:
            flash(str(error), "danger")
        else:
            flash(f"Se guardaron los cambios del área {area.nombre}.", "success")
            return redirect(url_for("areas.lista"))
    return render_template("areas/form.html", form=form, area=area)


@areas_bp.route("/<int:id_area>/estado", methods=["POST"])
@login_required
@rol_requerido(roles.ADMINISTRADOR)
def cambiar_estado(id_area: int):
    area = _area_o_404(id_area)
    activar = request.form.get("activo") == "1"
    try:
        area_service.cambiar_estado_area(current_user, area, activar, request.remote_addr)
    except ErrorDeValidacion as error:
        flash(str(error), "danger")
    else:
        flash(f"El área {area.nombre} quedó {'activa' if activar else 'dada de baja'}.", "success")
    return redirect(url_for("areas.lista"))


# --- Puestos de un área ---------------------------------------------------------

@areas_bp.route("/<int:id_area>/puestos", methods=["GET", "POST"])
@login_required
@rol_requerido(roles.ADMINISTRADOR)
def puestos(id_area: int):
    """Lista los puestos del área y, debajo, el formulario para agregar uno."""
    area = _area_o_404(id_area)
    form = PuestoForm()
    if form.validate_on_submit():
        try:
            puesto = area_service.crear_puesto(current_user, area, form.nombre.data,
                                               form.descripcion.data, request.remote_addr)
        except ErrorDeValidacion as error:
            flash(str(error), "danger")
        else:
            flash(f"Se agregó el puesto {puesto.nombre}.", "success")
            # Redirigir después de un POST (patrón Post/Redirect/Get): si el
            # usuario actualiza la página, no se vuelve a enviar el formulario.
            return redirect(url_for("areas.puestos", id_area=id_area))
    return render_template("areas/puestos.html", area=area, form=form,
                           filas=area_service.listar_puestos(area))


@areas_bp.route("/puestos/<int:id_puesto>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido(roles.ADMINISTRADOR)
def editar_puesto(id_puesto: int):
    puesto = db.session.get(Puesto, id_puesto) or abort(404)
    form = PuestoForm(obj=puesto)
    if form.validate_on_submit():
        try:
            area_service.actualizar_puesto(current_user, puesto, form.nombre.data,
                                           form.descripcion.data, request.remote_addr)
        except ErrorDeValidacion as error:
            flash(str(error), "danger")
        else:
            flash("Se guardó el puesto.", "success")
            return redirect(url_for("areas.puestos", id_area=puesto.id_departamento))
    return render_template("areas/puesto_form.html", form=form, puesto=puesto)


@areas_bp.route("/puestos/<int:id_puesto>/eliminar", methods=["POST"])
@login_required
@rol_requerido(roles.ADMINISTRADOR)
def eliminar_puesto(id_puesto: int):
    puesto = db.session.get(Puesto, id_puesto) or abort(404)
    id_area = puesto.id_departamento
    try:
        area_service.eliminar_puesto(current_user, puesto, request.remote_addr)
    except ErrorDeValidacion as error:
        flash(str(error), "danger")
    else:
        flash("Se eliminó el puesto.", "success")
    return redirect(url_for("areas.puestos", id_area=id_area))
