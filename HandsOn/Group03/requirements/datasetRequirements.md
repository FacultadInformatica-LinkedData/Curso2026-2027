# Dataset requirements

https://datos.madrid.es/dataset/208327-0-transporte-bicicletas-bicimad

## License 
This dataset operates under the Creative Commons Attribution 4.0 International (CC BY 4.0) license.
The entity in charge of the dataset is Empresa Municipal de Transportes, S.A. 

## Entity linking

## {Our dataset -> Other datasets}
- Address: This column gives us standard street-level data, allowing us to map our records to external geographic databases, cadastral registries or official city maps.

- Name: follows a predictable  {Number - Landmark} format. We can resolve our stations against external knowledge graphs such as Wikidata

## {Other datasets -> Our dataset}
- POINT_X and POINT_Y: These columns act as coordinates. External datasets may use these coordinates to establish spatial relationships, for example, to identify entities that fall within a certain radius of our stations.