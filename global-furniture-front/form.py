from flask import Flask, render_template, request, redirect, url_for, Response, make_response
import requests
from functools import wraps
import datetime
import time 
import requests
import base64
import json

app = Flask(__name__)
base_url = "http://localhost:5000"  # Reemplaza con la URL de tu backend

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
    file = request.files['imagen']
    data = {
        "categoria": request.form.get('categoria'),
        "caracteristicas": request.form.get('caracteristicas'),
        "modelos": request.form.get('modelos'),
        "plazo_fabricacion": request.form.get('plazo_fabricacion'),
        "fecha_lanzamiento": request.form.get('fecha_lanzamiento'),
        "informacion_adicional": request.form.get('informacion_adicional'),
        "file": base64.b64encode(file.read()).decode('utf-8'),
    }
    # Harcodeamos el nombre del pool
    response = requests.get(f"{base_url}/getprocessid/entrega-1")
    process_id = response.json()
    # Enviar los datos al backend para iniciar el proceso
    response1 = requests.post(f"{base_url}/initiateprocess/{process_id}", json=data)
    case_id = str(response1.json()['caseId'])
    #Buscar la tarea por caseid
    response2 = requests.get(f"{base_url}/searchactivitybycase/{case_id}/Completar-formulario-diseño")
    task_id = response2.json()[0]['id']
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
    materiales_dict = {}

    # Iterar sobre los campos del formulario
    for i in range(1, 5):
        material = request.form.get(f'material_{i}') or ' '
        cantidad = request.form.get(f'cantidad_{i}') or '0'
        print("Entro en el for " + str(i) + ": " + material + " " + cantidad)
        # Añade el material y la cantidad al diccionario
        materiales_dict[f'material_{i}'] = material
        materiales_dict[f'cantidad_{i}'] = int(cantidad)  # Convertir a int

    # Estructurar el dato final
    data = {
        "materiales": materiales_dict,
        "fecha_lanzamiento": request.form.get('fecha_lanzamiento')
    }

    #Seteo de variables de proceso los materiales y cantidades como si fuera un dump de json
    materials_json = json.dumps(data["materiales"])

    #Obtenemos el case id
    response = requests.get(f"{base_url}/get_case_id")
    case_id = response.json()

    # Setear las variables del proceso
    response0 = requests.put(f"{base_url}/setvariablebycase/{int(case_id)}/fecha_lanzamiento/{data['fecha_lanzamiento']}/java.lang.String")
    response = requests.put(f"{base_url}/setvariablebycase/{int(case_id)}/materials_cants/{materials_json}/java.lang.String")

    # Verificar si las variables se setearon correctamente
    if response.status_code != 200 or response0.status_code != 200:
        return "Error al establecer las variables del proceso"

    # Buscar la tarea actual por case_id
    response1 = requests.get(f"{base_url}/searchactivitybycase/{case_id}/Establecer-materiales-y-cantidades")
    
    task_id = response1.json()[0]['id']
    
    response2 = requests.get(f"{base_url}/get_user_by_username/antonio.operator")
    user_id = response2.json()[0]['id']
    
    # Asignar la tarea al usuario
    response3 = requests.put(f"{base_url}/assigntask/{str(task_id)}/{str(user_id)}")
    
    if response3.status_code == 200:
        # Completar la tarea para avanzar el flujo
        response4 = requests.post(f"{base_url}/completeactivity/{task_id}")
        """"
        if response4.status_code == 200:
            time.sleep(5)  # Espera de 5 segundos
            # Consulta al endpoint de Bonita para obtener las tareas pendientes para el caso
            response_tasks = requests.get(f"{base_url}/get_pending_tasks/{case_id}")
            
            if response_tasks.status_code == 200:
                tasks_data = response_tasks.json()

                # Busca en las tareas a ver si la tarea de reserva de materiales está pendiente o la de establecer para 
                # ver cual mostrar en el front
                if any(task for task in tasks_data if task["name"] == "Reservar materiales" and task["state"] == "ready"):
                    return render_template('reserve_materials.html')
                elif any(task for task in tasks_data if task["name"] == "Establecer materiales y cantidades" and task["state"] == "ready"):
                    return render_template('materials.html')
                else:
                    return "Estado desconocido. Por favor, revisa las tareas pendientes en Bonita."
            else:
                return "Error al consultar las tareas pendientes en Bonita."
        else:
            return "Error al avanzar el proceso"
        """
    else:
        return "Error al asignar la tarea"
    return "check"

if __name__ == '__main__':
    app.run(port=5001, debug=True)
