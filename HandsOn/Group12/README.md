# Galician Municipality Explorer

A small Streamlit application for exploring our Galician municipal
demographic knowledge graph through editable SPARQL SELECT queries.

## Features

- Provides an editable SPARQL query box.
- Sends queries to a local GraphDB repository.
- Displays results in a table using the variables returned by the query.
- Includes example queries for population density, linked municipalities,
  and counting linked municipalities.
- Uses RDFLib to parse queries and accepts SELECT queries only.

The default query displays the ten municipalities with the highest
population density, alongside their Wikidata URIs.

The dataset year is 2025. Municipalities without population-density
values are excluded from the default query, not treated as having
zero density.

## Prerequisites

- Python and the packages listed in requirements.txt.
- GraphDB running locally on port 7200.
- A repository named group12-revised containing the corrected
  t723-with-links.ttl dataset.

The app uses this SPARQL endpoint:

http://localhost:7200/repositories/group12-revised

If your GraphDB address or repository name differs, update ENDPOINT
in app.py.

## Install

From the WebSem folder, using the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r ".\municipality-explorer\requirements.txt"
```

## Run

Start GraphDB first, then run this command from the WebSem folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run ".\municipality-explorer\app.py"
```

Open the local address printed in the terminal.

Keep GraphDB and the Streamlit terminal running during the demonstration.
To stop Streamlit, press Ctrl+C in its terminal.

## Using the explorer

1. Keep the default query or replace it with another SPARQL SELECT query.
2. Include the PREFIX declarations needed by your query.
3. Click "Run query".
4. Read the results in the table.

The expandable example sections contain queries you can copy into
the query box.

With our corrected dataset loaded, the example count query returns
316 distinct local municipalities with Wikidata links.

## How it works

Query text → RDFLib parsing and query-type check → SPARQL request
→ GraphDB → JSON results → results table.

The application sends queries to GraphDB; it does not load the CSV
or generate RDF.

## Limitations

- Intended for a local demonstration, not a publicly deployed service.
- Assumes the local GraphDB endpoint allows queries without authentication.
- Supports SELECT queries, not ASK, CONSTRUCT, DESCRIBE or SPARQL Update.
- Query parsing is not a complete security sandbox.
- Large or complex queries may be slow; use LIMIT when exploring.
- The request timeout is 30 seconds.
- Returned values are displayed as text.
- Wikidata URIs identify external resources; the default query does not
  query Wikidata live.

## Backup version

app_fixed_query.py preserves the original predefined-query interface.