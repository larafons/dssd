from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)
base_url = "http://localhost:5000"  # Reemplaza con la URL de tu backend

@app.route('/design_collection')
def index():
    return render_template('form.html')

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

    # Enviar los datos al backend para iniciar el proceso
    response = requests.post(f"{base_url}/initiateprocess", json=data)

    if response.status_code == 200:
        return "Proceso iniciado exitosamente"
    else:
        return "Error al iniciar el proceso"

if __name__ == '__main__':
    app.run(debug=True)
