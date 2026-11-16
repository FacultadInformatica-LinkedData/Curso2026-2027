# BreatheMadrid: Android y knowledge graph

## Arquitectura

La pantalla **Datos semánticos** envía consultas HTTP POST a Apache Jena Fuseki. Fuseki carga una sola serialización del grafo real del grupo, `airquality-with-links.ttl`, y responde en SPARQL Results JSON. Kotlin interpreta los resultados y Compose muestra resumen, estaciones, detalles, estadísticas, series temporales, comparaciones y enlaces externos. No se carga también el archivo N-Triples porque contiene los mismos datos. El comportamiento completo del explorador se documenta en [SEMANTIC_EXPLORER.md](SEMANTIC_EXPLORER.md).

Inicio, Mapa, Detalle y Recomendaciones siguen leyendo `stations.json` y `hourly-readings.json` incluidos en Android. Son una instantánea histórica del 1 de octubre de 2026: 23 estaciones con registros y 2.203 lecturas válidas. El RDF completo tiene 24 estaciones, 11 contaminantes y 3.024 observaciones, también las inválidas. La pantalla semántica nunca sustituye una respuesta fallida por datos JSON locales.

En el mapa, **Analizar datos RDF** abre directamente el detalle semántico de la estación elegida. El `id` corto del JSON (por ejemplo, `16`) se convierte en el código oficial (`28079016`); la consulta SPARQL devuelve ese código junto con la URI RDF (`http://breathemadrid.es/resource/station/arturo-soria`). Se comprobó que las 23 estaciones del mapa tienen correspondencia única en el grafo. Si falta una correspondencia, el explorador lo indica sin elegir otra estación. La pantalla de destino consulta Fuseki y el botón de volver regresa al mapa.

## Iniciar Fuseki y actualizar los datos

Se necesita Docker Desktop con el motor Linux activo. Desde la raíz de BreatheMadrid, ejecutar:

    docker compose up -d --build
    .\scripts\demo-check.ps1

Endpoint del ordenador: `http://localhost:3030/breathemadrid/sparql`. Fuseki carga el grafo al arrancar en modo solo lectura. El Dockerfile descarga la distribución oficial de Apache Jena Fuseki 6.2.0 y comprueba su SHA-256.

Compose carga `data/airquality.ttl`, la versión incluida del RDF de Group04. Las consultas de mediciones funcionan con ese archivo. La demo de enlaces de contaminantes y estaciones que se describe abajo requiere `airquality-with-links.ttl`. Para usarlo, configura `BREATHEMADRID_RDF` con su ruta y vuelve a ejecutar `docker compose up -d`. Para cargar de nuevo un Turtle modificado en la misma ruta:

    docker compose restart fuseki
    .\scripts\verify-sparql.ps1

Para detenerlo: `docker compose down`. El servidor se publica en el puerto 3030 de la máquina local para permitir la demo desde un teléfono en la misma red. No se ha desplegado públicamente; usar solo una red de confianza.

## Ejecutar Android y configurar la URL

Con el emulador arrancado, ejecutar `scripts/demo-check.ps1`: comprueba Docker, Fuseki, el endpoint, los resultados y ADB; configura `adb reverse tcp:3030 tcp:3030` si falta. Después, abrir el proyecto en Android Studio y ejecutar la variante debug. La URL inicial `http://127.0.0.1:3030/breathemadrid/sparql` llega al ordenador mediante ese túnel ADB; sin él, `localhost` dentro de Android se refiere al propio dispositivo. El campo de URL se despliega con **Conexión**. En un teléfono físico conectado por USB también se puede usar `adb reverse`. Para usarlo por Wi-Fi sin ADB, editar el campo y sustituir `127.0.0.1` por la IP local del ordenador. El ordenador y el móvil deben estar en la misma red y el firewall debe permitir el puerto 3030. En este equipo, la ruta habitual del emulador `10.0.2.2` no alcanzó el puerto publicado por Docker; el túnel ADB sí funcionó.

Solo la variante debug permite HTTP local sin TLS mediante `app/src/debug/AndroidManifest.xml`. Una versión desplegada públicamente necesitaría HTTPS y control de acceso. La URL se puede modificar desde la pantalla y no contiene credenciales.

## Consultas SPARQL

Las consultas están en `GraphQueries` dentro de `SparqlClient.kt`. Las iniciales cuentan individuos, listan estaciones con sus subclases y cuentan observaciones válidas por estación. Las adicionales recuperan detalles, agregan mediciones válidas con `COUNT/AVG/MIN/MAX`, obtienen series horarias y exploran `owl:sameAs` y `rdfs:seeAlso`. Los identificadores usados en `VALUES` se validan como URIs de recursos locales; la búsqueda textual se aplica en memoria. Las consultas usadas se pueden inspeccionar desde la pantalla.

Se usa `airquality-with-links.ttl` porque sus propiedades `bm:` coinciden con las consultas y mappings de los hands-on 4 y 5. La versión `airquality-updated.ttl` reutiliza otras propiedades, como `schema:name`; no se mezclan ambas versiones.

## Verificaciones

- `docker compose up -d --build` inició Fuseki con el Turtle del grupo.
- Las consultas de resumen, detalle, estadísticas, serie y enlaces respondieron con SPARQL Results JSON.
- La consulta de resumen devolvió 24 estaciones, 11 contaminantes y 3.024 observaciones.
- La consulta de estaciones devolvió 24 filas con nombre, URI y tipo.
- `scripts/verify-sparql.ps1` comprueba esos valores, las 2.203 observaciones válidas repartidas entre 23 estaciones, un detalle, una serie y los enlaces externos.
- `scripts/demo-check.ps1` comprueba Docker, Fuseki, el endpoint, las consultas y ADB, y prepara el túnel si falta.
- `:app:assembleDebug` y `:app:testDebugUnitTest` terminaron correctamente.
- La APK se instaló en el emulador Pixel 7. Con `adb reverse`, se comprobaron el resumen 24/11/3024, el detalle de Arturo Soria, su análisis NO₂, una comparación y los enlaces externos. La consulta se pudo repetir y el regreso a Inicio funcionó.
- Se retiró temporalmente el túnel ADB: la pantalla mostró un error explícito, sin resultados locales de sustitución. Se restauró el túnel y la consulta volvió a funcionar.

## Limitaciones y guion de demo (60–90 segundos)

El endpoint es local. Si está apagado o inaccesible, la pantalla semántica muestra un error; las demás pantallas siguen funcionando con sus JSON. El RDF corresponde al 1 de octubre de 2026: consultar el grafo ahora no convierte esas mediciones en datos actuales.
Si falla únicamente la tercera consulta, el resumen y el listado permanecen visibles y se muestra un error en el recuento por estación.

Antes de la presentación, iniciar Fuseki y ejecutar `scripts/demo-check.ps1` con el emulador arrancado. En Android, pulsar **Datos semánticos · SPARQL** y **Consultar el grafo**. Mostrar 24/11/3024; seleccionar Arturo Soria y ver su detalle; en **Análisis**, elegir Arturo Soria + NO₂ y mostrar sus 18 puntos. Abrir **Ver consultas SPARQL** y señalar `bm:observedAt`, `bm:observesPollutant` y `bm:isValid true`. En **Enlaces**, mostrar un `owl:sameAs` de Wikidata. Explicación breve: «Android consulta Fuseki, que lee nuestro RDF y devuelve SPARQL JSON. Las otras pantallas muestran una instantánea local».
