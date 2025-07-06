import streamlit as st
from download.stations import download_normal_values
from download.stations import download_stations_info

# -----------------------------FUNCTIONS-----------------------------

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


# -------------------------------MAIN PROGRAM-------------------------------------

st.set_page_config(layout="wide")

st.title("Valores normales (1991-2020)")
st.write("Fuente: red de estaciones meteorológicas de AEMET.")

if "stations_info" not in st.session_state:
    mensaje_container = st.empty()
    st.session_state.mensajes = []
    st.session_state.stations_info = download_stations_info.download_stations_info(message = agregar_mensaje)

df_info = st.session_state.stations_info
province = st.selectbox("Selecciona una provincia", df_info['provincia'].unique(), key="provincia")
station_name = st.selectbox("Selecciona una estación", df_info[df_info['provincia'] == province]['nombre'].unique(), key="estacion")

# # Cacheamos provincia e id de estacion elegida
# if "province" not in st.session_state or "station_name" not in st.session_state or \
#     st.session_state.get("province") != province or st.session_state.get("station_name") != station_name:
#         st.session_state.province = province
#         st.session_state.station_name = station_name

# Mostrar un campo de entrada para que el usuario ingrese la API Key
api_key = st.text_input("Introduce tu API Key", type="password")
if not api_key:
    st.warning("Por favor, introduce tu API Key para continuar.")
else:
    st.success("API Key introducida correctamente.")
    df_info.rename({"idema": "indicativo"}, axis = 1, inplace=True)
    station_id = df_info[df_info['nombre'] == station_name]['indicativo'].values[0]

    if "normal_vals" not in st.session_state or "metadata" not in st.session_state:
        mensaje_container = st.empty()
        st.session_state.mensajes = []
        st.session_state.normal_vals, st.session_state.metadata = download_normal_values.download_normal_values(api_key, station_id, agregar_mensaje)
        normal_vals = st.session_state.normal_vals
        metadata = st.session_state.metadata

    st.markdown(f"### Valores normales de la estación {station_name} ({station_id}) en {province}")
    st.dataframe(normal_vals, use_container_width=True)

    st.markdown("### Metadatos de la estación")
    st.dataframe(metadata, use_container_width=True)

