# Floral resource availability and honeybee flower visitations in Oslo, Norway

[https://doi.org/10.5061/dryad.9kd51c5qk](https://doi.org/10.5061/dryad.9kd51c5qk)

The dataset contains locality level floral resource estimates for 100 sites in Oslo, Norway, and pollinator visitation events observed at the same localities.

## Description of the data and file structure

The project includes the following data files, all of which use the string "N/A" to indicate missing or non-recorded values:

#### floral\_visitation\_data.txt
This tab-delimited text file includes observations of flying and sitting pollinators along transects in urban areas in Oslo, Norway. It contains data columns with the following headers:

| Column header | Description |
| ------------- | ----------- |
| trap\_number | a unique identifier for the locality |
| inventory\_date | the date on which observations were made |
| observer1 | initials of the primary observer on the transect |
| observer2 | initials of the secondary observer on the transect (if present) |
| observation\_start | time at which survey began |
| observation\_end | time at which survey ended |
| temperature | air temperature during survey |
| sky\_cover | estimate of cloud cover during survey |
| wind | wind conditions during survey |
| rain | precipitation during survey |
| additional\_comments | comments about site, proximity of honeybee hives, and observations made |
| pollinator\_species\_latin | scientific name of the pollinator observed |
| sex | sex of the pollinator observed |
| individuals\_flying | number of individuals observed flying in the transect area |
| individuals\_sitting | number of individuals observed sitting in the transect area |
| plant\_species\_latin | scientific name of the plant on which the pollinator was seated (if pollinator was sitting) |


#### floral\_density\_data.txt
This tab-delimited text file includes quantitative inventories of plants occurring along transects in urban areas in Oslo, Norway. It contains data columns with the following headers:

| Column header | Description |
| ------------- | ----------- |
| trap\_number | a unique identifier for the locality |
| inventory\_date | the date on which observations were made |
| plant\_species\_latin | scientific name of the blooming plant observed |
| flower\_number | number of flowers observed |
| transect\_width\_cm | width of transect in cm |
| transect\_length\_m | length of transect in m |
| comments | additional comments about the transect and observations |


Fuente:
Dryad Digital Repository

Dataset:
Floral resource availability and honeybee flower visitations in Oslo, Norway

DOI:
10.5061/dryad.9kd51c5qk

Licencia:
CC0 1.0 Universal (Public Domain Dedication)

Uso en este proyecto:
Los archivos originales se conservan sin modificaciones en `raw/oslo/`.
Los datos procesados o derivados se almacenan en `data/project2/processed/`.