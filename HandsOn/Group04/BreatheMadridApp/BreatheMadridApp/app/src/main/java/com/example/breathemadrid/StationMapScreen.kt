package com.example.breathemadrid

import android.location.Location
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import org.json.JSONArray
import org.json.JSONObject
import java.io.Serializable
import java.time.LocalDateTime
import java.util.Locale
internal val Screen = Color(0xFFF2F6F5)
internal val Border = Color(0xFFC6D1CF)
internal val Ink = Color(0xFF17242C)
internal val Muted = Color(0xFF586873)
internal val Blue = Color(0xFF1D5D77)


internal data class MapPoint(val lat: Double, val lon: Double) : Serializable {
    fun distanceTo(station: Station): Float {
        val distance = FloatArray(1)
        Location.distanceBetween(lat, lon, station.lat, station.lon, distance)
        return distance[0] / 1000f
    }
}

internal fun formatDistance(km: Float): String =
    String.format(Locale.forLanguageTag("es-ES"), "%.1f km", km)

private enum class Pollutant(val code: String?, val label: String) {
    ALL(null, "Todos"), NO2("8", "NO₂"), PM10("10", "PM10"), O3("14", "O₃"), PM25("9", "PM₂.₅")
}

@Composable
internal fun StationMapScreen(
    snapshot: AirSnapshot,
    selected: String,
    reference: MapPoint,
    location: MapPoint?,
    onStationSelected: (String) -> Unit,
    onHome: () -> Unit,
    onLocationSelected: (MapPoint) -> Unit,
    onInfo: () -> Unit,
    onAnalyzeRdf: (String) -> Unit,
    onDetails: (String, String) -> Unit
) {
    var pollutant by rememberSaveable { mutableStateOf(Pollutant.ALL) }
    var candidate by rememberSaveable { mutableStateOf<MapPoint?>(null) }
    val activity = LocalContext.current as ComponentActivity
    var granted by remember { mutableStateOf(activity.canShowLocation()) }
    var deviceLocation by remember { mutableStateOf<Location?>(null) }
    var centerRequest by remember { mutableIntStateOf(0) }
    var locateWhenReady by rememberSaveable { mutableStateOf(false) }
    var locationMessage by remember { mutableStateOf<String?>(null) }
    val permissions = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {
        granted = activity.canShowLocation()
        locateWhenReady = granted
        locationMessage = if (granted) null else "Puedes permitir la ubicación en los ajustes de Android."
    }
    ObserveMapLocation(activity, granted) { fix ->
        deviceLocation = fix
        if (fix != null) {
            locationMessage = null
            if (locateWhenReady) {
                centerRequest++
                locateWhenReady = false
            }
        }
    }
    val station = snapshot.stations.firstOrNull { it.id == selected }
    val pin = candidate ?: location
    val stationState = remember(snapshot.stations, selected, pollutant, pin, reference) {
        JSONObject()
            .put("selected", selected)
            .put("showStationNumbers", pollutant == Pollutant.ALL)
            .put("center", JSONArray().put(reference.lat).put(reference.lon))
            .put("pin", pin?.let { JSONArray().put(it.lat).put(it.lon) } ?: JSONObject.NULL)
            .put("stations", JSONArray().apply {
                snapshot.stations.forEach { item ->
                    val reading = pollutant.code?.let(item.readings::get)
                    val label = when {
                        pollutant == Pollutant.ALL -> "Estación ${item.id}"
                        reading != null -> "${pollutant.label}: ${reading.display()}"
                        else -> "${pollutant.label}: sin lectura válida"
                    }
                    put(JSONObject().put("id", item.id).put("name", item.name)
                        .put("lat", item.lat).put("lon", item.lon)
                        .put("value", reading?.display() ?: JSONObject.NULL)
                        .put("label", label))
                }
            })
    }
    val mapState = remember(stationState, deviceLocation, centerRequest) {
        JSONObject()
            .put("stationState", stationState)
            .put("centerRequest", centerRequest)
            .put("device", deviceLocation?.let {
                JSONObject().put("lat", it.latitude).put("lon", it.longitude)
                    .put("accuracy", if (it.hasAccuracy()) it.accuracy.toDouble() else 0.0)
            } ?: JSONObject.NULL)
    }

    Column(Modifier.fillMaxSize().background(HomeBackground).safeDrawingPadding()) {
        Row(
            Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 12.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            Pollutant.entries.forEach { option ->
                FilterChip(
                    selected = pollutant == option,
                    onClick = { pollutant = option },
                    label = { Text(option.label) },
                    shape = androidx.compose.foundation.shape.CircleShape,
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = Accent,
                        selectedLabelColor = Color.White
                    )
                )
            }
        }
        Box(Modifier.weight(1f).fillMaxWidth()) {
            MadridMap(
                mapState,
                onStationSelected = { candidate = null; onStationSelected(it) },
                onPointSelected = { candidate = it },
                modifier = Modifier.fillMaxSize()
            )
            FilledIconButton(
                onClick = {
                    granted = activity.canShowLocation()
                    when {
                        !granted -> permissions.launch(mapLocationPermissions)
                        deviceLocation != null -> centerRequest++
                        else -> {
                            locateWhenReady = true
                            locationMessage = "Buscando ubicación. Comprueba que esté activada en Android."
                        }
                    }
                },
                modifier = Modifier.align(Alignment.TopEnd).padding(10.dp)
                    .semantics { contentDescription = "Centrar en mi ubicación" },
                colors = IconButtonDefaults.filledIconButtonColors(containerColor = Color.White, contentColor = Accent)
            ) { Text("◎", style = MaterialTheme.typography.headlineSmall) }
            locationMessage?.let { message ->
                Surface(Modifier.align(Alignment.TopStart).padding(start = 10.dp, top = 10.dp, end = 68.dp),
                    shape = CardShape, color = Color.White, shadowElevation = 2.dp) {
                    Text(message, Modifier.padding(8.dp), style = MaterialTheme.typography.bodySmall, color = Ink)
                }
            }
        }
        Surface(shape = CardShape, color = Color.White, shadowElevation = 3.dp) {
            Column(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(3.dp)) {
                val point = candidate
                if (point != null) {
                    Text("Ubicación elegida", fontWeight = FontWeight.Bold, color = Ink)
                    Text(String.format(Locale.ROOT, "%.5f, %.5f", point.lat, point.lon),
                        style = MaterialTheme.typography.bodySmall, color = Muted)
                    MapAction("Usar esta ubicación") {
                        candidate = null
                        onLocationSelected(point)
                    }
                } else if (station != null) {
                    Text("${station.name} · ${formatDistance(reference.distanceTo(station))}",
                        fontWeight = FontWeight.Bold, color = Ink)
                    Text(station.address, style = MaterialTheme.typography.bodySmall, color = Muted)
                    val pollutants = if (pollutant == Pollutant.ALL) {
                        listOf(Pollutant.NO2, Pollutant.PM10, Pollutant.O3)
                    } else listOf(pollutant)
                    Text(pollutants.joinToString("   ·   ") { item ->
                        "${item.label}: ${station.readings[item.code]?.display() ?: "sin lectura válida"}"
                    }, style = MaterialTheme.typography.bodySmall, color = Ink)
                    val reading = pollutant.code?.let(station.readings::get)
                    val date = reading?.let { LocalDateTime.parse(it.time).format(readingTimeFormat) } ?: snapshot.date
                    Text("Datos históricos · $date", style = MaterialTheme.typography.bodySmall, color = Muted)
                    MapAction("Ver detalle de la estación") {
                        onDetails(station.id, pollutant.code ?: "14")
                    }
                    MapAction("Analizar datos RDF") { onAnalyzeRdf(station.id) }
                }
                Text("Toca el mapa para elegir una ubicación.", style = MaterialTheme.typography.bodySmall, color = Muted)
            }
        }
        HomeNavigation(mapSelected = true, onHome = onHome, onMap = {}, onInfo = onInfo)
    }
}

@Composable
private fun MapAction(label: String, onClick: () -> Unit) {
    Button(onClick, Modifier.fillMaxWidth(), colors = ButtonDefaults.buttonColors(containerColor = Blue)) {
        Text(label)
    }
}
