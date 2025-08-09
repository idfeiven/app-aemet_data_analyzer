import folium
import tarfile
import pandas as pd
from folium import IFrame
from folium import Element
import xml.etree.ElementTree as ET
from folium.plugins import Fullscreen


# Namespace CAP v1.2
ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
severity_map = {'rojo': 3, 'naranja': 2, 'amarillo': 1}


def extract_xml(tar_bytes: bytes) -> list[bytes]:
    """
    Devuelve una lista de contenidos XML (en bytes) a partir de un archivo .tar en memoria.
    """
    xml_files = []
    with tarfile.open(fileobj=tar_bytes) as tar:
        for member in tar.getmembers():
            if member.name.endswith(".xml"):
                f = tar.extractfile(member)
                if f is not None:
                    xml_files.append(f.read())
    return xml_files


def parse_xml_content(xml_content):
    """Parsea el contenido de XML CAP y extrae polígonos y títulos"""
    root = ET.fromstring(xml_content)

    warnings = []
    infos = root.findall('cap:info', ns)
    for info in infos:
        lang = info.find('cap:language', ns).text
        area_elem = info.find('cap:area', ns)
        area_name = area_elem.find('cap:areaDesc', ns).text
        polygons = area_elem.findall('cap:polygon', ns)
        param_elem = info.findall('cap:parameter', ns)
        headline = info.find('cap:headline', ns).text
        description = info.find('cap:description', ns).text if info.find('cap:description', ns) is not None else ""
        date_emitted = info.find('cap:effective', ns).text if info.find('cap:effective', ns) is not None else ""
        date_ini = info.find('cap:onset', ns).text if info.find('cap:onset', ns) is not None else ""
        date_end = info.find('cap:expires', ns).text if info.find('cap:expires', ns) is not None else ""
        type_warn = info.find('cap:certainty', ns).text if info.find('cap:certainty', ns) is not None else ""

        for poly in polygons:
            coords = [tuple(map(float, p.split(','))) for p in poly.text.strip().split()]
            warnings.append({
                'lang': lang,
                'area': area_name,
                'headline': headline,
                'polygon': coords,
                'params': [p.find('cap:value', ns).text for p in param_elem],
                'description': description,
                'datetime_emitted': date_emitted,
                'datetime_ini': date_ini,
                'datetime_end': date_end,
                'type_warning': type_warn,
            })
    
    df_warnings = pd.DataFrame(warnings)
    df_warnings = df_warnings[df_warnings['lang'] == 'es-ES']
    df_warnings['severity'] = df_warnings['params'][0][0]
    df_warnings = df_warnings[df_warnings['severity'] != 'verde']

    if not df_warnings.empty:
        df_warnings['type_warning'] = df_warnings['params'][0][1].split(";")[1]
        df_warnings['probability'] = df_warnings['params'][0][2]        
        df_warnings['severity_level'] = df_warnings['severity'].map(severity_map).fillna(0).astype(int)
        df_warnings.loc[:,'datetime_ini'] = pd.to_datetime(df_warnings['datetime_ini'], utc=True).dt.tz_convert('Europe/Madrid').dt.tz_localize(None)
        df_warnings.loc[:,'datetime_end'] = pd.to_datetime(df_warnings['datetime_end'], utc=True).dt.tz_convert('Europe/Madrid').dt.tz_localize(None)
        df_warnings.loc[:,'datetime_emitted'] = pd.to_datetime(df_warnings['datetime_emitted'], utc=True).dt.tz_convert('Europe/Madrid').dt.tz_localize(None)

        df_warnings = df_warnings.drop_duplicates(subset=['description', 'severity', 'datetime_ini', 'datetime_end'])

    return df_warnings

def get_df_warnings(xml_files):
    import pandas as pd

    print(f"🔎 Recibidos {len(xml_files)} archivos XML")

    df_warnings = pd.DataFrame()
    for idx, file in enumerate(xml_files):
        print(f"📂 Procesando XML {idx + 1}")
        try:
            warning_area = parse_xml_content(file)
            print(f"   ↳ parse_xml_content() devuelve: {len(warning_area)} filas")
        except Exception as e:
            print(f"   ❌ Error procesando XML: {e}")
            continue

        if not warning_area.empty:
            df_warnings = pd.concat([df_warnings, warning_area])

    df_warnings[['datetime_emitted', 'datetime_ini', 'datetime_end']] = df_warnings[['datetime_emitted', 'datetime_ini', 'datetime_end']].astype('datetime64[ns]')
    
    print(f"✅ DataFrame final: {len(df_warnings)} filas")
    return df_warnings

def create_map(df_warnings, center=(40.4, -3.7), zoom=6):
    m = folium.Map(location=center, zoom_start=zoom)

    for area in df_warnings.area.unique():
        warn_area = df_warnings[df_warnings.area == area]

        html_popup_base = f"""
                <div style="font-family: Arial; font-size: 13px; max-width: 200px;">
                    <div style="font-weight: bold; font-size: 16px;">{warn_area['area'].values.flatten()[0]}</div>
                """
        popup_all = ""
        for type_warning in warn_area.type_warning.unique():
                warn = warn_area[warn_area.type_warning == type_warning].iloc[0]
                # Construir el HTML enriquecido para el popup
                html_popup = f"""
                    <div style="margin-top: 5px; font-family: Arial; font-weight: bold; font-size: 14px;">{warn['type_warning']}</div>
                    <div style="margin-top: 5px; font-family: Arial; font-size: 13px"><strong>Aviso:</strong> {warn['severity']}</div>
                    <div style="margin-top: 5px; font-family: Arial; font-size: 13px"><strong>Probabilidad:</strong> {warn['probability']}</div>
                    <div style="margin-top: 5px; font-family: Arial; font-size: 13px">Activo desde</div>
                    <div style="margin-top: 5px; font-family: Arial; font-size: 13px">{warn['datetime_ini']}</div>
                    <div style="margin-top: 5px; font-family: Arial; font-size: 13px">hasta</div>
                    <div style="margin-top: 5px; font-family: Arial; font-size: 13px">{warn['datetime_end']}</div>
                    <div style="margin-top: 5px; font-family: Arial; font-size: 13px"><strong>Comentario:</strong>{warn['description']}</div>
                </div>
                """
                popup_all = popup_all + html_popup
        popup = html_popup_base + popup_all + "</div>"

        iframe = IFrame(html=popup, width=200, height=250)
        popup = folium.Popup(iframe, max_width=200)

        folium.Polygon(
            locations=warn_area['polygon'].values[0],
            popup=popup,
            color=_get_warning_color(warn_area['severity_level'].max()),
            fill=True,
            fill_opacity=0.5
        ).add_to(m)
    
    # Añadir el botón de pantalla completa
    Fullscreen(position='bottomright', title='Pantalla completa', title_cancel='Salir de pantalla completa').add_to(m)

    # Añadir título
    title = Element("h3")
    title.text = f"Avisos AEMET para el día {df_warnings['datetime_ini'].dt.date.unique().values.flatten()[0]}"
    title.add_to(m)

    return m


def _get_warning_color(severity_level):
    """Devuelve el color del polígono según la severidad"""
    if severity_level == 1:
        return '#f4e72a'
    elif severity_level == 2:
        return '#f4a72a'
    elif severity_level == 3:
        return '#f42a2a'
    else:
        return '#ffffff'  # Color por defecto


def plot_aemet_warnings(date, tar_bytes):
    """Genera un mapa con los avisos activos de AEMET"""

    xml_files = extract_xml(tar_bytes)
    df_warnings = get_df_warnings(xml_files)

    df_warnings_date = df_warnings[(df_warnings['datetime_ini'].dt.date <= date.date()) &
                                   (df_warnings['datetime_end'].dt.date >= date.date())]
    
    if date == pd.to_datetime(pd.to_datetime("today").date()):
        print("Filtering out today's warnings")
        df_warnings_date = df_warnings_date[df_warnings_date['datetime_end'] >= pd.to_datetime("today")]

    map_obj = create_map(df_warnings_date)

    return map_obj
