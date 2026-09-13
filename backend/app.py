import os

from flask import Flask, jsonify
from flask_cors import CORS

from database import (
    asegurar_columnas,
    cargar_datos_iniciales,
    conectar_db,
    crear_tablas,
)
from routes import BLUEPRINTS

app = Flask(__name__)
CORS(app)


@app.route("/")
def inicio():
    return jsonify({
        "mensaje": "API de Almada 2 funcionando correctamente"
    })


for blueprint in BLUEPRINTS:
    app.register_blueprint(blueprint)


if __name__ == "__main__":
    crear_tablas()
    asegurar_columnas()
    cargar_datos_iniciales()
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
        host=os.environ.get("ALMADA2_HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000"))
    )
