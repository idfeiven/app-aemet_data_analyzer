# pages/mapa.py (Página del mapa interactivo)
import pandas as pd
import streamlit as st
import plotly.express as px
from download.stations import download_today_observation
from download.stations import download_stations_info
# st.cache_data.clear()

# -----------------------------FUNCTIONS--------------------------------

def parse_stations_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parses and cleans meteorological station data to prepare it for display or analysis.

    This function performs the following operations:
    - Converts the 'fint' column (timestamp) to datetime format and removes timezone info.
    - Filters the DataFrame to only include rows corresponding to the most recent timestamp.
    - Renames key columns to more descriptive, user-friendly labels, typically for display.

    Args:
        df (pd.DataFrame): The original DataFrame containing raw station data. It must include
                           a column named 'fint' with timestamps and various meteorological variables.

    Returns:
        pd.DataFrame: A cleaned and formatted DataFrame containing only the latest available data,
                      with renamed columns for readability.
    """
    df = df.copy()
    df['fint'] = df['fint'].apply(pd.to_datetime)
    df['fint'] = df['fint'].dt.tz_localize(None)
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


def get_colormap_variable(variable: str) -> str:
    """
    Returns a color map based on the variable name.

    Args:
        variable (str): The name of the variable to determine the color map.

    Returns:
        str: The name of the color map to be used for the variable.
    """
    if variable in ['Precipitación (mm)', 'Espesor de nieve (cm)']:
        return "BuPu"
    elif variable in ['Velocidad máxima (m/s)', 'Velocidad media (m/s)']:
        return "turbo"
    elif variable in ['Dirección media del viento (º)', 'Dirección racha máxima (º)']:
        return "hsv"
    elif variable in ['Humedad relativa (%)']:
        return "Viridis_r"
    elif variable in ['Presión absoluta (hPa)', 'Presión al nivel del mar (hPa)']:
        return "rdpu"
    else:
        return "Viridis"

# -------------------------------MAIN PROGRAM-------------------------------------
st.set_page_config(layout="wide")

st.title("Últimas observaciones")
st.markdown("## Mapa interactivo")
st.write("Fuente: red de estaciones meteorológicas de AEMET.")

# Cacheamos info y datos
if "data_stations" not in st.session_state:
    mensaje_container = st.empty()
    st.session_state.mensajes = []
    st.session_state.data_stations = download_today_observation.download_today_observation(message = agregar_mensaje)

if "stations_info" not in st.session_state:
    mensaje_container = st.empty()
    st.session_state.mensajes = []
    st.session_state.stations_info = download_stations_info.download_stations_info(message = agregar_mensaje)


df = st.session_state.data_stations
df_info = st.session_state.stations_info

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
    # datetime = st.selectbox(label = "Selecciona un instante de tiempo", options = df['fint'].unique(), index = 0)

    datetime = st.select_slider(
        "Selecciona una hora",
        options=df['fint'].unique(),
        value=df['fint'].unique()[-1]
    )
    
    # Cacheamos la variable elegida
    if "col" not in st.session_state or "datetime" not in st.session_state or\
        st.session_state.get("col") != col or st.session_state.get("datetime") != datetime:
        st.session_state.col = col
        st.session_state.datetime = datetime

    df_filtered = df[df['fint'] == datetime]

    fig = px.scatter_mapbox(df_filtered.dropna(subset=[col]),
                            lat = "lat",
                            lon = "lon",
                            hover_name = "ubi",
                            hover_data = col,
                            color = col,
                            color_continuous_scale = get_colormap_variable(col),
                            title = f"{col} {datetime} en las estaciones de AEMET",
                            size_max=15,
                            zoom=5)
       
    # Cambiar el tipo de marcador y tamaño del mapa
    fig.update_traces(marker=dict(size=12,
                                  color=df_filtered[col],
                                  colorscale="Viridis"))

    # Usar un estilo de mapa para la visualización
    fig.update_layout(mapbox_style="open-street-map", 
                  margin={"r":0,"t":0,"l":0,"b":0},
                  width=2000, height=600)
    
    # Cacheamos el mapa interactivo
    if "fig" not in st.session_state or st.session_state.get("fig") != fig:
        st.session_state.fig = fig

    st.plotly_chart(fig, use_container_width=True)

else:
    st.write("No se ha podido obtener datos de las estaciones de AEMET")


if not type(df_info) == None:

   st.markdown("## Gráficas de datos horarios")

   province = st.selectbox(label = "Selecciona una provincia", options = df_info['provincia'].unique(), index = 0)
   station_name = st.selectbox(label = "Selecciona una estación", options = df_info[df_info['provincia'] == province]['nombre'].unique(), index = 0) 
   
   # Cacheamos provincia e id de estacion elegida
   if "province" not in st.session_state or "station_name" not in st.session_state or \
       st.session_state.get("province") != province or st.session_state.get("station_name") != station_name:
            st.session_state.province = province
            st.session_state.station_name = station_name

   df.rename({"idema": "indicativo"}, axis = 1, inplace=True)
   df_station = df.merge(df_info, how = "left")
   df_station = df_station[df_station['nombre'] == station_name]

   if not df_station.empty:
       col_stn = st.selectbox(label = "Selecciona una variable", options = df_station[cols_to_choose].columns, key = "variable_station")
       
       # Cacheamos la variable elegida
       if "col_stn" not in st.session_state or st.session_state.get("col_stn") != col_stn:
            st.session_state.col_stn = col_stn
       
       fig = px.line(df_station, x='fint', y=col_stn, title=f"{col_stn} en {station_name} ({province})")
       st.plotly_chart(fig, use_container_width=True)
   else:
       st.write("No se han encontrado datos para la estación seleccionada.")