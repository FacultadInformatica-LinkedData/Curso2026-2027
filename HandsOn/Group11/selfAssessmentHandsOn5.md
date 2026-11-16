# Hands-on assignment 5 – Self assessment

## Checklist

**Every RDF file:**

- [X] Has at least one owl:sameAs property that links to another dataset

## Comments on the self-assessment

The metro_name column was reconciled against Wikidata using the metro station type.

112 out of 113 metro-related values were successfully linked to Wikidata. The remaining case, Palas de Rey, belongs to Madrid Metro Ligero and could not be automatically reconciled as a conventional metro station, so it was intentionally left unmatched instead of forcing an incorrect link.

The City column was also reconciled against Wikidata. All 631 rows were successfully linked to Madrid (Q2807).
