# pages/mapa.py (Página del mapa interactivo)
import pandas as pd
import streamlit as st
import plotly.express as px
from download.stations import download_today_observation

st.cache_data.clear()

# -----------------------------FUNCTIONS--------------------------------

def parse_stations_data(df):

    df = df.copy()
    df['fint'] = df['fint'].apply(pd.to_datetime)
    df['fint'] = df['fint'].dt.tz_localize(None)
    df = df[df['fint'] == df['fint'].iloc[-1]]
    dict_rename = dict({'prec': 'Precipitación (mm)',
                        'vmax': 'Velocidad máxima (m/s)',
                        'vv': 'Velocidad media (m/s)',
                        'dv': 'Dirección media del viento (º)',
                        'dmax': 'Dirección racha máxima (º)',
                        'hr': 'Humedad relativa (%)',
                        'ta': 'Temperatura (ºC)',
                        'tamax': 'Temperatura máxima (ºC)',
                        'tamin': 'Temperatura mínima (ºC)',
                        'pres': 'Presión absoluta (hPa)',
                        'pres_nmar': 'Presión al nivel del mar (hPa)',
                        'nieve': 'Espesor de nieve (cm)'})
    df.rename(dict_rename, axis = 1, inplace = True)

    return df

# Función para mostrar mensaje en tiempo real
def agregar_mensaje(msg):
    st.session_state.mensajes.append(msg)
    html = f"""
    <div style="background-color:#111; color:#0f0; padding:10px;
                height:300px; overflow-y:auto; font-family:monospace;
                font-size:14px; border:1px solid #444;">
        {"<br>".join(st.session_state.mensajes)}
    </div>
    """
    mensaje_container.markdown(html, unsafe_allow_html=True)

# -------------------------------MAIN PROGRAM-------------------------------------
st.set_page_config(layout="wide")


st.title("Última observación")
st.write("Fuente: red de estaciones de AEMET.")

if "data_stations" not in st.session_state:
    mensaje_container = st.empty()
    st.session_state.mensajes = []
    st.session_state.data_stations = download_today_observation.download_today_observation(message = agregar_mensaje)

df = st.session_state.data_stations

if not type(df) == None:

    # df = st.session_state.data_stations
    df = parse_stations_data(df)
    cols_to_choose = ['Precipitación (mm)',
                      'Velocidad máxima (m/s)',
                      'Velocidad media (m/s)',
                      'Dirección media del viento (º)',
                      'Dirección racha máxima (º)',
                      'Humedad relativa (%)',
                      'Temperatura (ºC)',
                      'Temperatura máxima (ºC)',
                      'Temperatura mínima (ºC)',
                      'Presión absoluta (hPa)',
                      'Presión al nivel del mar (hPa)',
                      'Espesor de nieve (cm)']

    st.write(f"Última actualización: {df['fint'].iloc[-1]}")

    col = st.selectbox(label = "Selecciona una variable", options = df[cols_to_choose].columns)

    fig = px.scatter_mapbox(df,
                            lat = "lat",
                            lon = "lon",
                            hover_name = "ubi",
                            hover_data = col,
                            color = col,
                            color_continuous_scale = "Viridis",
                            size_max=15,
                            zoom=5)
    
    # Cambiar el tipo de marcador y tamaño del mapa
    fig.update_traces(marker=dict(size=12, color=df[col], colorscale="Viridis"))


    # Usar un estilo de mapa para la visualización
    fig.update_layout(mapbox_style="open-street-map", 
                  margin={"r":0,"t":0,"l":0,"b":0},
                  width=2000, height=600)
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("No se ha podido obtener datos de las estaciones de AEMET")