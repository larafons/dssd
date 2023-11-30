from flask import Flask, render_template, request, redirect, url_for, Response, make_response
import requests
from functools import wraps
import datetime
import time 
import requests
import base64
import json
import matplotlib.pyplot as plt
from cryptography.fernet import Fernet

app = Flask(__name__)
base_url = "http://localhost:5000" 

key = Fernet.generate_key()
cipher_suite = Fernet(key)

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
            # Decrypt
            plain_text = (cipher_suite.decrypt(user_role)).decode()
            if role == plain_text:
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

@app.route('/set_materials/<int:case_id>', methods=['GET'])
@login_required
@require_role('operator')
def set_materials(case_id):
    return render_template('materials.html', case =case_id)

@app.route('/design_collection', methods=['GET'])
@login_required
@require_role('designer')
def design_collection():
    return render_template('design.html')

@app.route('/designers', methods=['GET'])
@login_required
@require_role('designer')
def designers():
    return render_template('designer.html')

@app.route('/charge_order', methods=['GET'])
@login_required
@require_role('marketing')
def update_collection():
    collections = requests.get(f"{base_url}/get_not_sede")
    return render_template('charge_order.html', collections=collections.json())

@app.route('/operators', methods=['GET'])
@login_required
@require_role('operator')
def operator_page():
    response = requests.get(f"{base_url}/get_all_pending_tasks")
    tasks= response.json()
    filtered_tasks = [task for task in tasks if task['name'] in ('Establecer materiales y cantidades', 'Reservar materiales', 'Confirmar Plan de Fabricación', 'Consultas de plazos', 'Cancelar reservas')]
    return render_template('operator.html', tasks=filtered_tasks)

@app.route('/marketing', methods=['GET'])
@login_required
@require_role('marketing')
def marketing_page():
    return render_template('marketing.html')

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
        #Very hard encryption
        data = "VLLC!AirForces".encode()
        cipher_role = cipher_suite.encrypt(role_data_json["name"].encode())
        #Redirige a a persona dependiendo del rol
        if (role_data_json["name"] == 'designer'):
            resp = make_response(redirect('/designers'))
        elif (role_data_json["name"] == 'operator'):
            resp = make_response(redirect('/operators'))
        elif (role_data_json["name"] == 'marketing'):
            resp = make_response(redirect('/marketing'))
        # Establecer la cookie X-Bonita-API-Token en la respuesta
        resp.set_cookie('role', cipher_role)
        resp.set_cookie('X-Bonita-API-Token', token["bonita_token"])
        resp.set_cookie('JSESSIONID', token["bonita_auth"])
        return resp

@app.route('/logout', methods=['POST'])
def submit_logout():
    # Enviar los datos al backend para el logout de sesión
    response = requests.post(f"{base_url}/logout")
    # Remove cookies
    resp = make_response(redirect('/login'))
    resp.delete_cookie('X-Bonita-API-Token')
    resp.delete_cookie('JSESSIONID')
    resp.delete_cookie('role')
    return resp

@app.route('/submit_design', methods=['POST'])
@login_required
def submit_design(): 
    # Obtener los datos del formulario
    file = request.files['imagen']
    data = {
        "nombre": request.form.get('nombre'),
        "categoria": request.form.get('categoria'),
        "caracteristicas": request.form.get('caracteristicas'),
        "modelos": request.form.get('modelos'),
        "plazo_fabricacion": request.form.get('plazo_fabricacion'),
        "fecha_lanzamiento": request.form.get('fecha_lanzamiento'),
        "informacion_adicional": request.form.get('informacion_adicional'),
        "file": base64.b64encode(file.read()).decode('utf-8'),
        "sede": "Ninguna",
        "finalizadaOperator": False,
        "finalizadaMarketing": False,
        "case_id": 101,
        "mostrar": True
    }
    plazo_fabricacion= request.form.get('plazo_fabricacion')
    fecha_lanzamiento= request.form.get('fecha_lanzamiento')
    fecha_lanzamiento = datetime.datetime.strptime(fecha_lanzamiento, '%Y-%m-%d') 
    if fecha_lanzamiento < datetime.datetime.now()+datetime.timedelta(days=int(plazo_fabricacion)):
        return render_template('sweet_alert.html', message="error al designar la coleccion, la fecha de lanzamiento debe ser mayor al plazo de fabricacion", url="/designers")
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
    #Guardo el plazo de fabricacion en la variable de proceso
    response33 = requests.put(f"{base_url}/setvariablebycase/{int(case_id)}/plazo_fabricacion/{plazo_fabricacion}/java.lang.String")
    #Asignar la tarea al usuario
    response4 = requests.put(f"{base_url}/assigntask/{str(task_id)}/{str(user_id)}")
    if response4.status_code == 200:
        #Completar la tarea
        response5 = requests.post(f"{base_url}/completeactivity/{task_id}")
        if response5.status_code == 200:
            return render_template('sweet_alert.html', message="Proceso iniciado con éxito", url="/designers")
        else:
            return render_template('sweet_alert.html', message="error al inciar el proceso", url="/designers")
    else:
        return render_template('sweet_alert.html', message="error al inciar el proceso", url="/designers")


@app.route('/submit_materials/<int:case>', methods=['POST'])
@login_required
def submit_materials(case=-1): 
    materiales_dict = {}
    # Iterar sobre los campos del formulario
    for i in range(1, 5):
        material = request.form.get(f'material_{i}') or ' '
        cantidad = request.form.get(f'cantidad_{i}') or '0'
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

    # Usar un valor predeterminado para case si es None
    if case == -1: 
        # Obtener el case id
        response = requests.get(f"{base_url}/get_case_id")
        case_id = response.json()
    else:
        # Utilizar el valor proporcionado para case
        case_id = case
    # Setear las variables del proceso
    response0 = requests.put(f"{base_url}/setvariablebycase/{int(case_id)}/fecha_lanzamiento/{data['fecha_lanzamiento']}/java.lang.String")
    response = requests.put(f"{base_url}/setvariablebycase/{int(case_id)}/materials_cants/{materials_json}/java.lang.String")

    plazo_fabricacion = requests.get(f"{base_url}/getvariablebycase/{int(case_id)}/plazo_fabricacion")
    plazo_fabricacion = plazo_fabricacion.json()['plazo_fabricacion']
    fecha_lanzamiento = data['fecha_lanzamiento']
    fecha_lanzamiento = datetime.datetime.strptime(fecha_lanzamiento, '%Y-%m-%d') 
    if fecha_lanzamiento < datetime.datetime.now()+datetime.timedelta(days=int(plazo_fabricacion)):
        return render_template('sweet_alert.html', message="error al setear los materiales, la fecha de lanzamiento debe ser mayor al plazo de fabricacion", url="/operators")
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
    sigue = True
    if response3.status_code == 200:
        # Completar la tarea para avanzar el flujo
        response4 = requests.post(f"{base_url}/completeactivity/{task_id}")

        if response4.status_code == 200:
            # Consulta al endpoint de Bonita para obtener las tareas pendientes para el caso
            response_tasks = requests.get(f"{base_url}/get_pending_tasks/{int(case_id)}")
            if response_tasks.status_code == 200:
                tasks_data = response_tasks.json()
                while not any(task for task in tasks_data if task["name"] in ("Reservar materiales","Establecer materiales y cantidades") and task["state"] == "ready" and task["caseId"] == str(case_id)) or sigue:
                    time.sleep(5)
                    sigue = False
                    response_tasks = requests.get(f"{base_url}/get_pending_tasks/{int(case_id)}")
                    tasks_data = response_tasks.json()
                    if any(task for task in tasks_data if task["name"] == "Reservar materiales" and task["state"] == "ready"):
                        #Obtengo la respuesta de la api que se almaceno como var de proceso en bonita
                        response_proveedores = requests.get(f"{base_url}/getvariablebycase/{int(case_id)}/proveedores")
                        proveedores = response_proveedores.json()
                        #Casteo de string a json diccionario en python
                        proveedores_data = json.loads(proveedores['proveedores'])
                        return render_template('reserve_materials.html',proveedores=proveedores_data, case= case_id)
                    elif any(task for task in tasks_data if task["name"] == "Establecer materiales y cantidades" and task["state"] == "ready"):
                        return render_template('sweet_alert.html', message="cantidad de materiales no disponible para la fecha ingresada, pruebe con otros materiales u otra coleccion", url= "/operators")

            else:
                return "Error al consultar las tareas pendientes en Bonita."
        else:
            return "Error al avanzar el proceso"
    else:
        return "Error al asignar la tarea"

@app.route('/confirmar_proveedores/<int:case>', methods=['POST'])
@login_required
def confirmar_proveedores(case=-1):
    # Recopilar datos del formulario
    datos_confirmados = {}
    fechaMax = "2000-01-01"
    for material, proveedores in request.form.items():
        if (proveedores.split(",")[1] > fechaMax):
            fechaMax = proveedores.split(",")[1]
        datos_confirmados[material] = proveedores # nombre,fecha
    # Usar un valor predeterminado para case si es None
    if case == -1: 
        # Obtener el case id
        response = requests.get(f"{base_url}/get_case_id")
        case_id = response.json()
    else:
        # Utilizar el valor proporcionado para case
        case_id = case
    response_materials = requests.get(f"{base_url}/getvariablebycase/{int(case_id)}/materials_cants")
    response = requests.put(f"{base_url}/setvariablebycase/{int(case_id)}/fecha_entrega/{fechaMax}/java.lang.String")
    materials = response_materials.json()
    #Casteo de string a json diccionario en python
    materials_data = json.loads(materials['materials_cants'])
    for material, prov in datos_confirmados.items():
        for key, value in materials_data.items():
            if material == value:
                consulta = {
                    f"material_{key[-1]}": material,
                    f"cantidad_{key[-1]}": materials_data[f"cantidad_{key[-1]}"],
                    f"name_{key[-1]}": prov.split(",")[0],
                    f"fecha_{key[-1]}": prov.split(",")[1]
                }
                consulta_json = json.dumps(consulta)
                response = requests.put(f"{base_url}/setvariablebycase/{int(case_id)}/reserva_material_{key[-1]}/{consulta_json}/java.lang.String")
    if response.status_code != 200:
        return "Error al establecer las variables del proceso"
    # Buscar la tarea actual por case_id
    response1 = requests.get(f"{base_url}/searchactivitybycase/{case_id}/Reservar-materiales")
    task_id = response1.json()[0]['id']
    if response1.status_code == 200:
        response2 = requests.get(f"{base_url}/get_user_by_username/antonio.operator")
        user_id = response2.json()[0]['id']
        # Asignar la tarea al usuario
        requests.put(f"{base_url}/assigntask/{str(task_id)}/{str(user_id)}")
        # Completar la tarea para avanzar el flujo
        response2 = requests.post(f"{base_url}/completeactivity/{task_id}")
        if response2.status_code == 200:
            time.sleep(7)
            # Consulta al endpoint de Bonita para obtener las tareas pendientes para el caso
            response_tasks = requests.get(f"{base_url}/get_pending_tasks/{int(case_id)}")
            if response_tasks.status_code == 200:
                tasks_data = response_tasks.json()
                # Busca en las tareas a ver si la tarea de reserva de materiales está pendiente o la de establecer para 
                if any(task for task in tasks_data if task["name"] == "Reservar espacios de fabricacion para la coleccion" and task["state"] == "ready"):
                    response_espacios = requests.get(f"{base_url}/getvariablebycase/{int(case_id)}/espacios")
                    espacios = response_espacios.json()
                    #Casteo de string a json diccionario en python
                    espacios_data = json.loads(espacios['espacios'])
                    return render_template('reserva_espacios.html',espacios=espacios_data,case= case_id)

@app.route("/confirmar_espacio/<int:case>", methods=["POST"])
@require_role('operator')
@login_required
def confirmar_espacio(case=-1):
    espacio_seleccionado = request.form.get('espacio')

    if case == -1: 
        # Obtener el case id
        response = requests.get(f"{base_url}/get_case_id")
        case_id = response.json()
    else:
        # Utilizar el valor proporcionado para case
        case_id = case
    response = requests.put(f"{base_url}/setvariablebycase/{int(case_id)}/espacio_seleccionado/{espacio_seleccionado}/java.lang.String")
    # Buscar la tarea actual por case_id
    response1 = requests.get(f"{base_url}/searchactivitybycase/{case_id}/Reservar-espacios-de-fabricacion-para-la-coleccion")
    task_id = response1.json()[0]['id']
    if response1.status_code == 200:
        response2 = requests.get(f"{base_url}/get_user_by_username/antonio.operator")
        user_id = response2.json()[0]['id']
        # Asignar la tarea al usuario
        requests.put(f"{base_url}/assigntask/{str(task_id)}/{str(user_id)}")
        # Completar la tarea para avanzar el flujo
        response2 = requests.post(f"{base_url}/completeactivity/{task_id}")

        if response2.status_code == 200:
            time.sleep(7)
            response_tasks = requests.get(f"{base_url}/get_pending_tasks/{int(case_id)}")
            if response_tasks.status_code == 200:
                tasks_data = response_tasks.json()
                # Busca en las tareas a ver si la tarea de reserva de materiales está pendiente o la de establecer para 
                # ver cual mostrar en el front
                if any(task for task in tasks_data if task["name"] == "Confirmar Plan de Fabricacion" and task["state"] == "ready"):
                    #Obtengo la respuesta de la api que se almaceno como var de proceso en bonita
                    espacio = requests.get(f"{base_url}/getvariablebycase/{int(case_id)}/espacio_seleccionado")
                    espacio = espacio.json()['espacio_seleccionado']
                    fecha_entrega = requests.get(f"{base_url}/getvariablebycase/{int(case_id)}/fecha_entrega")
                    fecha_entrega = fecha_entrega.json()['fecha_entrega']
                    lanzamiento = requests.get(f"{base_url}/getvariablebycase/{int(case_id)}/fecha_lanzamiento")
                    lanzamiento = lanzamiento.json()['fecha_lanzamiento']
                    materiales = []
                    for i in range(1, 5):
                        x = str(i)
                        material = requests.get(f"{base_url}/getvariablebycase/{int(case_id)}/reserva_material_{x}")
                        material =  json.loads(material.json()[f"reserva_material_{x}"])
                        if material[f"cantidad_{x}"] > 0:
                            materiales.append(material[f"material_{x}"] + " : " + str(material[f"cantidad_{x}"]) + " unidades para la fecha " + material[f"fecha_{x}"])
                    return render_template('confirmation.html',espacio=espacio,fecha_entrega=fecha_entrega,lanzamiento=lanzamiento,materiales=materiales, case= case_id)


@app.route('/confirm_plan/<int:case>', methods=['POST'])
@require_role('operator')
@login_required
def confirm_plan(case=-1):
    confirmo = request.form.get('confirmo')
    if case == -1: 
        # Obtener el case id
        response = requests.get(f"{base_url}/get_case_id")
        case_id = response.json()
    else:
        # Utilizar el valor proporcionado para case
        case_id = case
    response = requests.put(f"{base_url}/setvariablebycase/{int(case_id)}/confirmo/{confirmo}/java.lang.Boolean")
    response1 = requests.get(f"{base_url}/searchactivitybycase/{case_id}/Confirmar-Plan-de-Fabricacion")
    task_id = response1.json()[0]['id']
    response2 = requests.get(f"{base_url}/get_user_by_username/antonio.operator")
    user_id = response2.json()[0]['id']
    requests.put(f"{base_url}/assigntask/{str(task_id)}/{str(user_id)}")
    response2 = requests.post(f"{base_url}/completeactivity/{task_id}")
    response3 = requests.post(f"{base_url}/send_collection/{case}")
    time.sleep(7)
    if confirmo == 'true':
        return render_template('sweet_alert.html', message="éxito al confirmar plan de fabricación", url="/operators")
    else:
        return render_template('sweet_alert.html', message="éxito al cancelar el plan de fabricación", url="/operators")


@app.route('/update_collection', methods=['POST'])
@login_required
@require_role('marketing')
def update_order():
    collection_id = request.form['collection_id']
    new_sede = request.form['new_sede']
    # Actualizar en la base de datos (usando pymongo)
    response = requests.post(f"{base_url}/update_collection/{collection_id}/{new_sede}")
    response2 = requests.get(f"{base_url}/searchactivitybycase/{collection_id}/Cargar-ordenes-de-distribucion")
    task_id = response2.json()[0]['id']
    response = requests.post(f"{base_url}/send_collection_marketing/{collection_id}")
    #Buscar usuario generico
    response3 = requests.get(f"{base_url}/get_user_by_username/daniela.marketing")
    user_id = response3.json()[0]['id']
    #Asignar la tarea al usuario
    response4 = requests.put(f"{base_url}/assigntask/{str(task_id)}/{str(user_id)}")
    if response4.status_code == 200:
        #Completar la tarea
        response5 = requests.post(f"{base_url}/completeactivity/{task_id}")
        if response5.status_code == 200:
            response = requests.get(f"{base_url}/get_not_sede")
            return render_template('charge_order.html', collections=response.json(), message='Sede actualizada correctamente')

@app.route('/enviar_lote/<int:case>', methods=['POST'])
def enviar_lote(case=-1):
    if case == -1: 
        # Obtener el case id
        response = requests.get(f"{base_url}/get_case_id")
        case_id = response.json()
    else:
        # Utilizar el valor proporcionado para case
        case_id = case
    # Actualizar en la base de datos (usando pymongo)
    response2 = requests.get(f"{base_url}/searchactivitybycase/{case}/Asociar-lotes-con-sede")
    task_id1 = response2.json()[0]['id']
    task_id2 = response2.json()[1]['id']

    #Buscar usuario generico
    response3 = requests.get(f"{base_url}/get_user_by_username/daniela.marketing")
    user_id = response3.json()[0]['id']

    #Asignar la tarea al usuario
    response4 = requests.put(f"{base_url}/assigntask/{str(task_id1)}/{str(user_id)}")
    response4 = requests.put(f"{base_url}/assigntask/{str(task_id2)}/{str(user_id)}")
    if response4.status_code == 200:
        #Completar la tarea
        response5 = requests.post(f"{base_url}/completeactivity/{task_id1}")
        response5 = requests.post(f"{base_url}/completeactivity/{task_id2}")
        if response5.status_code == 200:
            requests.post(f"{base_url}/finish_collection/{case}")
            unset = requests.get(f"{base_url}/get_unset_collections")
            set= requests.get(f"{base_url}/get_set_collections")
            nueva = []
            for item in set.json():
                response = requests.get(f"{base_url}/getvariablebycase/{int(item['case_id'])}/termino")
                if response.json()['termino'] == '200':
                    nueva.append(item)
            return render_template('coleccion_sede.html', unset= unset.json(), set=nueva)


@app.route('/sedes', methods=['GET'])
@login_required
@require_role('marketing')
def sedes():
    unset = requests.get(f"{base_url}/get_unset_collections")
    set= requests.get(f"{base_url}/get_set_collections")
    nueva = []
    for item in set.json():
        response = requests.get(f"{base_url}/getvariablebycase/{int(item['case_id'])}/termino")
        if response.json()['termino'] == '200':
            nueva.append(item)
    return render_template('coleccion_sede.html', unset= unset.json(), set=nueva)

@app.route('/indicators', methods=["GET"])
@login_required
@require_role('marketing')
def get_indicators():
    collections_sedes = requests.get(f"{base_url}/get_all_sedes")
    datos = list(collections_sedes.json())
    # Contabilizar las ocurrencias
    conteo = {}
    for item in datos:
        sede = item['sede']
        if sede in conteo:
            conteo[sede] += 1
        else:
            conteo[sede] = 1

    # Obtengo todos los cases para consultar por los espacios en el id
    conteo_espacios = {}
    confirmados = 0
    sin_confirmar= 0
    case_ids_response = requests.get(f"{base_url}/get_all_cases")
    case_ids_data = case_ids_response.json()
    # Recorro cada caso
    for caso in case_ids_data:
        case_id = caso['id']
        # Obtengo el espacio seleccionado para el caso actual
        espacio_response = requests.get(f"{base_url}/getvariablebycase/{int(case_id)}/espacio_seleccionado")
        plan_response = requests.get(f"{base_url}/getvariablebycase/{int(case_id)}/confirmo")
        plan = plan_response.json()
        if plan.get('confirmo') == 'true':
            confirmados = confirmados + 1
        else:
            sin_confirmar = sin_confirmar + 1
        # Verifico si la respuesta fue exitosa antes de intentar acceder al JSON
        if espacio_response.status_code == 200:
            espacio_data = espacio_response.json()
            # Obtengo el valor del espacio seleccionado y verifico si es nulo
            espacio_seleccionado = espacio_data.get('espacio_seleccionado')
            # Si el espacio no es nulo, lo cuento en el diccionario
            if espacio_seleccionado is not None:
                if espacio_seleccionado == 'null': 
                    if 'Sin asignar' in conteo_espacios:
                        conteo_espacios['Sin asignar'] =+1
                    else:
                        conteo_espacios['Sin asignar'] =1
                else:
                    if espacio_seleccionado in conteo_espacios:
                        conteo_espacios[espacio_seleccionado] += 1
                    else:
                        conteo_espacios[espacio_seleccionado] = 1

    prom_dias_fabrication = requests.get(f"{base_url}/get_prom_dias")
    
    result = requests.get(f"{base_url}/get_finished")
    result = result.json()
    total_tareas = result['finalizadas'] + result['pendientes']

    # Calcula el porcentaje de tareas finalizadas
    if total_tareas > 0:
        porcentaje_finalizadas = (result['finalizadas'] / total_tareas) * 100
    else:
        porcentaje_finalizadas = 0
    # Calcula el porcentaje de planes confirmados
    if total_tareas > 0:
        porcentaje_finalizadas = (result['finalizadas'] / total_tareas) * 100
    else:
        porcentaje_finalizadas = 0    
    return render_template('indicators.html', datos = conteo, espacios=conteo_espacios, promedio = prom_dias_fabrication.json(), porcentaje = porcentaje_finalizadas, confirmados= confirmados, sin_confirmar= sin_confirmar)


if __name__ == '__main__':
    app.run(port=5001, debug=True)
