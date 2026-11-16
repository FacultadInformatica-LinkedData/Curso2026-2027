import os
import re
import urllib.parse
import pandas as pd
import pydeck as pdk
import streamlit as st
from rdflib import Graph

# Configuración de la página
st.set_page_config(
    page_title="Educa Madrid - Consultas SPARQL y Buscador",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Educa Madrid: Explotación del Grafo de Conocimiento")
st.markdown("""
Aplicación web semántica basada en **Grafos de Conocimiento** y **Linked Data**.  
Permite interrogar directamente el grafo RDF (`centros-educativos-with-links.ttl`) mediante **consultas SPARQL** y explorar en el mapa interactivo los **1.619 centros educativos** de Madrid.
""")

# 1. Carga del grafo desde ./rdf/centros-educativos-with-links.ttl
@st.cache_resource
def load_graph():
    g = Graph()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_paths = [
        os.path.join(base_dir, "rdf", "centros-educativos-with-links.ttl"),
        os.path.join(base_dir, "centros-educativos-with-links.ttl"),
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            g.parse(path, format="turtle")
            return g, path
    return g, None

g, loaded_path = load_graph()

def clean_uri_tail(val):
    if val is None:
        return None
    text = str(val).strip()
    if text.startswith("http://") or text.startswith("https://"):
        text = text.split("/")[-1]
    return urllib.parse.unquote(text).replace("_", " ")

def format_center_type(val):
    if val is None or str(val).strip() == "":
        return None
    raw = str(val).strip().split("/")[-1]
    spaced = re.sub(r"(?<!^)(?=[A-ZÁÉÍÓÚÑ])", " ", raw)
    return spaced if spaced else None

def render_center_card(row):
    """Muestra la ficha completa de un centro mostrando únicamente los campos presentes en el grafo."""
    c1, c2 = st.columns(2)
    with c1:
        if pd.notna(row["Dirección"]):
            cp_str = f" (CP: {row['Código Postal']})" if pd.notna(row["Código Postal"]) else ""
            st.markdown(f"**📍 Dirección:** {row['Dirección']}{cp_str}")
        if pd.notna(row["Distrito"]) or pd.notna(row["Barrio"]):
            dist_link = f"[{row['Distrito']}]({row['Wikidata Distrito']})" if pd.notna(row["Wikidata Distrito"]) else (row["Distrito"] or "")
            barrio_link = f"[{row['Barrio']}]({row['Wikidata Barrio']})" if pd.notna(row["Wikidata Barrio"]) else (row["Barrio"] or "")
            st.markdown(f"**🏛️ Distrito:** {dist_link} | **Barrio:** {barrio_link}")
        if pd.notna(row["Descripción"]):
            st.markdown(f"**📖 Descripción / Enseñanza:** {row['Descripción']}")
        if pd.notna(row["Equipamiento"]):
            st.markdown(f"**🛠️ Equipamiento:** {row['Equipamiento']}")
    with c2:
        if pd.notna(row["Transporte"]):
            st.markdown(f"**🚌 Transporte:** {row['Transporte']}")
        if pd.notna(row["Accesibilidad"]):
            st.markdown(f"**♿ Código de Accesibilidad:** `{row['Accesibilidad']}`")
        if pd.notna(row["Horario"]):
            st.markdown(f"**⏰ Horario:** {row['Horario']}")
        if pd.notna(row["Teléfono"]):
            st.markdown(f"**📞 Teléfono:** {row['Teléfono']}")
        if pd.notna(row["Email"]):
            st.markdown(f"**✉️ Email:** {row['Email']}")
        if pd.notna(row["Web"]):
            st.markdown(f"**🌐 Ficha Oficial:** [Ver en Portal de Madrid]({row['Web']})")
    st.caption(f"URI del recurso: `{row['URI']}`")

# 2. Catálogo de 10 preguntas SPARQL listas para ejecutar
PREDEFINED_QUERIES = {
    "1. Total de centros educativos por distrito y su enlace owl:sameAs a Wikidata": """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?distrito (COUNT(DISTINCT ?centro) AS ?totalCentros) ?wikidataDistrito
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri .
    ?distUri rdfs:label ?distrito ;
             owl:sameAs ?wikidataDistrito .
}
GROUP BY ?distrito ?wikidataDistrito
ORDER BY DESC(?totalCentros)""",

    "2. Top 20 barrios con más centros educativos y su entidad en Wikidata": """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?barrio ?distrito (COUNT(DISTINCT ?centro) AS ?totalCentros) ?wikidataBarrio
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:hasAddress ?addr .
    ?addr ont:inNeighborhood ?barrioUri ;
          ont:inDistrict ?distUri .
    ?barrioUri rdfs:label ?barrio ;
               owl:sameAs ?wikidataBarrio .
    ?distUri rdfs:label ?distrito .
}
GROUP BY ?barrio ?distrito ?wikidataBarrio
ORDER BY DESC(?totalCentros)
LIMIT 20""",

    "3. Distribución de centros según su código de accesibilidad": """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>

SELECT ?codigoAccesibilidad (COUNT(DISTINCT ?centro) AS ?totalCentros)
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:accessibilityCode ?codigoAccesibilidad .
}
GROUP BY ?codigoAccesibilidad
ORDER BY DESC(?totalCentros)""",

    "4. Centros totalmente adaptados (accesibilidad = '3') con sus datos de contacto": """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?nombre ?distrito ?barrio ?telefono ?email
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:centerName ?nombre ;
            ont:accessibilityCode "3" ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri ;
          ont:inNeighborhood ?barrioUri .
    ?distUri rdfs:label ?distrito .
    ?barrioUri rdfs:label ?barrio .
    OPTIONAL { ?centro ont:telephone ?telefono . }
    OPTIONAL { ?centro ont:email ?email . }
}
ORDER BY ?distrito ?nombre""",

    "5. Centros que disponen simultáneamente de Comedor y Horario ampliado": """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?nombre ?distrito ?barrio ?equipamiento
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:centerName ?nombre ;
            ont:equipment ?equipamiento ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri ;
          ont:inNeighborhood ?barrioUri .
    ?distUri rdfs:label ?distrito .
    ?barrioUri rdfs:label ?barrio .
    FILTER(CONTAINS(LCASE(?equipamiento), "comedor") && CONTAINS(LCASE(?equipamiento), "horario ampliado"))
}
ORDER BY ?distrito ?nombre""",

    "6. Centros con enseñanza bilingüe (filtrando por descripción)": """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?nombre ?distrito ?barrio ?descripcion
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:centerName ?nombre ;
            ont:description ?descripcion ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri ;
          ont:inNeighborhood ?barrioUri .
    ?distUri rdfs:label ?distrito .
    ?barrioUri rdfs:label ?barrio .
    FILTER(CONTAINS(LCASE(?descripcion), "bilingüe"))
}
ORDER BY ?distrito ?nombre""",

    "7. Centros con conexión directa a Cercanías Renfe": """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?nombre ?distrito ?transporte
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:centerName ?nombre ;
            ont:transportation ?transporte ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri .
    ?distUri rdfs:label ?distrito .
    FILTER(CONTAINS(LCASE(?transporte), "renfe") || CONTAINS(LCASE(?transporte), "cercanías"))
}
ORDER BY ?distrito ?nombre""",

    "8. Conteo de centros por tipología (ont:centerType)": """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>

SELECT ?tipo (COUNT(DISTINCT ?centro) AS ?totalCentros)
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:centerType ?tipo .
}
GROUP BY ?tipo
ORDER BY DESC(?totalCentros)""",

    "9. Relación jerárquica de Barrios y Distritos con sus respectivas URIs de Wikidata": """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?distrito ?wikidataDistrito ?barrio ?wikidataBarrio
WHERE {
    ?barrioUri a ont:Neighborhood ;
               rdfs:label ?barrio ;
               ont:belongsToDistrict ?distUri ;
               owl:sameAs ?wikidataBarrio .
    ?distUri rdfs:label ?distrito ;
             owl:sameAs ?wikidataDistrito .
}
ORDER BY ?distrito ?barrio""",

    "10. Consulta libre personalizada (Edita el código SPARQL directamente)": """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?centro ?nombre ?pk ?distrito ?barrio
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:centerName ?nombre ;
            ont:pk ?pk ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri ;
          ont:inNeighborhood ?barrioUri .
    ?distUri rdfs:label ?distrito .
    ?barrioUri rdfs:label ?barrio .
}
ORDER BY ?nombre
LIMIT 25"""
}

# 3. Extracción exacta de los 1.619 centros (evitando producto cartesiano en direcciones compartidas)
@st.cache_data
def get_centers_dataframe(_graph):
    query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        
        SELECT ?centro ?pk ?nombre ?tipo ?desc ?horario ?equipamiento ?transporte ?telefono ?email ?url ?accesibilidad 
               ?streetType ?streetName ?streetNumber ?postalCode 
               (SAMPLE(?latVal) AS ?lat) (SAMPLE(?longVal) AS ?long)
               ?distritoUri ?distritoLabel ?wikidataDistrito 
               ?barrioUri ?barrioLabel ?wikidataBarrio
        WHERE {
            ?centro rdf:type ont:EducationalCenter ;
                    ont:centerName ?nombre .
            
            OPTIONAL { ?centro ont:pk ?pk . }
            OPTIONAL { ?centro ont:centerType ?tipo . }
            OPTIONAL { ?centro ont:description ?desc . }
            OPTIONAL { ?centro ont:schedule ?horario . }
            OPTIONAL { ?centro ont:equipment ?equipamiento . }
            OPTIONAL { ?centro ont:transportation ?transporte . }
            OPTIONAL { ?centro ont:telephone ?telefono . }
            OPTIONAL { ?centro ont:email ?email . }
            OPTIONAL { ?centro ont:contentUrl ?url . }
            OPTIONAL { ?centro ont:accessibilityCode ?accesibilidad . }
            
            OPTIONAL { 
                ?centro ont:hasAddress ?addr .
                OPTIONAL { ?addr ont:streetType ?streetType . }
                OPTIONAL { ?addr ont:streetName ?streetName . }
                OPTIONAL { ?addr ont:streetNumber ?streetNumber . }
                OPTIONAL { ?addr ont:postalCode ?postalCode . }
                OPTIONAL { ?addr ont:latitude ?latVal . }
                OPTIONAL { ?addr ont:longitude ?longVal . }
                OPTIONAL { 
                    ?addr ont:inDistrict ?distritoUri .
                    OPTIONAL { ?distritoUri rdfs:label ?distritoLabel . }
                    OPTIONAL { ?distritoUri owl:sameAs ?wikidataDistrito . }
                }
                OPTIONAL { 
                    ?addr ont:inNeighborhood ?barrioUri .
                    OPTIONAL { ?barrioUri rdfs:label ?barrioLabel . }
                    OPTIONAL { ?barrioUri owl:sameAs ?wikidataBarrio . }
                }
            }
        }
        GROUP BY ?centro ?pk ?nombre ?tipo ?desc ?horario ?equipamiento ?transporte ?telefono ?email ?url ?accesibilidad 
                 ?streetType ?streetName ?streetNumber ?postalCode 
                 ?distritoUri ?distritoLabel ?wikidataDistrito 
                 ?barrioUri ?barrioLabel ?wikidataBarrio
    """
    results = _graph.query(query)
    data = []
    
    for row in results:
        st_type = str(row.streetType) if row.streetType is not None else ""
        st_name = str(row.streetName) if row.streetName is not None else ""
        st_num = str(row.streetNumber) if row.streetNumber is not None else ""
        direccion = f"{st_type} {st_name}, {st_num}".strip(" ,") if st_name else None
        
        distrito = str(row.distritoLabel) if row.distritoLabel is not None else clean_uri_tail(row.distritoUri)
        barrio = str(row.barrioLabel) if row.barrioLabel is not None else clean_uri_tail(row.barrioUri)
        
        try:
            lat = float(row.lat) if row.lat is not None else None
            lon = float(row.long) if row.long is not None else None
        except ValueError:
            lat, lon = None, None
            
        data.append({
            "URI": str(row.centro),
            "PK": str(row.pk) if row.pk is not None else None,
            "Nombre": str(row.nombre) if row.nombre is not None else None,
            "Tipo": format_center_type(row.tipo),
            "TipoRaw": str(row.tipo) if row.tipo is not None else None,
            "Descripción": str(row.desc) if row.desc is not None else None,
            "Distrito": distrito,
            "Wikidata Distrito": str(row.wikidataDistrito) if row.wikidataDistrito is not None else None,
            "Barrio": barrio,
            "Wikidata Barrio": str(row.wikidataBarrio) if row.wikidataBarrio is not None else None,
            "Dirección": direccion,
            "Código Postal": str(row.postalCode) if row.postalCode is not None else None,
            "Teléfono": str(row.telefono) if row.telefono is not None else None,
            "Email": str(row.email) if row.email is not None else None,
            "Transporte": str(row.transporte) if row.transporte is not None else None,
            "Horario": str(row.horario) if row.horario is not None else None,
            "Equipamiento": str(row.equipamiento) if row.equipamiento is not None else None,
            "Accesibilidad": str(row.accesibilidad) if row.accesibilidad is not None else None,
            "Web": str(row.url) if row.url is not None else None,
            "lat": lat,
            "lon": lon
        })
        
    df_out = pd.DataFrame(data)
    # Garantizar unicidad estricta por instancia EducationalCenter (1.619 centros)
    return df_out.drop_duplicates(subset=["URI"]).reset_index(drop=True)

def build_dynamic_sparql(distrito, barrio, tipo_raw, cp, acc, nombre_txt, desc_txt, equip_txt, transp_txt):
    filters = []
    if distrito != "Todos":
        filters.append(f'FILTER(?distrito = "{distrito}")')
    if barrio != "Todos":
        filters.append(f'FILTER(?barrio = "{barrio}")')
    if tipo_raw != "Todos":
        filters.append(f'FILTER(?tipo = "{tipo_raw}")')
    if cp != "Todos":
        filters.append(f'FILTER(?cp = "{cp}")')
    if acc != "Todos":
        filters.append(f'FILTER(?accesibilidad = "{acc}")')
    if nombre_txt:
        filters.append(f'FILTER(CONTAINS(LCASE(?nombre), "{nombre_txt.lower()}"))')
    if desc_txt:
        filters.append(f'FILTER(BOUND(?descripcion) && CONTAINS(LCASE(?descripcion), "{desc_txt.lower()}"))')
    if equip_txt:
        filters.append(f'FILTER(BOUND(?equipamiento) && CONTAINS(LCASE(?equipamiento), "{equip_txt.lower()}"))')
    if transp_txt:
        filters.append(f'FILTER(BOUND(?transporte) && CONTAINS(LCASE(?transporte), "{transp_txt.lower()}"))')

    filter_block = "\n    ".join(filters)
    return f"""PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?nombre ?distrito ?barrio ?cp ?accesibilidad ?telefono ?email
WHERE {{
    ?centro a ont:EducationalCenter ;
            ont:centerName ?nombre ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri ;
          ont:inNeighborhood ?barrioUri .
    ?distUri rdfs:label ?distrito .
    ?barrioUri rdfs:label ?barrio .
    OPTIONAL {{ ?addr ont:postalCode ?cp . }}
    OPTIONAL {{ ?centro ont:centerType ?tipo . }}
    OPTIONAL {{ ?centro ont:accessibilityCode ?accesibilidad . }}
    OPTIONAL {{ ?centro ont:description ?descripcion . }}
    OPTIONAL {{ ?centro ont:equipment ?equipamiento . }}
    OPTIONAL {{ ?centro ont:transportation ?transporte . }}
    OPTIONAL {{ ?centro ont:telephone ?telefono . }}
    OPTIONAL {{ ?centro ont:email ?email . }}
    {filter_block}
}}
ORDER BY ?distrito ?nombre"""

if len(g) == 0:
    st.error("⚠️ No se pudo cargar el grafo RDF. Verifica que `rdf/centros-educativos-with-links.ttl` exista en la carpeta.")
else:
    df = get_centers_dataframe(g)
    st.caption(f"✅ Grafo cargado desde `{os.path.basename(loaded_path)}` — **{len(g):,} tripletas RDF** y **{len(df):,} centros educativos únicos**.")

    # Barra lateral de filtros
    st.sidebar.header("🔍 Filtros del Buscador")
    
    distritos_disp = sorted(df["Distrito"].dropna().unique().tolist())
    distrito_sel = st.sidebar.selectbox("Distrito:", ["Todos"] + distritos_disp)
    
    if distrito_sel != "Todos":
        barrios_disp = sorted(df[df["Distrito"] == distrito_sel]["Barrio"].dropna().unique().tolist())
    else:
        barrios_disp = sorted(df["Barrio"].dropna().unique().tolist())
    barrio_sel = st.sidebar.selectbox("Barrio:", ["Todos"] + barrios_disp)
    
    tipos_disp = sorted(df["Tipo"].dropna().unique().tolist())
    tipo_sel = st.sidebar.selectbox("Tipología de Centro:", ["Todos"] + tipos_disp)
    
    cps_disp = sorted(df["Código Postal"].dropna().unique().tolist())
    cp_sel = st.sidebar.selectbox("Código Postal:", ["Todos"] + cps_disp)
    
    acc_disp = sorted(df["Accesibilidad"].dropna().unique().tolist())
    acc_sel = st.sidebar.selectbox("Código de Accesibilidad:", ["Todos"] + acc_disp)
    
    nombre_txt = st.sidebar.text_input("Nombre del centro contiene:", "")
    desc_txt = st.sidebar.text_input("Enseñanza / Etapa (ej. Infantil, ESO, Bilingüe):", "")
    equip_txt = st.sidebar.text_input("Equipamiento (ej. Comedor, Horario ampliado):", "")
    transp_txt = st.sidebar.text_input("Transporte (ej. Metro, Renfe, línea bus):", "")
    
    # Aplicar filtros al DataFrame
    df_filtrado = df.copy()
    tipo_raw_sel = "Todos"
    if distrito_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Distrito"] == distrito_sel]
    if barrio_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Barrio"] == barrio_sel]
    if tipo_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo"] == tipo_sel]
        raw_matches = df[df["Tipo"] == tipo_sel]["TipoRaw"].dropna().unique()
        if len(raw_matches) > 0:
            tipo_raw_sel = raw_matches[0]
    if cp_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Código Postal"] == cp_sel]
    if acc_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Accesibilidad"] == acc_sel]
    if nombre_txt:
        df_filtrado = df_filtrado[df_filtrado["Nombre"].str.contains(nombre_txt, case=False, na=False)]
    if desc_txt:
        df_filtrado = df_filtrado[df_filtrado["Descripción"].str.contains(desc_txt, case=False, na=False)]
    if equip_txt:
        df_filtrado = df_filtrado[df_filtrado["Equipamiento"].str.contains(equip_txt, case=False, na=False)]
    if transp_txt:
        df_filtrado = df_filtrado[df_filtrado["Transporte"].str.contains(transp_txt, case=False, na=False)]

    # KPIs superiores
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏫 Centros Encontrados", len(df_filtrado))
    col2.metric("📍 Distritos", df_filtrado["Distrito"].nunique() if not df_filtrado.empty else 0)
    col3.metric("🏘️ Barrios", df_filtrado["Barrio"].nunique() if not df_filtrado.empty else 0)
    col4.metric("🎓 Tipologías", df_filtrado["Tipo"].nunique() if not df_filtrado.empty else 0)
    
    st.markdown("---")
    
    tab_sparql, tab_list, tab_map, tab_stats = st.tabs([
        "🔎 Consultas SPARQL a la BBDD",
        "📋 Fichas de Centros",
        "🗺️ Mapa Geográfico Interactivo",
        "📊 Estadísticas"
    ])
    
    with tab_sparql:
        st.subheader("Motor de Consultas SPARQL en Vivo")
        modo_sparql = st.radio(
            "Modo de consulta:",
            ["Catálogo de 10 Preguntas Predefinidas / Editor Libre", "Ver Consulta SPARQL generada por tus Filtros Laterales"],
            horizontal=True
        )
        
        if modo_sparql == "Catálogo de 10 Preguntas Predefinidas / Editor Libre":
            pregunta_elegida = st.selectbox("Selecciona una pregunta para cargar su código SPARQL:", list(PREDEFINED_QUERIES.keys()))
            query_text = st.text_area("Código SPARQL (puedes editarlo libremente):", value=PREDEFINED_QUERIES[pregunta_elegida], height=250)
        else:
            dynamic_q = build_dynamic_sparql(distrito_sel, barrio_sel, tipo_raw_sel, cp_sel, acc_sel, nombre_txt, desc_txt, equip_txt, transp_txt)
            query_text = st.text_area("Consulta SPARQL construida automáticamente a partir de tus filtros:", value=dynamic_q, height=280)
            
        if st.button("▶️ Ejecutar Consulta SPARQL sobre el Grafo", type="primary"):
            try:
                q_res = g.query(query_text)
                cols = [str(v) for v in q_res.vars]
                rows = [[str(cell) if cell is not None else "" for cell in r] for r in q_res]
                df_sparql = pd.DataFrame(rows, columns=cols)
                st.success(f"Consulta ejecutada con éxito. Resultados obtenidos: **{len(df_sparql)}**")
                st.dataframe(df_sparql, use_container_width=True)
            except Exception as e:
                st.error(f"Error de sintaxis o ejecución en SPARQL: {e}")

    with tab_list:
        st.subheader(f"Listado de Centros Educativos ({len(df_filtrado)})")
        if df_filtrado.empty:
            st.info("No existen centros en el grafo que cumplan simultáneamente todos los filtros seleccionados.")
        else:
            mostrar_df = df_filtrado.head(100)
            if len(df_filtrado) > 100:
                st.caption("Mostrando los primeros 100 centros. Usa los filtros laterales para acotar más.")
            for _, row in mostrar_df.iterrows():
                titulo_tipo = f" — ({row['Tipo']})" if pd.notna(row["Tipo"]) else ""
                with st.expander(f"🏫 {row['Nombre']}{titulo_tipo}"):
                    render_center_card(row)

    with tab_map:
        st.subheader("Mapa Geográfico Interactivo")
        df_mapa = df_filtrado.dropna(subset=["lat", "lon"]).copy().reset_index(drop=True)
        if df_mapa.empty:
            st.info("Ninguno de los centros filtrados dispone de coordenadas geográficas registradas.")
        else:
            st.caption(
                f"Mostrando **{len(df_mapa)}** centros con coordenadas reales. "
                "**Pasa el ratón** sobre cualquier punto para ver su resumen o **haz clic sobre un punto** para abrir su ficha completa debajo."
            )
            # Columnas auxiliares para el globo emergente (tooltip) sin alterar los datos originales
            df_mapa["t_tipo"] = df_mapa["Tipo"].fillna("Sin especificar")
            df_mapa["t_dir"] = df_mapa["Dirección"].fillna("-")
            df_mapa["t_dist"] = df_mapa["Distrito"].fillna("-")
            df_mapa["t_barrio"] = df_mapa["Barrio"].fillna("-")
            df_mapa["t_tel"] = df_mapa["Teléfono"].fillna("-")
            df_mapa["t_acc"] = df_mapa["Accesibilidad"].fillna("-")

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df_mapa,
                id="centros_layer",
                get_position=["lon", "lat"],
                get_color=[220, 38, 38, 210],
                get_radius=45,
                radius_min_pixels=6,
                radius_max_pixels=18,
                pickable=True,
                auto_highlight=True,
            )

            view_state = pdk.ViewState(
                latitude=float(df_mapa["lat"].mean()),
                longitude=float(df_mapa["lon"].mean()),
                zoom=11 if len(df_mapa) > 15 else 13,
                pitch=0,
            )

            tooltip = {
                "html": (
                    "<b>🏫 {Nombre}</b><br/>"
                    "<b>Tipo:</b> {t_tipo}<br/>"
                    "<b>Dirección:</b> {t_dir}<br/>"
                    "<b>Distrito:</b> {t_dist} ({t_barrio})<br/>"
                    "<b>Teléfono:</b> {t_tel} | <b>Accesibilidad:</b> {t_acc}"
                ),
                "style": {
                    "backgroundColor": "#1f2937",
                    "color": "white",
                    "fontSize": "13px",
                    "padding": "10px",
                    "borderRadius": "6px",
                },
            }

            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip=tooltip,
                map_style="road",
            )

            # Soportar selección por clic directamente en el mapa (Streamlit >= 1.35)
            clicked_index = None
            try:
                event = st.pydeck_chart(deck, use_container_width=True, on_select="rerun", selection_mode="single-object")
                objs = event.selection.get("objects", {}) if hasattr(event, "selection") else {}
                if "centros_layer" in objs and len(objs["centros_layer"]) > 0:
                    clicked_obj = objs["centros_layer"][0]
                    # Localizar el centro clicado por su URI
                    if "URI" in clicked_obj:
                        matches = df_mapa.index[df_mapa["URI"] == clicked_obj["URI"]].tolist()
                        if matches:
                            clicked_index = matches[0]
            except TypeError:
                st.pydeck_chart(deck, use_container_width=True)

            st.markdown("#### 📌 Ficha del Centro Seleccionado en el Mapa")
            opciones_mapa = [f"{r['Nombre']} ({r['Distrito']} - {r['Barrio']})" for _, r in df_mapa.iterrows()]
            idx_por_defecto = clicked_index if clicked_index is not None else 0
            
            seleccion_manual = st.selectbox(
                "Centro seleccionado (haz clic en un punto del mapa o elígelo en la lista):",
                 options=range(len(opciones_mapa)),
                format_func=lambda i: opciones_mapa[i],
                index=idx_por_defecto,
            )
            
            centro_detalle = df_mapa.iloc[seleccion_manual]
            with st.container(border=True):
                st.markdown(f"### 🏫 {centro_detalle['Nombre']}")
                render_center_card(centro_detalle)

    with tab_stats:
        c_stat1, c_stat2 = st.columns(2)
        with c_stat1:
            st.subheader("Centros por Distrito")
            if not df_filtrado.empty:
                st.bar_chart(df_filtrado["Distrito"].value_counts())
        with c_stat2:
            st.subheader("Centros por Código de Accesibilidad")
            if not df_filtrado.empty:
                st.bar_chart(df_filtrado["Accesibilidad"].value_counts())