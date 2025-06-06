import os
import sys
import streamlit as st
sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))

homepage = st.Page("modules/stations_location.py", title = "Inicio")
last_obs = st.Page("modules/last_observation.py", title = "Última observación")
historical_data = st.Page("modules/historical_data.py", title = "Datos históricos")

pg = st.navigation([homepage,
                    last_obs,
                    historical_data
                    ]
                  )

pg.run()