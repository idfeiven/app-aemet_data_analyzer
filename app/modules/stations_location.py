# pages/mapa.py (Página del mapa interactivo)
import pandas as pd
import streamlit as st
import plotly.express as px
from download.stations import download_stations_info

# Función para mostrar mensaje en tiempo real
def agregar_mensaje(msg: str) -> None:
    """
    Appends a message to Streamlit session state and displays all messages in a styled HTML box.

    This function is used to log real-time messages in a scrollable, monospaced console-style
    container within a Streamlit app. Messages are stored in `st.session_state.mensajes`.

    Args:
        msg (str): The message to append and display.

    Notes:
        Requires that `mensaje_container` is a previously defined Streamlit container and
        that `st.session_state.mensajes` is a list initialized before use.
    """
    st.session_state.mensajes.append(msg)
    html = f"""
    <div style="background-color:#111; color:#0f0; padding:10px;
                height:150px; overflow-y:auto; font-family:monospace;
                font-size:16px; border:1px solid #444;">
        {"<br>".join(st.session_state.mensajes)}
    </div>
    """
    mensaje_container.markdown(html, unsafe_allow_html=True)

st.set_page_config(layout="wide")

st.title("Estaciones meteorológicas de AEMET")

st.write("En esta app web podrás visualizar datos de las estaciones de AEMET, así como realizar análisis de los datos.")
st.write("Toda la información aquí expuesta pertenece a AEMET.")

st.markdown("## Mapa de Estaciones Meteorológicas de AEMET")

if "df_stations_info" not in st.session_state:
    mensaje_container = st.empty()
    st.session_state.mensajes = []
    st.session_state.df_stations_info = download_stations_info.download_stations_info(agregar_mensaje)

df = st.session_state.df_stations_info

if not st.session_state.df_stations_info.empty:
    fig = px.scatter_mapbox(df,
                            lat="latitud",
                            lon="longitud",
                            hover_name="nombre",
                            hover_data=["provincia", "altitud", "indicativo"],
                            zoom=5)
    
    # Cambiar el tipo de marcador y aumentar el tamaño
    fig.update_traces(marker=dict(size=15, color="black"))

    # Usar un estilo de mapa para la visualización
    fig.update_layout(mapbox_style="open-street-map", 
                  margin={"r":0,"t":0,"l":0,"b":0},
                  width=1000, height=600)
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("No se ha podido obtener información de las estaciones de AEMET")
