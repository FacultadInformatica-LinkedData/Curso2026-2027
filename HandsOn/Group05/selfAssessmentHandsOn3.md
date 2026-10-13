# Autoevaluación Entrega 3 Práctica – Grupo05

## Resumen del trabajo realizado.
En esta tercera entrega de la práctica nuestro objetivo era limpiar y preparar el dataset de polideportivos (centros deportivos municipales) del Ayuntamiento de Madrid para facilitar la posterior generación de RDF. Para ello hemos corregido errores de codificación y de formato, normalizado valores, separado información mezclada en algunas celdas y eliminado columnas sin contenido. Todo el proceso se ha realizado con la herramienta OpenRefine.

## Acciones detalladas
1.- Importación: el CSV original (200186-0-polideportivos-csv.csv) se ha importado en OpenRefine con codificación ISO-8859-1 y separador punto y coma (;). Estos ajustes no quedan registrados en el JSON, pero son necesarios para que tildes y eñes se lean correctamente (por ejemplo, "Barceló" o "PEÑA GRANDE").

2.- El texto en NOMBRE ha sido limpiado eliminando los espacios extra (con trim y sustituyendo espacios múltiples por uno solo). La columna DISTRITO se ha normalizado a formato título (con toTitlecase), por ejemplo "MONCLOA-ARAVACA" pasa a "Moncloa-Aravaca".

3.- Las columnas de texto largo (HORARIO, EQUIPAMIENTO, TRANSPORTE, DESCRIPCION y DESCRIPCION-ENTIDAD) contenían entidades HTML doblemente codificadas, como "&amp;iexcl;" o "&amp;ldquo;". Se han decodificado (con unescape("html") aplicado dos veces) y se han eliminado los espacios y saltos de línea sobrantes.

4.- Se han unificado LOCALIDAD (había un valor "Madrid" frente a 81 "MADRID") y PROVINCIA (había una celda vacía, rellenada con "MADRID").

5.- En el centro Pueblo Nuevo el email estaba en la columna FAX y EMAIL estaba vacía. Se ha movido el email a EMAIL y se ha dejado FAX vacío.

6.- La columna EMAIL se ha limpiado para que contenga solo direcciones válidas: se han eliminado textos añadidos (por ejemplo, en La Fundi) y, cuando hay varias direcciones, se separan con punto y coma (;).

7.- TELEFONO y FAX tenían formatos muy distintos ("917 373 641", "91 359 33 39", "Taquilla: 915883465", varios números separados por "/", "-" o saltos de línea). Se han extraído los números de 9 dígitos y se han dejado sin espacios, separados por punto y coma (;) cuando hay más de uno, para poder dividirlos fácilmente al generar el RDF.

8.- COD-DISTRITO y COD-BARRIO se han convertido a enteros. Se han rellenado los códigos que faltaban a partir del barrio: San Andrés (barrio 1, distrito 17 Villaverde) y Ambroz (distrito 19 Vicálvaro).

9.- La columna TIPO contenía una ruta larga repetida ("/contenido/entidadesYorganismos/CentrosEspaciosDeporte/..."). Se ha dejado solo la categoría final (Pabellon, PiscinaVerano, Sauna...), que podrá usarse como clase o tipo en la ontología.

10.- PK, LATITUD y LONGITUD han sido convertidas a números.

11.- Se han eliminado las columnas PUERTA y ESCALERAS, que estaban completamente vacías.

## Problemas conocidos
- El código de barrio de Ambroz (COD-BARRIO) sigue vacío porque no hemos podido confirmar su valor en el callejero oficial.
- En TELEFONO se pierden las etiquetas informativas ("Taquilla", "Oficina", "Por ahora solo WhatsApp"); solo se conservan los números.
- En los textos largos hay palabras partidas que vienen así del original ("p istas", "s ala"). Se han mantenido porque son texto descriptivo y no afectan a la generación de RDF.
- NOMBRE-VIA mezcla nombres con y sin tilde ("DAOÍZ Y VELARDE" frente a "ALCANTARA"), y en un caso TIPO-NUM vale "S/N" aunque hay número. Se han dejado tal como vienen en el dataset original.
- ACCESIBILIDAD puede contener varios códigos separados por comas ("1,5,6"). Se mantiene así y se separará en el mapping RDF.

## Conclusión
Todos los cambios realizados han sido guardados en un nuevo csv: csv/200186-0-polideportivos-updated.csv; y las operaciones han sido almacenadas en un documento JSON: openrefine/history.json. Aplicando ese JSON al CSV original (importado con la codificación y el separador indicados) se obtiene exactamente el CSV entregado. El dataset queda limpio y preparado para la generación de RDF, salvo los problemas conocidos indicados arriba.