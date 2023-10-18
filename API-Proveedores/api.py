from flask import Flask, jsonify, request
import jwt
import datetime
import secrets
from functools import wraps

app = Flask(__name__)

SECRET_KEY = secrets.token_hex(32)

# Harcodeamos los datos iniciales
datos = {
    "algodon": [
        {"name": "Proveedor1", "cantidad": 100, "fecha": "2023-11-01"},
        {"name": "Proveedor2", "cantidad": 200, "fecha": "2023-11-02"},
        {"name": "Proveedor3", "cantidad": 300, "fecha": "2023-11-03"},
        {"name": "Proveedor4", "cantidad": 400, "fecha": "2023-11-04"},
        {"name": "Proveedor5", "cantidad": 500, "fecha": "2023-11-05"},
    ],
    "metal": [
        {"name": "Proveedor1", "cantidad": 100, "fecha": "2023-11-01"},
        {"name": "Proveedor2", "cantidad": 200, "fecha": "2023-11-02"},
        {"name": "Proveedor3", "cantidad": 300, "fecha": "2023-11-03"},
        {"name": "Proveedor4", "cantidad": 400, "fecha": "2023-11-04"},
        {"name": "Proveedor5", "cantidad": 500, "fecha": "2023-11-05"},
    ],
    "madera": [
        {"name": "Proveedor1", "cantidad": 100, "fecha": "2023-11-01"},
        {"name": "Proveedor2", "cantidad": 200, "fecha": "2023-11-02"},
        {"name": "Proveedor3", "cantidad": 300, "fecha": "2023-11-03"},
        {"name": "Proveedor4", "cantidad": 400, "fecha": "2023-11-04"},
        {"name": "Proveedor5", "cantidad": 500, "fecha": "2023-11-05"},
    ],
    "poliester": [
        {"name": "Proveedor1", "cantidad": 100, "fecha": "2023-11-01"},
        {"name": "Proveedor2", "cantidad": 200, "fecha": "2023-11-02"},
        {"name": "Proveedor3", "cantidad": 300, "fecha": "2023-11-03"},
        {"name": "Proveedor4", "cantidad": 400, "fecha": "2023-11-04"},
        {"name": "Proveedor5", "cantidad": 500, "fecha": "2023-11-05"},
    ],
}

reservas = {
    "algodon": [],
    "metal": [],
    "madera": [],
    "poliester": [],
}

users = {
    'walter.bates': 'bpm'
}

# Ruta de autenticación
@app.route('/login', methods=['POST'])
def login():
    
    body = request.get_json()
    username= body.get('username')
    password= body.get('password')

    if not username or not password:
        return jsonify({'message': 'Falta nombre de usuario o contraseña'}), 401

    if username in users and users[username] == password:
        # Crear un token JWT con un tiempo de expiración
        token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token})

    return jsonify({'message': 'Nombre de usuario o contraseña incorrectos'}), 401


# Decorador personalizado para verificar el token
def verify_token(route_function):
    @wraps(route_function)
    def decorated_route(*args, **kwargs):
        token = request.headers.get('Authorization')
        token = token.split(" ")[1]
        if token:
            try:
                # Verificar el token JWT con la clave secreta
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                # Si el token es válido, se permite el acceso a la función original
                return route_function(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({"message": "Token expirado"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"message": "Token inválido"}), 401
        else:
            return jsonify({"message": "Token no proporcionado"}), 401
    return decorated_route

@app.route('/buscar/<material>/<fecha>/<cant>', methods=['GET'])
@verify_token
def buscar(material, fecha, cant):
    if material in datos:
        result = [prov for prov in datos[material] if prov["cantidad"] > 0 and prov["fecha"] <= fecha and prov["cantidad"] >= int(cant)]
        return jsonify(result)
    return jsonify([])


@app.route('/reservar', methods=['POST'])
@verify_token
def reservar():
    data = request.get_json()
    material = data.get("material")
    proveedor = data.get("name")
    cantidad_reserva = data.get("cantidad")

    for prov in datos[material]:
        if prov["name"] == proveedor:
            if prov["cantidad"] >= cantidad_reserva:
                prov["cantidad"] -= cantidad_reserva
                reservas[material].append({"name": proveedor, "cantidad": cantidad_reserva, "fecha_reserva": prov["fecha"]})
                return jsonify({"status": "Reserva realizada con éxito"})
            else:
                return jsonify({"status": "No hay suficiente cantidad para reservar"}), 400
    return jsonify({"status": "Proveedor no encontrado"}), 404

@app.route('/cancelar', methods=['POST'])
@verify_token
def cancelar():
    data = request.json
    material = data["material"]
    proveedor = data["name"]
    cantidad_cancelada = data["cantidad"]
    fecha_cancelar = data["fecha"]

    for reserva in reservas[material]:
        if (reserva["name"] == proveedor and reserva["cantidad"] == cantidad_cancelada and reserva["fecha_reserva"] == fecha_cancelar):
            for x in datos[material]:
                if (x["name"] == proveedor):
                    x["cantidad"] += cantidad_cancelada
            reservas[material].remove(reserva)
            return jsonify({"status": "Reserva cancelada con éxito"})
    return jsonify({"status": "No se pudo cancelar: reserva inexistente."}), 404

if __name__ == "__main__":
    app.run(port=5002,debug=True)
