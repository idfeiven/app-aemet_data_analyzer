import streamlit as st
from download.stations import download_extreme_values
from download.stations import download_stations_info

# -----------------------------FUNCTIONS-----------------------------

# Función para mostrar mensaje en tiempo real
def add_message(msg: str) -> None:
    """
    Appends a message to Streamlit session state and displays all messages in a styled HTML box.

    This function is used to log real-time messages in a scrollable, monospaced console-style
    container within a Streamlit app. Messages are stored in `st.session_state.mensajes`.

    Args:
        msg (str): The message to append and display.

    Notes:
        Requires that `mensaje_container` is a previously defined Streamlit container and
        that `st.session_state.messages` is a list initialized before use.
    """
    st.session_state.messages.append(msg)
    html = f"""
    <div style="background-color:#111; color:#0f0; padding:10px;
                height:150px; overflow-y:auto; font-family:monospace;
                font-size:16px; border:1px solid #444;">
        {"<br>".join(st.session_state.messages)}
    </div>
    """
    message_container.markdown(html, unsafe_allow_html=True)


def get_parameter(variable: str) -> str:
    """
    Returns the parameter code based on the variable name.

    Args:
        variable (str): The name of the variable (e.g., "Temperatura", "Precipitación", "Velocidad del viento").

    Returns:
        str: The corresponding parameter code.
    """
    if variable == "Temperatura":
        return "T"
    elif variable == "Precipitación":
        return "P"
    elif variable == "Velocidad del viento":
        return "V"
    else:
        raise ValueError("Variable no reconocida.")

# -------------------------------MAIN PROGRAM-------------------------------------

st.set_page_config(layout="wide")

st.title("Valores extremos de las estaciones meteorológicas de AEMET")
st.write("Fuente: red de estaciones meteorológicas de AEMET.")

# Caché stations info
if "stations_info" not in st.session_state:
    message_container = st.empty()
    st.session_state.messages = []
    st.session_state.stations_info = download_stations_info.download_stations_info(message = add_message)

df_info = st.session_state.stations_info
province = st.selectbox("Selecciona una provincia", df_info['provincia'].unique(), key="provincia")
station_name = st.selectbox("Selecciona una estación", df_info[df_info['provincia'] == province]['nombre'].unique(), key="estacion")
variable = st.selectbox("Selecciona una variable", ["Temperatura", "Precipitación", "Velocidad del viento"], key="variable")

# Mostrar un campo de entrada para que el usuario ingrese la API Key
api_key = st.text_input("Introduce tu API Key", type="password")
if not api_key:
    st.warning("Por favor, introduce tu API Key para continuar.")
    st.stop()
else:
    st.success("API Key introducida correctamente.")
    df_info.rename({"idema": "indicativo"}, axis = 1, inplace=True)
    station_id = df_info[df_info['nombre'] == station_name]['indicativo'].values[0]

    # Caché extreme values and metadata
    if "extreme_vals" not in st.session_state or "metadata" not in st.session_state or st.session_state.get("parameter") != get_parameter(variable):
        message_container = st.empty()
        st.session_state.messages = []
        extreme_vals, metadata = download_extreme_values.download_extreme_values(api_key, station_id, get_parameter(variable), add_message)

    st.markdown(f"### Valores extremos de {variable} de la estación {station_name} ({station_id}) en {province}")
    st.dataframe(extreme_vals, use_container_width=True)

    st.markdown("### Metadatos de la variable")
    st.dataframe(metadata, use_container_width=True)

