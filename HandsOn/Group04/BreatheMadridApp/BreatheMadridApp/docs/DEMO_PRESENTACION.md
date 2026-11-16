# Demo de BreatheMadrid: SPARQL en Android

## Preparación (antes de presentar)

Desde la raíz del proyecto Android, con Docker Desktop y el emulador iniciados:

```powershell
docker compose up -d --build
.\scripts\demo-check.ps1
.\gradlew.bat :app:installDebug
```

El comprobador debe mostrar `[OK]` para Docker, Fuseki, endpoint, consultas, ADB, dispositivo y túnel. Configura `adb reverse tcp:3030 tcp:3030` si falta. Si ya está instalada la APK reciente, no hace falta repetir `installDebug`. Abre **BreatheMadrid** en el emulador. La URL inicial de la pantalla semántica es `http://127.0.0.1:3030/breathemadrid/sparql`.

## Recorrido de unos 60 segundos

1. Desde Inicio, pulsa **Datos semánticos · SPARQL** y **Consultar el grafo**. Señala 24 estaciones, 11 contaminantes y 3.024 observaciones.
2. Pulsa **Arturo Soria**. Muestra tipo, municipio, coordenadas, contaminantes y recuentos 96/72/24.
3. En **Análisis**, selecciona **Arturo Soria** y **NO₂**. Muestra las 18 mediciones válidas, media 14,33 µg/m3 y la gráfica horaria.
4. Abre **Ver consultas SPARQL** y señala `bm:observedAt`, `bm:observesPollutant`, `bm:isValid true` y `AVG`.
5. Si queda tiempo, entra en **Enlaces** y señala un `owl:sameAs` a Wikidata. Explica: «Android manda la consulta HTTP a Fuseki. Fuseki consulta nuestro RDF y devuelve SPARQL Results JSON; Kotlin lo transforma en los datos que vemos en Compose».

## Alcance real

Solo **Datos semánticos** consulta Fuseki en directo. Inicio, mapa, detalle, gráficas y recomendaciones usan JSON incluidos en la APK: una instantánea histórica del 1 de octubre de 2026 con 23 estaciones con lecturas y 2.203 lecturas válidas. El grafo completo conserva 24 estaciones y 3.024 observaciones, incluidas las inválidas. La app no convierte esas observaciones históricas en datos actuales. Mantuvimos el resto de la app sin cambios para preservar las pantallas que ya funcionaban.

## Preguntas breves

**¿Cómo utiliza la aplicación el knowledge graph?** La pantalla Datos semánticos consulta Fuseki para listar estaciones, ver detalles, calcular estadísticas, dibujar series, comparar estaciones y explorar enlaces. Las demás pantallas todavía usan JSON local.

**¿Qué aporta SPARQL frente a archivos JSON?** Permite consultar clases y relaciones del grafo, por ejemplo unir observaciones con estaciones y contar solo las válidas, sin preparar un JSON distinto para cada pregunta.

**¿Dónde se ejecutan las consultas?** En Apache Jena Fuseki, en el ordenador. Android envía las consultas por HTTP y recibe SPARQL Results JSON.

**¿Cómo se relacionan estaciones y observaciones?** Cada observación usa `bm:observedAt` para apuntar a su estación. La consulta sigue esa relación y agrupa por estación.

**¿Por qué algunas pantallas usan datos locales?** Eran funcionalidades existentes basadas en la instantánea JSON. La integración SPARQL se añadió como sección demostrable sin reescribir el mapa ni las gráficas.

**¿Qué ocurre si Fuseki no está disponible?** Datos semánticos muestra un error de conexión y no inventa resultados. Las pantallas locales siguen funcionando.

## Si falla la demo

- **Docker no disponible:** abre Docker Desktop y espera a que arranque el motor Linux; repite `docker compose up -d --build`.
- **Fuseki no está activo:** ejecuta `docker compose up -d --build`; para ver la causa, `docker compose logs fuseki`.
- **Recuentos incorrectos:** comprueba la ruta RDF de `compose.yaml`, ejecuta `docker compose restart fuseki` y luego `.\scripts\verify-sparql.ps1`.
- **Emulador sin conexión:** comprueba `adb devices` y ejecuta `adb reverse tcp:3030 tcp:3030`; vuelve a pulsar **Consultar el grafo**.
- **No hay tiempo para reparar:** enseña el RDF y las consultas en el repositorio y explica el error observado. No presentes las pantallas JSON como una consulta SPARQL.

El servicio es local; no hay endpoint público ni datos en tiempo real del Ayuntamiento. En un móvil por Wi-Fi, hay que cambiar la URL por la IP local del ordenador y permitir el puerto 3030 en el firewall.
