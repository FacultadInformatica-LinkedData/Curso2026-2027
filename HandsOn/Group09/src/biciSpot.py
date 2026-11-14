import streamlit as st
import rdflib
import folium
import pandas as pd
import urllib.parse
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN
st.set_page_config(page_title="BiciSpot Madrid", layout="wide", initial_sidebar_state="expanded")

st.title("🚲 BiciSpot Madrid - Linked Bike Parking Finder")
st.markdown("Aplicación de explotación del Grafo de Conocimiento de Aparcabicis de Madrid.")

@st.cache_resource
def load_graph():
    g = rdflib.Graph()
    g.parse("../rdf/aparcabicis_madrid-with-links.ttl", format="turtle")
    return g

g = load_graph()

# 2. OBTENER DISTRITOS
query_distritos = """
    PREFIX ont: <http://smartcity.linkeddata.es/bicis/ontology#>
    SELECT DISTINCT ?nombreDistrito
    WHERE {
        ?b a ont:BicycleParking ;
           ont:inDistrict ?d .
        BIND(REPLACE(STR(?d), "http://smartcity.linkeddata.es/bicis/resource/District/", "") AS ?nombreDistrito)
    }
"""
res_distritos = g.query(query_distritos)
lista_distritos_raw = [urllib.parse.unquote(str(row.nombreDistrito)) for row in res_distritos]
lista_distritos_raw.sort()

lista_distritos = ["Todos los distritos"] + lista_distritos_raw
distrito_seleccionado = st.selectbox("📍 Selecciona un Distrito:", lista_distritos)

# 3. CONSULTA SPARQL
if distrito_seleccionado == "Todos los distritos":
    filtro_sparql = ""
else:
    distrito_uri = urllib.parse.quote(distrito_seleccionado)
    filtro_sparql = f'FILTER(CONTAINS(STR(?d), "{distrito_uri}"))'

query_aparcabicis = f"""
    PREFIX ont: <http://smartcity.linkeddata.es/bicis/ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    
    SELECT ?id ?modelo ?capacidad ?direccion ?lat ?lon ?wikidata
    WHERE {{
        ?b a ont:BicycleParking ;
           ont:latitude ?lat ;
           ont:longitude ?lon ;
           ont:inDistrict ?d .
        
        OPTIONAL {{ ?b ont:id ?id . }}
        OPTIONAL {{ ?b ont:hasModel ?modelo . }}
        OPTIONAL {{ ?b ont:hasCapacity ?capacidad . }}
        OPTIONAL {{ ?b ont:streetAddress ?direccion . }}
        OPTIONAL {{ ?d owl:sameAs ?wikidata . }}
        
        {filtro_sparql}
    }}
"""
res_aparcabicis = g.query(query_aparcabicis)

# 4. PREPARAR DATOS Y EXTRACCIÓN WIKIDATA
datos_tabla = []
coordenadas_dict = {}
enlace_wikidata = None

for row in res_aparcabicis:
    lat = float(row.lat)
    lon = float(row.lon)
    modelo = str(row.modelo) if row.modelo else "N/A"
    capacidad = str(row.capacidad) if row.capacidad else "N/A"
    direccion = urllib.parse.unquote(str(row.direccion)) if row.direccion else "N/A"
    id_bici = str(row.id) if row.id else "N/A"
    
    if not enlace_wikidata and row.wikidata:
        enlace_wikidata = str(row.wikidata)
    
    datos_tabla.append({
        "ID": id_bici,
        "Dirección": direccion,
        "Modelo": modelo,
        "Plazas": capacidad,
        "Latitud": lat,
        "Longitud": lon
    })
    coordenadas_dict[id_bici] = [lat, lon]

df_aparcabicis = pd.DataFrame(datos_tabla)

# --- TARJETAS DE MÉTRICAS Y WIKIDATA ---
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Aparcabicis", len(res_aparcabicis))
with col2:
    if enlace_wikidata and distrito_seleccionado != "Todos los distritos":
        st.markdown("<br>", unsafe_allow_html=True)
        st.link_button("🌐 Ver distrito en Wikidata", enlace_wikidata)

st.divider()

# 5. TABLA INTERACTIVA
st.markdown("### 📋 Listado de Aparcabicis (Selecciona una fila para aislar en el mapa)")
id_seleccionado = None

if not df_aparcabicis.empty:
    event = st.dataframe(
        df_aparcabicis,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    if event.selection.rows:
        fila_index = event.selection.rows[0]
        id_seleccionado = df_aparcabicis.iloc[fila_index]["ID"]

# 6. DIBUJAR EL MAPA 
if id_seleccionado and id_seleccionado in coordenadas_dict:
    centro_mapa = coordenadas_dict[id_seleccionado]
    zoom = 18
elif not df_aparcabicis.empty:
    centro_mapa = [df_aparcabicis.iloc[0]["Latitud"], df_aparcabicis.iloc[0]["Longitud"]]
    zoom = 13
else:
    centro_mapa = [40.4168, -3.7038]
    zoom = 12

mapa = folium.Map(location=centro_mapa, zoom_start=zoom)

for index, row in df_aparcabicis.iterrows():
    if id_seleccionado and row["ID"] != id_seleccionado:
        continue
        
    color_icono = "red" if id_seleccionado else "green"
    popup_text = f"<b>Aparcabicis {row['ID']}</b><br>🚲 Modelo: {row['Modelo']}<br>🅿️ Plazas: {row['Plazas']}<br>📍 Dirección: {row['Dirección']}"
    
    folium.Marker(
        [row["Latitud"], row["Longitud"]],
        popup=folium.Popup(popup_text, max_width=250),
        icon=folium.Icon(color=color_icono, icon="bicycle", prefix="fa")
    ).add_to(mapa)

st_folium(mapa, width="100%", height=500, returned_objects=[])

# 7. CONSULTA SPARQL EN TEXTO PLANO
with st.expander("🔍 Ver consulta SPARQL utilizada"):
    st.markdown("Esta es la consulta ejecutada en tiempo real contra el Grafo de Conocimiento (ABox):")
    st.code(query_aparcabicis, language="text")