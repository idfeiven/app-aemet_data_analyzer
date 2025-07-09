'''
This module plots climate 
from a reference period
for AEMET weather stations.

(c) 2025 Iván Domínguez Fuentes
'''

import pandas as pd
import streamlit as st
import plotly.colors as pc
import plotly.graph_objects as go
from download.stations import download_stations_info
from download.stations import download_history_observation

# ----------------------------FUNCTIONS----------------------------

@st.cache_data
def parse_data(df):
    df = _parse_dates(df)
    df = _convert_columns_to_numeric(df)
    df = _change_column_names(df)
    return df

def _parse_dates(df):
    df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d', errors='coerce')
    return df

def _convert_columns_to_numeric(df):
    cols_to_num = [
        "altitud", "tmed", "tmax", "tmin", "prec", "dir", "velmedia",
        "racha", "sol", "presMax", "presMin", "hrMedia", "hrMax", "hrMin"
    ]
    if "prec" in df.columns:
        df["prec"] = df["prec"].astype(str).str.replace("Ip", "0.0", regex=False)

    for col in cols_to_num:
        if col in df.columns:
            df[col] = df[col].str.replace(",", ".").astype(float)
    return df

def _change_column_names(df):
    return df.rename(columns={
        "altitud": "Altitud (m)",
        "tmed": "Temperatura media (°C)",
        "tmax": "Temperatura máxima (°C)",
        "tmin": "Temperatura mínima (°C)",
        "prec": "Precipitación (mm)",
        "dir": "Dirección del viento (°)",
        "velmedia": "Velocidad media del viento (m/s)",
        "racha": "Racha máxima del viento (m/s)",
        "sol": "Horas de sol",
        "presMax": "Presión máxima (hPa)",
        "presMin": "Presión mínima (hPa)",
        "hrMedia": "Humedad relativa media (%)",
        "hrMax": "Humedad relativa máxima (%)",
        "hrMin": "Humedad relativa mínima (%)"
    })

def plot_interactive_data_by_year(df, value_col, title, yaxis_title, color_palette='Viridis'):
    fig = go.Figure()
    df = df.dropna(subset=['fecha', value_col])
    if df.empty:
        return fig

    df.loc[:, 'aligned_date'] = pd.to_datetime('2000-' + df.fecha.dt.strftime('%m-%d'))
    years = sorted(df.fecha.dt.year.unique())
    color_list = pc.sample_colorscale(color_palette, [i / max(len(years)-1, 1) for i in range(len(years))])

    for i, year in enumerate(years):
        yearly_data = df[df.fecha.dt.year == year]
        if yearly_data.empty:
            continue
        fig.add_trace(go.Scatter(
            x=yearly_data['aligned_date'],
            y=yearly_data[value_col],
            mode='lines',
            name=str(year),
            line=dict(color=color_list[i])
        ))

    fig.update_layout(
        title=title,
        xaxis_title='Día del año',
        yaxis_title=yaxis_title,
        xaxis=dict(tickformat='%d-%m'),
        height=500,
        width=900
    )
    return fig

def add_message(msg: str) -> None:
    st.session_state.messages.append(msg)
    html = f"""
    <div style="background-color:#111; color:#0f0; padding:10px;
                height:150px; overflow-y:auto; font-family:monospace;
                font-size:16px; border:1px solid #444;">
        {"<br>".join(st.session_state.messages)}
    </div>
    """
    st.session_state.message_container.markdown(html, unsafe_allow_html=True)

# --------------------------MAIN--------------------------

st.set_page_config(
    page_title="Gráficas del clima de estaciones AEMET",
    page_icon="🌤️",
    layout="wide"
)

st.title("Gráficas del clima de estaciones AEMET")
st.write("Este módulo permite visualizar gráficas del clima de estaciones AEMET a partir de un periodo de referencia.")

api_key = st.text_input("Introduce tu API Key", type="password")
if not api_key:
    st.warning("Por favor, introduce tu API Key para continuar.")
    st.stop()

st.session_state.api_key = api_key

if "stations_info" not in st.session_state:
    st.session_state.message_container = st.empty()
    st.session_state.messages = []
    st.session_state.stations_info = download_stations_info.download_stations_info(message=add_message)

df_info = st.session_state.stations_info

province = st.selectbox("Selecciona una provincia", df_info['provincia'].unique())
st.session_state.province = province

station_name = st.multiselect("Selecciona una estación", options=df_info[df_info['provincia'] == province]['nombre'].unique())
st.session_state.station_name = station_name

station_ids = df_info[df_info['nombre'].isin(station_name)]["indicativo"].tolist()
station_id_str = ','.join(station_ids)

ref_period = st.selectbox("Selecciona un período de referencia", options=["1981-2010", "1991-2020"])
date_ini = ref_period.split("-")[0] + "-01-01"
date_end = ref_period.split("-")[1] + "-12-31"

if st.button("Descargar datos"):
    if not station_id_str:
        st.warning("Por favor, selecciona al menos una estación.")
        st.stop()
    st.session_state.message_container = st.empty()
    st.session_state.messages = []
    raw_data = download_history_observation.download_history_observation(
        date_ini, date_end, station_id_str, api_key, add_message
    )
    st.session_state.data = raw_data
    st.session_state.data_parsed = parse_data(raw_data)
    st.success("Datos descargados y procesados correctamente.")

if "data_parsed" in st.session_state and not st.session_state.data_parsed.empty:
    var = st.selectbox("Selecciona una variable para graficar", options=[
        "Temperatura media (°C)",
        "Temperatura máxima (°C)",
        "Temperatura mínima (°C)",
        "Precipitación (mm)",
        "Dirección del viento (°)",
        "Velocidad media del viento (m/s)",
        "Racha máxima del viento (m/s)",
        "Horas de sol",
        "Presión máxima (hPa)",
        "Presión mínima (hPa)",
        "Humedad relativa media (%)",
        "Humedad relativa máxima (%)",
        "Humedad relativa mínima (%)"])

    for station in st.session_state.data_parsed['indicativo'].unique():
        station_data = st.session_state.data_parsed[
            st.session_state.data_parsed['indicativo'] == station
        ]
        station_name = station_data['nombre'].iloc[0]
        if var in station_data.columns and not station_data[var].dropna().empty:
            fig = plot_interactive_data_by_year(
                df=station_data,
                value_col=var,
                title=f"{var} en {station} {station_name} ({province})",
                yaxis_title=var
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No hay datos disponibles para la variable '{var}' en la estación {station_name}.")
    
    st.dataframe(st.session_state.data_parsed, use_container_width=True)
else:
    st.info("Por favor, descarga los datos para poder visualizar las gráficas.")
