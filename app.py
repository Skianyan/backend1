import pandas as pd
import math
from flask import Flask, request, jsonify, render_template
import logging 

pd.options.mode.chained_assignment = None

# --- CONFIGURACIÓN DE ARCHIVOS ---
FILE_EXTENSION = '.csv'
FOLDER_LOCATION = 'data/'

# Asegúrate de que estos nombres de archivo coincidan exactamente con tus CSV
FILE_DATOS = FOLDER_LOCATION + 'Denue2024 - Datos' + FILE_EXTENSION
FILE_MUNICIPIO = FOLDER_LOCATION + 'Denue2024 - Dic_Municipio' + FILE_EXTENSION
FILE_DIRECCION = FOLDER_LOCATION + 'Denue2024 - Direccion' + FILE_EXTENSION
FILE_CONTACTO = FOLDER_LOCATION + 'Denue2024 - Contacto' + FILE_EXTENSION
FILE_LOCALIDAD = FOLDER_LOCATION + 'Denue2024 - Dic_Localidad' + FILE_EXTENSION
FILE_ACTIVIDAD = FOLDER_LOCATION + 'Denue2024 - Dic_Actividad' + FILE_EXTENSION
FILE_TIPOASENT = FOLDER_LOCATION + 'Denue2024 - Dic_TipoAsent' + FILE_EXTENSION

# --- Inicialización de Flask ---
app = Flask(__name__)
# DataFrame Maestro para almacenar todos los datos unidos
df_maestro = pd.DataFrame() 

def load_master_dataframe():
    global df_maestro

    try:
        # 1. Cargar tablas base y diccionarios
        df_datos = pd.read_csv(FILE_DATOS, encoding='latin1')
        df_mun   = pd.read_csv(FILE_MUNICIPIO, encoding='latin1')
        df_dir   = pd.read_csv(FILE_DIRECCION, encoding='latin1')
        df_cont  = pd.read_csv(FILE_CONTACTO, encoding='latin1')
        df_loc   = pd.read_csv(FILE_LOCALIDAD, encoding='latin1')
        df_act   = pd.read_csv(FILE_ACTIVIDAD, encoding='latin1')
        df_ta    = pd.read_csv(FILE_TIPOASENT, encoding='latin1')

        # 1.1 Fecha y año de registro SOBRE df_datos
        df_datos['fecha_alta'] = pd.to_datetime(
            df_datos['fecha_alta'],
            errors='coerce',
            infer_datetime_format=True
        )
        df_datos['year_registro'] = df_datos['fecha_alta'].dt.year

        # 2. Unión principal con Datos (ya incluye year_registro)
        df = df_datos.copy()

        # 2.1 Municipio
        df = df.merge(
            df_mun[['cve_mun', 'municipio']],
            on='cve_mun',
            how='left'
        )

        # 2.2 Localidad
        df = df.merge(
            df_loc[['cve_loc', 'localidad']],
            on='cve_loc',
            how='left'
        )

        # 2.3 Dirección -> para tipo de asentamiento y CP
        df = df.merge(
            df_dir[['id_cliente', 'id_tipo_asent', 'cod_postal']],
            on='id_cliente',
            how='left'
        )

        # 2.4 Diccionario de tipo de asentamiento
        df = df.merge(
            df_ta[['id_tipo_asent', 'tipo_asent']],
            on='id_tipo_asent',
            how='left'
        )

        # 2.5 Diccionario de actividad económica
        df = df.merge(
            df_act[['codigo_act', 'nombre_act']],
            on='codigo_act',
            how='left'
        )

        # 2.6 Datos de contacto (telefono, correo, www)
        df_cont['id'] = df_cont['id'].astype('int64')
        df = df.merge(
            df_cont[['id', 'telefono', 'correoelec', 'www']],
            left_on='id_cliente',
            right_on='id',
            how='left'
        )
        df.drop(columns=['id'], inplace=True)

        # 3. Limpiar coordenadas inválidas
        df = df[(df['latitud'].notna()) & (df['longitud'].notna())]

        df_maestro = df.reset_index(drop=True)
        print(f"✅ DataFrame Maestro creado. Total de negocios unidos: {len(df_maestro)}")

    except FileNotFoundError as e:
        print(f"❌ Error al cargar archivo: {e}. Asegúrate de que todos los CSV estén presentes.")
        df_maestro = pd.DataFrame()
    except Exception as e:
        print(f"❌ Error durante la unión de datos: {e}")
        df_maestro = pd.DataFrame()



# --- RUTAS DE LA APLICACIÓN ---

# 1. Ruta Raíz (Para servir el index.html)
@app.route('/')
def index():
    # Recuerda que index.html debe estar en una carpeta llamada 'templates'
    return render_template('index.html')

@app.route('/api/years_disponibles')
def api_years_disponibles():
    global df_maestro
    if df_maestro is None or df_maestro.empty:
        return jsonify([])

    years = (
        df_maestro['year_registro']
        .dropna()
        .astype(int)
        .sort_values()
        .unique()
        .tolist()
    )
    return jsonify(years)

# 2. Endpoint de API (Para la consulta BBOX)
@app.route('/api/datos_negocios')
def api_datos_negocios():
    global df_maestro
    if df_maestro is None or df_maestro.empty:
        return jsonify({"error": "Datos no cargados"}), 500

    # 1. Parámetros de BBOX
    try:
        lat_min = float(request.args.get('lat_min'))
        lat_max = float(request.args.get('lat_max'))
        lon_min = float(request.args.get('lon_min'))
        lon_max = float(request.args.get('lon_max'))
    except (TypeError, ValueError):
        return jsonify({"error": "Parámetros de coordenadas inválidos"}), 400

    df_filtrado = df_maestro[
        (df_maestro['latitud']  >= lat_min) &
        (df_maestro['latitud']  <= lat_max) &
        (df_maestro['longitud'] >= lon_min) &
        (df_maestro['longitud'] <= lon_max)
    ]

    # 2. Filtro opcional por año de registro
    year = request.args.get('year', default=None, type=int)
    if year is not None:
        df_filtrado = df_filtrado[df_filtrado['year_registro'] == year]


    # 3. Columnas que vas a exponer al mapa
    columnas_salida = [
        'nom_estab',
        'raz_social',
        'municipio',
        'localidad',
        'nombre_act',
        'tipo_asent',
        'telefono',
        'correoelec',
        'www',
        'cod_postal',
        'latitud',
        'longitud',
        'year_registro',
    ]

    datos_respuesta = df_filtrado[columnas_salida].copy()

    # 4. Limpiar NaN -> None para JSON válido
    datos_respuesta = datos_respuesta.astype(object).where(
        pd.notnull(datos_respuesta),
        None
    )

    return jsonify(datos_respuesta.to_dict(orient='records'))


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- Ejecución de la Aplicación ---
if __name__ == '__main__':
    # Cargar y unir los datos antes de iniciar el servidor
    load_master_dataframe()
    
    # Ejecutar el servidor Flask
    # Nota: El puerto 5000 es el predeterminado
    app.run(debug=True)