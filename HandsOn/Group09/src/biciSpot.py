import streamlit as st
import rdflib
import folium
import pandas as pd
import urllib.parse
from streamlit_folium import st_folium

# 1. CONFIGURACIÓN Y ESTILOS
st.set_page_config(page_title="BiciSpot Madrid", page_icon="🚲", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Importar fuente Pacifico desde Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Pacifico&display=swap');
    
    /* Aplicar Pacifico solo al título principal */
    h1 { 
        font-family: 'Pacifico', cursive !important; 
        color: #27cf27 !important; 
        font-weight: normal;
    }
    
    /* Títulos secundarios con fuente normal y color verde */
    h2, h3 { 
        color: #27cf27 !important; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
    }
    
    .subtitle { color: #a0a0a0; font-size: 1.1rem; margin-top: -15px; margin-bottom: 30px; }
    div[data-testid="metric-container"] { background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #27cf27; }
    div[data-testid="metric-container"] > div > div > div > p { color: #27cf27 !important; }
    .stLinkButton > a { background-color: #27cf27 !important; color: #000000 !important; font-weight: bold; border: none !important; border-radius: 6px; transition: all 0.3s ease; }
    .stLinkButton > a:hover { background-color: #20aa20 !important; color: white !important; box-shadow: 0 4px 10px rgba(39, 207, 39, 0.4); }
    hr { border-top: 1px solid #27cf27 !important; opacity: 0.3; }
    .streamlit-expanderHeader { color: #27cf27 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🚲 BiciSpot Madrid")
st.markdown('<p class="subtitle">Explorador del Grafo de Conocimiento de Aparcabicis de Madrid</p>', unsafe_allow_html=True)

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
distrito_seleccionado = st.selectbox("📍 Selecciona un Distrito para explorar:", lista_distritos)

# 3. CONSULTA SPARQL
if distrito_seleccionado == "Todos los distritos":
    filtro_sparql = ""
else:
    distrito_uri = urllib.parse.quote(distrito_seleccionado)
    filtro_sparql = f'FILTER(CONTAINS(STR(?d), "{distrito_uri}"))'

# Limpiada la consulta SPARQL: ya no pedimos ni pintamos la capacidad (plazas)
query_aparcabicis = f"""
    PREFIX ont: <http://smartcity.linkeddata.es/bicis/ontology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    
    SELECT ?id ?modelo ?direccion ?lat ?lon ?wikidata
    WHERE {{
        ?b a ont:BicycleParking ;
           ont:latitude ?lat ;
           ont:longitude ?lon ;
           ont:inDistrict ?d .
        
        OPTIONAL {{ ?b ont:id ?id . }}
        OPTIONAL {{ ?b ont:hasModel ?modelo . }}
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
    direccion = urllib.parse.unquote(str(row.direccion)) if row.direccion else "N/A"
    id_bici = str(row.id) if row.id else "N/A"
    
    if not enlace_wikidata and row.wikidata:
        enlace_wikidata = str(row.wikidata)
    
    datos_tabla.append({
        "ID": id_bici,
        "Dirección": direccion,
        "Modelo": modelo,
        "Latitud": lat,
        "Longitud": lon
    })
    coordenadas_dict[id_bici] = [lat, lon]

df_aparcabicis = pd.DataFrame(datos_tabla)

# --- TARJETAS DE MÉTRICAS Y WIKIDATA ---
st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    st.metric("Total Aparcabicis", len(res_aparcabicis))
with col2:
    if not df_aparcabicis.empty:
        st.metric("Distrito", distrito_seleccionado if distrito_seleccionado != "Todos los distritos" else "Madrid (General)")
    else:
        st.metric("Distrito", "Sin datos")
with col3:
    if enlace_wikidata and distrito_seleccionado != "Todos los distritos":
        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
        st.link_button("🌐 Explorar Distrito en Wikidata", enlace_wikidata, use_container_width=True)

st.divider()

# 5. TABLA INTERACTIVA (Con columnas ocultas por defecto)
st.markdown("### 📋 Directorio de Estaciones (Selecciona una fila para aislarla en el mapa)")
id_seleccionado = None

if not df_aparcabicis.empty:
    event = st.dataframe(
        df_aparcabicis,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        height=250,
        column_config={
            # Ocultamos ID y Modelo. El profesor puede activarlas desde el menú de la tabla.
            "ID": None,
            "Modelo": None
        }
    )
    
    if event.selection.rows:
        fila_index = event.selection.rows[0]
        id_seleccionado = df_aparcabicis.iloc[fila_index]["ID"]

# 6. DIBUJAR EL MAPA 
st.markdown("### 🗺️ Visualización Espacial")
if id_seleccionado and id_seleccionado in coordenadas_dict:
    centro_mapa = coordenadas_dict[id_seleccionado]
    zoom = 18
elif not df_aparcabicis.empty:
    centro_mapa = [df_aparcabicis.iloc[0]["Latitud"], df_aparcabicis.iloc[0]["Longitud"]]
    zoom = 13
else:
    centro_mapa = [40.4168, -3.7038]
    zoom = 12

# Quitamos el tiles="cartodbpositron" para que Folium use su mapa nativo (sin fallos de API KEY)
mapa = folium.Map(location=centro_mapa, zoom_start=zoom)

for index, row in df_aparcabicis.iterrows():
    if id_seleccionado and row["ID"] != id_seleccionado:
        continue
        
    color_icono = "red" if id_seleccionado else "green"
    
    # Lógica de popups: Si está aislado, revela los datos técnicos. Si no, solo la dirección.
    if id_seleccionado:
        popup_text = f"""
        <div style="font-family: Arial; min-width: 200px;">
            <h4 style="color: #27cf27; margin-bottom: 5px;">Aparcabicis {row['ID']}</h4>
            <hr style="margin: 5px 0;">
            <b>🚲 Modelo:</b> {row['Modelo']}<br>
            <b>📍 Dirección:</b> {row['Dirección']}
        </div>
        """
    else:
        popup_text = f"""
        <div style="font-family: Arial; min-width: 200px;">
            <h4 style="color: #27cf27; margin-bottom: 5px;">Estación de Bicicletas</h4>
            <hr style="margin: 5px 0;">
            <b>📍 Dirección:</b> {row['Dirección']}
        </div>
        """
        
    folium.Marker(
        [row["Latitud"], row["Longitud"]],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color=color_icono, icon="bicycle", prefix="fa")
    ).add_to(mapa)

st_folium(mapa, width="100%", height=450, returned_objects=[])

# 7. CONSULTA SPARQL EN TEXTO PLANO
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("🔍 Ver consulta SPARQL en tiempo real"):
    st.markdown("Código ejecutado contra el Grafo de Conocimiento (ABox):")
    st.code(query_aparcabicis, language="text")