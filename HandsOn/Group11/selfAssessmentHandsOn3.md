# Hands-on Assignment 3 – Self-assessment

## Checklist

**Data import and analysis:**

- [x] The selected BiciMAD dataset was successfully imported into OpenRefine.
- [x] The dataset contains 631 records and 12 columns.
- [x] The data was analyzed to identify potential errors and inconsistencies.
- [x] No missing values or duplicate station identifiers were found.

**Data cleaning and transformation:**

- [x] Unnecessary trailing commas and extra spaces were removed from the `Address` column.
- [x] Extra whitespace was removed from station names in the `Name` column.
- [x] Decimal separators in `POINT_X` and `POINT_Y` were standardized using dots instead of commas.
- [x] The `PosicionSTR` column was normalized using the cleaned geographic coordinates.
- [x] The columns `OBJECTID`, `Activate`, `Ligth`, `NoAvailable` and `TotalBases` were converted to numeric values.
- [x] The `number` column was preserved as a string because some station identifiers contain letters.
- [x] All 631 records were preserved during the cleaning process.

**Data validation:**

- [x] All station identifiers remain unique.
- [x] Geographic coordinates are represented consistently.
- [x] No new missing values were introduced.
- [x] The original distribution of station states was preserved:
  - IN_SERVICE: 626
  - NOT_IN_SERVICE: 3
  - END_OF_LIFE: 1
  - PLANNED: 1

**Deliverables:**

- [x] The OpenRefine transformation history was exported as a JSON file containing 10 operations.
- [x] The cleaned dataset was exported as a CSV file.
- [x] This self-assessment document was completed.

## Comments on the self-assessment

The BiciMAD dataset was already relatively clean, with no missing values or duplicate station identifiers. However, several transformations were necessary to improve consistency and facilitate future RDF generation.

The main improvements involved standardizing geographic coordinates, cleaning textual fields and converting numeric attributes to the appropriate data types.

The `number` column was intentionally preserved as text because it contains alphanumeric identifiers such as `25A`, `25B` and `508-old`.

All original records were preserved, including stations that are not currently in service or are planned.

The cleaning process was performed using OpenRefine, and the transformation history was exported to allow the operations to be reproduced.