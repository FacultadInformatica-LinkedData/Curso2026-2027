# Hands-on assignment 3 – Self assessment

## Checklist

**Every resource described in the CSV file:**

- [x] Has a unique identifier in a column (not an auto-increased integer)
- [x] Is related to a class in the ontology

**Every class in the ontology:**

- [ ] Is related to a resource described in the CSV file

**Every column in the CSV file:**

- [x] Is trimmed
- [x] Is properly encoded (e.g., dates, booleans)
- [x] Is related to a property in the ontology

**Every property in the ontology:**

- [ ] Is related to a column in the CSV file

## Comments on the self-assessment

### Work done

We cleaned the three datasets of the group with OpenRefine 3.10: `instalaciones_deportivas_basicas` (607 rows), `polideportivos` (82 rows) and `piscinas_publicas` (56 rows). Each dataset has its own operation history in `openrefine/<name>.json` and its cleaned data in `csv/<name>-updated.csv`. The original CSV files are kept unchanged.

**Import settings (not stored in the JSON):** character encoding ISO-8859-1, column separator `;`, quote character `"`, and "Parse cell text into numbers" unticked. The JSON must be applied to a project created with these settings. The `polideportivos` JSON uses `cell.cross("piscinas_publicas", "PK")`, so the project of the pools must exist, with that name, and its JSON must be applied first (the PK is converted to a number in both).

**Reproducibility:** we imported the original files into a clean OpenRefine, applied only the saved JSON files, and exported the CSV again. The result was identical, byte by byte, to the delivered `*-updated.csv` files.

### Cleaning operations (same for the three files unless stated)

1. `PK` converted to number (unique in every file, it is the identifier of the individual and is used in the URI `facility/{PK}`).
2. Text columns (`NOMBRE`, `HORARIO`, `EQUIPAMIENTO`, `TRANSPORTE`, `DESCRIPCION`, `NOMBRE-VIA`, `CLASE-VIAL`, `BARRIO`, `DISTRITO`): HTML entities decoded twice (the source has `&amp;Ntilde;` for Ñ, `&amp;iexcl;` for ¡), repeated and non-breaking spaces collapsed, trimmed. The remaining columns are only trimmed.
3. `TELEFONO`: only 9-digit numbers are kept, separated by `;` (the source has several numbers in one cell, labels such as "Taquilla:" and "S/T"). The prefix 34 is removed.
4. `EMAIL`: only valid e-mail addresses are kept, in lower case, separated by `;`. One address that was stored in `FAX` was moved here.
5. `DISTRITO`: the placeholder text "DISTRITO" (21 rows of the basic facilities) is replaced by an empty value.
6. `LONGITUD`: the sign of one wrong longitude (`PK 50334831`, `+3.64`) is corrected. `LATITUD` and `LONGITUD` are converted to numbers.
7. `ACCESIBILIDAD` is split into `ACCESIBILIDAD-NIVEL` (one code, 0 to 3, mobility level) and `ACCESIBILIDAD-EXTRAS` (codes 4 to 6, separated by `;`), as the ontology has a level and features. The original column is removed.
8. `COD-BARRIO` is set from the district and neighbourhood name, using a list built from the rows that have both. It fills the missing numbers that can be derived (6 in the basic facilities and 1 in each of the other two files) and corrects one wrong number (Legazpi). `SAN ANDRES` is set to 1, as it is the neighbourhood called `VILLAVERDE ALTO C.H.` in the other rows.
9. New column `ID-BARRIO` = district code + `-` + neighbourhood number (for example `4-2`), the identifier used in `neighbourhood/{ID-BARRIO}`. It is left empty when the district code of the source disagrees with the district name (2 rows with a neighbourhood) or when the neighbourhood is unknown.
10. `COD-DISTRITO` is set from the district name (1 to 21), because the source has missing codes and three codes that do not match the name. It is converted to number, as `COD-BARRIO`.
11. `TIPO`: only the last segment of the path is kept (`PistaFutbolSala`), used in `facilityType/{TIPO}`.
12. `polideportivos` only: new column `HAS-SWIMMING-POOL` (`true`/`false`) from the pools dataset (55 of the 82 centres are in the pools file).
13. Columns removed because they are empty, constant or have no property in the ontology: `DESCRIPCION-ENTIDAD`, `TIPO-NUM`, `ORIENTACION`, `PLANTA`, `PUERTA`, `ESCALERAS`, `LOCALIDAD`, `PROVINCIA`, `COORDENADA-X`, `COORDENADA-Y`, `FAX`.

### Relation between columns and ontology properties

| Column | Ontology term |
|---|---|
| `PK` | `ms:sourceKey` and the URI of the individual (`msr:facility/{PK}`) |
| `NOMBRE` | `rdfs:label` |
| `HAS-SWIMMING-POOL` | `ms:hasSwimmingPool` |
| `HORARIO` | `ms:openingHours` |
| `EQUIPAMIENTO` | `ms:equipment` |
| `TRANSPORTE` | `ms:transport` |
| `DESCRIPCION` | `ms:description` |
| `ACCESIBILIDAD-NIVEL` | `ms:hasAccessibilityLevel` |
| `ACCESIBILIDAD-EXTRAS` | `ms:hasAccessibilityFeature` |
| `CONTENT-URL` | `ms:webPage` (property added to the ontology in this hands-on) |
| `CLASE-VIAL`, `NOMBRE-VIA`, `NUM`, `CODIGO-POSTAL` | `ms:streetType`, `ms:streetName`, `ms:streetNumber`, `ms:postalCode` |
| `COD-BARRIO`, `ID-BARRIO`, `BARRIO` | `ms:neighbourhoodNumber`, `ms:locatedInNeighbourhood` (and the URI of the neighbourhood), `rdfs:label` of the neighbourhood |
| `COD-DISTRITO`, `DISTRITO` | `ms:districtCode`, `ms:locatedInDistrict` (and `ms:belongsToDistrict`), `rdfs:label` of the district |
| `LATITUD`, `LONGITUD` | `ms:latitude`, `ms:longitude` |
| `TELEFONO`, `EMAIL` | `ms:phone`, `ms:email` (several values separated by `;` are split in the mapping) |
| `TIPO` | `ms:hasFacilityType` and the URI of the facility type |

### Why two boxes are not ticked

- **Every class is related to a resource of the CSV:** `ms:City` has no row in the CSV. The only city is Madrid and the individual `city/madrid` is created as a constant in the mapping (the column `LOCALIDAD` was removed because it always has the same value). `ms:SportsFacility` and `ms:AccessibilityValue` are superclasses used only to group classes; their individuals are created through `ms:BasicSportsFacility`, `ms:SportsCentre`, `ms:AccessibilityLevel` and `ms:AccessibilityFeature`. The accessibility levels and features are individuals created from the values of the two accessibility columns.
- **Every property is related to a column:** `ms:partOfCity` links each district with the city and has no column (it is created in the mapping with the constant `city/madrid`).

### Known problems

- 31 of the 607 basic facilities have no `ID-BARRIO`: 21 have no district or neighbourhood at all in the source, 5 have a district but no neighbourhood, 3 are in the neighbourhood `AMBROZ` (whose number we could not confirm) and 2 have a district code that disagrees with the district name, so their neighbourhood number cannot be trusted. In the sports centres and pools only `AMBROZ` is missing.
- Two neighbourhood numbers are shared by two different neighbourhoods in the source (`11-7`: Peseta and Abrantes; `12-4`: Almendrales and Moscardó). We could not decide which one is right without an external list, so they are kept as they are. The other repeated numbers are different spellings of the same name.
- Phone labels ("Taquilla", "Oficina") are lost, only the numbers are kept.
- Names of streets, districts and neighbourhoods are in capital letters and, in some rows, without accents. We kept them as in the source.
- The free-text fields (`HORARIO`, `EQUIPAMIENTO`, `TRANSPORTE`) are not structured and are kept as text.
