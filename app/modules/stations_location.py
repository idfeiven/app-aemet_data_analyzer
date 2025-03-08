# pages/mapa.py (Página del mapa interactivo)
import sys
import folium
import pandas as pd
import streamlit as st
from pathlib import Path
import plotly.express as px
from download.info import download_stations_info


st.title("Estaciones meteorológicas de AEMET")

st.write("En esta app web podrás visualizar datos de las estaciones de AEMET, así como realizar análisis de los datos.")
st.write("Toda la información aquí expuesta pertenece a AEMET.")

st.markdown("## Mapa de Estaciones Meteorológicas de AEMET")

if "df_stations_info" not in st.session_state:
    st.session_state.df_stations_info = download_stations_info.download_stations_info()

df = st.session_state.df_stations_info

if not st.session_state.df_stations_info.empty:
    fig = px.scatter_mapbox(df,
                            lat="latitud",
                            lon="longitud",
                            hover_name="nombre",
                            zoom=5)
    
    # Cambiar el tipo de marcador y aumentar el tamaño
    fig.update_traces(marker=dict(size=15, color="red"))

    # Usar un estilo de mapa para la visualización
    fig.update_layout(mapbox_style="open-street-map", 
                  margin={"r":0,"t":0,"l":0,"b":0},
                  width=1000, height=600)
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("No se ha podido obtener información de las estaciones de AEMET")
