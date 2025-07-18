import os
import glob
import folium
import tarfile
import pandas as pd
from pathlib import Path
from folium import IFrame
import xml.etree.ElementTree as ET

# Namespace CAP v1.2
ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
severity_map = {'rojo': 3, 'naranja': 2, 'amarillo': 1}


def find_files(directorio, patron="*.xml", recursivo=True):
    """
    Devuelve una lista de rutas de archivos que coinciden con un patrón dentro de un directorio.
    
    Parámetros:
        directorio (str): Ruta base donde buscar.
        patron (str): Patrón de búsqueda, e.g. '*.xml', '*datos*.csv'.
        recursivo (bool): Si debe buscar en subdirectorios.

    Retorna:
        List[str]: Lista de rutas que coinciden.
    """
    if recursivo:
        patron_busqueda = os.path.join(directorio, "**", patron)
    else:
        patron_busqueda = os.path.join(directorio, patron)
    
    return glob.glob(patron_busqueda, recursive=recursivo)


def parse_cap_file(xml_path):
    """Parsea archivo XML CAP y extrae polígonos y títulos"""
    tree = ET.parse(xml_path)
    root = tree.getroot()

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
                'date_emitted': date_emitted,
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
        df_warnings["date_ini"] = pd.to_datetime(df_warnings["datetime_ini"], utc=True).dt.date

        df_warnings = df_warnings.drop_duplicates(subset=['type_warning', 'severity', 'datetime_ini', 'datetime_end'])
        
        df_warnings['severity_level'] = df_warnings['severity'].map(severity_map).fillna(0).astype(int)
        
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
            locations=warn['polygon'],
            popup=popup,
            color=_get_warning_color(warn['severity_level'].max()),
            fill=True,
            fill_opacity=0.5
        ).add_to(m)

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

def get_df_warnings():

    files = find_files(Path(__file__).parent / "data")

    warnings = []
    for file in files:
        warning_area = parse_cap_file(file)
        warnings.append(warning_area)
    warnings = pd.concat(warnings, ignore_index=True)

    return warnings

def plot_aemet_warnings(date, warnings):
    """Genera un mapa con los avisos activos de AEMET"""
    warnings = warnings[warnings['date_ini'] == date]
    map_obj = create_map(warnings)

    return map_obj
