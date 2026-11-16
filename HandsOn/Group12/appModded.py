import json
import urllib.parse
import urllib.request
from rdflib.plugins.sparql.parser import parseQuery

import pandas as pd
import streamlit as st

ENDPOINT = "http://localhost:7200/repositories/group12-revised"

PREFIXES = """
PREFIX vocab: <https://w3id.org/smartinfra-galicia/ontology/Demographics#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

DEFAULT_QUERY = """SELECT ?name ?density ?wikidata WHERE {
  ?municipality a vocab:Municipality ;
                vocab:hasName ?name ;
                vocab:hasDemographicInformation ?observation ;
                owl:sameAs ?wikidata .

  ?observation vocab:hasPopulationDensity ?density .

  FILTER(STRSTARTS(STR(?wikidata), "http://www.wikidata.org/entity/"))
}
ORDER BY DESC(?density)
LIMIT 10
"""

st.set_page_config(
    page_title="Galician Municipality Explorer",
    page_icon=":bar_chart:",
    layout="wide",
)

st.title("Galician Municipality Explorer")
st.caption(
    "Explore the group's demographic knowledge graph through SPARQL. "
    "The default query shows the municipalities with the highest population density."
)

st.subheader("SPARQL query")
st.caption(
    "Edit the query or paste another SELECT query, then choose Run query. "
    "The app sends read-only queries to the local GraphDB repository."
)

query_text = st.text_area(
    "SPARQL SELECT query",
    value=PREFIXES + DEFAULT_QUERY,
    height=280,
    key="sparql_query",
)

run_clicked = st.button("Run query", type="primary", use_container_width=True)

if run_clicked:
    query = query_text.strip()

    if not query:
        st.error("Please enter a SPARQL query.")
        st.stop()

    try:
        parsed_query = parseQuery(query)
    except Exception as error:
        st.error("The query could not be parsed. Check your SPARQL syntax.")
        st.caption(str(error))
        st.stop()

    if parsed_query[1].name != "SelectQuery":
        st.error("This explorer currently supports SELECT queries only.")
        st.stop()

    else:
        try:
            params = urllib.parse.urlencode({"query": query})
            url = f"{ENDPOINT}?{params}"

            request = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/sparql-results+json",
                    "User-Agent": "GalicianMunicipalityExplorer/1.0",
                },
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))

            bindings = payload.get("results", {}).get("bindings", [])

            if not bindings:
                st.info("The query ran successfully, but returned no results.")
            else:
                rows = []
                for binding in bindings:
                    row = {}
                    for variable, value in binding.items():
                        row[variable] = value.get("value", "")
                    rows.append(row)

                results = pd.DataFrame(rows)

                st.subheader("Results")
                st.caption(f"{len(results)} result(s)")

                if "wikidata" in results.columns:
                    results["wikidata"] = results["wikidata"].apply(
                        lambda value: f"[Open Wikidata]({value})"
                        if value
                        else ""
                    )

                st.dataframe(
                    results,
                    use_container_width=True,
                    hide_index=True,
                )

        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            st.error(
                f"GraphDB returned HTTP error {error.code}. "
                "Check that the query is valid and that the repository is running."
            )
            st.caption(details[:1000])

        except Exception as error:
            st.error(
                "Could not run the query. Check that GraphDB is running and "
                "that the repository name in ENDPOINT is correct."
            )
            st.caption(str(error))

else:
    st.info(
        "Choose **Run query** to send the query to GraphDB. "
        "The default query returns the ten municipalities with the highest population density."
    )

with st.expander("Example: count linked municipalities"):
    st.code(
        PREFIXES
        + """
SELECT (COUNT(DISTINCT ?municipality) AS ?linkedMunicipalities)
WHERE {
  ?municipality a vocab:Municipality ;
                owl:sameAs ?wikidata .

  FILTER(
    STRSTARTS(STR(?municipality), "https://w3id.org/smartinfra-galicia/resource/Municipality/")
    &&
    STRSTARTS(STR(?wikidata), "http://www.wikidata.org/entity/")
  )
}
""",
        language="sparql",
    )

with st.expander("Example: municipalities and Wikidata links"):
    st.code(
        PREFIXES
        + """
SELECT ?name ?wikidata
WHERE {
  ?municipality a vocab:Municipality ;
                vocab:hasName ?name ;
                owl:sameAs ?wikidata .

  FILTER(STRSTARTS(STR(?wikidata), "http://www.wikidata.org/entity/"))
}
ORDER BY ?name
LIMIT 10
""",
        language="sparql",
    )

st.caption(
    "Data year: 2025. Municipalities without a population-density value are excluded "
    "from the default query; they are not treated as having zero density."
)