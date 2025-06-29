import io
import time
import datetime
import pandas as pd
import streamlit as st
from download.info import download_stations_info
from download.stations import download_history_observation

# -----------------------------------------------FUNCTIONS-----------------------------------

def get_dates(date_range: tuple) -> tuple[str, str]:
    """
    Parses a tuple of datetime objects and returns start and end dates as formatted strings.

    If the tuple is valid and contains two datetime objects, the function returns their
    string representations in 'YYYY-MM-DD' format and displays them using Streamlit.

    Args:
        date_range (tuple): A tuple containing two datetime objects (start and end dates).

    Returns:
        tuple[str, str]: A tuple with start and end dates as strings.
                         Returns (None, None) if input is not valid.
    """
    # Verificar si el usuario ha seleccionado un rango válido
    if isinstance(date_range, tuple) and len(date_range) == 2:
        date_ini = date_range[0].strftime("%Y-%m-%d")
        date_end = date_range[1].strftime("%Y-%m-%d")
        st.write(f"📅 Fecha inicio: {date_ini}")
        st.write(f"📅 Fecha fin: {date_end}")
        # Devolver los valores como strings
        return date_ini, date_end
    else:
        return None, None

# Función para convertir DataFrame a Excel en memoria
def to_excel(df: pd.DataFrame) -> bytes:
    """
    Converts a Pandas DataFrame to an in-memory Excel file in `.xlsx` format.

    The resulting Excel file is written to memory using `openpyxl` and can be used
    for download or further processing without saving to disk.

    Args:
        df (pd.DataFrame): The DataFrame to convert.

    Returns:
        bytes: The byte content of the Excel file.
    """
    output = io.BytesIO()  # Crear un buffer en memoria
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")  # Guardar en hoja "Datos"
    return output.getvalue()  # Obtener bytes del archivo

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
                height:300px; overflow-y:auto; font-family:monospace;
                font-size:14px; border:1px solid #444;">
        {"<br>".join(st.session_state.mensajes)}
    </div>
    """
    mensaje_container.markdown(html, unsafe_allow_html=True)

# -----------------------------------------------MAIN PROGRAM-----------------------------------
# st.set_page_config(layout="wide")

st.title("Datos históricos")
st.markdown("### En esta página puedes descargar datos históricos de las estaciones de AEMET")
st.write("Toda la información expuesta aquí pertenece a AEMET. Esta página es simplemente divulgativa.")
st.write("Fuente de los datos: AEMET OpenData")
st.warning("Los tiempos de descarga pueden variar mucho en función del rendimiento de la API AEMET OpenData. Se estima la descarga completa entre 20-40 minutos.")

# Selector de rango de fechas
today = datetime.datetime.today().date()
date_min = datetime.datetime(1914,1,1).date()
date_range = st.date_input("Selecciona el rango de fechas",
                            (today - datetime.timedelta(days = 30), today),
                            min_value=date_min,
                            max_value=today,
                            format="YYYY-MM-DD",)
date_ini, date_end = get_dates(date_range)

# Mostrar un campo de entrada para que el usuario ingrese la API Key
api_key = st.text_input("Introduce tu API Key", type="password")

# Guardamos en caché las fechas introducidas o los cambios,
# así como el valor de la API key
if date_range not in st.session_state or \
st.session_state.get("date_ini") != date_ini or \
st.session_state.get("date_end") != date_end or \
api_key not in st.session_state or \
"mensajes" not in st.session_state:
    st.session_state["date_range"] = date_range
    st.session_state["date_ini"] = date_ini
    st.session_state["date_end"] = date_end
    st.session_state["api_key"] = api_key
    st.session_state.mensajes = []

# Guardamos en caché la información de las estaciones
if "stations_info" not in st.session_state:
    mensaje_container = st.empty()
    st.session_state["stations_info"] = download_stations_info.download_stations_info(agregar_mensaje)
stations_info = st.session_state["stations_info"]

# Si la petición de información de estaciones es exitosa y existen todos los campos
# rellenados, comienza la descarga.
if len(stations_info) != 0:

    province = st.selectbox(label = "Selecciona una provincia", options = stations_info["provincia"].unique())
    stations_info_province = stations_info[stations_info["provincia"] == province]

    station_name = st.multiselect(label = "Selecciona una estación", options = stations_info_province["nombre"].unique())
    try:
        station_id = stations_info_province[stations_info_province["nombre"].isin(station_name)]["indicativo"].values.flatten()
        station_id = ','.join(station_id)
        st.write(f"Se descargarán los datos de la/s estación/es {station_id}")
    except Exception as e:
        st.warning('Selecciona una o varias estaciones')
        
    # Verificar si el campo no está vacío
    if api_key:
        st.success("API Key recibida con éxito.")

        st.write("Seguimiento del proceso de descarga")
        mensaje_container = st.empty()
        station_data_history = download_history_observation.download_history_observation(date_ini,
                                                                                        date_end,
                                                                                        station_id,
                                                                                        api_key,
                                                                                        agregar_mensaje)
        
        if not station_data_history.empty:
            st.dataframe(station_data_history)

            data_excel = to_excel(station_data_history)

            # Botón para descargar como Excel
            st.success("Descarga completada con éxito")
            st.download_button(
                label="📥 Descargar como Excel",
                data=data_excel,
                file_name=f"{station_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            st.warning("No existen datos para esta estación en el período seleccionado.")

    else:
        st.warning("Por favor, introduce tu API Key. Si no tienes una API key visita https://opendata.aemet.es/centrodedescargas/altaUsuario?")

else:
    st.warning("No se ha podido obtener información de las estaciones de AEMET")