from flask import Flask, jsonify, request
import jwt
import datetime
import secrets
from functools import wraps
import requests
from flask_restx import Api, Resource, fields

authorizations = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    },
}

app = Flask(__name__)
api = Api(app, version='1.0', title='API de Proveedores', description='API para gestionar proveedores', authorizations=authorizations, security='Bearer Auth')

SECRET_KEY = secrets.token_hex(32)

ns = api.namespace('proveedor', description='Operaciones de proveedor')

# Harcodeamos los datos iniciales
datos = {
    "algodon": [
        {"name": "Proveedor1", "cantidad": 100, "fecha": "2023-12-01"},
        {"name": "Proveedor2", "cantidad": 200, "fecha": "2023-12-02"},
        {"name": "Proveedor3", "cantidad": 300, "fecha": "2023-12-03"},
        {"name": "Proveedor4", "cantidad": 400, "fecha": "2023-12-04"},
        {"name": "Proveedor5", "cantidad": 500, "fecha": "2023-12-05"},
    ],
    "metal": [
        {"name": "Proveedor1", "cantidad": 100, "fecha": "2023-12-01"},
        {"name": "Proveedor2", "cantidad": 200, "fecha": "2023-12-02"},
        {"name": "Proveedor3", "cantidad": 300, "fecha": "2023-12-03"},
        {"name": "Proveedor4", "cantidad": 400, "fecha": "2023-12-04"},
        {"name": "Proveedor5", "cantidad": 500, "fecha": "2023-12-05"},
    ],
    "madera": [
        {"name": "Proveedor1", "cantidad": 100, "fecha": "2023-12-01"},
        {"name": "Proveedor2", "cantidad": 200, "fecha": "2023-12-02"},
        {"name": "Proveedor3", "cantidad": 300, "fecha": "2023-12-03"},
        {"name": "Proveedor4", "cantidad": 400, "fecha": "2023-12-04"},
        {"name": "Proveedor5", "cantidad": 500, "fecha": "2023-12-05"},
    ],
    "poliester": [
        {"name": "Proveedor1", "cantidad": 100, "fecha": "2023-12-01"},
        {"name": "Proveedor2", "cantidad": 200, "fecha": "2023-12-02"},
        {"name": "Proveedor3", "cantidad": 300, "fecha": "2023-12-03"},
        {"name": "Proveedor4", "cantidad": 400, "fecha": "2023-12-04"},
        {"name": "Proveedor5", "cantidad": 500, "fecha": "2023-12-05"},
    ],
}

# la reserva de espacios tiene 2 elementos, fecha de inicio y fecha de fin
reservas = {
    "algodon": [],
    "metal": [],
    "madera": [],
    "poliester": [],
}

reservas_espacios = {
    "espacio_1": [{"fecha_inicio": "2023-11-10", "fecha_fin": "2023-12-20"}, ],
    "espacio_2": [{"fecha_inicio": "2024-02-11", "fecha_fin": "2024-03-28"}, {"fecha_inicio": "2024-05-11", "fecha_fin": "2024-06-28"}],
    "espacio_3": [],
    "espacio_4": [],
    "espacio_5": [],
}

users = {
    'walter.bates': 'bpm'
}

login_model = api.model('Login', {
    'username': fields.String(required=True, description='Nombre de usuario'),
    'password': fields.String(required=True, description='Contraseña del usuario'),
})

consulta_espacio_model = api.model('Consulta espacio', {
    'fecha_inicio': fields.String(required=True, description='Fecha de inicio de la reserva del espacio'),
    'cant_dias': fields.Integer(required=True, description='Cantidad de dias a reservar'),
})

reserva_model = api.model('Reserva', {
    'materiales_reserva': fields.Nested(api.model('Materiales_reserva', {
        'material_1': fields.String(description='Tipo de material 1'),
        'cantidad_1': fields.Integer(description='Cantidad de material 1'),
        'name_1': fields.String(description='Nombre del proveedor 1'),
        'material_2': fields.String(description='Tipo de material 2'),
        'cantidad_2': fields.Integer(description='Cantidad de material 2'),
        'name_2': fields.String(description='Nombre del proveedor 2'),
        'material_3': fields.String(description='Tipo de material 3'),
        'cantidad_3': fields.Integer(description='Cantidad de material 3'),
        'name_3': fields.String(description='Nombre del proveedor 3'),
        'material_4': fields.String(description='Tipo de material 4'),
        'cantidad_4': fields.Integer(description='Cantidad de material 4'),
        'name_4': fields.String(description='Nombre del proveedor 4'),
    }))
})

reserva_espacio_model = api.model('Reserva espacio', {
    'fecha_inicio': fields.String(required=True, description='Fecha de inicio de la reserva del espacio'),
    'cant_dias': fields.Integer(required=True, description='Cantidad de dias a reservar'),
    'espacio': fields.String(required=True, description='Nombre del espacio a reservar'),
})

model_material_busqueda = api.model('MaterialBusqueda', {
    'materiales': fields.Nested(api.model('Materiales', {
        'material_1': fields.String(description='Tipo de material 1'),
        'cantidad_1': fields.Integer(description='Cantidad de material 1'),
        'material_2': fields.String(description='Tipo de material 2'),
        'cantidad_2': fields.Integer(description='Cantidad de material 2'),
        'material_3': fields.String(description='Tipo de material 3'),
        'cantidad_3': fields.Integer(description='Cantidad de material 3'),
        'material_4': fields.String(description='Tipo de material 4'),
        'cantidad_4': fields.Integer(description='Cantidad de material 4'),
    })),
    'fecha_lanzamiento': fields.String(description='Fecha de lanzamiento en formato Año-Mes-Día')
})

cancelar_model = api.model('Cancelar', {
    'materiales_cancelar': fields.Nested(api.model('Materiales_cancelar', {
        'material_1': fields.String(description='Tipo de material 1'),
        'cantidad_1': fields.Integer(description='Cantidad de material 1'),
        'name_1': fields.String(description='Nombre del proveedor 1'),
        'fecha_1': fields.String(required=True, description='Fecha de cancelacion 1'),
        'material_2': fields.String(description='Tipo de material 2'),
        'cantidad_2': fields.Integer(description='Cantidad de material 2'),
        'name_2': fields.String(description='Nombre del proveedor 2'),
        'fecha_2': fields.String(required=True, description='Fecha de cancelacion 2'),
        'material_3': fields.String(description='Tipo de material 3'),
        'cantidad_3': fields.Integer(description='Cantidad de material 3'),
        'name_3': fields.String(description='Nombre del proveedor 3'),
        'fecha_3': fields.String(required=True, description='Fecha de cancelacion 3'),
        'material_4': fields.String(description='Tipo de material 4'),
        'cantidad_4': fields.Integer(description='Cantidad de material 4'),
        'name_4': fields.String(description='Nombre del proveedor 4'),
        'fecha_4': fields.String(required=True, description='Fecha de cancelacion 4'),
    })),
    'espacio': fields.String(required=True, description='Nombre del espacio a cancelar'),
    'fecha_espacio': fields.String(required=True, description='Fecha del espacio a cancelar')
})


def cancelar_espacio(espacio, fecha_inicio):
    reservas = reservas_espacios[espacio]
    if reservas:
        for reserva in reservas:
            #como no existen dos reservas en las mismas fechas, (no pueden
            # existir dos con la misma fecha de inicio) solo filtramos por eso.
            if reserva['fecha_inicio'] == fecha_inicio:
                reservas.remove(reserva)
                return True
    return False

def cancelar_material(material, proveedor, cantidad_cancelada, fecha_cancelar):
    formatted_date = parse_and_format_date(fecha_cancelar)
    if not formatted_date:
        return {"message": "Formato de fecha inválido. Por favor, use el formato 'año-mes-día'."}, 400
    for reserva in reservas[material]:
        if (reserva["name"] == proveedor and reserva["cantidad"] == cantidad_cancelada and reserva["fecha_reserva"] == formatted_date):
            for x in datos[material]:
                if (x["name"] == proveedor):
                    x["cantidad"] += cantidad_cancelada
            reservas[material].remove(reserva)
            return True
    return False


@ns.route('/login')
class LoginResource(Resource):
    @ns.expect(login_model)
    @ns.response(200, 'Login exitoso')
    @ns.response(401, 'Login fallido')
    def post(self):
        body = request.get_json()
        username= body.get('username')
        password= body.get('password')

        if not username or not password:
            return {'message': 'Falta nombre de usuario o contraseña'}, 401

        if username in users and users[username] == password:
            # Crear un token JWT con un tiempo de expiración
            token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, SECRET_KEY, algorithm='HS256')
            return {'token': token}, 200

        return {'message': 'Nombre de usuario o contraseña incorrectos'}, 401


# Decorador personalizado para verificar el token
def verify_token(route_function):
    @wraps(route_function)
    def decorated_route(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token:
            try:
                # Verificar el token JWT con la clave secreta
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                # Si el token es válido, se permite el acceso a la función original
                return route_function(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return {"message": "Token expirado"}, 401
            except jwt.InvalidTokenError:
                return {"message": "Token inválido"}, 401
        else:
            return {"message": "Token no proporcionado"}, 401
    return decorated_route


def parse_and_format_date(date_string):
    try:
        # Intenta parsear la fecha
        parsed_date = datetime.datetime.strptime(date_string, '%Y-%m-%d')
        # Reformatea la fecha al formato deseado
        return parsed_date.strftime('%Y-%m-%d')
    except ValueError:
        # Si hay un error, retorna None
        return None


#getters

@ns.route('/get_reservas')
class GetResource(Resource):
    @ns.response(200, 'Búsqueda exitosa')
    @ns.response(400, 'Formato de fecha inválido')
    @ns.response(401, 'Token inválido, expirado o no proporcionado')
    def get(self):
        res = { "espacios": reservas,
                "reservas_espacios": reservas_espacios}
        return res
    
#Recurso para buscar proveedores
@ns.route('/buscar')
class BuscarResource(Resource):
    @ns.doc(security='Bearer Auth')
    @ns.expect(model_material_busqueda)
    @verify_token
    @ns.response(200, 'Búsqueda exitosa')
    @ns.response(400, 'Formato de fecha inválido')
    @ns.response(401, 'Token inválido, expirado o no proporcionado')
    def post(self):
        data = request.get_json()
        fecha_lanzamiento = data.get("fecha_lanzamiento")
        materiales = data.get("materiales")

        formatted_date = parse_and_format_date(fecha_lanzamiento)
        if not formatted_date:
            return {"message": "Formato de fecha inválido. Por favor, use el formato 'año-mes-día'."}, 400
        
        # Extraer materiales y cantidades
        mats = [v.strip() for k, v in materiales.items() if "material_" in k]
        cants = [v for k, v in materiales.items() if "cantidad_" in k]
        material_cant_list = [(mat, cant) for mat, cant in zip(mats, cants) if mat]


        results = {}
        for material, cant in material_cant_list:
            if material not in datos:
                return {"message": f"Material '{material}' no encontrado"}, 404

            results[material] = [prov for prov in datos[material] if prov["cantidad"] > 0 and prov["fecha"] <= formatted_date and prov["cantidad"] >= int(cant)]

        if all(results.values()):
            return {"message": "Búsqueda exitosa", "result": results}, 200
        else:
            return {"message": "No se encontraron proveedores que cumplan con los criterios"}, 404

# Recurso para reservar proveedores
@ns.route('/reservar')
class ReservarResource(Resource):
    # @ns.doc(security='Bearer Auth')
    @ns.expect(reserva_model)
    # @verify_token
    @ns.response(200, 'Reserva exitosa')
    @ns.response(400, 'No hay suficiente cantidad para reservar')
    @ns.response(401, 'Token inválido, expirado o no proporcionado')
    @ns.response(404, 'Proveedor no encontrado')
    def post(self):
        data = request.get_json()
        materiales_data = data.get("materiales_reserva")
        
        # Crear una lista para las reservas que se van a validar
        reservas_validar = []
        for i in range(1, 5):  # Iterar sobre los 4 grupos de materiales
            material = materiales_data.get(f'material_{i}', '')
            cantidad_reserva = materiales_data.get(f'cantidad_{i}', 0)
            proveedor = materiales_data.get(f'name_{i}', '')
            
            if material and proveedor and cantidad_reserva > 0:  # Solo procesar si se proporcionaron los tres valores
                # Verificar si el proveedor y la cantidad son válidos antes de reservar
                encontrado = False
                for prov in datos.get(material, []):
                    if prov["name"] == proveedor:
                        encontrado = True
                        if prov["cantidad"] < cantidad_reserva:
                            return {"status": "No hay suficiente cantidad para reservar"}, 400
                        else:
                            reservas_validar.append((material, proveedor, cantidad_reserva, prov["fecha"]))
                        break
                if not encontrado:
                    return {"status": "Proveedor no encontrado"}, 404

        # Si se pasa la validación, proceder a reservar todos los materiales
        for material, proveedor, cantidad_reserva, fecha_reserva in reservas_validar:
            for prov in datos[material]:
                if prov["name"] == proveedor:
                    prov["cantidad"] -= cantidad_reserva
                    reservas[material].append({
                        "name": proveedor, 
                        "cantidad": cantidad_reserva, 
                        "fecha_reserva": fecha_reserva
                    })
        print(reservas)
        return {"status": "Reserva realizada con éxito"}, 200


@ns.route('/cancelar')
class CancelarResource(Resource):
    @ns.doc(security='Bearer Auth')
    @ns.expect(cancelar_model)
    @verify_token
    @ns.response(200, 'Cancelación exitosa')
    @ns.response(400, 'Formato de fecha inválido')
    @ns.response(401, 'Token inválido, expirado o no proporcionado')
    @ns.response(404, 'No se pudo cancelar: reserva inexistente.')
    def post(self):
        data = request.get_json()
        materiales = data.get("materiales_cancelar")
        espacio = data.get("espacio")
        fecha = data.get("fecha_espacio")
        cancelar = cancelar_espacio(espacio, fecha)
        if cancelar:
            for i in range(1, 5):
                material = materiales.get(f'material_{i}')
                cantidad = materiales.get(f'cantidad_{i}')
                name = materiales.get(f'name_{i}')
                fecha = materiales.get(f'fecha_{i}')

                if material and cantidad and name and fecha:
                    if cantidad != 0 and name != '':
                        ok = cancelar_material(material, cantidad, name, fecha)
                        if not ok:
                            return {"status": "No se pudo cancelar: material inexistente."}, 404
            return {'message': 'Cancelacion exitosa'}, 200
        else:
            return {'message': 'no se pudo cancelar: reserva inexistente.'}, 404


# PROBAR    
@ns.route('/consultar_espacios')
class ConsultarEspaciosResource(Resource):
    @ns.doc(security='Bearer Auth')
    @ns.expect(consulta_espacio_model)
    @verify_token
    @ns.response(200, 'Consulta exitosa')
    @ns.response(400, 'Consulta invalida')
    @ns.response(401, 'Token inválido, expirado o no proporcionado')
    @ns.response(404, 'espacio de fabricación no disponible para la fecha indicada')
    def post(self):
        data = request.get_json()
        fecha_inicio = data.get("fecha_inicio")
        cant_dias = data.get("cant_dias")

        # Verificar si las respuestas fueron exitosas
        if not fecha_inicio or cant_dias <= 0:
            return {"message": "Consulta invalida"}, 400
        
        # Calcular la fecha de fin
        fecha_fin = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d") + datetime.timedelta(days=cant_dias)
        fecha_inicio = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")

        # Obtener espacios disponibles
        espacios_disponibles = []
        for espacio, reservas in reservas_espacios.items():
            disponible = True
            for reserva in reservas:
                reserva_inicio = datetime.datetime.strptime(reserva["fecha_inicio"], "%Y-%m-%d")
                reserva_fin = datetime.datetime.strptime(reserva["fecha_fin"], "%Y-%m-%d")
                # chequeo si mi fecha de inicio o mi fecha de fin estan dentro del rango de las reservas
                # ya establecidas. En caso de estarlo, no se agregan a los espacios que hay disponibles. (por eso el break)
                if (fecha_inicio > reserva_inicio and fecha_inicio < reserva_fin) or ( fecha_fin > reserva_inicio and fecha_fin < reserva_fin) or (fecha_inicio < reserva_inicio and fecha_fin > reserva_fin):
                    disponible = False
                    break

            if disponible:
                espacios_disponibles.append(espacio)
            print(espacios_disponibles)
        return {"message": "Búsqueda exitosa", "result": espacios_disponibles}, 200

@ns.route('/reservar_espacio')
class ConsultarEspaciosResource(Resource):
    # @ns.doc(security='Bearer Auth')
    @ns.expect(reserva_espacio_model)
    # @verify_token
    @ns.response(200, 'Reserva exitosa')
    @ns.response(400, 'Consulta invalida')
    @ns.response(401, 'Token inválido, expirado o no proporcionado')
    def post(self):
        data = request.get_json()
        fecha_inicio = data.get("fecha_inicio")
        cant_dias = data.get("cant_dias")
        nombre_espacio = data.get("espacio")
        print(reservas_espacios["espacio_3"])
        # Verificar si las respuestas fueron exitosas
        if not fecha_inicio or cant_dias <= 0 or nombre_espacio not in reservas_espacios.keys():
            return {"message": "Consulta invalida"}, 400
        
        # Calcular la fecha de fin
        fecha_fin = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d") + datetime.timedelta(days=cant_dias)

        fecha_fin = fecha_fin.strftime("%Y-%m-%d")
        # Agregarlo a espacios disponibles        
        reservas_espacios[nombre_espacio].append({"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin})
        print(reservas_espacios)
        return {"message": "reserva exitosa"}, 200

# @ns.route('/consultar_plazos')
# class ConsultarPlazosResource(Resource):
#     @ns.doc(security='Bearer Auth')
#     # @ns.expect(cancelar_model)
#     @verify_token
#     @ns.response(200, 'Cancelación exitosa')
#     @ns.response(400, 'Formato de fecha inválido')
#     @ns.response(401, 'Token inválido, expirado o no proporcionado')
#     @ns.response(404, 'No se pudo cancelar: reserva inexistente.')
#     def get(self):
#         data = request.json
#         material = data["material"]
#         proveedor = data["name"]
#         cantidad_cancelada = data["cantidad"]
#         fecha_cancelar = data["fecha"]
#         formatted_date = parse_and_format_date(fecha_cancelar)
#         print(formatted_date)
#         if not formatted_date:
#             return {"message": "Formato de fecha inválido. Por favor, use el formato 'año-mes-día'."}, 400
#         for reserva in reservas[material]:
#             print(reservas)
#             if (reserva["name"] == proveedor and reserva["cantidad"] == cantidad_cancelada and reserva["fecha_reserva"] == formatted_date):
#                 for x in datos[material]:
#                     if (x["name"] == proveedor):
#                         x["cantidad"] += cantidad_cancelada
#                 reservas[material].remove(reserva)
#                 return {"status": "Reserva cancelada con éxito"}
#         return {"status": "No se pudo cancelar: reserva inexistente."}, 404

if __name__ == "__main__":
    app.run(port=5002,debug=True)
