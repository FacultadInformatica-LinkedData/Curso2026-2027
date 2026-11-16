package com.example.breathemadrid

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import org.json.JSONObject
import java.time.LocalDate
import java.time.format.DateTimeFormatter

internal data class Reading(val value: String, val label: String, val unit: String, val time: String) {
    fun display() = "${value.replace('.', ',')} $unit"
}

internal data class Station(
    val id: String,
    val name: String,
    val address: String,
    val district: String,
    val lat: Double,
    val lon: Double,
    val readings: Map<String, Reading>
)

internal data class AirSnapshot(val stations: List<Station>, val date: String)

internal val readingTimeFormat = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm")

@Composable
internal fun rememberAirSnapshot(): AirSnapshot {
    val context = LocalContext.current
    val dataset = remember(context) {
        context.assets.open("map/stations.json").bufferedReader().use { JSONObject(it.readText()) }
    }
    val stations = remember(dataset) {
        val entries = dataset.getJSONArray("stations")
        List(entries.length()) { index ->
            val item = entries.getJSONObject(index)
            val readings = item.getJSONObject("readings")
            Station(
                item.getString("id"), item.getString("name"), item.getString("address"),
                item.getString("district"), item.getDouble("lat"), item.getDouble("lon"),
                readings.keys().asSequence().associateWith { key ->
                    val reading = readings.getJSONObject(key)
                    Reading(reading.getString("value"), reading.getString("label"),
                        reading.getString("unit"), reading.getString("time"))
                }
            )
        }
    }
    val date = LocalDate.parse(dataset.getJSONArray("dates").getString(0))
    return AirSnapshot(stations, date.format(DateTimeFormatter.ofPattern("dd/MM/yyyy")))
}
