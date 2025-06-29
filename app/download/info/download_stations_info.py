'''
This program uses AEMET OpenData
to download station information
from the AEMET station network

Author: Iván Domínguez Fuentes

(c) 2025
'''

import time
import yaml
import requests
import pandas as pd
import streamlit as st
from pathlib import Path

# todo fix false errors when downloading
# -----------------------------FUNCTIONS----------------------------------

def load_config_file() -> dict:
    """
    Loads the YAML configuration file located in the `etc` folder.

    Returns:
        dict: Dictionary containing the configuration loaded from `config.yml`.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If an error occurs while parsing the YAML file.
    """
    fpath = Path(__file__).parent.parent / "etc" / "config.yml"

    with open(fpath, 'r') as file:
        config = yaml.safe_load(file)
    
    return config


def get_stations_info(config: dict) -> pd.DataFrame | None:
    """
    Downloads the inventory information of weather stations from the AEMET API.

    It performs multiple retries (up to 10) in case of network errors or invalid responses.

    Args:
        config (dict): Configuration dictionary containing:
            - url_base (str): Base URL of the API.
            - endpoints['stations']['inventory_all'] (str): Endpoint path for retrieving the station inventory.
            - api_key (str): API key string.

    Returns:
        pd.DataFrame | None: A DataFrame containing station information if the download succeeds,
                             or None if all retries fail.

    Side Effects:
        Displays progress and error messages via Streamlit (`st.write`).

    Raises:
        requests.exceptions.RequestException: If a connection error occurs.
    """

    url = config['url_base'] + config['endpoints']['stations']['inventory_all'] + config['api_key']
    retries = 0
    max_retries = 10

    while retries <= max_retries:
        st.write(f'Intentos: {retries}')
        
        try:
            response = requests.get(url)

            if response.status_code == 200:
                st.write(f'{response.reason}. Successful request to the API')
                response_json = response.json()

                try:
                    data = requests.get(response_json['datos'])

                    if data.status_code == 200:
                        st.write(f' - {data.reason}. Successful data request.')
                        data_json = data.json()

                        df_stations_info = pd.DataFrame(data_json)
                        return df_stations_info
                    else:
                        st.write(f' - {response.status_code}. {response.reason}')
                        retries += 1
                        time.sleep(5)

                except Exception as e:
                    st.write(f"{response.json()['descripcion']}")
                    retries += 1
                    time.sleep(5)

            else:
                st.write(f'{response.status_code}. {response.reason}')
                retries += 1
                time.sleep(5)

        except requests.exceptions.RequestException as e:
            st.write(f'Failed to request to the API. {e}.')
            retries += 1
            time.sleep(5)


def _parse_coordinate(coord: str) -> float:
    """
    Converts a coordinate string in DMS (degrees, minutes, seconds) format with a direction
    into a signed decimal degree value.

    Example input format: '403000N' or '0023015W'.

    Args:
        coord (str): Coordinate string in DMS format followed by the direction character.

    Returns:
        float: Decimal degrees. Negative if direction is 'S' or 'W'.

    Raises:
        ValueError: If the coordinate format is invalid.
    """
    degrees = int(coord[:2])  # Primeros dos dígitos son los grados
    minutes = int(coord[2:4])  # Siguientes dos son los minutos
    seconds = int(coord[4:6])  # Últimos dos son los segundos
    direction = coord[-1]  # Última letra es la dirección

    decimal_degrees = degrees + (minutes / 60) + (seconds / 3600)

    return -decimal_degrees if direction in ['S', 'W'] else decimal_degrees


def parse_stations_info(df_stations_info: pd.DataFrame):
    """
    Cleans and transforms the stations DataFrame:
    - Converts coordinates from DMS to decimal degrees.
    - Converts altitude to float.
    - Normalizes province names.

    Args:
        df_stations_info (pd.DataFrame): DataFrame containing station information,
            expected to have the columns: 'latitud', 'longitud', 'altitud', 'provincia'.

    Returns:
        pd.DataFrame: The cleaned DataFrame with converted coordinates, float altitudes,
                      and corrected province names.
    """
    df_stations_info['latitud'] = df_stations_info['latitud'].apply(_parse_coordinate)
    df_stations_info['longitud'] = df_stations_info['longitud'].apply(_parse_coordinate)
    df_stations_info['altitud'] = df_stations_info['altitud'].apply(float)
    df_stations_info['provincia'] = df_stations_info['provincia'].str.replace('BALEARES', 'ILLES BALEARS')
    df_stations_info['provincia'] = df_stations_info['provincia'].str.replace('SANTA CRUZ DE TENERIFE', 'STA. CRUZ DE TENERIFE')

    return df_stations_info


# -----------------------------MAIN PROGRAM----------------------------------


def download_stations_info() -> pd.DataFrame | None:
    '''
    Main method for download stations info from AEMET.
    '''
    config = load_config_file()
    df_stations_info = get_stations_info(config)

    if len(df_stations_info) != 0:
        df_stations_info = parse_stations_info(df_stations_info)
    else:
        st.write("Could not parse stations information.")

    return df_stations_info

