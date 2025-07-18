import os
import sys
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))

homepage = st.Page("modules/homepage.py", title = "AEMET Data Analyzer")
stations_location = st.Page("modules/stations_location.py", title = "Ubicación de las estaciones de AEMET")
last_obs = st.Page("modules/last_observation.py", title = "Últimas observaciones")
historical_data = st.Page("modules/historical_data.py", title = "Datos históricos")
climate_plotter = st.Page("modules/climate_plotter.py", title = "Gráficos climáticos")
normal_values = st.Page("modules/normal_values.py", title = "Valores normales (1991-2020)")
extreme_values = st.Page("modules/extreme_values.py", title = "Valores extremos")
warnings = st.Page("modules/warnings.py", title = "Avisos meteorológicos de AEMET")

pages = {
    "Inicio": [homepage],
    "Observación": [stations_location, last_obs, historical_data, climate_plotter, normal_values, extreme_values],
    "Avisos": [warnings]
}

pg = st.navigation(pages)

pg.run()