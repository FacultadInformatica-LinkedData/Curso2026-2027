# Hands-on assignment 5 – Self assessment

## Checklist

**Every RDF file:**

- [x] Has at least one owl:sameAs property that links to another dataset

## Comments on the self-assessment

- We linked our data with Wikidata. The 11 pollutants and the municipality of Madrid are linked with `owl:sameAs`. The stations are linked with `rdfs:seeAlso` to the place where they are (a square, park, street or district), because the stations themselves are not in Wikidata and they are not the same thing as the place.
- 21 of the 24 stations have a link. For Farolillo, Castellana and Urb. Embajada we did not find a place in Wikidata that matched well, so we left them without a link.
- Observations and station types are not linked because there is nothing equivalent in other datasets. The observations already reach Wikidata through their station and pollutant.
- `airquality-with-links.ttl` and `airquality-with-links.nt` have the same 20,817 triples (the 20,785 of Hands-on 4 plus 32 links). Queries Q9 and Q10 use the Wikidata endpoint, so they need an internet connection.
