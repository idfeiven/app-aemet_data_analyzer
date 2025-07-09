'''
This program uses AEMET OpenData
to download historic observations
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
from datetime import datetime
from dateutil.relativedelta import relativedelta

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


def get_dates_for_requests(date_ini: str, date_end: str) -> pd.DataFrame:
    """
    Splits the requested time interval into sub-intervals to comply with API limitations.

    If the interval exceeds 6 months, it is divided into 6-month segments. Otherwise, 
    a single interval is returned. Dates are formatted to the API's expected format.

    Args:
        date_ini (str): Start date in 'YYYY-MM-DD' format.
        date_end (str): End date in 'YYYY-MM-DD' format.

    Returns:
        pd.DataFrame: A DataFrame with two columns:
            - 'date_ini': List of initial dates for each request segment.
            - 'date_end': List of final dates for each request segment.
    """
    date_ini = pd.to_datetime(date_ini)
    date_ini = datetime(date_ini.year, date_ini.month, date_ini.day)

    date_end = pd.to_datetime(date_end)
    date_end = datetime(date_end.year, date_end.month, date_end.day)

    time_diff = relativedelta(date_end, date_ini)
    dates = pd.DataFrame()

    if time_diff.years > 0 or time_diff.months >= 6:
        dates_ini = pd.date_range(date_ini, date_end, freq = "6MS")
        dates_end = dates_ini + pd.DateOffset(months = 6)
        dates["date_ini"] = dates_ini.strftime("%Y-%m-%dT%H:%M:%SUTC")
        dates["date_end"] = dates_end.strftime("%Y-%m-%dT%H:%M:%SUTC")
        return dates
    
    else:
        dates["date_ini"] = [date_ini.strftime("%Y-%m-%dT%H:%M:%SUTC")]
        dates["date_end"] = [date_end.strftime("%Y-%m-%dT%H:%M:%SUTC")]
        return dates


def get_urls_for_requests(dates: pd.DataFrame, station_id: str, config: dict, api_key: str):
    """
    Generates the URLs needed to request climatological data from the AEMET API.

    Args:
        dates (pd.DataFrame): DataFrame containing 'date_ini' and 'date_end' columns.
        station_id (str): The station identifier (IDEMA code).
        config (dict): Dictionary with API configuration, including:
            - 'url_base': Base URL for API requests.
            - 'endpoints': Dictionary with endpoint templates.
        api_key (str): AEMET API key.

    Returns:
        pd.DataFrame: DataFrame with a single column 'urls', containing formatted request URLs.
    """
    urls = pd.DataFrame()

    config['api_key'] = f'/?api_key={api_key}'

    url_fill = config['url_base'] + config['endpoints']['stations']['climatology'] + config['api_key']

    urls['urls'] = dates.apply(lambda row: url_fill.format(fechaIniStr = row["date_ini"],
                                                           fechaFinStr = row["date_end"],
                                                           idema = station_id), axis = 1)
    
    return urls


def get_historical_data(urls: pd.DataFrame,
                        max_retries: int,
                        wait_time: int|float,
                        message: callable):
    """
    Downloads historical data from the AEMET API using a list of URLs.

    Each request is retried on failure up to `max_retries` times with a delay of `wait_time` seconds
    between attempts. A custom `message` function is used to log progress or errors (e.g., `st.write`).

    Args:
        urls (pd.DataFrame): DataFrame with a column 'urls' containing the request URLs.
        max_retries (int): Maximum number of retries per request.
        wait_time (int | float): Delay in seconds between retries.
        message (callable): Function used to display messages during the request process.

    Returns:
        pd.DataFrame: DataFrame with the concatenated historical data from successful requests.
                      If no data is retrieved, an empty DataFrame is returned.

    Notes:
        - Handles specific HTTP status codes (200, 401, 404, 429).
        - Ignores requests with no data available.
        - Supports JSON payload validation and handles empty responses.
    """
    count = 0
    data = pd.DataFrame()

    for url in urls['urls']:

        count+=1
        retries = 1
        message(f'Peticiones realizadas: {count}/{len(urls)}')

        while retries <= max_retries:

            message(f'Intento {retries}/{max_retries}')

            try:
                response = requests.get(url, timeout = 10)

                if response.status_code == 200:

                    if response.text.strip():
                        response_json = response.json()

                        if response_json['estado'] == 200:
                            url_data = response_json['datos']

                            try:
                                data_response = requests.get(url_data, timeout = 10)
                                
                                if data_response.status_code == 200:
                                    data_json = data_response.json()

                                    if data_response.text.strip():
                                        
                                        if type(data_json) == dict and data_json['estado']:
                                            message(f' --- No se pudo realizar la petición de datos. {data_json['descripcion']}')
                                            retries += 1
                                            time.sleep(wait_time)

                                        else:
                                            data = pd.concat([data, pd.DataFrame(data_json)], axis = 0)
                                            message('--- Datos descargados con éxito.')
                                            break
                                    else:
                                        message(f' --- Respuesta vacía. Reintentando petición')
                                        retries += 1
                                        time.sleep(wait_time)
                                        
                                elif data_response.status_code == 404:
                                    message(f' --- {data_response.status_code} {data_response.reason}. Siguiente petición')
                                    continue
                                else:
                                    message(f' --- {response.status_code} {response.reason}. Reintentando petición')
                                    retries += 1
                                    time.sleep(wait_time)                               

                            except requests.exceptions.RequestException as e:
                                message(f" --- No se pudo realizar la petición de datos. {e}")
                                retries += 1
                                time.sleep(wait_time)

                        else:
                            message(f' -- No se pudo realizar la petición de datos. {response_json['descripcion']}')
                            if response_json['descripcion'].startswith("No hay datos"): # No hay datos que satisfagan esos criterios, nos vamos a la siguiente petición
                                break
                            else:
                                retries += 1 
                                time.sleep(wait_time)

                    else:
                        message(f' -- Respuesta vacía. Reintentando petición')
                        retries += 1
                        time.sleep(wait_time)

                elif response.status_code == 404:
                    message(f' - {response.status_code}. {response.reason}')
                    continue
                elif response.status_code == 401:
                    message(f' - {response.status_code}. {response.reason}')
                    continue
                elif response.status_code == 429:
                    message(f' - {response.status_code}. {response.reason}')
                    message(' - Esperando 1 minuto para realizar de nuevo la petición')
                    retries += 1
                    time.sleep(60)

            except requests.exceptions.RequestException as e:
                message(f"Could not request to AEMET OpenData. {e}")
                retries += 1
                time.sleep(wait_time)

        time.sleep(wait_time/2)
    
    return data

# -----------------------------MAIN PROGRAM----------------------------

def download_history_observation(date_ini,
                                 date_end,
                                 station_id,
                                 api_key,
                                 message):
    '''
    Main method for download_history_observation
    '''
            
    config = load_config_file()
    dates = get_dates_for_requests(date_ini, date_end)
    urls = get_urls_for_requests(dates, station_id, config, api_key)
    data = get_historical_data(urls,
                            max_retries = 20,
                            wait_time = 10,
                            message=message)
    if not data.empty:
        data.reset_index(inplace = True)
        data.drop("index", axis = 1, inplace = True)
    
        return data
    else:
        st.warning("No hay datos para esta estación en el período seleccionado.")
        return pd.DataFrame()