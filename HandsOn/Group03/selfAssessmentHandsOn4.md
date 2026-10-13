# Hands-on assignment 4 – Self assessment

## Checklist

### BiciMad dataset:

#### bm:Bikestation
- [X] name -> rdfs:label
- [X] stationId -> bm:stationId
- [X] totalBases -> bm:totalCapacity
- [X] We added bm:hasPoint with geo:Point
- [X] We added bm:hasState with bm:StationSate
- [X] We added bm:locatedOnStreet with bm:Street
#### geo:Point
- [X] latitude -> geo:lat
- [X] longitude -> geo:long

#### bm:StationState
- [X] isActivated -> bm:isActivated
- [X] operationalState -> bm:operationalState
- [X] unavailableBases -> bm:unavailableBases

### Callejero Oficial dataset:

#### bm:Street
- [X] streetName -> rdfs:label
- [X] streetCode -> bm:streetCode
- [X] streetName -> bm:streetName
- [X] districtCode -> bm:districtCode
- [X] neighborhoodCode -> bm:neighborhoodCode
- [X] postalCode -> bm:postalCode

### Matching
- [X] We used the {streetName, streetType} columns from both datasets to  match

## Comments on the self-assessment
Note: We tried to transform our RML document to YARRRML, but couldn't execute it with Morph; it seems 2 join conditions are not supported.
