"""
Punto de entrada: este es el archivo que se ejecuta para levantar el sistema.

    python run.py

Después se entra desde el navegador a http://127.0.0.1:5000
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # host="0.0.0.0" -> escucha en todas las interfaces de red de la PC, así
    #                   los compañeros de la misma red pueden entrar con
    #                   http://IP-DE-ESTA-PC:5000 . Con "127.0.0.1" solo
    #                   podría entrar esta misma PC.
    # debug=True     -> recarga sola al guardar cambios y muestra los errores
    #                   en el navegador. SOLO para desarrollo: en el servidor
    #                   real va en False, porque mostraría el código a cualquiera.
    app.run(host="0.0.0.0", port=5000, debug=True)
