# Fuentes espaciales — Proyecto 2

Este archivo documenta las fuentes GIS que se utilizarán para construir el paisaje espacial de Oslo.  
El objetivo es trabajar únicamente con fuentes públicas y verificables, evitando inventar coordenadas o geometrías.

## 1. NINA SPARE — Portal de capas de Oslo

Documentación oficial de capas:

https://ninanor.github.io/SPARE_project/layers.html

La plataforma incluye, entre otras, las siguientes capas relevantes para este proyecto:

### 1.1 Parker — Oslo Kommune, 2018

Descripción: áreas verdes administradas por Bymiljøetaten y los distritos de Oslo.

Uso propuesto:
- representar parques y espacios verdes reales;
- generar posibles `FloralPatch`;
- calcular área, centroides y distancias.

Estado:
- fuente verificada;
- endpoint/API exacto pendiente de localizar.

### 1.2 Egnethet for pollinerende insekter — NINA, 2022

Descripción: capa de idoneidad del hábitat para insectos polinizadores. Representa variación espacial en la disponibilidad temporal de recursos florales y está relacionada con el trabajo de Stange et al. (2017).

Uso propuesto:
- asignar un índice de calidad o aptitud a cada parche;
- apoyar la estimación espacial de disponibilidad floral;
- complementar los datos observados de Dryad.

Importante:
esta capa no sustituye las mediciones de flores del dataset de Dryad. Se utilizará como información espacial complementaria.

Estado:
- fuente verificada;
- endpoint/API exacto pendiente de localizar.

### 1.3 Honningbie frie soner — Oslo Kommune / BYM

Descripción: zonas dentro del área urbana de Oslo donde existen restricciones para mantener abejas melíferas, creadas para reducir competencia con abejas silvestres y otros polinizadores.

Uso propuesto:
- definir zonas donde no se pueden colocar colmenas;
- generar restricciones para el problema de optimización;
- eliminar sitios candidatos inválidos.

Estado:
- fuente verificada;
- endpoint/API exacto pendiente de localizar.

## 2. Miljødirektoratet — Naturvernområder

Servicio ArcGIS FeatureServer:

https://kart3.miljodirektoratet.no/arcgis/rest/services/vern/FeatureServer

Capa principal de polígonos:

https://kart3.miljodirektoratet.no/arcgis/rest/services/vern/FeatureServer/0

Características verificadas:
- geometría: polígonos;
- CRS: EPSG:25833;
- unidades: metros;
- permite consultas GIS;
- admite formatos JSON, GeoJSON y PBF en sus capas.

Uso propuesto:
- identificar áreas naturales protegidas;
- utilizar algunas de estas zonas como restricciones espaciales si corresponde;
- complementar las restricciones para sitios candidatos de colmenas.

## 3. Miljødirektoratet — Restricciones en áreas protegidas

Servicio:

https://kart3.miljodirektoratet.no/arcgis/rest/services/vern_restriksjonsomraader/FeatureServer

CRS:
EPSG:25833.

Nota:
este dataset contiene principalmente restricciones de circulación y aviación. No debe interpretarse automáticamente como una prohibición para colocar colmenas.

Uso:
solo como información espacial complementaria si alguna restricción resulta relevante para el modelo.

## 4. Dryad — Datos ecológicos de Oslo

Los archivos originales están almacenados en:

`data/project2/raw/oslo/`

Archivos:

- `floral_density_data_dryad_version.txt`
- `floral_visitation_data_dryad_version.txt`

Estos datos NO contienen coordenadas geográficas de los traps.

Uso:
- distribución observada de densidad floral;
- especies;
- actividad de polinizadores;
- condiciones meteorológicas observadas;
- calibración y validación del modelo.

No deben inventarse coordenadas para `trap_number`.

## Separación metodológica

El modelo utilizará dos tipos de información:

### Geografía observada
Procedente de capas GIS públicas:
- parques;
- áreas verdes;
- aptitud de hábitat;
- zonas restringidas;
- áreas protegidas.

### Ecología observada
Procedente de Dryad:
- número de flores;
- densidad floral;
- especies;
- actividad de polinizadores;
- clima observado.

Las variables como capacidad floral total, polen, néctar, agotamiento y competencia serán modeladas o derivadas y deberán identificarse explícitamente como tales.

## Estado actual

Verificadas:
- documentación NINA SPARE;
- capa de parques descrita;
- capa de aptitud para polinizadores descrita;
- zonas libres de abejas descritas;
- FeatureServer de áreas protegidas de Miljødirektoratet.

## Endpoints GIS verificados

### Parker — Oslo Kommune, 2018

Feature Layer:

https://services8.arcgis.com/PHc9pAOcTcVH6T4R/arcgis/rest/services/Greenspace/FeatureServer/0

Item ID:

`941ca1ab497f4ce18f56f9d5cc1a4f6f`

Uso:
- polígonos reales de parques/áreas verdes;
- cálculo de área y centroides;
- generación de `FloralPatch`;
- generación inicial de sitios candidatos.

Estado:
- endpoint localizado;
- tipo: `ArcGISFeatureLayer`;
- descargable mediante consultas REST/GeoJSON.

---

### Honningbie frie soner — BYM

Feature Layer:

https://services8.arcgis.com/PHc9pAOcTcVH6T4R/arcgis/rest/services/Honning_Oslobyg/FeatureServer/0

Item ID:

`f138885dbf7244dead9457eec77beb80`

Uso:
- identificar zonas donde no deben colocarse colmenas;
- restricción espacial para los sitios candidatos;
- restricción posterior para RANDOM, GREEDY y NSGA-II.

Estado:
- endpoint localizado;
- tipo: `ArcGISFeatureLayer`;
- descargable mediante consultas REST/GeoJSON.

---

### Egnethet for pollinerende insekter — NINA, 2022

Map Service:

https://tiles.arcgis.com/tiles/PHc9pAOcTcVH6T4R/arcgis/rest/services/Egnethet_for_pollinerende_insekter/MapServer

Item ID:

`e590700234f34f5d8afe35f2ad8b3313`

Uso:
- representar espacialmente la aptitud del hábitat para polinizadores;
- complementar la estimación de calidad de los parches;
- visualizar zonas de mayor y menor idoneidad.

Estado:
- endpoint localizado;
- tipo: `ArcGISTiledMapServiceLayer`;
- no tratar todavía como Feature Layer vectorial;
- pendiente verificar si existe raster descargable o servicio de datos asociado.