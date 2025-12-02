import pandas as pd
from flask import Flask, render_template, jsonify
import os

# --- Configuración de Flask ---
app = Flask(__name__)

# Nombre del archivo de datos
DATA_FILE = 'Denue2024.csv'

# --- 1. Carga y Preparación de Datos con Pandas ---
def cargar_datos_denue():
    """Carga el CSV, selecciona las columnas de interés y las limpia."""
    
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: No se encuentra el archivo de datos: {DATA_FILE}")
        return []

    try:
        # Intenta leer el archivo especificando el delimitador común en DENUE: '|' (pipe)
        # y la codificación para manejar caracteres especiales del español.
        df = pd.read_csv(DATA_FILE, encoding='latin1', sep=',') 
        
        # Si el error persiste, prueba con otro delimitador, como el punto y coma:
        # df = pd.read_csv(DATA_FILE, encoding='latin1', sep=';')
        
        # Verifica las primeras columnas para confirmar que se leyó correctamente
        print("Columnas leídas exitosamente:", df.columns.tolist()[:5], "...") 

        # Selecciona las columnas necesarias
        data = df[['id_cliente', 'nom_estab', 'latitud', 'longitud']].copy()
        
        # ... [El resto del código de limpieza y conversión permanece igual] ...
        
        # Convierte las columnas de latitud y longitud a numérico
        data['latitud'] = pd.to_numeric(data['latitud'], errors='coerce')
        data['longitud'] = pd.to_numeric(data['longitud'], errors='coerce')
        data.dropna(subset=['latitud', 'longitud'], inplace=True)
        
        data_json = data.to_dict('records')
        
        return data_json
        
    except Exception as e:
        print(f"Ocurrió un error al procesar el archivo CSV: {e}")
        return []

# Carga los datos una sola vez al iniciar la aplicación para optimizar
NEGOCIOS_DATA = cargar_datos_denue()

# --- 2. Rutas de Flask ---

# Ruta principal: Muestra el mapa
@app.route('/')
def index():
    """Renderiza la plantilla HTML del mapa."""
    # Puedes pasar la cantidad de negocios cargados como información en la plantilla
    num_negocios = len(NEGOCIOS_DATA)
    return render_template('index.html', num_negocios=num_negocios)

# Ruta API: Sirve los datos de ubicación en formato JSON
@app.route('/api/datos_negocios')
def datos_negocios():
    """Retorna los datos de latitud, longitud y nombre del establecimiento."""
    # Retorna la lista de diccionarios como JSON
    return jsonify(NEGOCIOS_DATA)

# --- Ejecución ---
if __name__ == '__main__':
    # Ejecuta el servidor Flask
    # (debug=True es útil para desarrollo)
    app.run(debug=True)