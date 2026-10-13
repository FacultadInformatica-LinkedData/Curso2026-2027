# Hands-on assignment 3 – Self assessment

## Checklist

List the changes applied to the dataset(s):

# BiciMad dataset

[x] **Coordinate correction:** in `POINT_X` and `POINT_Y`, the decimal comma was replaced with a dot, and the values were converted to numeric type. They were then renamed to `longitude` and `latitude`.

[x] **Numeric type conversion:** the columns `NoAvailable`, `Ligth`, `TotalBases` and `OBJECTID` were converted to numbers. `NoAvailable` and `TotalBases` were later renamed to `unavailableBases` and `totalBases`.

[x] **Boolean conversion:** the column `Activate` was renamed to `isActivated`, and its values were converted from `"1"`/`"0"` to `true`/`false`.

[x] **State column cleaning:** leading and remaining whitespaces were removed (`trim`) in `State`, the type was forced to text (`toString`), and it was renamed to `operationalState`.

[x] **Full address normalization:** from `Address`, an uppercase version was created, and from it another version without commas and with `trim` applied, which became `fullAddress`. The original columns `Address` and `address_uppercase` were removed.

[x] **Creation of `ADDRESS_CLEAN`:** a column was generated with the address in lowercase, without accents or special characters, without street numbers and with abbreviations expanded (`c/` → `calle`, `avda.`/`av.` → `avenida`, `pº` → `paseo`), everything with the command `trim`.

[x] **Street type extraction (`streetType`):** the first word of `fullAddress` was extracted (`split()[0]`). Variants were unified (`AV.`, `AV/`, `AVDA.` → `AVENIDA`; `C/` → `CALLE`). Any value outside the list of valid street types (AVENIDA, CALLE, CAMINO, CARRERA, CARRETERA, CIUDAD, FACULTAD, GLORIETA, INTERCAMBIADOR, PARQUE, PASEO, PLAZA, PLAZUELA, RONDA) was set to `CALLE`.

[x] **Street name extraction (`streetName`):** the street type at the beginning was removed (CALLE, PLAZA, PASEO, AVENIDA…), as well as building numbers (`Nº`, `NUMERO`, trailing numbers), text in parentheses or square brackets, location references (`FRENTE`, `ENFRENTE`, `ESQUINA`) and the prefixes `C/` and `AV.`. For streets of type `CAMINO`, the numeric text after the name was also removed.

[x] **Preposition/article extraction (`STREET_PREPOSITION`):** a column was created with the initial element of the street name (`DE`, `DEL`, `DE LA`, `DE LAS`, `EL`, `LOS`…) using Python. The prepositions were then removed from `streetName`, so that it only contains the street name for future mapping.

[x] **Accent removal in `streetName`:** accented characters and characters with diaeresis were replaced with their unaccented equivalents (`replaceChars("ÁÉÍÓÚÜáéíóúü", "AEIOUUaeiouu")`).

[x] **Removal of unnecessary columns:** the column `PosicionSTR` was deleted, since the coordinates are already split into two columns: `longitude` and `latitude`.

[x] **Column renaming:** the naming was unified according to the ontology: `number` → `stationId`, `Name` → `name`, `STREET_NAME` → `streetName`, `STREET_TYPE` → `streetType`, `ADDRESS_NOCOMMA` → `fullAddress`, and the typo `ADRESS_CLEAN` was corrected to `ADDRESS_CLEAN`.

# El Callejero dataset

[x] **Decimal separator fixed in the numeric coordinate columns.** In `UTMX_ETRS`, `UTMY_ETRS`, `UTMX_ED` and `UTMY_ED` the decimal comma was replaced by a point (value.replace(",",".")) and the columns were then converted to numbers (value.toNumber()), so they can be used in calculations and in the later reconciliation/export.

[x] **Geographic coordinates converted to decimal degrees.** `LATITUD` and `LONGITUD` were stored in degrees-minutes-seconds format (e.g. 40°25'12.3'' N). A GREL expression with a regex extracts degrees, minutes and seconds and computes deg + min/60 + sec/3600, applying a negative sign for S (latitude) and W (longitude). Values that don't match the pattern become null.

[x] **Postal codes normalised.** `COD_POSTAL` was padded with leading zeros to exactly 5 digits (("00000"+value).slice(-5)), repeated whitespace was collapsed, and the column was finally set as text so the leading zeros are not lost.

[x] **Data types fixed.** Converted columns to number: `COD_NDP`, `DISTRITO`, `ANGULO_ROTULACION`, `NUMERO` and `BARRIO`. Converted columns to text: `CLASE_APP`.

[x] **Whitespace cleaned.** `BARRIO` was trimmed and had consecutive spaces/non-breaking spaces collapsed into a single space.

[x] **Inconsistent values unified with mass edits (clustering).**
  - `VIA_NOMBRE_ACENTOS`: SAGRADOS CORÓNES / SAGRADOS CORAZONES → SAGRADOS CORAZONES; MONTANA / MONTAÑA → MONTAÑA.
  - `VIA_NOMBRE`: MONTANA / MONTAÑA → MONTAÑA.
  - `VIA_PAR`: DE / DE ` (trailing space) → `DE.
  - `CALIFICADOR`: cells with one or several blank spaces → a single space.
  - `CLASE_APP`: NUMERO → NÚMERO (missing accent).

[x] **Rows removed by street type.** Using a facet on `VIA_CLASE`, all rows with type `AUTOPISTA`, `AUTOVÍA`, `PUENTE` and `PLAZUELA` were deleted (four separate removal operations), as they are not relevant for the analysis / not comparable with the BiciMad data.

[x] **Columns renamed to a common schema.** `COD_VIA` → `streetCode`, `VIA_NOMBRE` → `streetName`, `VIA_CLASE` → `streetType`, `DISTRITO` → `districtCode`, `BARRIO` → `neighborhoodCode`, `COD_POSTAL` → `postalCode`. (Some intermediate renames, such as `COD_VIA(SI)` and `neighborhoodcode`, were corrections of earlier steps and don't change the final result.)

[x] **Accents removed from street names.** In `streetName`, ÁÉÍÓÚÜáéíóúü were replaced by their unaccented equivalents (AEIOUUaeiouu), to make matching with other datasets easier. The step was first tried with Python and then redone with GREL; the final effect is the same.

[x] **Exploratory step, not kept in the final dataset.** Columns `numNombres` and `nombres` were created with cell.cross(...) against the CallejeroOficial project to check how many different names each `streetCode` has, and were removed afterwards (an earlier attempt pointing at NOMBRE_PROYECTO was also discarded).

## Comments on the self-assessment

The main difficulty with the BiciMad dataset was its low quality and lack of consistency. Numeric values such as the coordinates used a decimal comma, several numeric columns were stored as text, and boolean values were encoded as `"1"`/`"0"`. The `Address` column was the most problematic: it mixed street type, street name, building number and location references in a free-text field, with the same street type written in several ways (`AV.`, `AVDA.`, `C/`). Column names were also inconsistent and contained typos (e.g. `Ligth`). As a result, a significant part of the work consisted of cleaning, splitting and standardizing the data before it could be linked reliably.

In the Callejero history, several operations are corrections of previous ones (duplicated renames, Python → GREL, the cross-check columns created and deleted), so the net number of effective changes is smaller than the 47 steps recorded in OpenRefine.
