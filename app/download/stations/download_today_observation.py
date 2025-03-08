'''
This program uses AEMET OpenData
to download last observations
from the AEMET station network

Author: Iván Domínguez Fuentes

(c) 2025
'''

import yaml
import requests
import pandas as pd
import streamlit as st
from pathlib import Path


# -----------------------------FUNCTIONS----------------------------

def load_config_file():
    fpath = Path(__file__).parent.parent / "etc" / "config.yml"

    with open(fpath, 'r') as file:
        config = yaml.safe_load(file)
    
    return config


def get_today_observation(config):

    url = config['url_base'] + config['endpoints']['observation']['all'] + config['api_key']

    try:
        response = requests.get(url)

        if response.status_code == 200:
            print(f'{response.status_code}. {response.reason}')
            json_response = response.json()

            try: 
                url_data = json_response['datos']

                data = requests.get(url_data)

                if response.status_code == 200:
                    print(f' - Datos obtenidos con éxito')
                    data_json = data.json()
                    df_data = pd.DataFrame(data_json)

                    return df_data
                else:
                    print(f'{response.status_code}. {response.reason}')
                    return pd.DataFrame()

            except:
                print(f'{url_data['descripcion']}')
                return pd.DataFrame()
        
        else:
            print(f'{response.status_code}. {response.reason}')
            return pd.DataFrame()

    except Exception as e:
        print(f"Failed to request from AEMET OpenData. {e}")
        return pd.DataFrame()

# -----------------------------MAIN PROGRAM----------------------------

def download_today_observation():
    
    config = load_config_file()
    today_obs = get_today_observation(config)

    return today_obs