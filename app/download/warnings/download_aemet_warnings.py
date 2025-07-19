'''
This script downloads current weather warnings from the AEMET API.

Author: Iván Domínguez Fuentes

(c) 2025
'''

import io
import time
import yaml
import requests
import pandas as pd
from pathlib import Path


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


def get_current_warnings(config: dict, area: str, message: callable) -> pd.DataFrame | None:
    """
    Downloads the current weather warnings from the AEMET API for a specified area.

    Performs multiple retries (up to 10) in case of network errors or invalid responses.

    Args:
        config (dict): Configuration dictionary containing:
            - url_base (str): Base URL of the API.
            - endpoints['warnings']['current'] (str): Endpoint path for retrieving current warnings.
        api_key (str): API key for authenticating with the API.
        area (str): Area code for which to retrieve warnings.
        message (callable): Function to log messages (e.g., `st.write` for Streamlit).

    Returns:
        pd.DataFrame | None: DataFrame containing metadata about the warnings if successful,
                             or None if all retries fail.

    Side Effects:
        Saves the downloaded warnings file to disk.
        Displays progress and error messages via the provided `message` function.

    Raises:
        requests.exceptions.RequestException: If a connection error occurs.
    """
    # config['api_key'] = f'/?api_key={api_key}'
    url = config['url_base'] + config['endpoints']['warnings']['current'] + config['api_key']

    url = url.format(
                     area=area,
                     )

    retries = 0
    max_retries = 10

    while retries <= max_retries:
        message(f'Attempt {retries + 1} to download warnings...')
        
        try:
            response = requests.get(url)

            if response.status_code == 200:
                message(f' - {response.reason}. Successful request to the API')
                response_json = response.json()

                try:
                    response_data = requests.get(response_json['datos'])
                    
                    if response_data.status_code == 200:
                        message(f' -- {response_data.reason}. Successful data request.')
                        tar_bytes = io.BytesIO(response_data.content)
                        return tar_bytes
                    else:
                        message(f' -- {response_data.status_code}. {response_data.reason}')
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


def download_aemet_warnings(area: str, message: callable) -> str:
    """Descarga y guarda en memoria el archivo .tar de avisos activos"""
    
    config = load_config_file()
    tar_bytes = get_current_warnings(config, area, message)

    return tar_bytes
