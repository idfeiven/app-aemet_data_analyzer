'''
This program uses AEMET OpenData
to download station information
from the AEMET station network

Author: Iván Domínguez Fuentes

(c) 2025
'''

import yaml
import requests
import pandas as pd
import streamlit as st
from pathlib import Path

# -----------------------------FUNCTIONS----------------------------------

def load_config_file():
    fpath = Path(__file__).parent.parent / "etc" / "config.yml"

    with open(fpath, 'r') as file:
        config = yaml.safe_load(file)
    
    return config

def get_stations_info(config):

    url = config['url_base'] + config['endpoints']['stations']['inventory_all'] + config['api_key']

    try:
        response = requests.get(url)

        if response.status_code == 200:
            print(f'{response.reason}. Successful request to the API')
            response_json = response.json()

            try:
                data = requests.get(response_json['datos'])
            except Exception as e:
                print(f'{response.json['descripcion']}')
                return pd.DataFrame()

            if data.status_code == 200:
                print(f' - {data.reason}. Successful data request.')
                data_json = data.json()

                df_stations_info = pd.DataFrame(data_json)
                return df_stations_info
            else:
                print(f' - {response.status_code}. {response.reason}')
                return pd.DataFrame()

        else:
            print(f'{response.status_code}. {response.reason}')
            return pd.DataFrame()

    except Exception as e:
        print(f'Failed to request to the API. {e}.')
        return pd.DataFrame()


def _parse_coordinate(coord: str) -> float:
    """Convierte coordenadas en formato 'XXXXXXN' o 'XXXXXXE' a float con signo."""
    degrees = int(coord[:2])  # Primeros dos dígitos son los grados
    minutes = int(coord[2:4])  # Siguientes dos son los minutos
    seconds = int(coord[4:6])  # Últimos dos son los segundos
    direction = coord[-1]  # Última letra es la dirección

    decimal_degrees = degrees + (minutes / 60) + (seconds / 3600)

    return -decimal_degrees if direction in ['S', 'W'] else decimal_degrees


def parse_stations_info(df_stations_info):

    df_stations_info['latitud'] = df_stations_info['latitud'].apply(_parse_coordinate)
    df_stations_info['longitud'] = df_stations_info['longitud'].apply(_parse_coordinate)
    df_stations_info['altitud'] = df_stations_info['altitud'].apply(float)
    df_stations_info['provincia'] = df_stations_info['provincia'].str.replace('BALEARES', 'ILLES BALEARS')
    df_stations_info['provincia'] = df_stations_info['provincia'].str.replace('SANTA CRUZ DE TENERIFE', 'STA. CRUZ DE TENERIFE')

    return df_stations_info


# -----------------------------MAIN PROGRAM----------------------------------

@st.cache_data
def download_stations_info():
    config = load_config_file()
    df_stations_info = get_stations_info(config)

    if not df_stations_info.empty:
        df_stations_info = parse_stations_info(df_stations_info)
    else:
        print("Could not parse stations information.")

    return df_stations_info

