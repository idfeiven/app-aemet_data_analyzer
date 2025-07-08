import streamlit as st
from download.stations import download_normal_values
from download.stations import download_stations_info

# -----------------------------FUNCTIONS-----------------------------

# Función para mostrar mensaje en tiempo real
def add_message(msg: str) -> None:
    """
    Appends a message to Streamlit session state and displays all messages in a styled HTML box.

    This function is used to log real-time messages in a scrollable, monospaced console-style
    container within a Streamlit app. Messages are stored in `st.session_state.messages`.

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


# -------------------------------MAIN PROGRAM-------------------------------------

st.set_page_config(layout="wide")

st.title("Valores normales (1991-2020)")
st.write("Fuente: red de estaciones meteorológicas de AEMET.")

if "stations_info" not in st.session_state:
    message_container = st.empty()
    st.session_state.messages = []
    st.session_state.stations_info = download_stations_info.download_stations_info(message = add_message)

df_info = st.session_state.stations_info
province = st.selectbox("Selecciona una provincia", df_info['provincia'].unique(), key="provincia")
station_name = st.selectbox("Selecciona una estación", df_info[df_info['provincia'] == province]['nombre'].unique(), key="estacion")

# Mostrar un campo de entrada para que el usuario ingrese la API Key
api_key = st.text_input("Introduce tu API Key", type="password")
if not api_key:
    st.warning("Por favor, introduce tu API Key para continuar.")
else:
    st.success("API Key introducida correctamente.")
    df_info.rename({"idema": "indicativo"}, axis = 1, inplace=True)
    station_id = df_info[df_info['nombre'] == station_name]['indicativo'].values[0]

    if "normal_vals" not in st.session_state or "metadata" not in st.session_state:
        message_container = st.empty()
        st.session_state.messages = []
        st.session_state.normal_vals, st.session_state.metadata = download_normal_values.download_normal_values(api_key, station_id, add_message)
        normal_vals = st.session_state.normal_vals
        metadata = st.session_state.metadata

    st.markdown(f"### Valores normales de la estación {station_name} ({station_id}) en {province}")
    st.dataframe(normal_vals, use_container_width=True)

    st.markdown("### Metadatos de la estación")
    st.dataframe(metadata, use_container_width=True)

