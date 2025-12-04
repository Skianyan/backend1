import pandas as pd
from flask import Flask, request, jsonify, render_template

# --- Inicialización y Carga de Datos ---
app = Flask(__name__)

# Nombre del archivo CSV subido
CSV_FILE = 'Denue2024mod.csv' 

try:
    # Cargar el archivo CSV en un DataFrame de pandas una sola vez al inicio
    # Esto asume que el archivo tiene las columnas 'latitud' y 'longitud'
    # Usamos low_memory=False para evitar warnings si las columnas tienen tipos mixtos
    df_negocios = pd.read_csv(CSV_FILE, low_memory=False)
    
    # ⚠️ Importante: Asegurar que las columnas de latitud y longitud sean numéricas
    # Reemplaza 'latitud' y 'longitud' si tus columnas tienen nombres diferentes
    df_negocios['latitud'] = pd.to_numeric(df_negocios['latitud'], errors='coerce')
    df_negocios['longitud'] = pd.to_numeric(df_negocios['longitud'], errors='coerce')
    
    # Eliminar filas con valores no numéricos (NaN) después de la conversión
    df_negocios.dropna(subset=['latitud', 'longitud'], inplace=True)
    
    print(f"✅ Datos cargados correctamente. Total de negocios: {len(df_negocios)}")
    
except FileNotFoundError:
    print(f"❌ Error: El archivo {CSV_FILE} no se encontró.")
    df_negocios = pd.DataFrame() # Crear un DataFrame vacío para evitar errores
except Exception as e:
    print(f"❌ Error al cargar o procesar el CSV: {e}")
    df_negocios = pd.DataFrame()

@app.route('/')
def index():
    """
    Ruta para servir la página principal (index.html).
    """
    return render_template('index.html')

# ---------------------------------------------

@app.route('/api/datos_negocios', methods=['GET'])
def get_negocios_bbox():
    """
    Endpoint para filtrar negocios del CSV basados en el Bounding Box (BBOX).
    """
    
    # 1. Verificar si hay datos cargados
    if df_negocios.empty:
        return jsonify({"error": "No hay datos cargados en el servidor."}), 500

    # 2. Obtener los parámetros del BBOX (lat_min, lon_min, etc.)
    try:
        lat_min = float(request.args.get('lat_min'))
        lon_min = float(request.args.get('lon_min'))
        lat_max = float(request.args.get('lat_max'))
        lon_max = float(request.args.get('lon_max'))
    except (TypeError, ValueError):
        # Manejar el caso donde los parámetros BBOX no se envían o no son válidos
        return jsonify({"error": "Parámetros BBOX inválidos o faltantes."}), 400

    # 3. Aplicar el filtro espacial usando pandas
    
    # Usamos una máscara booleana para filtrar el DataFrame
    filtro = (
        (df_negocios['latitud'] >= lat_min) & 
        (df_negocios['latitud'] <= lat_max) &
        (df_negocios['longitud'] >= lon_min) & 
        (df_negocios['longitud'] <= lon_max)
    )
    
    # Aplicar el filtro
    df_filtrado = df_negocios[filtro]
    
    # 4. Seleccionar solo las columnas necesarias para la respuesta
    # Nota: Si tu CSV usa nombres diferentes, ajústalos aquí
    datos_respuesta = df_filtrado[['nom_estab', 'latitud', 'longitud']]
    
    # 5. Convertir el DataFrame filtrado a un formato JSON compatible con el frontend
    # 'records' genera una lista de diccionarios, que es ideal para JavaScript
    return jsonify(datos_respuesta.to_dict('records'))

# ---------------------------------------------

if __name__ == '__main__':
    # El archivo index.html debe estar en la carpeta 'templates' o se debe configurar la ruta
    # Para el ejemplo, si solo tienes el index.html y el app.py en la misma carpeta,
    # puedes usar un puerto diferente si es necesario.
    app.run(debug=True)