'''
This program uses AEMET OpenData
to download last observations
from the AEMET station network

Author: Iván Domínguez Fuentes

(c) 2025
'''

import time
import yaml
import requests
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


def get_today_observation(config, message):
    """
    Retrieves today's meteorological observations from the AEMET OpenData API.

    The function sends a request to the "all observations" endpoint defined in the config,
    and if successful, retrieves and parses the actual data from the secondary URL provided
    in the initial API response. It retries indefinitely on failure, logging messages through
    the `message` callback function.

    Args:
        config (dict): Dictionary containing API configuration. Must include:
            - 'url_base': Base URL for the API.
            - 'endpoints': Dictionary with endpoints (requires ['observation']['all']).
            - 'api_key': API key for authentication.
        message (callable): Function to log messages (e.g., `st.write` for Streamlit).

    Returns:
        pd.DataFrame: DataFrame containing today's observation data for all available stations.

    Notes:
        - Retries indefinitely until a valid response is obtained.
        - Handles HTTP errors and unexpected data issues with retries and logging.
        - The secondary data URL is extracted from the 'datos' field in the JSON response.
    """
    url = config['url_base'] + config['endpoints']['observation']['all'] + config['api_key']
    
    while True:
        try:
            response = requests.get(url)

            if response.status_code == 200:
                message(f'{response.status_code}. {response.reason}')
                json_response = response.json()

                try: 
                    url_data = json_response['datos']

                    data = requests.get(url_data)

                    if response.status_code == 200:
                        message(f' - Datos obtenidos con éxito')
                        data_json = data.json()
                        df_data = pd.DataFrame(data_json)
                        return df_data
                    
                    else:
                        message(f'{response.status_code}. {response.reason}')
                        time.sleep(5)

                except:
                    message(f'{url_data['descripcion']}')
                    time.sleep(5)
            
            else:
                message(f'{response.status_code}. {response.reason}')
                time.sleep(5)

        except Exception as e:
            message(f"Failed to request from AEMET OpenData. {e}")
            time.sleep(5)
        

# -----------------------------MAIN PROGRAM----------------------------

def download_today_observation(message):
    '''
    Main method for download_today_observation
    '''
    
    config = load_config_file()
    today_obs = get_today_observation(config, message)

    return today_obs