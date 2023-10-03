from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)
base_url = "http://localhost:5000"  # Reemplaza con la URL de tu backend

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/design_collection')
def index():
    return render_template('form.html')

@app.route('/login', methods=['POST'])
def submitlogin():
    username = request.form.get('username')
    password = request.form.get('password')
    print(password)

    data = {
        "username": username,
        "password": password
    }
    # Enviar los datos al backend para el inicio de sesión
    response = requests.post(f"{base_url}/login", json=data)
    if response.status_code == 200:
        return redirect('/design_collection')

@app.route('/submit', methods=['POST'])
def submit():
    # Obtener los datos del formulario
    data = {
        "categoria": request.form.get('categoria'),
        "modelos": request.form.get('modelos'),
        "plazo_fabricacion": request.form.get('plazo_fabricacion'),
        "fecha_lanzamiento": request.form.get('fecha_lanzamiento'),
        "informacion_adicional": request.form.get('informacion_adicional')
    }
    # Harcodeamos el nombre del pool
    response = request.get(f"{base_url}/get_process_id/entrega-1")
    print(response)
    # Enviar los datos al backend para iniciar el proceso
    response1 = requests.post(f"{base_url}/initiateprocess", json=data)

    if response1.status_code == 200:
        return "Proceso iniciado exitosamente"
    else:
        return "Error al iniciar el proceso"

if __name__ == '__main__':
    app.run(port=5001, debug=True)
