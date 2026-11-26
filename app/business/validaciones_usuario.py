"""
Reglas de negocio para los datos de un usuario.

Están en la capa de negocio, y no en el formulario, porque las usa más de
un lugar: el comando crear-admin (consola) y, desde el paso 0.3, el alta de
usuarios desde la web. Si cada lugar tuviera su propia copia, tarde o
temprano una quedaría desactualizada.

Cada función recibe el dato, lo valida y devuelve el valor "limpio"
(normalizado). Si algo está mal, lanza ErrorDeValidacion con un mensaje
para mostrarle al usuario.
"""
import re
import secrets
import unicodedata
from datetime import date


class ErrorDeValidacion(Exception):
    """Error con un mensaje pensado para mostrarle al usuario."""


# --- Legajo -------------------------------------------------------------------

DIGITOS_LEGAJO = 5


def normalizar_legajo(valor: str | int) -> str:
    """Valida el legajo y lo devuelve con 5 dígitos: "5" -> "00005".

    Reglas: solo números, entre 1 y 5 dígitos, y distinto de cero.
    """
    texto = str(valor).strip()
    # \d con re.ASCII acepta solo 0-9. Sin ASCII, \d también aceptaría
    # dígitos de otros alfabetos (por ejemplo "٥", el 5 arábigo).
    if not re.fullmatch(r"\d{1,%d}" % DIGITOS_LEGAJO, texto, flags=re.ASCII):
        raise ErrorDeValidacion(
            f"El legajo debe tener solo números, de 1 a {DIGITOS_LEGAJO} dígitos.")
    numero = int(texto)
    if numero == 0:
        raise ErrorDeValidacion("El legajo no puede ser 0.")
    # :05d -> formato entero de 5 posiciones, completando con ceros.
    return f"{numero:0{DIGITOS_LEGAJO}d}"


# --- Email --------------------------------------------------------------------

# Se usan solo si la base no tiene el parámetro dominios_email_permitidos.
DOMINIOS_POR_DEFECTO = (
    "gmail.com", "gmail.com.ar",
    "outlook.com", "outlook.com.ar",
    "hotmail.com", "hotmail.com.ar",
    "yahoo.com", "yahoo.com.ar",
)

# Formato básico: algo@dominio.ext, sin espacios.
_PATRON_EMAIL = re.compile(r"[^@\s]+@([^@\s]+\.[^@\s]+)")


def validar_formato_email(email: str) -> str:
    """Controla solo el formato (algo@dominio.ext). Devuelve el email en minúsculas."""
    email = email.strip().lower()
    if not _PATRON_EMAIL.fullmatch(email):
        raise ErrorDeValidacion("El email no tiene un formato válido.")
    return email


def normalizar_email(email: str, dominios_permitidos: tuple[str, ...]) -> str:
    """Valida el formato y el dominio. Devuelve el email en minúsculas.

    El dominio se compara COMPLETO (lo que está después de la @). Si
    comparáramos con "termina en gmail.com", pasaría "x@falsogmail.com".
    """
    email = validar_formato_email(email)
    dominio = email.rsplit("@", 1)[1]
    if dominio not in dominios_permitidos:
        raise ErrorDeValidacion(
            "Solo se aceptan emails de estos dominios: " + ", ".join(dominios_permitidos) + ".")
    return email


# --- Contraseña ---------------------------------------------------------------

LARGO_MINIMO_CLAVE = 8
# Partes del nombre más cortas que esto no se controlan: prohibir "li" (de
# "Li") o "ana" dentro de cualquier palabra sería demasiado restrictivo.
LARGO_MINIMO_PARTE_NOMBRE = 3


def _sin_acentos(texto: str) -> str:
    """'María José' -> 'maria jose'. Así "Maria2026!" se detecta igual."""
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def validar_clave(clave: str, nombre: str, apellido: str, legajo: str) -> str:
    """Controla la complejidad de la contraseña y que no contenga datos personales.

    Devuelve la misma clave si es válida (igual que las otras funciones de
    este archivo, así se pueden usar todas de la misma manera).

    Junta TODOS los problemas y los informa juntos, para que el usuario los
    corrija de una vez y no de a uno por intento.
    """
    problemas = []

    if len(clave) < LARGO_MINIMO_CLAVE:
        problemas.append(f"mínimo {LARGO_MINIMO_CLAVE} caracteres")
    if not any(c.isupper() for c in clave):
        problemas.append("al menos una mayúscula")
    if not any(c.islower() for c in clave):
        problemas.append("al menos una minúscula")
    if not any(c.isdigit() for c in clave):
        problemas.append("al menos un número")
    # Carácter especial: todo lo que no es letra, número ni espacio
    # (+ - @ / . * _ # ! $ % etc.).
    if not any(not c.isalnum() and not c.isspace() for c in clave):
        problemas.append("al menos un carácter especial (por ejemplo + - @ / . * _)")

    clave_simple = _sin_acentos(clave)
    for parte in _sin_acentos(f"{nombre} {apellido}").split():
        if len(parte) >= LARGO_MINIMO_PARTE_NOMBRE and parte in clave_simple:
            problemas.append(f"sin tu nombre ni apellido (contiene \"{parte}\")")
            break

    legajo_sin_ceros = legajo.lstrip("0")
    if legajo in clave or (len(legajo_sin_ceros) >= 3 and legajo_sin_ceros in clave):
        problemas.append("sin tu número de legajo")

    if problemas:
        raise ErrorDeValidacion("La contraseña no cumple: " + "; ".join(problemas) + ".")
    return clave


# --- Datos generales -------------------------------------------------------------

def texto_obligatorio(valor: str | None, nombre_campo: str, largo_maximo: int) -> str:
    """Saca los espacios de los extremos y controla que no quede vacío ni sea muy largo."""
    valor = (valor or "").strip()
    if not valor:
        raise ErrorDeValidacion(f"{nombre_campo} es obligatorio.")
    if len(valor) > largo_maximo:
        raise ErrorDeValidacion(f"{nombre_campo} admite hasta {largo_maximo} caracteres.")
    return valor


def texto_opcional(valor: str | None, nombre_campo: str, largo_maximo: int) -> str | None:
    """Como texto_obligatorio, pero un campo vacío se guarda como NULL."""
    valor = (valor or "").strip()
    if not valor:
        return None
    if len(valor) > largo_maximo:
        raise ErrorDeValidacion(f"{nombre_campo} admite hasta {largo_maximo} caracteres.")
    return valor


def validar_fecha_nacimiento(fecha: date | None) -> date | None:
    """La fecha de nacimiento, si se carga, tiene que ser anterior a hoy."""
    if fecha is not None and fecha >= date.today():
        raise ErrorDeValidacion("La fecha de nacimiento tiene que ser anterior a hoy.")
    return fecha


# --- Contraseña temporal ------------------------------------------------------------

LARGO_CLAVE_TEMPORAL = 12


def generar_clave_temporal(nombre: str, apellido: str, legajo: str) -> str:
    """Genera una contraseña aleatoria que cumple todas las reglas.

    Se usa al crear un usuario o al restablecerle la contraseña. Usa el
    módulo secrets, y no random: random es predecible (sirve para juegos o
    simulaciones), secrets está hecho para claves y tokens.
    """
    # Sin letras que se confunden al dictarlas o copiarlas: O/0, l/1/I.
    mayusculas = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    minusculas = "abcdefghijkmnpqrstuvwxyz"
    numeros = "23456789"
    especiales = "#@*+-_"
    todos = mayusculas + minusculas + numeros + especiales

    while True:
        # Un carácter de cada grupo, para cumplir la regla, y el resto al azar.
        caracteres = [secrets.choice(mayusculas), secrets.choice(minusculas),
                      secrets.choice(numeros), secrets.choice(especiales)]
        caracteres += [secrets.choice(todos) for _ in range(LARGO_CLAVE_TEMPORAL - 4)]
        # Mezcla el orden, para que no empiece siempre con una mayúscula.
        secrets.SystemRandom().shuffle(caracteres)
        clave = "".join(caracteres)
        try:
            # Por si al azar contiene parte del nombre o el legajo.
            return validar_clave(clave, nombre, apellido, legajo)
        except ErrorDeValidacion:
            continue
