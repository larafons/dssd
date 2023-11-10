from flask import Flask, request
import jwt
import datetime
import secrets
from functools import wraps
import requests
from flask_restx import Api, Resource, fields

base_url = "http://localhost:5000" 

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
    "espacio_2": [{"fecha_inicio": "2024-02-11", "fecha_fin": "2024-03-28"}, {"fecha_inicio": "2024-05-11", "fecha_fin": "2023-06-28"}],
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

reserva_model = api.model('Reserva', {
    'material': fields.String(required=True, description='Tipo de material (algodon, metal, madera o poliester)'),
    'name': fields.String(required=True, description='Nombre del proveedor'),
    'cantidad': fields.Integer(required=True, description='Cantidad a reservar'),
})

reserva_espacio_model = api.model('Reserva espacio', {
    'fecha_inicio': fields.String(required=True, description='Fecha de inicio de la reserva del espacio'),
    'fecha_fin': fields.String(required=True, description='Fecha de fin de la reserva del espacio')
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
    'material': fields.String(required=True, description='Tipo de material (algodon, metal, madera o poliester)'),
    'name': fields.String(required=True, description='Nombre del proveedor'),
    'cantidad': fields.Integer(required=True, description='Cantidad a cancelar'),
    'fecha': fields.String(required=True, description='Fecha de cancelación'),
})

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
    @ns.doc(security='Bearer Auth')
    @ns.expect(reserva_model)
    @verify_token
    @ns.response(200, 'Reserva exitosa')
    @ns.response(400, 'No hay suficiente cantidad para reservar')
    @ns.response(401, 'Token inválido, expirado o no proporcionado')
    @ns.response(404, 'Proveedor no encontrado')
    def post(self):
        data = request.get_json()
        material = data.get("material")
        proveedor = data.get("name")
        cantidad_reserva = data.get("cantidad")

        for prov in datos[material]:
            if prov["name"] == proveedor:
                if prov["cantidad"] >= cantidad_reserva:
                    prov["cantidad"] -= cantidad_reserva
                    reservas[material].append({"name": proveedor, "cantidad": cantidad_reserva, "fecha_reserva": prov["fecha"]})
                    print(reservas)
                    return {"status": "Reserva realizada con éxito"}
                else:
                    return {"status": "No hay suficiente cantidad para reservar"}, 400
        return {"status": "Proveedor no encontrado"}, 404

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
        data = request.json
        material = data["material"]
        proveedor = data["name"]
        cantidad_cancelada = data["cantidad"]
        fecha_cancelar = data["fecha"]
        formatted_date = parse_and_format_date(fecha_cancelar)
        print(formatted_date)
        if not formatted_date:
            return {"message": "Formato de fecha inválido. Por favor, use el formato 'año-mes-día'."}, 400
        for reserva in reservas[material]:
            print(reservas)
            if (reserva["name"] == proveedor and reserva["cantidad"] == cantidad_cancelada and reserva["fecha_reserva"] == formatted_date):
                for x in datos[material]:
                    if (x["name"] == proveedor):
                        x["cantidad"] += cantidad_cancelada
                reservas[material].remove(reserva)
                return {"status": "Reserva cancelada con éxito"}
        return {"status": "No se pudo cancelar: reserva inexistente."}, 404

# PROBAR    
@ns.route('/consultar_espacios')
class ConsultarEspaciosResource(Resource):
    @verify_token
    def post(self):
        case_id = requests.get(f"{base_url}/get_case_id")
        # Obtener la fecha de inicio y el plazo de fabricación
        fecha_inicio_response = requests.get(f"{base_url}/getvariablebycase/{int(case_id)}/fecha_entrega")
        plazo_fabricacion_response = requests.get(f"{base_url}/getvariablebycase/{int(case_id)}/plazo_fabricacion")

        # Verificar si las respuestas fueron exitosas
        if fecha_inicio_response.status_code != 200 or plazo_fabricacion_response.status_code != 200:
            return "Error al obtener la información de fecha de inicio o plazo de fabricación", 500

        fecha_inicio = fecha_inicio_response.json()
        plazo_fabricacion_str = plazo_fabricacion_response.json()

        # Convertir plazo de fabricación a entero
        try:
            plazo_fabricacion = int(plazo_fabricacion_str)
        except ValueError:
            return "El plazo de fabricación no es un número válido", 400

        # Calcular la fecha de fin
        fecha_fin = datetime.strptime(fecha_inicio, "%Y-%m-%d") + timedelta(days=plazo_fabricacion)

        # Obtener espacios disponibles
        espacios_disponibles = []
        for espacio, reservas in reservas_espacios.items():
            disponible = True
            for reserva in reservas:
                reserva_inicio = datetime.strptime(reserva["fecha_inicio"], "%Y-%m-%d")
                reserva_fin = datetime.strptime(reserva["fecha_fin"], "%Y-%m-%d")

                if fecha_inicio < reserva_fin and fecha_fin > reserva_inicio:
                    disponible = False
                    break

            if disponible:
                espacios_disponibles.append(espacio)
            print(espacios_disponibles)
        return jsonify({"espacios_disponibles": espacios_disponibles})





if __name__ == "__main__":
    app.run(port=5002,debug=True)
