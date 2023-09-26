from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
base_url= "http://localhost:8080/bonita/"

@app.route('/login', methods=['POST'])
def login():
    return Process.login()

@app.route('/getall', methods=['GET'])
def getall():
    return Process.get_all_processes()

class Process:
    @staticmethod
    def login():
        try:
            # Crear una cookie jar para almacenar las cookies
            cookieJar = requests.Session()
            # Realizar la solicitud POST al servicio de inicio de sesión
            login_url = f"{base_url}/loginservice"
            payload = {
                "username": "walter.bates",
                "password": "bpm",
                "redirect": "false"
            }

            response = cookieJar.post(login_url, data=payload)
            print(response)
            if response.status_code == 204:
                # Almacenar el token de Bonita en una variable de sesión
                token = cookieJar.cookies.get("X-Bonita-API-Token")
                print(token)
                if token:
                    print('entra')
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
        response = requests.get(f"{base_url}/API/bpm/process?p=0&c=1000")
        print(response)
        return response.json()

    @staticmethod
    def get_process_name(process_id):
        response = requests.get(f"{base_url}/API/bpm/process/{process_id}")
        process = response.json()['data']
        return process['name']

    @staticmethod
    def get_process_id(process_name):
        response = requests.get(f"{base_url}/API/bpm/process?f=name:{process_name}&f=activationState=ENABLED")
        process = response.json()['data'][0]
        return process['id']

    @staticmethod
    def get_count_processes():
        response = requests.get(f"{base_url}/API/bpm/process?p=0&c=1000")
        return len(response.json()['data'])

    @staticmethod
    def initiate_process(process_id):
        response = requests.post(f"{base_url}/API/bpm/process/{process_id}/instantiation")
        return response

    @staticmethod
    def set_variable(task_id, variable, value, tipo):
        task_response = requests.get(f"{base_url}/API/bpm/userTask/{task_id}")
        case_id = task_response.json()['data']['caseId']
        response = requests.put(f"{base_url}/API/bp/caseVariable/{case_id}/{variable}", json={variable: value, 'type': tipo})
        return response

    @staticmethod
    def set_variable_by_case(case_id, variable, value, tipo):
        response = requests.put(f"{base_url}/API/bp/caseVariable/{case_id}/{variable}", json={variable: value, 'type': tipo})
        return response
    
    @staticmethod
    def get_process_name(process_id):
        response = requests.get(f"{base_url}/API/bpm/process/{process_id}")
        process = response.json()['data']
        return process['name']

    @staticmethod
    def get_process_id(process_name):
        response = requests.get(f"{base_url}API/bpm/process?f=name:{process_name}&p=08c-180-version%20desc&f=activationState=ENABLED")
        process = response.json()['data'][0]
        return process['id']

    @staticmethod
    def get_count_processes():
        response = requests.get(f"{base_url}API/bpm/process?p=05c-1000")
        return len(response.json()['data'])

    @staticmethod
    def initiate_process(process_id):
        response = requests.post(f"{base_url}API/bpm/process/{process_id}/instantiation")
        return response

    @staticmethod
    def set_variable(task_id, variable, value, tipo):
        task_response = requests.get(f"API/bpm/userTask/{task_id}")
        case_id = task_response.json()['data']['caseId']
        response = requests.put(f"{base_url}API/bpm/caseVariable/{case_id}/{variable}", json={variable: value, 'type': tipo})
        return response

    @staticmethod
    def set_variable_by_case(case_id, variable, value, tipo):
        response = requests.put(f"{base_url}API/bp/caseVariable/{case_id}/{variable}", json={variable: value, 'type': tipo})
        return response

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
