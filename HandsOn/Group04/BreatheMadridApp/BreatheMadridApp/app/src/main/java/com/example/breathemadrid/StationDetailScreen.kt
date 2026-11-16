package com.example.breathemadrid

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import org.json.JSONObject
import java.time.LocalDateTime
import java.util.Locale
import kotlin.math.ceil

private val detailPollutants = linkedMapOf(
    "8" to "NO₂", "10" to "PM10", "14" to "O₃", "9" to "PM₂.₅",
    "1" to "SO₂", "6" to "CO", "7" to "NO", "12" to "NOₓ",
    "20" to "TOL", "30" to "BEN", "35" to "EBE"
)
private val Available = Color(0xFFE1F1E8)

@Composable
internal fun StationDetailScreen(station: Station, date: String, initialPollutant: String, onBack: () -> Unit) {
    val context = LocalContext.current
    val series = remember(context, station.id) {
        context.assets.open("map/hourly-readings.json").bufferedReader().use {
            JSONObject(it.readText()).optJSONObject(station.id)
        }
    }
    val codes = remember(series, station) {
        val recorded = series?.keys()?.asSequence().orEmpty().toSet() + station.readings.keys
        (detailPollutants.keys.take(4) + detailPollutants.keys.filter { it in recorded } + recorded).distinct()
    }
    var pollutant by rememberSaveable(station.id, initialPollutant) {
        mutableStateOf(initialPollutant.takeIf { it in codes } ?: codes.first())
    }
    val label = detailPollutants[pollutant] ?: station.readings[pollutant]?.label ?: pollutant
    val unit = station.readings[pollutant]?.unit ?: if (pollutant == "6") "mg/m³" else "µg/m³"
    val values = remember(series, pollutant) {
        val hours = series?.optJSONArray(pollutant)
        List(24) { index -> hours?.optDouble(index)?.takeIf { it.isFinite() }?.toFloat() }
    }

    Column(Modifier.fillMaxSize().background(HomeBackground).safeDrawingPadding()) {
        Surface(color = Color.White, shadowElevation = 2.dp) {
            Row(Modifier.fillMaxWidth().padding(end = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onBack, modifier = Modifier.semantics { contentDescription = "Volver" }) {
                    Text("←", color = Ink, style = MaterialTheme.typography.titleLarge)
                }
                Column(Modifier.padding(vertical = 8.dp)) {
                    Text("Detalle: ${station.name}", color = Ink, style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold)
                    Text("Código de estación: ${station.id}", color = Muted, style = MaterialTheme.typography.bodySmall)
                }
            }
        }
        Column(
            Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState())
                .padding(horizontal = 14.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {
                Text(station.address, color = Ink, style = MaterialTheme.typography.bodyMedium)
                Text(String.format(Locale.ROOT, "Coordenadas: %.5f, %.5f", station.lat, station.lon),
                    color = Muted, style = MaterialTheme.typography.bodySmall)
            }
            Row(
                Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                codes.forEach { code ->
                    FilterChip(
                        selected = pollutant == code,
                        onClick = { pollutant = code },
                        label = { Text(detailPollutants[code] ?: station.readings[code]?.label ?: code) },
                        shape = CircleShape,
                        colors = FilterChipDefaults.filterChipColors(selectedContainerColor = Color(0xFFDCEBF6))
                    )
                }
            }
            Text("Tendencia horaria · $label", color = Ink, style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold)
            Text("Mediciones del $date", color = Muted, style = MaterialTheme.typography.bodySmall)
            if (values.any { it != null }) {
                HourlyChart(values, unit)
            } else {
                Surface(color = Color(0xFFEDF0F0), shape = CardShape) {
                    val message = if (series?.has(pollutant) == true || pollutant in station.readings) {
                        "Sin lecturas horarias válidas"
                    } else {
                        "Contaminante sin registros para esta estación"
                    }
                    Text(message, color = Muted,
                        modifier = Modifier.fillMaxWidth().padding(12.dp))
                }
            }
            Text("Lecturas de la estación", color = Ink, style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold)
            Surface(color = Color.White, shape = CardShape, shadowElevation = 2.dp) {
                Column {
                    codes.forEachIndexed { index, code ->
                        if (index > 0) HorizontalDivider(color = Border)
                        val reading = station.readings[code]
                        Column(Modifier.fillMaxWidth()
                            .background(if (reading == null) Color(0xFFEDF0F0) else if (code == pollutant) Available else Color.White)
                            .padding(horizontal = 12.dp, vertical = 8.dp)) {
                            val name = detailPollutants[code] ?: reading?.label ?: code
                            Text("$name: ${reading?.display() ?: "Sin lectura disponible"}",
                                color = if (reading == null) Muted else Ink, fontWeight = FontWeight.SemiBold)
                            if (reading != null) {
                                val observed = LocalDateTime.parse(reading.time).format(readingTimeFormat)
                                Text("$observed · Media horaria", color = Muted, style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }
            }
            Text("Fuente: Datos Abiertos del Ayuntamiento de Madrid", color = Muted,
                style = MaterialTheme.typography.bodySmall)
        }
        Surface(color = Color.White, shadowElevation = 3.dp) {
            Button(
                onClick = {}, enabled = false,
                modifier = Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 4.dp)
            ) {
                Text("Recibir alerta de mejora · Próximamente", textAlign = TextAlign.Center)
            }
        }
    }
}

@Composable
private fun HourlyChart(values: List<Float?>, unit: String) {
    val peak = values.filterNotNull().maxOrNull() ?: return
    val step = if (peak <= 4f) 1f else 5f
    val top = (ceil(peak / (4 * step)) * 4 * step).coerceAtLeast(4 * step)
    val firstHour = values.indexOfFirst { it != null }.coerceAtMost(22)
    val lastHour = values.indexOfLast { it != null }.coerceAtLeast(firstHour + 1)
    val tickHours = (0..3).map { firstHour + (lastHour - firstHour) * it / 3 }.distinct()
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(unit, color = Muted, style = MaterialTheme.typography.labelSmall)
        Row(Modifier.fillMaxWidth().height(124.dp), horizontalArrangement = Arrangement.spacedBy(5.dp)) {
            Column(Modifier.fillMaxHeight().width(32.dp), verticalArrangement = Arrangement.SpaceBetween) {
                (4 downTo 0).forEach { tick ->
                    Text((top * tick / 4).toInt().toString(), color = Muted, style = MaterialTheme.typography.labelSmall)
                }
            }
            Canvas(Modifier.weight(1f).fillMaxHeight().padding(vertical = 7.dp)
                .semantics { contentDescription = "Tendencia horaria con ${values.count { it != null }} lecturas válidas" }) {
                fun point(index: Int, value: Float) = Offset(
                    size.width * (index - firstHour) / (lastHour - firstHour),
                    size.height * (1f - value / top)
                )
                for (tick in 0..4) {
                    val y = size.height * tick / 4
                    drawLine(Border, Offset(0f, y), Offset(size.width, y))
                }
                for (index in firstHour..lastHour) {
                    val current = values[index]?.let { point(index, it) } ?: continue
                    if (index > firstHour) {
                        values[index - 1]?.let { previous ->
                            drawLine(Blue, point(index - 1, previous), current, 2.dp.toPx(), StrokeCap.Round)
                        }
                    }
                    drawCircle(Blue, 2.dp.toPx(), current)
                }
            }
        }
        Row(Modifier.fillMaxWidth().padding(start = 37.dp), horizontalArrangement = Arrangement.SpaceBetween) {
            tickHours.forEach { hour ->
                Text(String.format(Locale.ROOT, "%02d:00", hour + 1), color = Muted,
                    style = MaterialTheme.typography.labelSmall)
            }
        }
    if ((firstHour..lastHour).any { values[it] == null }) {
            Text("Las horas sin lectura se muestran como huecos.", color = Muted,
                style = MaterialTheme.typography.bodySmall)
        }
    }
}
