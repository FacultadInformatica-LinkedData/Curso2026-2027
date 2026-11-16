package com.example.breathemadrid

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.time.LocalDateTime
import kotlinx.coroutines.launch
import org.json.JSONObject

internal val HomeBackground = Color(0xFFF8F8F7)
internal val Accent = Color(0xFF176DA4)
private val Outline = Color(0xFFDADDDD)
internal val CardShape = RoundedCornerShape(12.dp)
private val homePollutants = listOf("8" to "NO₂", "10" to "PM10", "14" to "O₃")

internal enum class OutdoorActivity(val label: String) {
    RUN("Correr"), BIKE("Ir en bicicleta"), WALK("Caminar")
}

@Composable
internal fun HomeScreen(
    snapshot: AirSnapshot,
    zone: Station,
    location: MapPoint?,
    activity: OutdoorActivity,
    selectedStationId: String?,
    onZoneSelected: (String) -> Unit,
    onActivitySelected: (OutdoorActivity) -> Unit,
    onOpenMap: () -> Unit,
    onInfo: () -> Unit,
    onKnowledgeGraph: () -> Unit,
    onStationSelected: (String) -> Unit
) {
    var zonesOpen by remember { mutableStateOf(false) }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()
    val zones = remember(snapshot.stations) {
        snapshot.stations.distinctBy { it.district }.sortedBy { it.district }
    }
    val nearby = remember(snapshot.stations, zone, location) {
        val reference = location ?: MapPoint(zone.lat, zone.lon)
        snapshot.stations.map { it to reference.distanceTo(it) }.sortedBy { it.second }
    }
    val summaryStation = snapshot.stations.firstOrNull { it.id == selectedStationId }
        ?: nearby.firstOrNull { (station, _) -> station.readings.isNotEmpty() }?.first
    val context = LocalContext.current
    val hourly = remember(context) {
        context.assets.open("map/hourly-readings.json").bufferedReader().use { JSONObject(it.readText()) }
    }
    val advice = remember(summaryStation, hourly) {
        summaryStation?.let { historicalAdvice(it, hourly.optJSONObject(it.id)) }
    }

    Column(Modifier.fillMaxSize().background(HomeBackground).safeDrawingPadding()) {
        LazyColumn(
            Modifier.weight(1f).fillMaxWidth(),
            state = listState,
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            item {
                Text("BreatheMadrid", color = Ink, fontSize = 23.sp, fontWeight = FontWeight.Bold)
                TextButton(onClick = onKnowledgeGraph) {
                    Text("Datos semánticos · SPARQL", fontSize = 16.sp)
                }
            }
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.weight(1f)) {
                        val shape = RoundedCornerShape(6.dp)
                        Row(
                            Modifier.fillMaxWidth().clip(shape).border(1.dp, Outline, shape)
                                .clickable(role = Role.Button) { zonesOpen = true }
                                .heightIn(min = 48.dp).padding(horizontal = 12.dp, vertical = 5.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(Modifier.weight(1f)) {
                                Text("Selecciona tu zona", fontSize = 11.sp, color = Muted)
                                Text(if (location == null) "${zone.district}, Madrid" else "Ubicación elegida",
                                    fontSize = 14.sp, color = Ink)
                            }
                            Text("▾", color = Ink, modifier = Modifier.padding(start = 8.dp))
                        }
                        DropdownMenu(expanded = zonesOpen, onDismissRequest = { zonesOpen = false }) {
                            zones.forEach { candidate ->
                                DropdownMenuItem(text = { Text(candidate.district) }, onClick = {
                                    onZoneSelected(candidate.id)
                                    zonesOpen = false
                                })
                            }
                        }
                    }
                    Box(
                        Modifier.size(48.dp).clip(RoundedCornerShape(8.dp)).background(Color(0xFFDBEAF7))
                            .semantics { contentDescription = "Abrir mapa" }
                            .clickable(role = Role.Button, onClick = onOpenMap),
                        contentAlignment = Alignment.Center
                    ) { HomeIcon("Mapa", Accent) }
                }
            }
            item {
                Text("Actividad al aire libre", color = Ink, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                Row(
                    Modifier.fillMaxWidth().selectableGroup().padding(top = 4.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    OutdoorActivity.entries.forEach { option ->
                        val active = activity == option
                        Box(
                            Modifier.weight(1f).heightIn(min = 44.dp).clip(CircleShape)
                                .background(if (active) Accent else Color.White)
                                .border(1.dp, if (active) Accent else Outline, CircleShape)
                                .selectable(active, role = Role.RadioButton) { onActivitySelected(option) }
                                .padding(horizontal = 6.dp, vertical = 8.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(option.label, color = if (active) Color.White else Ink,
                                fontSize = 13.sp, textAlign = TextAlign.Center)
                        }
                    }
                }
            }
            item {
                val categoryColor = when (advice?.category) {
                    0, 1 -> Color(0xFF187540)
                    2 -> Color(0xFF865A00)
                    3, 4 -> Color(0xFFA32F30)
                    5 -> Color(0xFF69438D)
                    else -> Muted
                }
                ElevatedCard(
                    modifier = Modifier.fillMaxWidth(),
                    shape = CardShape,
                    colors = CardDefaults.elevatedCardColors(containerColor = Color.White)
                ) {
                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            ActivityIcon(activity, categoryColor)
                            Column(Modifier.weight(1f)) {
                                Text("Calidad del aire", color = Ink, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                                Text(advice?.let { adviceCategories[it.category] } ?: "Datos insuficientes",
                                    color = categoryColor, fontSize = 23.sp, lineHeight = 25.sp,
                                    fontWeight = FontWeight.Bold)
                            }
                        }
                        if (advice != null) {
                            val time = advice.time.format(readingTimeFormat)
                            Text(activity.adviceFor(advice.category), color = Ink, fontSize = 13.sp, lineHeight = 17.sp)
                            Text("Evaluación parcial del $time · ${summaryStation?.name.orEmpty()}",
                                color = Muted, fontSize = 11.sp, lineHeight = 14.sp)
                            Text(advice.pollutants.joinToString(" · "), color = Muted, fontSize = 11.sp,
                                lineHeight = 14.sp)
                        } else {
                            summaryStation?.let { Text(it.name, color = Muted, fontSize = 12.sp) }
                            Text("Sin datos suficientes para orientar sobre esta actividad.",
                                color = Muted, fontSize = 13.sp)
                        }
                    }
                }
            }
            item {
                Text("Estaciones cercanas", color = Ink, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                Text(if (location == null) "Ordenadas por distancia al punto de referencia de ${zone.district}."
                    else "Ordenadas por distancia a la ubicación elegida.",
                    color = Muted, fontSize = 12.sp)
            }
            items(nearby, key = { it.first.id }) { (station, distance) ->
                HomeStationCard(station, distance, station.id == summaryStation?.id) {
                    onStationSelected(station.id)
                    scope.launch { listState.scrollToItem(0) }
                }
            }
        }
        HomeNavigation(mapSelected = false, onHome = {}, onMap = onOpenMap, onInfo = onInfo)
    }
}

@Composable
private fun ActivityIcon(activity: OutdoorActivity, color: Color) {
    Canvas(Modifier.size(36.dp)) {
        val unit = size.width / 24
        fun point(x: Int, y: Int) = Offset(x * unit, y * unit)
        fun limb(x1: Int, y1: Int, x2: Int, y2: Int) {
            drawLine(color, point(x1, y1), point(x2, y2), 2.2f * unit, StrokeCap.Round)
        }
        when (activity) {
            OutdoorActivity.RUN -> {
                drawCircle(color, 2.3f * unit, point(16, 4))
                limb(13, 8, 10, 14)
                limb(13, 8, 17, 12)
                limb(17, 12, 21, 12)
                limb(13, 8, 8, 8)
                limb(8, 8, 5, 11)
                limb(10, 14, 15, 17)
                limb(15, 17, 13, 22)
                limb(10, 14, 7, 18)
                limb(7, 18, 3, 18)
            }
            OutdoorActivity.BIKE -> {
                drawCircle(color, 4f * unit, point(5, 17), style = Stroke(1.5f * unit))
                drawCircle(color, 4f * unit, point(19, 17), style = Stroke(1.5f * unit))
                drawCircle(color, 2f * unit, point(15, 4))
                limb(12, 7, 8, 11)
                limb(8, 11, 12, 14)
                limb(12, 14, 11, 18)
                limb(12, 7, 16, 10)
                limb(16, 10, 18, 10)
                limb(18, 10, 19, 17)
            }
            OutdoorActivity.WALK -> {
                drawCircle(color, 2.3f * unit, point(13, 4))
                limb(12, 8, 11, 14)
                limb(12, 8, 8, 11)
                limb(8, 11, 7, 15)
                limb(12, 8, 16, 13)
                limb(16, 13, 19, 13)
                limb(11, 14, 8, 22)
                limb(11, 14, 15, 18)
                limb(15, 18, 16, 22)
            }
        }
    }
}

@Composable
internal fun HomeNavigation(mapSelected: Boolean, onHome: () -> Unit, onMap: () -> Unit, onInfo: () -> Unit) {
    HorizontalDivider(color = Outline)
    NavigationBar(containerColor = Color.White, windowInsets = WindowInsets(0, 0, 0, 0)) {
        NavigationBarItem(selected = !mapSelected, onClick = onHome, icon = { HomeIcon("Inicio", Accent) }, label = { Text("Inicio") })
        NavigationBarItem(selected = mapSelected, onClick = onMap, icon = { HomeIcon("Mapa", Accent) }, label = { Text("Mapa") })
        NavigationBarItem(selected = false, onClick = onInfo, icon = { HomeIcon("Información", Accent) }, label = { Text("Información") })
    }
}

@Composable
private fun HomeStationCard(station: Station, distance: Float, isSelected: Boolean, onSelect: () -> Unit) {
    val primary = homePollutants.firstOrNull { (code, _) -> station.readings[code] != null } ?: homePollutants.first()
    val reading = station.readings[primary.first]
    val distanceLabel = formatDistance(distance)
    ElevatedCard(
        onClick = onSelect,
        modifier = Modifier.fillMaxWidth().semantics { selected = isSelected },
        shape = CardShape,
        colors = CardDefaults.elevatedCardColors(containerColor = Color.White)
    ) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Text("${station.name} · $distanceLabel", color = Ink, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
            if (isSelected) {
                Text("Estación de referencia", color = Accent, fontSize = 12.sp)
            }
            Text("${primary.second}: ${reading?.display() ?: "Sin lectura válida"}",
                color = Blue, fontSize = 21.sp, fontWeight = FontWeight.Bold)
            if (reading != null) {
                Text("Lectura histórica · ${LocalDateTime.parse(reading.time).format(readingTimeFormat)}",
                    color = Muted, fontSize = 12.sp)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                homePollutants.filter { it != primary }.forEach { (code, label) ->
                    val other = station.readings[code]
                    Text("$label: ${other?.display() ?: "—"}", color = Ink, fontSize = 12.sp,
                        modifier = Modifier.background(Color(0xFFEDF2F4), CircleShape)
                            .padding(horizontal = 8.dp, vertical = 3.dp))
                }
            }
            Text("Fuente: Datos Abiertos Madrid", color = Muted, fontSize = 11.sp)
            Text("Las mediciones corresponden a la estación.",
                color = Muted, fontSize = 11.sp)
        }
    }
}

@Composable
private fun HomeIcon(label: String, color: Color) {
    Canvas(Modifier.size(20.dp)) {
        val unit = size.width / 24
        fun point(x: Int, y: Int) = Offset(x * unit, y * unit)
        val path = Path()
        when (label) {
            "Inicio" -> {
                path.moveTo(2 * unit, 11 * unit)
                path.lineTo(12 * unit, 3 * unit)
                path.lineTo(22 * unit, 11 * unit)
                path.lineTo(19 * unit, 11 * unit)
                path.lineTo(19 * unit, 21 * unit)
                path.lineTo(5 * unit, 21 * unit)
                path.lineTo(5 * unit, 11 * unit)
                path.close()
                drawPath(path, color)
            }
            "Mapa" -> {
                path.moveTo(12 * unit, 22 * unit)
                path.cubicTo(9 * unit, 19 * unit, 4 * unit, 13 * unit, 4 * unit, 10 * unit)
                path.cubicTo(4 * unit, 0f, 20 * unit, 0f, 20 * unit, 10 * unit)
                path.cubicTo(20 * unit, 13 * unit, 15 * unit, 19 * unit, 12 * unit, 22 * unit)
                drawPath(path, color, style = Stroke(2 * unit))
                drawCircle(color, 2.5f * unit, point(12, 10))
            }
            else -> {
                drawCircle(color, 9 * unit, style = Stroke(2 * unit))
                drawCircle(color, unit, point(12, 7))
                drawLine(color, point(12, 10), point(12, 17), 2 * unit)
            }
        }
    }
}
