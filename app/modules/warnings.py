import pandas as pd
import streamlit as st
from datetime import datetime
from streamlit_folium import st_folium
from download.warnings import download_aemet_warnings, warnings_plotter
 
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


# -------------------------------MAIN PROGRAM-------------------------------------
st.cache_data.clear()

st.set_page_config(layout="wide")
st.title("Avisos meteorológicos de AEMET")
st.write("Fuente: AEMET (Agencia Estatal de Meteorología)")

# Descargar avisos si no están ya en memoria
if "warnings" not in st.session_state:
    try:
        message_container = st.empty()
        st.session_state.messages = []
        st.session_state.warnings = download_aemet_warnings.download_aemet_warnings(area='esp', message=add_message)
    except Exception as e:
        st.error(f'Error while downloading warnings: {e}')
        st.stop()
    
# Mostrar selector de fecha
date = st.selectbox(
    label="Selecciona una fecha para ver los avisos activos:",
    options=pd.date_range(datetime.today().date(), periods=3).strftime("%Y-%m-%d"),
    key="selected_date"
)

if "warnings_map" not in st.session_state or st.session_state.date != date:
    st.session_state.date = date
    tar_bytes = st.session_state.warnings
    tar_bytes.seek(0)  # ⬅️ Reposicionar cursor antes de leer
    try:
        st.session_state.warnings_map = warnings_plotter.plot_aemet_warnings(date, tar_bytes)
    except Exception as e:
        st.error(f'Error found when generating interactive map: {e}')
        st.stop()

# Mostrar el mapa (fuera del condicional para que siempre se muestre)
st.subheader("Mapa de Avisos Activos")
st_folium(st.session_state.warnings_map, width=1000, height=500)

