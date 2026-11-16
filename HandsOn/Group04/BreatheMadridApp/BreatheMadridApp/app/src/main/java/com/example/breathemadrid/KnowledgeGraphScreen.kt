package com.example.breathemadrid

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch
import java.util.Locale

private const val EmulatorEndpoint = "http://127.0.0.1:3030/breathemadrid/sparql"
private val sections = listOf("Estaciones", "Análisis", "Comparar", "Enlaces")

@Composable
internal fun KnowledgeGraphScreen(targetStationCode: String? = null, onBack: () -> Unit) {
    val typography = MaterialTheme.typography
    MaterialTheme(
        typography = typography.copy(
            bodyLarge = typography.bodyLarge.copy(fontSize = 17.sp, lineHeight = 25.sp),
            bodyMedium = typography.bodyMedium.copy(fontSize = 16.sp, lineHeight = 23.sp),
            bodySmall = typography.bodySmall.copy(fontSize = 14.sp, lineHeight = 20.sp),
            titleMedium = typography.titleMedium.copy(fontSize = 19.sp, lineHeight = 26.sp),
            labelLarge = typography.labelLarge.copy(fontSize = 15.sp, lineHeight = 21.sp)
        )
    ) {
        Surface(color = HomeBackground, contentColor = Ink) {
            KnowledgeGraphContent(targetStationCode, onBack)
        }
    }
}

@Composable
private fun KnowledgeGraphContent(targetStationCode: String?, onBack: () -> Unit) {
    var endpoint by remember { mutableStateOf(EmulatorEndpoint) }
    var loading by remember { mutableStateOf(false) }
    var result by remember { mutableStateOf<GraphResult?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var section by remember { mutableIntStateOf(0) }
    var showQueries by remember { mutableStateOf(false) }
    var showEndpoint by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(targetStationCode) {
        if (targetStationCode != null) {
            loading = true; error = null; result = null
            try { result = SparqlClient(endpoint).load() }
            catch (exception: Exception) { error = exception.message ?: "Error desconocido" }
            finally { loading = false }
        }
    }

    Column(Modifier.fillMaxSize().background(HomeBackground).safeDrawingPadding()) {
        Row(Modifier.fillMaxWidth().background(Accent).padding(horizontal = 8.dp),
            verticalAlignment = Alignment.CenterVertically) {
            TextButton(onClick = onBack) { Text("←", color = Color.White) }
            Text("Datos semánticos", color = Color.White,
                style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        }
        if (showEndpoint) {
            OutlinedTextField(value = endpoint, onValueChange = { endpoint = it; result = null },
                label = { Text("Endpoint SPARQL") },
                supportingText = { Text("Emulador: adb reverse · Móvil: IP local del ordenador") },
                singleLine = true, modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp))
        }
        Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically) {
            Button(onClick = {
                loading = true; error = null; result = null
                scope.launch {
                    try { result = SparqlClient(endpoint).load() }
                    catch (exception: Exception) { error = exception.message ?: "Error desconocido" }
                    finally { loading = false }
                }
            }, enabled = !loading) { Text("Consultar el grafo") }
            if (loading) { Spacer(Modifier.width(12.dp)); CircularProgressIndicator(Modifier.size(24.dp)) }
            Spacer(Modifier.weight(1f))
            TextButton(onClick = { showEndpoint = !showEndpoint }) { Text("Conexión") }
        }
        error?.let { Text("No se pudo consultar el grafo: $it",
            color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(16.dp)) }
        result?.let { graph ->
            if (targetStationCode != null && graph.stations.none { it.code == targetStationCode }) {
                Text("La estación seleccionada no tiene correspondencia en el grafo RDF.",
                    color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(16.dp))
            }
            Column(Modifier.padding(horizontal = 16.dp, vertical = 4.dp)) {
                GraphValue("Estaciones", graph.summary.stations.toString())
                GraphValue("Contaminantes", graph.summary.pollutants.toString())
                GraphValue("Observaciones", graph.summary.observations.toString())
            }
            Text("Datos recibidos de Fuseki. Las otras pantallas usan JSON local del 01/10/2026.",
                modifier = Modifier.padding(horizontal = 16.dp), style = MaterialTheme.typography.bodySmall)
            ScrollableTabRow(selectedTabIndex = section, edgePadding = 8.dp) {
                sections.forEachIndexed { index, label ->
                    Tab(selected = section == index, onClick = { section = index }, text = { Text(label) })
                }
            }
            when (section) {
                0 -> StationExplorer(graph, endpoint, targetStationCode)
                1 -> AnalysisExplorer(graph, endpoint)
                2 -> CompareExplorer(graph, endpoint)
                else -> LinkExplorer(endpoint)
            }
        } ?: run {
            SparqlQueriesButton(
                expanded = showQueries,
                onClick = { showQueries = !showQueries },
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)
            )
            if (showQueries) {
                Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(16.dp)) {
                    SparqlQueryText(GraphQueries.summary)
                }
            }
        }
    }
}

@Composable
private fun GraphValue(label: String, value: String) {
    Text(style = MaterialTheme.typography.bodyMedium, text = buildAnnotatedString {
        append("$label: ")
        pushStyle(SpanStyle(fontWeight = FontWeight.SemiBold))
        append(value)
        pop()
    })
}

@Composable
private fun SparqlQueryText(query: String) {
    Surface(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        shape = MaterialTheme.shapes.small,
        color = Color(0xFFEAF0F4),
        contentColor = Ink
    ) {
        Text(
            query.trimIndent(),
            modifier = Modifier.horizontalScroll(rememberScrollState()).padding(12.dp),
            style = MaterialTheme.typography.bodySmall,
            fontFamily = FontFamily.Monospace
        )
    }
}

@Composable
private fun SparqlQueriesButton(expanded: Boolean, onClick: () -> Unit, modifier: Modifier = Modifier) {
    FilledTonalButton(
        onClick = onClick,
        modifier = modifier.fillMaxWidth().heightIn(min = 48.dp)
    ) {
        Text(
            if (expanded) "Ocultar consultas SPARQL" else "Ver consultas SPARQL",
            fontWeight = FontWeight.SemiBold
        )
    }
}

@Composable
private fun StationExplorer(graph: GraphResult, endpoint: String, targetStationCode: String?) {
    var search by remember { mutableStateOf("") }
    var type by remember { mutableStateOf("Todos") }
    var byCount by remember { mutableStateOf(false) }
    var selected by remember { mutableStateOf<GraphStation?>(null) }
    var detail by remember { mutableStateOf<StationDetail?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }
    var showQuery by remember { mutableStateOf(false) }
    val counts = remember(graph) { graph.validObservationsByStation.associate { it.uri to it.total } }
    val scope = rememberCoroutineScope()
    LaunchedEffect(graph, targetStationCode) {
        val station = graph.stations.singleOrNull { it.code == targetStationCode }
        if (station != null) {
            selected = station; detail = null; error = null; loading = true
            try { detail = SparqlClient(endpoint).stationDetail(station) }
            catch (exception: Exception) { error = exception.message ?: "No se pudo cargar el detalle." }
            finally { loading = false }
        }
    }
    val filtered = remember(graph, search, type, byCount) {
        graph.stations.filter { it.name.contains(search, ignoreCase = true) &&
            (type == "Todos" || it.category == type) }
            .let { if (byCount) it.sortedWith(compareByDescending<GraphStation> { station -> counts[station.uri] ?: 0 }.thenBy { station -> station.name }) else it.sortedBy { station -> station.name } }
    }
    LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        selected?.let { station ->
            item {
                TextButton(onClick = { selected = null; detail = null; error = null }) { Text("← Todas las estaciones") }
                Text(station.name, style = MaterialTheme.typography.titleLarge)
                if (loading) CircularProgressIndicator(Modifier.size(24.dp))
                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
            detail?.let { data ->
                item {
                    SparqlQueriesButton(showQuery, onClick = { showQuery = !showQuery })
                    if (showQuery) {
                        SparqlQueryText(GraphQueries.stationDetail(station.uri))
                        SparqlQueryText(GraphQueries.stationCounts(station.uri))
                    }
                }
                item {
                    Text("Tipo: ${station.category}")
                    Text("Municipio: ${data.municipality ?: "No indicado"}")
                    Text("Coordenadas: ${data.latitude ?: "?"}, ${data.longitude ?: "?"}")
                    GraphValue("Observaciones totales", data.total.toString())
                    GraphValue("Válidas", data.valid.toString())
                    GraphValue("Inválidas", data.invalid.toString())
                    data.seeAlso?.let { ExternalLink(it, "Recurso relacionado (rdfs:seeAlso)") }
                    HorizontalDivider()
                    Text("Contaminantes medidos", fontWeight = FontWeight.Bold)
                }
                items(data.pollutants) { pollutant ->
                    Text("${pollutant.name} · ${pollutant.unit ?: "unidad no indicada"}")
                }
            }
        } ?: run {
            item {
                OutlinedTextField(value = search, onValueChange = { search = it },
                    label = { Text("Buscar estación") }, modifier = Modifier.fillMaxWidth())
                Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    listOf("Todos", "Urbana de tráfico", "Urbana de fondo", "Suburbana").forEach { option ->
                        FilterChip(selected = type == option, onClick = { type = option }, label = { Text(option) })
                    }
                }
                TextButton(onClick = { byCount = !byCount }) {
                    Text(if (byCount) "Orden: observaciones válidas ↓" else "Orden: nombre A–Z")
                }
                graph.validObservationsError?.let { Text("Recuento no disponible: $it", color = MaterialTheme.colorScheme.error) }
                Text("${filtered.size} estaciones", style = MaterialTheme.typography.bodySmall)
            }
            item {
                SparqlQueriesButton(showQuery, onClick = { showQuery = !showQuery })
                if (showQuery) {
                    SparqlQueryText(GraphQueries.summary)
                    SparqlQueryText(GraphQueries.stations)
                    SparqlQueryText(GraphQueries.validObservationsByStation)
                }
            }
            items(filtered, key = { it.uri }) { station ->
                Column(Modifier.fillMaxWidth().clickable {
                    selected = station; detail = null; error = null; loading = true
                    scope.launch {
                        try { detail = SparqlClient(endpoint).stationDetail(station) }
                        catch (exception: Exception) { error = exception.message ?: "No se pudo cargar el detalle." }
                        finally { loading = false }
                    }
                }.padding(vertical = 7.dp)) {
                    Text(station.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                    Text("${station.category} · ${counts[station.uri] ?: 0} observaciones válidas",
                        style = MaterialTheme.typography.bodySmall)
                    HorizontalDivider()
                }
            }
        }
    }
}

@Composable
private fun StationPicker(label: String, stations: List<GraphStation>, selected: GraphStation?, onSelect: (GraphStation) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Box {
        OutlinedButton(onClick = { expanded = true }) { Text("$label: ${selected?.name ?: "Elegir"}") }
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            stations.forEach { station ->
                DropdownMenuItem(text = { Text(station.name) }, onClick = { expanded = false; onSelect(station) })
            }
        }
    }
}

@Composable
private fun PollutantPicker(pollutants: List<GraphPollutant>, selected: GraphPollutant?, onSelect: (GraphPollutant) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Box {
        OutlinedButton(onClick = { expanded = true }) { Text("Contaminante: ${selected?.name ?: "Elegir"}") }
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            pollutants.forEach { pollutant ->
                DropdownMenuItem(text = { Text(pollutant.name) }, onClick = { expanded = false; onSelect(pollutant) })
            }
        }
    }
}

@Composable
private fun AnalysisExplorer(graph: GraphResult, endpoint: String) {
    var station by remember { mutableStateOf<GraphStation?>(null) }
    var detail by remember { mutableStateOf<StationDetail?>(null) }
    var pollutant by remember { mutableStateOf<GraphPollutant?>(null) }
    var analysis by remember { mutableStateOf<MeasurementAnalysis?>(null) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var showQuery by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item {
            Text("Análisis de contaminación", style = MaterialTheme.typography.titleMedium)
            StationPicker("Estación", graph.stations, station) { chosen ->
                station = chosen; detail = null; pollutant = null; analysis = null; error = null; loading = true
                scope.launch {
                    try { detail = SparqlClient(endpoint).stationDetail(chosen) }
                    catch (exception: Exception) { error = exception.message ?: "No se pudo cargar la estación." }
                    finally { loading = false }
                }
            }
            detail?.let { data ->
                PollutantPicker(data.pollutants, pollutant) { chosen ->
                    pollutant = chosen; analysis = null; error = null; loading = true
                    scope.launch {
                        try { analysis = SparqlClient(endpoint).analysis(data.station, chosen) }
                        catch (exception: Exception) { error = exception.message ?: "No se pudo analizar." }
                        finally { loading = false }
                    }
                }
            }
            if (loading) CircularProgressIndicator(Modifier.size(24.dp))
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        }
        analysis?.let { data ->
            item {
                SparqlQueriesButton(showQuery, onClick = { showQuery = !showQuery })
                if (showQuery && station != null && pollutant != null) {
                    SparqlQueryText(GraphQueries.stats(station!!.uri, pollutant!!.uri))
                    SparqlQueryText(GraphQueries.series(station!!.uri, pollutant!!.uri))
                }
            }
            item {
                StatsBlock(data.stats)
                if (data.points.isNotEmpty()) {
                    Text("Serie horaria · ${data.stats.unit ?: "unidad no indicada"}", fontWeight = FontWeight.Bold)
                    TimeSeriesChart(data.points, Modifier.fillMaxWidth().height(190.dp))
                    Text("${data.points.first().dateTime} → ${data.points.last().dateTime}",
                        style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}

@Composable
private fun StatsBlock(stats: MeasurementStats) {
    if (stats.count == 0) { Text("No hay mediciones válidas para esta combinación."); return }
    val unit = stats.unit?.let { " $it" }.orEmpty()
    GraphValue("Mediciones válidas", stats.count.toString())
    GraphValue("Media", stats.average.format() + unit)
    GraphValue("Mínimo", stats.minimum.format() + unit)
    GraphValue("Máximo", stats.maximum.format() + unit)
    Text("Primera: ${stats.first ?: "—"}")
    Text("Última: ${stats.last ?: "—"}")
}

private fun Double?.format(): String = this?.let { String.format(Locale.ROOT, "%.2f", it) } ?: "—"

@Composable
private fun TimeSeriesChart(points: List<MeasurementPoint>, modifier: Modifier = Modifier, other: List<MeasurementPoint> = emptyList()) {
    if (points.isEmpty()) return
    val all = points + other
    val minimum = all.minOf { it.value }
    val maximum = all.maxOf { it.value }
    val span = (maximum - minimum).takeIf { it > 0 } ?: 1.0
    val times = all.map { it.dateTime }.distinct().sorted()
    val first = times.first()
    val last = times.last()
    Canvas(modifier.background(Color.White)) {
        val left = 24.dp.toPx(); val right = size.width - 12.dp.toPx()
        val top = 12.dp.toPx(); val bottom = size.height - 20.dp.toPx()
        drawLine(Color.Gray, Offset(left, top), Offset(left, bottom), 1.dp.toPx())
        drawLine(Color.Gray, Offset(left, bottom), Offset(right, bottom), 1.dp.toPx())
        fun plot(series: List<MeasurementPoint>, color: Color) {
            if (series.isEmpty()) return
            val path = Path()
            series.forEachIndexed { index, point ->
                val fraction = if (first == last) 0.5f else
                    (times.binarySearch(point.dateTime).coerceAtLeast(0).toFloat() / (times.size - 1).coerceAtLeast(1))
                val x = left + (right - left) * fraction
                val y = bottom - (bottom - top) * ((point.value - minimum) / span).toFloat()
                if (index == 0) path.moveTo(x, y) else path.lineTo(x, y)
                drawCircle(color, 3.dp.toPx(), Offset(x, y))
            }
            drawPath(path, color, style = Stroke(width = 2.dp.toPx()))
        }
        plot(points, Color(0xFF3559A6))
        plot(other, Color(0xFFD36A29))
    }
    Text("${minimum.format()} – ${maximum.format()} · ${first.hourLabel()} → ${last.hourLabel()}",
        style = MaterialTheme.typography.bodySmall)
}

private fun String.hourLabel(): String = if (length >= 16) substring(11, 16) else this

@Composable
private fun CompareExplorer(graph: GraphResult, endpoint: String) {
    var first by remember { mutableStateOf<GraphStation?>(null) }
    var second by remember { mutableStateOf<GraphStation?>(null) }
    var firstDetail by remember { mutableStateOf<StationDetail?>(null) }
    var secondDetail by remember { mutableStateOf<StationDetail?>(null) }
    var pollutant by remember { mutableStateOf<GraphPollutant?>(null) }
    var firstAnalysis by remember { mutableStateOf<MeasurementAnalysis?>(null) }
    var secondAnalysis by remember { mutableStateOf<MeasurementAnalysis?>(null) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    val common = remember(firstDetail, secondDetail) {
        val secondUris = secondDetail?.pollutants?.map { it.uri }?.toSet().orEmpty()
        firstDetail?.pollutants?.filter { it.uri in secondUris }.orEmpty()
    }
    LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item {
            Text("Comparar estaciones", style = MaterialTheme.typography.titleMedium)
            StationPicker("Primera", graph.stations, first) { chosen ->
                first = chosen; firstDetail = null; pollutant = null; firstAnalysis = null; secondAnalysis = null; loading = true; error = null
                if (second?.uri == chosen.uri) { second = null; secondDetail = null }
                scope.launch {
                    try { firstDetail = SparqlClient(endpoint).stationDetail(chosen) }
                    catch (exception: Exception) { error = exception.message ?: "Error de estación" }
                    finally { loading = false }
                }
            }
            StationPicker("Segunda", graph.stations.filter { it.uri != first?.uri }, second) { chosen ->
                second = chosen; secondDetail = null; pollutant = null; firstAnalysis = null; secondAnalysis = null; loading = true; error = null
                scope.launch {
                    try { secondDetail = SparqlClient(endpoint).stationDetail(chosen) }
                    catch (exception: Exception) { error = exception.message ?: "Error de estación" }
                    finally { loading = false }
                }
            }
            if (first != null && second != null && common.isEmpty() && !loading && firstDetail != null && secondDetail != null)
                Text("Estas estaciones no comparten contaminantes medidos.")
            if (common.isNotEmpty()) PollutantPicker(common, pollutant) { chosen ->
                pollutant = chosen; firstAnalysis = null; secondAnalysis = null; error = null; loading = true
                scope.launch {
                    try {
                        firstAnalysis = SparqlClient(endpoint).analysis(firstDetail!!.station, chosen)
                        secondAnalysis = SparqlClient(endpoint).analysis(secondDetail!!.station, chosen)
                    } catch (exception: Exception) { error = exception.message ?: "No se pudo comparar." }
                    finally { loading = false }
                }
            }
            if (loading) CircularProgressIndicator(Modifier.size(24.dp))
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        }
        if (firstAnalysis != null && secondAnalysis != null) item {
            val a = firstAnalysis!!; val b = secondAnalysis!!
            Text("${first!!.name} · ${first!!.category}", color = Color(0xFF3559A6), fontWeight = FontWeight.Bold)
            StatsBlock(a.stats)
            Spacer(Modifier.height(8.dp))
            Text("${second!!.name} · ${second!!.category}", color = Color(0xFF9A4519), fontWeight = FontWeight.Bold)
            StatsBlock(b.stats)
            if (a.stats.average != null && b.stats.average != null) {
                Text("Diferencia de medias: ${(a.stats.average - b.stats.average).format()} ${pollutant?.unit ?: ""}")
                Text("Comparación descriptiva; una media menor no demuestra que el aire sea seguro.",
                    style = MaterialTheme.typography.bodySmall)
            }
            if (a.points.map { it.dateTime } != b.points.map { it.dateTime })
                Text("Aviso: las estaciones no tienen mediciones válidas en todas las mismas horas.",
                    color = MaterialTheme.colorScheme.error)
            if (a.points.isNotEmpty() && b.points.isNotEmpty())
                TimeSeriesChart(a.points, Modifier.fillMaxWidth().height(190.dp), b.points)
            Text("Ambas series usan el mismo contaminante y solo observaciones válidas.", style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
private fun LinkExplorer(endpoint: String) {
    var links by remember { mutableStateOf<SemanticLinks?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(endpoint) {
        try { links = SparqlClient(endpoint).links() }
        catch (exception: Exception) { error = exception.message ?: "No se pudieron consultar los enlaces." }
    }
    LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item {
            Text("Enlaces semánticos", style = MaterialTheme.typography.titleMedium)
            Text("owl:sameAs identifica la misma entidad. rdfs:seeAlso señala un recurso relacionado; una estación no es el lugar que comparte su nombre.",
                style = MaterialTheme.typography.bodySmall)
            if (links == null && error == null) CircularProgressIndicator(Modifier.size(24.dp))
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        }
        links?.let { data ->
            item { Text("Contaminantes · owl:sameAs (${data.pollutants.size})", fontWeight = FontWeight.Bold) }
            items(data.pollutants) { link -> SemanticLinkRow(link, "Wikidata") }
            item { Text("Estaciones · rdfs:seeAlso (${data.stations.size})", fontWeight = FontWeight.Bold) }
            items(data.stations) { link -> SemanticLinkRow(link, "recurso relacionado") }
            item {
                Text("Las URIs locales y externas proceden de las consultas SPARQL.", style = MaterialTheme.typography.bodySmall)
                SparqlQueryText(GraphQueries.pollutantLinks)
                SparqlQueryText(GraphQueries.stationLinks)
            }
        }
    }
}

@Composable
private fun SemanticLinkRow(link: SemanticLink, destination: String) {
    var showUris by remember(link.localUri) { mutableStateOf(false) }
    Column {
        Text(link.name, fontWeight = FontWeight.SemiBold)
        ExternalLink(link.externalUri, "Abrir $destination")
        TextButton(onClick = { showUris = !showUris }) {
            Text(if (showUris) "Ocultar URIs" else "Ver URIs")
        }
        if (showUris) {
            Text("BreatheMadrid: ${link.localUri}", style = MaterialTheme.typography.bodySmall)
            Text("Externa: ${link.externalUri}", style = MaterialTheme.typography.bodySmall)
        }
        HorizontalDivider()
    }
}

@Composable
private fun ExternalLink(uri: String, label: String) {
    val context = LocalContext.current
    TextButton(onClick = {
        if (uri.startsWith("http://www.wikidata.org/entity/") || uri.startsWith("https://www.wikidata.org/entity/")) {
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(uri)))
        }
    }) { Text(label) }
}
