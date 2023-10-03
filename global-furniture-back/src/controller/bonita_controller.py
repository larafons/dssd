from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
base_url= "http://localhost:8080/bonita/"

cookieJar = requests.Session()

@app.route('/login', methods=['POST'])
def login():
    return Process.login()

@app.route('/getall', methods=['GET'])
def getall():
    return Process.get_all_processes()

@app.route('/getprocessname/<int:process_id>', methods=['GET'])
def get_process_name(process_id):
    return Process.get_process_name(process_id)

@app.route('/getprocessid/<string:process_name>', methods=['GET'])
def get_process_id(process_name):
    return Process.get_process_id(process_name)

@app.route('/getcountprocesses', methods=['GET'])
def get_count_processes():
    return str(Process.get_count_processes())

@app.route('/initiateprocess/<int:process_id>', methods=['POST'])
def initiate_process(process_id):
    response = Process.initiate_process(process_id)
    return response.json()

@app.route('/setvariable/<int:task_id>/<string:variable>/<value>/<string:tipo>', methods=['PUT'])
def set_variable(task_id, variable, value, tipo):
    response = Process.set_variable(task_id, variable, value, tipo)
    return jsonify(response.json())

@app.route('/setvariablebycase/<int:case_id>/<string:variable>/<value>/<string:tipo>', methods=['PUT'])
def set_variable_by_case(case_id, variable, value, tipo):
    response = Process.set_variable_by_case(case_id, variable, value, tipo)
    return jsonify(response.json())

@app.route('/assigntask/<int:task_id>/<int:user_id>', methods=['PUT'])
def assign_task(task_id, user_id):
    response = Process.assign_task(task_id, user_id)
    return jsonify(response.json())

@app.route('/searchactivitybycase/<int:case_id>', methods=['GET'])
def search_activity_by_case(case_id):
    response = Process.search_activity_by_case(case_id)
    return jsonify(response.json())

@app.route('/completeactivity/<int:task_id>', methods=['POST'])
def complete_activity(task_id):
    response = Process.complete_activity(task_id)
    return jsonify(response.json())

@app.route('/getvariable/<int:task_id>/<string:variable>', methods=['GET'])
def get_variable(task_id, variable):
    return jsonify(Process.get_variable(task_id, variable))

@app.route('/getvariablebycase/<int:case_id>/<string:variable>', methods=['GET'])
def get_variable_by_case(case_id, variable):
    return jsonify(Process.get_variable_by_case(case_id, variable))

class Process:
    @staticmethod
    def login():
        try:
            # Realizar la solicitud POST al servicio de inicio de sesión
            login_url = f"{base_url}/loginservice"
            payload = {
                "username": "walter.bates",
                "password": "bpm",
                "redirect": "false"
            }

            response = cookieJar.post(login_url, data=payload)
            if response.status_code == 204:
                # Almacenar el token de Bonita en una variable de sesión
                token = cookieJar.cookies.get("X-Bonita-API-Token")
                cookieJar.headers.update({
                    'bonita_token': cookieJar.cookies.get("X-Bonita-API-Token"),
                    'bonita_auth': cookieJar.cookies.get("JSESSIONID")
                })
                if token:
                    # Almacenar el token en una variable de sesión
                    session_token = token
                    return session_token
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
    def set_variable(task_id, variable, value, tipo):
        task_response = cookieJar.get(f"{base_url}API/bpm/userTask/{task_id}")
        case_id = task_response.json()['data']['caseId']
        response = cookieJar.put(f"{base_url}API/bp/caseVariable/{case_id}/{variable}", json={variable: value, 'type': tipo})
        return response

    @staticmethod
    def set_variable_by_case(case_id, variable, value, tipo):
        response = cookieJar.put(f"{base_url}API/bp/caseVariable/{case_id}/{variable}", json={variable: value, 'type': tipo})
        return response

    @staticmethod
    def get_count_processes():
        response = cookieJar.get(f"{base_url}API/bpm/process?p=05c-1000")
        return len(response.json()['data'])


    @staticmethod
    def assign_task(task_id, user_id):
        response = requests.put(f"{base_url}API/bpm/userTask/{task_id}", json={"userId": user_id})
        return response

    @staticmethod
    def search_activity_by_case(case_id):
        response = requests.get(f"{base_url}API/bpm/task?f=caseId{case_id}")
        return response
    
    @staticmethod
    def complete_activity(task_id):
        response = requests.post(f"{base_url}API/bpm/userTask/{task_id}/execution")
        return response

    @staticmethod
    def get_variable(task_id, variable):
        case_bonita = requests.get(f"{base_url}API/bpm/userTask/{task_id}")
        case_id = case_bonita.json()['data']['caseId']
        var_bonita = requests.get(f"{base_url}API/bpm/caseVariable/{case_id}/{variable}")
        return var_bonita.json()['data']

    @staticmethod
    def get_variable_by_case(case_id, variable):
        var_bonita = requests.get(f"{base_url}API/bpm/caseVariable/{case_id}/{variable}")
        return var_bonita.json()['data']

if __name__ == "__main__":
    app.run(debug=True)
