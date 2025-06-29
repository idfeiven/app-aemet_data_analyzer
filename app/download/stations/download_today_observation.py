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

def load_config_file():
    fpath = Path(__file__).parent.parent / "etc" / "config.yml"

    with open(fpath, 'r') as file:
        config = yaml.safe_load(file)
    
    return config


def get_today_observation(config, message):

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
    
    config = load_config_file()
    today_obs = get_today_observation(config, message)

    return today_obs