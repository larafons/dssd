from flask import Flask, request, jsonify
from functools import wraps
import requests
from pymongo import MongoClient

app = Flask(__name__)
base_url= "http://localhost:8080/bonita/"
base_url_api= "https://global-furniture-api.onrender.com" #http://localhost:5002/


#conexion a la base de datos de mongo
uri = "mongodb+srv://joaquincavenaghi:3cbNbq2GzlVUSzRV@dbglobalfurniture.zltrtey.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(uri)
db = client.dbglobalfurniture #accedemos a la coleccion dbglobalfurniture (es la q vamos a usar)

cookieJar = requests.Session()

def is_user_authenticated():
    #Se chequea en base al token de bonita
    return True if cookieJar.cookies.get("X-Bonita-API-Token") else False

# Decorador personalizado
def login_required(route_function):
    @wraps(route_function)
    def decorated_route(*args, **kwargs):
        # Verifica si el usuario está autenticado
        if not is_user_authenticated():
            return jsonify({"error": "Acceso no autorizado"}), 401  # Devuelve un error 401 no autorizado
        return route_function(*args, **kwargs)
    return decorated_route



@app.route('/login', methods=['POST'])
def login():
    body = request.get_json()
    username= body.get('username')
    password= body.get('password')
    return Process.login(username, password)

@app.route('/getall', methods=['GET'])
@login_required
def getall():
    return Process.get_all_processes()

@app.route('/getprocessname/<int:process_id>', methods=['GET'])
@login_required
def get_process_name(process_id):
    return Process.get_process_name(process_id)

@app.route('/getprocessid/<string:process_name>', methods=['GET'])
@login_required
def get_process_id(process_name):
    return Process.get_process_id(process_name)

@app.route('/getcountprocesses', methods=['GET'])
@login_required
def get_count_processes():
    return str(Process.get_count_processes())

@app.route('/initiateprocess/<int:process_id>', methods=['POST'])
@login_required
def initiate_process(process_id):
    data = request.get_json()
    db.model.insert_one(data)
    response = Process.initiate_process(process_id)
    return response.json()

@app.route('/get_pending_tasks/<int:case_id>', methods=['GET'])
@login_required
def get_pending_tasks(case_id):
    response = Process.get_pending_tasks(case_id)
    return jsonify(response.json())

@app.route('/setvariable/<int:task_id>/<string:variable>/<value>/<string:tipo>', methods=['PUT'])
@login_required
def set_variable(task_id, variable, value, tipo):
    response = Process.set_variable(task_id, variable, value, tipo)
    return jsonify(response.json())

@app.route('/setvariablebycase/<int:case_id>/<string:variable>/<value>/<string:tipo>', methods=['PUT'])
@login_required
def set_variable_by_case(case_id, variable, value, tipo):
    response = Process.set_variable_by_case(case_id, variable, value, tipo)
    return response

@app.route('/assigntask/<string:task_id>/<string:user_id>', methods=['PUT'])
@login_required
def assign_task(task_id, user_id):
    response = Process.assign_task(task_id, user_id)
    return str(response.status_code)

@app.route('/searchactivitybycase/<string:case_id>', methods=['GET'])
@login_required
def search_activity_by_case(case_id):
    response = Process.search_activity_by_case(case_id)
    return response

@app.route('/getvariable/<int:task_id>/<string:variable>', methods=['GET'])
@login_required
def get_variable(task_id, variable):
    return jsonify(Process.get_variable(task_id, variable))

@app.route('/getvariablebycase/<int:case_id>/<string:variable>', methods=['GET'])
@login_required
def get_variable_by_case(case_id, variable):
    return jsonify(Process.get_variable_by_case(case_id, variable))

@app.route('/get_all_variables/<string:case_id>', methods=['GET'])
@login_required
def get_all_variables(case_id):
    return jsonify(Process.get_all_variables_by_case(case_id))

@app.route('/completeactivity/<string:task_id>', methods=['POST'])
@login_required
def complete_activity(task_id):
    response = Process.complete_activity(task_id)
    return str(response.status_code)

@app.route('/get_user_by_username/<string:username>', methods=['GET'])
@login_required
def get_user_by_username(username):
    return jsonify(Process.get_user_by_username(username))

@app.route('/get_memberships/<int:user_id>', methods=['GET'])
@login_required
def get_memerships(user_id):
    return jsonify(Process.get_memberships(user_id))

@app.route('/get_role_data/<string:role_id>', methods=['GET'])
@login_required
def get_role_data(role_id):
    return jsonify(Process.get_role_data(role_id))

@app.route('/buscar/<string:material>/<string:fecha>/<int:cantidad>', methods=['GET'])
def get_material(material, fecha, cantidad):
    return jsonify(Process.get_material(material, fecha, cantidad))

@app.route('/get_case_id', methods=['GET'])
def get_case_id():
    return Process.get_case_id()


class Process:
    APItoken =''

    @staticmethod
    def login(username, password):
        try:
            # Realizar la solicitud POST al servicio de inicio de sesión
            login_url = f"{base_url}/loginservice"
            payload = {
                "username": username,
                "password": password,
                "redirect": "false"
            }
            response = cookieJar.post(login_url, data=payload)
            if response.status_code == 204:
                # Almacenar el token de Bonita en una variable de sesión
                token = cookieJar.cookies.get("X-Bonita-API-Token")
                sessionId = cookieJar.cookies.get("JSESSIONID")
                cookieJar.headers.update({
                    'bonita_token': cookieJar.cookies.get("X-Bonita-API-Token"),
                    'bonita_auth': cookieJar.cookies.get("JSESSIONID")
                })
                if token:
                    # Almacenar el token en una variable de sesión
                    payload = {
                        'bonita_token': token,
                        'bonita_auth': sessionId
                    }
                    return payload
                else:
                    return None  # Token no encontrado
            else:
                return None  # Autenticación fallida

        except requests.exceptions.RequestException as e:
            print(f"Error al hacer la solicitud: {str(e)}")
            return None
            
    @staticmethod
    def get_all_processes():
        try:
            # Utiliza la misma instancia de cookieJar creada en login()
            response = cookieJar.get(f"{base_url}API/bpm/process?p=0&c=1000")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error al hacer la solicitud: {str(e)}")
            return None

    @staticmethod
    def get_process_name(process_id):
        response = cookieJar.get(f"{base_url}API/bpm/process/{process_id}")
        process = response.json()['data']
        return process['name']

    @staticmethod
    def get_process_id(process_name):
        try:
            response = cookieJar.get(f"{base_url}API/bpm/process?f=name={process_name}&f=activationState=ENABLED")
            process = response.json()[0]
            return process["id"]
        except requests.exceptions.RequestException as e:
            print(f"Error al hacer la solicitud: {str(e)}")
            return None

    @staticmethod
    def get_count_processes():
        response = cookieJar.get(f"{base_url}API/bpm/process?p=0&c=1000")
        return len(response.json()['data'])

    @staticmethod
    def initiate_process(process_id):
        try:
            strprocess_id = str(process_id)
            cookieJar.headers.update({
                    'X-Bonita-API-Token': cookieJar.cookies.get("X-Bonita-API-Token")
                })
            response = cookieJar.post(f"{base_url}API/bpm/process/{strprocess_id}/instantiation")
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error al hacer la solicitud: {str(e)}")
            return None
        
    @staticmethod
    def get_pending_tasks(case_id):
        response = cookieJar.get(f"{base_url}/API/bpm/userTask?caseId={case_id}")
        return response

    @staticmethod
    def set_variable(task_id, variable, value, tipo):
        task_response = cookieJar.get(f"{base_url}API/bpm/userTask/{task_id}")
        case_id = task_response.json()['data']['caseId']
        response = cookieJar.put(f"{base_url}API/bpm/caseVariable/{case_id}/{variable}", json={variable: value, 'type': tipo})
        return response

    @staticmethod
    def set_variable_by_case(case_id, variable, value, tipo):
        print(value)
        print(tipo)
        response = cookieJar.put(f"{base_url}API/bpm/caseVariable/{case_id}/{variable}", json={"type": tipo, "value": value})
        return response

    @staticmethod
    def get_count_processes():
        response = cookieJar.get(f"{base_url}API/bpm/process?p=05c-1000")
        return len(response.json()['data'])

    @staticmethod
    def assign_task(task_id, user_id):
        response = cookieJar.put(f"{base_url}API/bpm/userTask/{task_id}", json={"assigned_id": user_id})
        return response

    @staticmethod
    def search_activity_by_case(case_id):
        response = cookieJar.get(f"{base_url}API/bpm/task?f=caseId={case_id}")
        return response.json()[0]
    
    @staticmethod
    def complete_activity(task_id):
        response = cookieJar.post(f"{base_url}API/bpm/userTask/{task_id}/execution", json={"state": "completed"})
        return response

    @staticmethod
    def get_variable(task_id, variable):
        case_bonita = cookieJar.get(f"{base_url}API/bpm/userTask/{task_id}")
        case_id = case_bonita.json()['data']['caseId']
        var_bonita = cookieJar.get(f"{base_url}API/bpm/caseVariable/{case_id}/{variable}")
        return var_bonita.json()['data']

    @staticmethod
    def get_variable_by_case(case_id, variable):
        var_bonita = cookieJar.get(f"{base_url}API/bpm/caseVariable/{case_id}/{variable}")
        return { var_bonita.json()['name'] : var_bonita.json()['value'] }
    
    @staticmethod
    def get_all_variables_by_case(case_id):
        var_bonita = cookieJar.get(f"{base_url}API/bpm/caseVariable?f=case_id={case_id}")
        return var_bonita.json()
    
    @staticmethod
    def get_task_by_id(case_id):
        var_bonita = cookieJar.get(f"{base_url}API/bpm/task/{case_id}")
        return var_bonita.json()
    
    @staticmethod
    def get_user_by_username(username):
        var_bonita = cookieJar.get(f"{base_url}API/identity/user?f=userName={username}")
        return var_bonita.json()
    
    @staticmethod
    def get_memberships(user_id):
        var_bonita = cookieJar.get(f"{base_url}API/identity/membership?f=user_id={user_id}")
        return var_bonita.json()
    
    @staticmethod
    def get_role_data(role_id):
        var_bonita = cookieJar.get(f"{base_url}API/identity/role/{role_id}")
        return var_bonita.json()
    
    @staticmethod
    def get_case_id():
        request = cookieJar.get(f"{base_url}API/bpm/case?f=name=entrega-1")
        process = request.json()[0]
        return process["rootCaseId"]
    
    @staticmethod
    def get_material(material, fecha, cantidad):

        # Credenciales de autenticación
        credentials = {
            "username": "walter.bates",
            "password": "bpm"
        }

        # Realizar una solicitud de autenticación para obtener un token JWT
        response = requests.post(f"{base_url_api}login", json=credentials)

        if response.status_code == 200:
            token = response.json().get('token')
            if token:
                # Almacenar el token en una variable
                APItoken = token
                print("Token JWT obtenido con éxito.")

                # Llamar al método /buscar/<material>/<fecha>/<cant> con el token
                buscar_url = f"{base_url_api}/buscar/{material}/{fecha}/{cantidad}"  # Reemplaza con los valores deseados
                headers = {'Authorization': f'Bearer {token}'}
                response = requests.get(buscar_url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    # Procesa los datos de la solicitud /buscar
                    print("Resultado de la búsqueda:")
                    print(data)
                    return data
                else:
                    print(f"Error al llamar la ruta de búsqueda: {response.status_code}, {response.json()}")
                    return(f"Error al llamar la ruta de búsqueda: {response.status_code}, {response.json()}")
            else:
                print("No se pudo obtener un token JWT.")
                return ("No se pudo obtener un token JWT.")
        else:
            print(f"Error en la autenticación: {response.status_code}, {response.json()}")
            return (f"Error en la autenticación: {response.status_code}, {response.json()}")

if __name__ == "__main__":
    app.run(debug=True)
