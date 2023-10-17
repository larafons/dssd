from flask import Flask, jsonify, request
import jwt
import datetime
import secrets

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

users = {
    'walter.bates': 'bpm',
    'usuario2': 'contrasena2',
}

# Ruta de autenticación
@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Falta nombre de usuario o contraseña'}), 401

    username = auth.username
    password = auth.password

    if username in users and users[username] == password:
        # Crear un token JWT con un tiempo de expiración
        token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token})

    return jsonify({'message': 'Nombre de usuario o contraseña incorrectos'}), 401

# Middleware para verificar el token JWT
def verify_token(func):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token:
            try:
                # Verificar el token JWT con la clave secreta
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                # Si el token es válido, se permite el acceso a la función original
                return func(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({"message": "Token expirado"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"message": "Token inválido"}), 401
        else:
            return jsonify({"message": "Token no proporcionado"}), 401

    return wrapper

@verify_token
@app.route('/buscar/<material>/<fecha>/<cant>', methods=['GET'])
def buscar(material, fecha, cant):
    if material in datos:
        result = [prov for prov in datos[material] if prov["cantidad"] > 0 and prov["fecha"] <= fecha and prov["cantidad"] >= int(cant)]
        return jsonify(result)
    return jsonify([])

@verify_token
@app.route('/reservar', methods=['POST'])
def reservar():
    data = request.json
    material = data["material"]
    proveedor = data["name"]
    cantidad_reserva = data["cantidad"]

    for prov in datos[material]:
        if prov["name"] == proveedor:
            if prov["cantidad"] >= cantidad_reserva:
                prov["cantidad"] -= cantidad_reserva
                return jsonify({"status": "Reserva realizada con éxito"})
            else:
                return jsonify({"status": "No hay suficiente cantidad para reservar"}), 400
    return jsonify({"status": "Proveedor no encontrado"}), 404

@verify_token
@app.route('/cancelar', methods=['POST'])
def cancelar():
    data = request.json
    material = data["material"]
    proveedor = data["name"]
    cantidad_cancelada = data["cantidad"]

    for prov in datos[material]:
        if prov["name"] == proveedor:
            prov["cantidad"] += cantidad_cancelada
            return jsonify({"status": "Reserva cancelada con éxito"})
    return jsonify({"status": "Proveedor no encontrado"}), 404

if __name__ == "__main__":
    app.run(port=5002,debug=True)
