# Madrid Sports Finder (Group 08)

A small web application that exploits the knowledge graph of Group 08. It reads the linked RDF
(`data/madridsports-with-links.ttl`, a copy of `rdf/madridsports-with-links.ttl`) and shows the 690 sports facilities
of Madrid on a map. The Turtle file is parsed in the browser with [N3.js](https://github.com/rdfjs/N3.js), so no
server-side code or SPARQL endpoint is needed.

## Run it

The page loads the data with `fetch`, so it must be served over HTTP (opening `index.html` directly will not work):

```bash
cd HandsOn/Group08/app
python3 -m http.server 8000
```

Then open <http://localhost:8000>. The map tiles need an internet connection; Leaflet and N3.js are included in `lib/`.

## What it does

Requirements from `requirements/applicationRequirements.html` that are implemented:

| Requirement | In the app |
|---|---|
| FR1 Map of all facilities, different marker per category | Green = basic facility, blue = sports centre |
| FR2 Filter by facility type | "Facility type" list (31 types from the graph) |
| FR3 Filter by district | "District" list, or click a bar of the chart |
| FR4 Filter by accessibility | Mobility level, or a feature (tactile paving, induction loop, sign language) |
| FR5 Detail card | Click a marker: type, address, opening hours, accessibility, equipment, transport, phone, email, source |
| FR6 Nearest facilities | "Use my location" lists the 5 closest facilities that match the filters |
| FR7 Facilities per district | Bar chart that follows the filters |
| FR8 Links to external entities | The district in the detail card links to its Wikidata entity (the `owl:sameAs` from Hands-on 5) |
| FR9 Attribution and licence | Footer: Ayuntamiento de Madrid, CC BY 4.0 |

Not implemented: filtering by neighbourhood (FR3, only district), and the Spanish/English switch. Facilities without
opening hours show "Not available".

## How it uses the graph

Every value shown comes from RDF triples: the facility classes (`ms:BasicSportsFacility`, `ms:SportsCentre`),
`ms:latitude` / `ms:longitude`, `ms:locatedInDistrict`, `ms:hasFacilityType`, `ms:hasAccessibilityLevel`,
`ms:hasAccessibilityFeature`, `ms:hasSwimmingPool`, `rdfs:label`, and `owl:sameAs` of the districts. The detail card
also shows the URI of the facility in the graph.

## Files

* `index.html`, `style.css`, `app.js`: the application.
* `data/madridsports-with-links.ttl`: the RDF used (copy of the Hands-on 5 output).
* `lib/`: Leaflet 1.9.4 and N3.js 1.17.2.
