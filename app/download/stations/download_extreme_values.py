'''
This program uses AEMET OpenData
to download extreme values
from the AEMET station network

Author: Iván Domínguez Fuentes

(c) 2025
'''

import time
import yaml
import requests
import numpy as np
import pandas as pd
from pathlib import Path

# -----------------------------FUNCTIONS----------------------------

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


def get_station_extreme_vals(config: dict, api_key: str, station_id: str, parameter: str, message: callable) -> pd.DataFrame | None:
    """
    Downloads the inventory information of weather stations from the AEMET API.

    It performs multiple retries (up to 10) in case of network errors or invalid responses.

    Args:
        config (dict): Configuration dictionary containing:
            - url_base (str): Base URL of the API.
            - endpoints['stations']['inventory_all'] (str): Endpoint path for retrieving the station inventory.
            - api_key (str): API key string.
        message (callable): Function to log messages (e.g., `st.write` for Streamlit).

    Returns:
        pd.DataFrame | None: A DataFrame containing station information if the download succeeds,
                             or None if all retries fail.

    Side Effects:
        Displays progress and error messages via Streamlit (`st.write`).

    Raises:
        requests.exceptions.RequestException: If a connection error occurs.
    """
    config['api_key'] = f'/?api_key={api_key}'
    url = config['url_base'] + config['endpoints']['stations']['extreme_values'] + config['api_key']

    url = url.format(api_key=api_key,
                     parametro=parameter,
                     idema=station_id)

    retries = 0
    max_retries = 10

    while retries <= max_retries:
        message(f'Attempt {retries + 1} to download extreme values...')
        
        try:
            response = requests.get(url)

            if response.status_code == 200:
                message(f' - {response.reason}. Successful request to the API')
                response_json = response.json()

                try:
                    response_data = requests.get(response_json['datos'])
                    
                    if response_data.status_code == 200:
                        message(f' -- {response_data.reason}. Successful data request.')
                        data_json = response_data.json()
                        try:
                            df_extr = pd.DataFrame(data_json)
                        except ValueError as e:
                            message(f" --- Incomplete data. {e}")
                            df_extr = pd.DataFrame()
                    else:
                        message(f' -- {response_data.status_code}. {response_data.reason}')
                        retries += 1
                        time.sleep(5)

                except requests.exceptions.RequestException as e:
                    message(f" -- {e}")
                    retries += 1
                    time.sleep(5)
                
                try:
                    response_metadata = requests.get(response_json['metadatos'])
                    if response_metadata.status_code == 200:
                        message(f' -- {response_metadata.reason}. Successful metadata request.')
                        metadata_json = response_metadata.json()
                        metadata = pd.DataFrame(metadata_json)

                        return df_extr, metadata
                    else:
                        message(f' -- {response_metadata.status_code}. {response_metadata.reason}')
                        retries += 1
                        time.sleep(5)
                except requests.exceptions.RequestException as e:
                    message(f" -- {e}")
                    retries += 1
                    time.sleep(5)

            else:
                message(f' - {response.status_code}. {response.reason}')
                retries += 1
                time.sleep(5)

        except requests.exceptions.RequestException as e:
            message(f'Failed to request to the API. {e}.')
            retries += 1
            time.sleep(5)

def parse_extreme_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.replace("", np.nan)
    df.dropna(axis=1, inplace=True)

    return df

def parse_metadata(metadata: pd.DataFrame) -> pd.DataFrame:
    info_df = metadata['campos'].apply(pd.Series)
    return info_df

# --------------------MAIN PROGRAM--------------------

def download_extreme_values(api_key: str, station_id: str, parameter: str, message: callable) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Downloads extreme values for a specific weather station from the AEMET API.

    Args:
        api_key (str): The API key for accessing the AEMET OpenData.
        station_id (str): The identifier of the weather station.
        message (callable): Function to log messages (e.g., `st.write` for Streamlit).

    Returns:
        tuple: A tuple containing:
            - df_normals (pd.DataFrame): DataFrame with normal values.
            - info_df (pd.DataFrame): DataFrame with metadata information.
    """
    config = load_config_file()
    df_extr, metadata = get_station_extreme_vals(config, api_key, station_id, parameter, message)

    try:
        df_extr = parse_extreme_values(df_extr)
        info_df = parse_metadata(metadata)
        dict_rename = {k:info_df[info_df.id == k]["descripcion"].values[0] for k in info_df.id}
        df_extr.rename(dict_rename, axis=1, inplace=True)
        df_extr = df_extr.loc[:,~df_extr.columns.duplicated()]

    except Exception as e:
        print(f"Error parsing data: {e}")
        df_extr = pd.DataFrame()
        info_df = pd.DataFrame()
    
    return df_extr, info_df