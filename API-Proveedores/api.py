from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

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

@app.route('/buscar/<material>/<fecha>', methods=['GET'])
def buscar(material, fecha):
    if material in datos:
        result = [prov for prov in datos[material] if prov["cantidad"] > 0 and prov["fecha"] <= fecha]
        return jsonify(result)
    return jsonify([])

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
