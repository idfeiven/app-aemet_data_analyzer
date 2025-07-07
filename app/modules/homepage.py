import streamlit as st

st.set_page_config(layout="wide")

st.title("Bienvenido a la app web AEMET Data Analyzer")
st.write("Esta aplicación te permite explorar, analizar y descargar datos meteorológicos de AEMET.")
st.write("Puedes navegar por las diferentes secciones utilizando el menú de navegación en la parte superior.")
st.write("Para comenzar, selecciona una de las opciones del menú:")
st.markdown("""
- **Ubicación de las estaciones**: Muestra un mapa interactivo con la ubicación de las estaciones meteorológicas de AEMET.
- **Últimas observaciones**: Consulta las últimas observaciones meteorológicas de las estaciones.
- **Datos históricos**: Explora los datos históricos de las estaciones meteorológicas.
- **Valores normales (1991-2020)**: Consulta los valores normales de las variables meteorológicas para el periodo 1991-2020.
- **Valores extremos**: Analiza los valores extremos de temperatura, precipitación y viento de las estaciones meteorológicas de AEMET.
""")
st.write("Para más información, visita la [página oficial de AEMET](https://www.aemet.es/).")
st.write("Si encuentras útil esta aplicación, tienes dudas o sugerencias, puedes contactar conmigo a través de mis redes: [Bluesky](https://bsky.app/profile/idfeiven.bsky.social) o [LinkedIn](https://www.linkedin.com/in/iv%C3%A1n-dom%C3%ADnguez-fuentes-5578a22ab/)")

st.write("¡Espero que disfrutes de la aplicación!")

st.write("Toda la información aquí expuesta pertenece a AEMET y se utiliza con fines educativos y de análisis.")