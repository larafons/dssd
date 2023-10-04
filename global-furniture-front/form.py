from flask import Flask, render_template, request, redirect, url_for, Response
import requests
from functools import wraps

app = Flask(__name__)
base_url = "http://localhost:5000"  # Reemplaza con la URL de tu backend

# Variable para almacenar el estado de autenticación (por ejemplo, True si el usuario está autenticado, False si no lo está)
is_authenticated = False

# Token de sesion (X-Bonita-API-Token)
token = None

# Función para verificar el estado de autenticación del usuario
def is_user_authenticated():
    return is_authenticated

# Decorador personalizado para proteger rutas
def login_required(route_function):
    @wraps(route_function)  # Usa wraps para mantener el nombre del endpoint original pq sino se rompe
    def decorated_route(*args, **kwargs):
        if not is_user_authenticated():
            return redirect('/login')
        return route_function(*args, **kwargs)
    return decorated_route

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/design_collection', methods=['GET'])
@login_required
def design_collection():
    return render_template('form.html')

@app.route('/login', methods=['POST'])
def submit_login():
    global is_authenticated,token
    username = request.form.get('username')
    password = request.form.get('password')

    data = {
        "username": username,
        "password": password
    }
    # Enviar los datos al backend para el inicio de sesión
    response = requests.post(f"{base_url}/login", json=data)
    if response.status_code == 200:
        # Establecer el estado de autenticación como True
        is_authenticated = True
        # Setea el cookie del token que retorna el login para que se almacene tambien en el front!!
        #???? chequear porque al final no se usa
        token = response.text

        return redirect('/design_collection')

@app.route('/submit', methods=['POST'])
@login_required
def submit_form(): 
    # Obtener los datos del formulario
    data = {
        "categoria": request.form.get('categoria'),
        "modelos": request.form.get('modelos'),
        "plazo_fabricacion": request.form.get('plazo_fabricacion'),
        "fecha_lanzamiento": request.form.get('fecha_lanzamiento'),
        "informacion_adicional": request.form.get('informacion_adicional')
    }
    # Harcodeamos el nombre del pool
    response = requests.get(f"{base_url}/getprocessid/entrega-1")

    process_id = response.text
    # Enviar los datos al backend para iniciar el proceso
    response1 = requests.post(f"{base_url}/initiateprocess/{process_id}", json=data)

    if response1.status_code == 200:
        return "Proceso iniciado exitosamente"
    else:
        return "Error al iniciar el proceso"

if __name__ == '__main__':
    app.run(port=5001, debug=True)
