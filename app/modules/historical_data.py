import io
import pandas as pd
import streamlit as st
import plotly.express as px
from download.stations import download_history_observation
from download.info import download_stations_info


def get_dates(date_range):
    # Verificar si el usuario ha seleccionado un rango válido
    if isinstance(date_range, tuple) and len(date_range) == 2:
        date_ini = date_range[0].strftime("%Y-%m-%d")
        date_end = date_range[1].strftime("%Y-%m-%d")
        st.write(f"📅 Fecha inicio: {date_ini}")
        st.write(f"📅 Fecha fin: {date_end}")
    else:
        date_ini, date_end = None, None
        st.warning("Selecciona un rango de fechas válido.")

    # Devolver los valores como strings
    return date_ini, date_end

# Función para convertir DataFrame a Excel en memoria
def to_excel(df):
    output = io.BytesIO()  # Crear un buffer en memoria
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")  # Guardar en hoja "Datos"
    return output.getvalue()  # Obtener bytes del archivo


st.title("Datos históricos")
st.markdown("### En esta página puedes descargar datos históricos de las estaciones de AEMET")
st.write("Toda la información expuesta aquí pertenece a AEMET. Esta página es simplemente divulgativa.")
st.write("Fuente de los datos: AEMET OpenData")
st.warning("La descarga de datos puede llevar mucho tiempo. Para series de datos muy largas la descarga completa de los datos se estima entre 40 y 50 minutos.")

stations_info = download_stations_info.download_stations_info()

if not stations_info.empty:

    if "stations_info" not in st.session_state:
        st.session_state.stations_info = stations_info
        stations_info = st.session_state.stations_info

    province = st.selectbox(label = "Selecciona una provincia", options = stations_info["provincia"].unique())
    stations_info_province = stations_info[stations_info["provincia"] == province]

    station_name = st.selectbox(label = "Selecciona una estación", options = stations_info_province["nombre"].unique())
    station_id = stations_info_province[stations_info_province["nombre"] == station_name]["indicativo"].values.flatten()[0]
    st.write(f"Se descargarán los datos de la estación {station_id}")

    # Selector de rango de fechas
    date_range = st.date_input("Selecciona el rango de fechas", [])
    date_ini, date_end = get_dates(date_range)

    # Mostrar un campo de entrada para que el usuario ingrese la API Key
    api_key = st.text_input("Introduce tu API Key", type="password")

    # Verificar si el campo no está vacío
    if api_key:
        st.success("API Key recibida con éxito.")

        station_data_history = download_history_observation.download_history_observation(date_ini,
                                                                                        date_end,
                                                                                        station_id,
                                                                                        api_key)

        if not station_data_history.empty:
            st.dataframe(station_data_history)

            data_excel = to_excel(station_data_history)

            # Botón para descargar como Excel
            st.download_button(
                label="📥 Descargar como Excel",
                data=data_excel,
                file_name=f"{station_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            st.write("No existen datos para esta estación en el período seleccionado.")

    else:
        st.warning("Por favor, introduce tu API Key. Si no tienes una API key visita https://opendata.aemet.es/centrodedescargas/altaUsuario?")

else:
    st.write("No se ha podido obtener información de las estaciones de AEMET")