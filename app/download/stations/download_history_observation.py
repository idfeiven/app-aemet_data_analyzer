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

def load_config_file():
    fpath = Path(__file__).parent.parent / "etc" / "config.yml"

    with open(fpath, 'r') as file:
        config = yaml.safe_load(file)
    
    return config


def get_dates_for_requests(date_ini, date_end):

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


def get_urls_for_requests(dates, station_id, config, api_key):

    urls = pd.DataFrame()

    config['api_key'] = api_key

    url_fill = config['url_base'] + config['endpoints']['stations']['climatology'] + config['api_key']

    urls['urls'] = dates.apply(lambda row: url_fill.format(fechaIniStr = row["date_ini"],
                                                           fechaFinStr = row["date_end"],
                                                           idema = station_id), axis = 1)
    
    return urls


def get_historical_data(urls,
                        max_retries = 10,
                        wait_time = 10):

    count = 0
    data = pd.DataFrame()

    for url in urls['urls']:

        count+=1
        retries = 1
        st.write(f'Peticiones realizadas: {count}/{len(urls)}')

        while retries <= max_retries:

            st.write(f'Intento {retries}/{max_retries}')

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
                                            st.write(f' --- No se pudo realizar la petición de datos. {data_json['descripcion']}')
                                            retries += 1
                                            time.sleep(wait_time)

                                        else:
                                            data = pd.concat([data, pd.DataFrame(data_json)], axis = 0)
                                            st.write('--- Datos descargados con éxito.')
                                            break
                                    else:
                                        st.write(f' --- Respuesta vacía. Reintentando petición')
                                        retries += 1
                                        time.sleep(wait_time)

                                else:
                                    st.write(f' --- {response.status_code} {response.reason}. Reintentando petición')
                                    retries += 1
                                    time.sleep(wait_time)                               

                            except requests.exceptions.RequestException as e:
                                st.write(f" --- Could not request data. {e}")
                                retries += 1
                                time.sleep(wait_time)

                        else:
                            st.write(f' -- No se pudo realizar la petición de datos. {response_json['descripcion']}')
                            retries += 1 
                            time.sleep(wait_time)

                    else:
                        st.write(f' -- Respuesta vacía. Reintentando petición')
                        retries += 1
                        time.sleep(wait_time)

                elif response.status_code == 404:
                    st.write(f' - {response.status_code}. {response.reason}')
                elif response.status_code == 401:
                    st.write(f' - {response.status_code}. {response.reason}')
                elif response.status_code == 429:
                    st.write(f' - {response.status_code}. {response.reason}')
                    st.write(' - Esperando 1 minuto para realizar de nuevo la petición')
                    retries += 1
                    time.sleep(60)

            except requests.exceptions.RequestException as e:
                st.write(f"Could not request to AEMET OpenData. {e}")
                retries += 1
                time.sleep(wait_time)

        time.sleep(wait_time/2)
    
    return data

# -----------------------------MAIN PROGRAM----------------------------

def download_history_observation(date_ini,
                                 date_end,
                                 station_id,
                                 api_key):

    config = load_config_file()
    dates = get_dates_for_requests(date_ini, date_end)
    urls = get_urls_for_requests(dates, station_id, config, api_key)
    data = get_historical_data(urls,
                            max_retries = 10,
                            wait_time = 10)
    if not data.empty:
        data.reset_index(inplace = True)
        data.drop("index", axis = 1, inplace = True)
    
        return data
    else:
        st.write("No hay datos para esta estación en el período seleccionado.")
        return pd.DataFrame()