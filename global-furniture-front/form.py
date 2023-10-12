from flask import Flask, render_template, request, redirect, url_for, Response, make_response
import requests
from functools import wraps
import datetime
import time 

app = Flask(__name__)
base_url = "http://localhost:5000"  # Reemplaza con la URL de tu backend
api_url = "http://localhost:5002"  # Reemplaza con la URL de tu API

# Decorador personalizado para proteger rutas
def login_required(route_function):
    @wraps(route_function)  # Usa wraps para mantener el nombre del endpoint original pq sino se rompe
    def decorated_route(*args, **kwargs):
        token = request.cookies.get('X-Bonita-API-Token')
        if not token:
            return redirect('/login')
        return route_function(*args, **kwargs)
    return decorated_route

# Define una función decoradora que verifica el rol del usuario
def require_role(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            # Obtiene el valor del rol de la cookie 'role'
            user_role = request.cookies.get('role')
            if user_role == role:
                # El usuario tiene el rol requerido, permite el acceso
                return view_func(*args, **kwargs)
            else:
                # El usuario no tiene el rol correspondiente, muestra un mensaje de denegación
                response = make_response('No tienes permiso para acceder a esta ruta', 403)
                return response
        return wrapped_view
    return decorator


def check_role(route_function):
    @wraps(route_function)  # Usa wraps para mantener el nombre del endpoint original pq sino se rompe
    def decorated_route(*args, **kwargs):
        token = request.cookies.get('X-Bonita-API-Token')
        if not token:
            return redirect('/login')
        return route_function(*args, **kwargs)
    return decorated_route

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/set_materials', methods=['GET'])
@login_required
@require_role('operator')
def set_materials():
    return render_template('materials.html')

@app.route('/design_collection', methods=['GET'])
@login_required
@require_role('designer')
def design_collection():
    return render_template('design.html')

@app.route('/get_variables/<string:case_id>', methods=['GET'])
@login_required
def get_variables(case_id):
    response = requests.get(f"{base_url}/get_all_variables/{case_id}")
    complete_activity = requests.put(f"{base_url}/completeactivity/{case_id}")
    return response.json()

@app.route('/login', methods=['POST'])
def submit_login():
    username = request.form.get('username')
    password = request.form.get('password')

    data = {
        "username": username,
        "password": password
    }
    # Enviar los datos al backend para el inicio de sesión
    response = requests.post(f"{base_url}/login", json=data)
    if response.status_code == 200:
        # Setea el cookie del token que retorna el login para que se almacene tambien en el front!!
        response_user = requests.get(f"{base_url}/get_user_by_username/{username}")
        userdata_json = response_user.json()
        user_id = int(userdata_json[0]["id"])
        res_role = requests.get(f"{base_url}/get_memberships/{user_id}")
        role_json = res_role.json()
        role_data = requests.get(f"{base_url}/get_role_data/{role_json[0]['role_id']}")
        role_data_json = role_data.json()
        token = response.json()
        resp = make_response(redirect('/design_collection'))
        # Establecer la cookie X-Bonita-API-Token en la respuesta
        resp.set_cookie('role', role_data_json["name"])
        resp.set_cookie('X-Bonita-API-Token', token["bonita_token"])
        resp.set_cookie('JSESSIONID', token["bonita_auth"])
        return resp

@app.route('/submit_design', methods=['POST'])
@login_required
def submit_design(): 
    # Obtener los datos del formulario
    data = {
        "categoria": request.form.get('categoria'),
        "caracteristicas": request.form.get('caracteristicas'),
        "modelos": request.form.get('modelos'),
        "plazo_fabricacion": request.form.get('plazo_fabricacion'),
        "fecha_lanzamiento": request.form.get('fecha_lanzamiento'),
        "informacion_adicional": request.form.get('informacion_adicional')
    }
    # Harcodeamos el nombre del pool
    response = requests.get(f"{base_url}/getprocessid/entrega-1")
    process_id = response.json()
    # Enviar los datos al backend para iniciar el proceso
    response1 = requests.post(f"{base_url}/initiateprocess/{process_id}", json=data)
    case_id = str(response1.json()['caseId'])
    #Buscar la tarea por caseid
    response2 = requests.get(f"{base_url}/searchactivitybycase/{case_id}")
    task_id = response2.json()['id']
    #Buscar usuario generico
    response3 = requests.get(f"{base_url}/get_user_by_username/walter.bates")
    user_id = response3.json()[0]['id']
    #Asignar la tarea al usuario
    response4 = requests.put(f"{base_url}/assigntask/{str(task_id)}/{str(user_id)}")
    if response4.status_code == 200:
        #Completar la tarea
        response5 = requests.post(f"{base_url}/completeactivity/{task_id}")
        if response5.status_code == 200:
            return "Proceso iniciado con exito"
        else:
            return "Error al iniciar el proceso"
    else:
        return "Error al iniciar el proceso"


@app.route('/submit_materials', methods=['POST'])
@login_required
def submit_materials(): 
    # Obtener los datos del formulario
    data = {
        "materiales": {
            request.form.get('material_1'): request.form.get('cantidad_1'),
            request.form.get('material_2'): request.form.get('cantidad_2'),
            request.form.get('material_3'): request.form.get('cantidad_3'),
            request.form.get('material_4'): request.form.get('cantidad_4')
        },
        "fecha_lanzamiento": request.form.get('fecha_lanzamiento')
    }
    
    # Filtrar materiales nulos o vacios
    data["materiales"] = {key: value for key, value in data["materiales"].items() if key and value}

    # Diccionario para almacenar proveedores por material
    proveedores_por_material = {}

    for material, cantidad in data["materiales"].items():
        response = requests.get(f"{api_url}/buscar/{material}/{data['fecha_lanzamiento']}/{cantidad}")
        proveedores = response.json()
        if not proveedores:  # Si no hay proveedores disponibles
            return render_template('materials.html')
        proveedores_por_material[material] = proveedores

    return render_template('reserve_materials.html', proveedores=proveedores_por_material)

if __name__ == '__main__':
    app.run(port=5001, debug=True)
