# Hands-on assignment 4 – Self assessment

## Checklist

**Every RDF file:**

- [ ] Uses the .nt extension
- [ ] Is serialized in the NTriples format
- [x] Follows the resource naming strategy
- [x] Uses class and property URIs that are the same as those used in the ontology

**Every URI in the RDF files:**

- [x] Is "readable" and has some meaning (e.g., it is not an auto-increased integer) 
- [x] Is not encoded as a string
- [x] Does not contain a double slash (i.e., “//”)

**Every individual in the RDF files:**

- [x] Has a label with the name of the individual
- [x] Has a type

**Every value in the RDF files:**

- [x] Is trimmed
- [x] Is properly encoded (e.g., dates, booleans)
- [x] Includes its datatype
- [x] Uses the correct datatype (e.g., values of 0-1 may be booleans and not integers, not every string made of numbers is a number)

## Comments on the self-assessment
- Aunque en la checklist de evaluación se indica el uso de la extensión `.nt` y el formato NTriples (dejados sin marcar por honestidad), en las instrucciones principales de la práctica (Deliverables) se pide expresamente: *"An RDF file in the Turtle syntax with the data transformed into RDF (“*.ttl” under an “rdf” directory)"*. Hemos seguido esta última instrucción principal entregando nuestros datos en Turtle (.ttl).

## Difficulties encountered
- We had to adjust the mapping rules to correctly concatenate the street type, name, and number into a single `streetAddress` string.
- Handling the URIs for Districts and Neighborhoods dynamically based on the dataset columns using templates.

## Tools used
- Morph-KGC / RMLMapper for the transformation process.
- Protégé to verify the ontology structure.