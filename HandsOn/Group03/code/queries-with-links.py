"""Verifica el enlazado owl:sameAs entre el KG de BiciMAD y Wikidata."""

import sys
from string import Template

#Necesita rdflib y sparqlwrapper
from rdflib import Graph
from SPARQLWrapper import JSON, POST, SPARQLWrapper

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "bicimad-link-checker/0.1 (UPM coursework; contact: you@example.com)"

LOCAL_PREFIXES = """
PREFIX bm:  <https://bicismart.madrid.data.es/ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
"""

WIKIDATA_PREFIXES = """
PREFIX wd:       <http://www.wikidata.org/entity/>
PREFIX wdt:      <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd:       <http://www.bigdata.com/rdf#>
"""

LOCAL_QUERIES = {
    "Q1 Calles totales y enlazadas": """
        SELECT (COUNT(DISTINCT ?street) AS ?streets) (COUNT(?wd) AS ?linked)
        WHERE {
          ?street a bm:Street .
          OPTIONAL { ?street owl:sameAs ?wd }
        }""",
    "Q2 IRIs no canónicas (esperado: vacío)": """
        SELECT ?street ?wd
        WHERE {
          ?street owl:sameAs ?wd .
          FILTER (!STRSTARTS(STR(?wd), "http://www.wikidata.org/entity/Q"))
        }""",
    "Q3 QIDs compartidas por varias calles (esperado: vacío)": """
        SELECT ?wd (COUNT(?street) AS ?n)
        WHERE { ?street owl:sameAs ?wd }
        GROUP BY ?wd
        HAVING (COUNT(?street) > 1)""",
}

WIKIDATA_QUERIES = {
    "Q4 Tipos (P31) de las entidades enlazadas": """
        SELECT ?type ?typeLabel (COUNT(?item) AS ?n)
        WHERE {
          VALUES (?item ?streetName) { $links }
          OPTIONAL { ?item wdt:P31 ?type }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "es". }
        }
        GROUP BY ?type ?typeLabel
        ORDER BY DESC(?n)""",
    "Q5 Entidades fuera de Madrid (esperado: vacío)": """
        SELECT ?streetName ?item ?itemLabel ?placeLabel
        WHERE {
          VALUES (?item ?streetName) { $links }
          FILTER NOT EXISTS { ?item wdt:P131* wd:Q2807 }
          OPTIONAL { ?item wdt:P131 ?place }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "es". }
        }""",
}


def query_local(graph: Graph, query: str) -> list[dict]:
    result = graph.query(LOCAL_PREFIXES + query)
    return [{str(var): row[var] for var in result.vars} for row in result]


def query_wikidata(query: str) -> list[dict]:
    client = SPARQLWrapper(WIKIDATA_ENDPOINT, agent=USER_AGENT)
    client.setMethod(POST)  # 200+ IRIs en VALUES: con GET la URL sería demasiado larga
    client.setReturnFormat(JSON)
    client.setQuery(WIKIDATA_PREFIXES + query)
    bindings = client.queryAndConvert()["results"]["bindings"]
    return [{var: value["value"] for var, value in row.items()} for row in bindings]


def print_result(title: str, rows: list[dict]) -> None:
    print(f"\n== {title}: {len(rows)} fila(s)")
    for row in rows[:20]:
        print("   " + " | ".join(f"{var}={value}" for var, value in row.items()))


def main(ttl_path: str) -> None:
    graph = Graph()
    graph.parse(ttl_path, format="turtle")

    for title, query in LOCAL_QUERIES.items():
        print_result(title, query_local(graph, query))

    linked = query_local(graph, """
        SELECT ?wd ?streetName
        WHERE { ?street owl:sameAs ?wd ; bm:streetName ?streetName }""")
    links = " ".join(f"(<{row['wd']}> {row['streetName'].n3()})" for row in linked)
    for title, query in WIKIDATA_QUERIES.items():
        print_result(title, query_wikidata(Template(query).substitute(links=links)))


if __name__ == "__main__":
    main(sys.argv[1])