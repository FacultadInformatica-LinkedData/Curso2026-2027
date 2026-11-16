# Hands-on assignment 3 – Self assessment

## Checklist


- [x] Dataset was imported into OpenRefine.
- [x] I removed rows containing unnecessarry information for the RDF tranformation such as the metadata row and additional notes at the end of the file.
- [x] Municipalities are identified by a five-digit INE Code preceeding its name thus any field that does not meet this requirement was removed.
- [x] I separated the INE Code from the municipality field as the code and the municipality were categorized into a single cell.
- [x] I added a new column called 'Year'.
- [x] Missing values were represented as '-' and I have changed all matching values as 'N/A' (Not applicable).
- [x] Decimal values were changed to '.' as they were represented with ',' before.
- [x] Exported cleaned and prepped dataset as 'xxx-updated.csv'
- [x] All OpenRefine operations were exported into a JSON file.

## Comments on the self-assessment

1. The origina dataset contained a lot of unnecessary information that would be of no use for the RDF generation.
I have left only the important data such as the INE Code, Municipality name and its corresponding geographical information as well as the observation date (which was added as a brand new column).

2. I am unsure whether the step I have taken to replace all non-numeric values (represented as '-') as 'N/A' is the right step. I would need to consult the professor regarding this step and whether this would affect any and all following steps.


