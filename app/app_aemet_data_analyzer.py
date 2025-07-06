import os
import sys
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))

homepage = st.Page("modules/homepage.py", title = "AEMET Data Analyzer")
stations_location = st.Page("modules/stations_location.py", title = "Ubicación de las estaciones de AEMET")
last_obs = st.Page("modules/last_observation.py", title = "Últimas observaciones")
historical_data = st.Page("modules/historical_data.py", title = "Datos históricos")
normal_values = st.Page("modules/normal_values.py", title = "Valores normales (1991-2020)")
extreme_values = st.Page("modules/extreme_values.py", title = "Valores extremos")

pages = {
    "Inicio": [homepage],
    "Observación": [stations_location, last_obs, historical_data, normal_values, extreme_values]}

pg = st.navigation(pages)

pg.run()