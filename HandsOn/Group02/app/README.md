# Madrid Green Spaces — Aplicación web (Grupo 02)

Aplicación web local, basada en **Python + RDFLib + SPARQL**. Usa el grafo de conocimiento `parks-with-links-updated.ttl` de Grupo 02.


## Ejecutar en Windows

python -m pip install -r requirements.txt
python app.py


Abre **http://127.0.0.1:5000** en el navegador mientras el terminal sigue ejecutando el servidor.
Para detenerlo pulsa `Ctrl+C`.

## Funcionalidades

1. Buscar parques por nombre y filtrar por distrito (Todos por defecto).
2. Consultar el número de parques en cada distrito.
3. Consultar los enlaces `owl:sameAs` de parques con Wikidata.
4. Mostrar las fichas de parques con enlaces al Ayuntamiento de Madrid.
