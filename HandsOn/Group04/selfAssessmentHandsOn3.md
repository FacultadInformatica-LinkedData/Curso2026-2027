# Hands-on assignment 3 – Self assessment

## Checklist

**The "openrefine" directory:**

- [x] Contains a JSON file with the operations performed on the station metadata dataset
- [ ] Contains a JSON file with the operations performed on the air quality measurements dataset

**The "csv" directory:**

- [x] Contains an updated CSV file for the station metadata dataset
- [ ] Contains an updated CSV file for the air quality measurements dataset

**Dataset: 212629-0-estaciones-control-aire-csv.csv (station metadata)**

- [x] Data was imported correctly into OpenRefine (separator: `;`, encoding: UTF-8)
- [x] Redundant columns were removed (LONGITUD_ETRS89, LATITUD_ETRS89, COORDENADA_X_ETRS89, COORDENADA_Y_ETRS89, COD_VIA)
- [x] Pollutant indicator columns (NO2, SO2, CO, PM10, PM2_5, O3, BTX) were transformed from "X"/empty to true/false
- [x] Street columns (VIA_CLASE, VIA_PAR, VIA_NOMBRE) were joined into a single VIA_COMPLETA column and the originals removed
- [x] Date column (Fecha alta) was transformed from dd/MM/yyyy to ISO format yyyy-MM-dd
- [x] Multiple spaces in DIRECCION and VIA_COMPLETA were normalized to single spaces
- [x] Trailing period was removed from DIRECCION (station 40: "Río Grande." → "Río Grande")
- [x] No duplicate rows were found (24 unique station codes, names and coordinates)
- [x] Inconsistencies in abbreviations (C/, Avda., Plaza, Paseo) and separators (esq., -, /) in DIRECCION were identified but not modified, as they come from the original source

**Dataset: calair_tiemporeal.csv (air quality measurements)**

- [x] Data was imported correctly into OpenRefine
- [x] Data was analysed for errors and inconsistencies
- [x] Necessary transformations were applied to facilitate RDF generation
- [x] No duplicate or conflicting rows were found
- [x] A normalized FECHA column was created from ANO, MES and DIA
- [x] Hourly measurement columns (H01-V01 ... H24-V24) were transposed into rows
- [x] HORA, VALOR_MEDICION and ES_VALIDA were generated to obtain one row per hourly observation
- [x] Invalid measurements were identified using VALIDEZ; their placeholder value 0 was replaced by an empty value
- [x] VALOR_MEDICION was converted to numeric values
- [x] A unique ID_OBSERVACION was generated for every hourly observation
- [x] ESTACION codes were normalized into COD_ESTACION with three digits
- [x] PUNTO_MUESTREO and MAGNITUD were checked for consistency and preserved
