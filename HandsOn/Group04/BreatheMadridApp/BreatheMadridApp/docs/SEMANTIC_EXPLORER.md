# Explorador semántico de BreatheMadrid

## Qué hace

La pantalla **Datos semánticos** envía consultas SPARQL HTTP POST a Apache Jena Fuseki, que carga `airquality-with-links.ttl`. Kotlin interpreta SPARQL Results JSON en `GraphResult`, `StationDetail`, `MeasurementAnalysis` y `SemanticLinks`. Compose presenta cuatro pestañas. Ninguna de estas vistas utiliza los JSON de la app como fuente de resultados semánticos.

- **Estaciones:** las 24 estaciones provienen de `bm:Station`, `bm:stationName` y las tres subclases. Los recuentos válidos se obtienen de `bm:Observation` + `bm:observedAt` + `bm:isValid true`. Búsqueda, filtro y ordenación se realizan sobre esos resultados recibidos del endpoint.
- **Detalle:** consulta coordenadas, municipio (`bm:locatedIn`), contaminantes medidos (`bm:measuresPollutant`), total/válidas/inválidas y `rdfs:seeAlso`. Ejemplo verificado: Arturo Soria, 96 observaciones, 72 válidas y 24 inválidas.
- **Análisis:** el usuario elige una estación y uno de sus contaminantes. SPARQL calcula `COUNT`, `AVG`, `MIN` y `MAX` sobre observaciones válidas con `bm:value`, además de la primera y última `bm:dateTime`. Una segunda consulta trae la serie ordenada para la gráfica Compose. Para Arturo Soria + NO₂: 18 puntos, media 14,33, mínimo 6, máximo 32 µg/m3.
- **Comparar:** selecciona dos estaciones distintas y un contaminante presente en ambas. Ejecuta las mismas consultas de estadísticas y serie para cada una, muestra la diferencia de medias y avisa si las horas con datos válidos no coinciden. Es una comparación descriptiva; no concluye que el aire sea seguro.
- **Enlaces:** consulta 11 enlaces `owl:sameAs` de contaminantes y 21 `rdfs:seeAlso` de estaciones. Cada fila muestra el nombre, permite desplegar la URI local y la externa, y abrir Wikidata. `sameAs` afirma identidad; `seeAlso` solo apunta a un recurso relacionado.

Los identificadores de estación y contaminante usados en las consultas proceden de los recursos previamente seleccionados en el grafo. `SparqlClient` comprueba el patrón de URI local antes de insertarla en una cláusula `VALUES`; el texto libre de búsqueda nunca se concatena a SPARQL. Las peticiones y el parseo se ejecutan en `Dispatchers.IO`, con tiempos máximos de conexión y lectura. La UI muestra carga, ausencia de resultados y errores. Si falla la consulta opcional de recuentos por estación, el resumen y el listado siguen visibles.

## Gráfica y límites de los datos

La gráfica nueva está dibujada con `Canvas`, sin dependencias adicionales. El eje horizontal sigue el orden de `xsd:dateTime` y el vertical la concentración; se muestra la unidad del contaminante y las horas inicial y final. Para comparar, las dos series comparten el mismo eje temporal y escala. No se trazan mediciones inválidas ni se inventan puntos para las horas ausentes.

Capturas reales del emulador: [listado de estaciones](screenshots/semantic-overview.png) y [análisis de Arturo Soria + NO₂](screenshots/semantic-analysis.png).

El RDF contiene observaciones históricas del 1 de octubre de 2026, no datos actuales. Las pantallas antiguas —inicio, mapa, detalle, gráficas y recomendaciones— siguen usando `stations.json` y `hourly-readings.json`. Solo el explorador semántico consulta Fuseki. La vista depende de un servidor local y del túnel ADB en el emulador. No hay consulta federada a Wikidata; los enlaces externos ya presentes en el RDF son suficientes para la demo sin depender de Internet externo.

**Riesgo de presentación:** en este equipo, una segunda apertura del emulador con ventana quedó bloqueada al arrancar; el emulador sin ventana volvió a funcionar y todas las consultas pasaron. Antes de clase, abre Pixel 7 desde Android Studio y comprueba que la ventana responde. Si no aparece, reinicia el emulador desde Device Manager y vuelve a ejecutar `scripts/demo-check.ps1`. Las capturas de abajo proceden de ejecuciones reales de la APK, no de un diseño simulado.

## Ejecutar y comprobar

Desde la raíz del proyecto Android, con Docker Desktop y el emulador arrancados:

```powershell
docker compose up -d --build
.\scripts\demo-check.ps1
.\gradlew.bat :app:assembleDebug :app:testDebugUnitTest
```

El verificador ejecuta consultas reales y comprueba 24/11/3024, 2.203 observaciones válidas en 23 estaciones, el detalle de Arturo Soria, una serie NO₂ de 18 puntos y los 11/21 enlaces externos. `demo-check.ps1` comprueba también Docker, Fuseki, ADB y el túnel `tcp:3030` (lo configura si falta). Instala o ejecuta la variante debug en Android Studio. La URL inicial en Android es `http://127.0.0.1:3030/breathemadrid/sparql`, accesible por `adb reverse`.

## Verificación realizada

Se verificaron directamente las consultas contra Fuseki y se compiló la APK con los tests Android. En el emulador se comprobó el listado y detalle de Arturo Soria, el análisis NO₂ (18 puntos), la comparación de Escuelas Aguirre con Arturo Soria y la lista de enlaces. La comparación mostró 15 frente a 18 mediciones NO₂ y medias 8,33 frente a 14,33 µg/m3. Se comprobó también que el endpoint devuelve cero mediciones válidas para una combinación de la estación Urb. Embajada. El manejo de fallo de conexión ya se había probado retirando temporalmente `adb reverse`.

No se han modificado el RDF, la ontología, los CSV ni las pantallas antiguas. No se ha desplegado el endpoint públicamente.
