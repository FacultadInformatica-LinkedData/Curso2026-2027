package com.example.breathemadrid

import org.json.JSONObject
import java.time.LocalDateTime

internal data class HistoricalAdvice(val time: LocalDateTime, val category: Int, val pollutants: List<String>)

internal val adviceCategories = listOf(
    "Buena", "Razonablemente buena", "Regular", "Desfavorable",
    "Muy desfavorable", "Extremadamente desfavorable"
)

private data class AdviceBand(val code: String, val label: String, val hours: Int, val limits: List<Int>)

private val bands = listOf(
    AdviceBand("8", "NO₂", 1, listOf(40, 90, 120, 230, 340, 1000)),
    AdviceBand("1", "SO₂", 1, listOf(100, 200, 350, 500, 750, 1250)),
    AdviceBand("14", "O₃", 8, listOf(50, 100, 130, 240, 380, 800)),
    AdviceBand("10", "PM10", 24, listOf(20, 40, 50, 100, 150, 1200)),
    AdviceBand("9", "PM₂.₅", 24, listOf(10, 20, 25, 50, 75, 800))
)

internal fun historicalAdvice(station: Station, series: JSONObject?): HistoricalAdvice? {
    val time = station.readings.values.maxOfOrNull { LocalDateTime.parse(it.time) } ?: return null
    // The CSV hours run from H01 to H24. H24 ends at midnight the next day.
    val hour = if (time.hour == 0) 24 else time.hour
    val categories = bands.mapNotNull { band ->
        val average = if (band.hours == 1) {
            station.readings[band.code]?.takeIf { LocalDateTime.parse(it.time) == time }?.value?.toDoubleOrNull()
        } else {
            if (hour < band.hours) return@mapNotNull null
            val readings = series?.optJSONArray(band.code) ?: return@mapNotNull null
            val window = (hour - band.hours until hour).map { index ->
                readings.optDouble(index).takeIf { it.isFinite() && it >= 0 } ?: return@mapNotNull null
            }
            window.average()
        }
        if (average == null || !average.isFinite() || average < 0) return@mapNotNull null
        val category = band.limits.indexOfFirst { average <= it }
        if (category == -1) null else band.label to category
    }
    return HistoricalAdvice(time, categories.maxOfOrNull { it.second } ?: return null, categories.map { it.first })
}

internal fun OutdoorActivity.adviceFor(category: Int): String = when (category) {
    0, 1 -> when (this) {
        OutdoorActivity.RUN -> "Condiciones favorables para correr al aire libre."
        OutdoorActivity.BIKE -> "Condiciones favorables para ir en bicicleta al aire libre."
        OutdoorActivity.WALK -> "Condiciones favorables para caminar al aire libre."
    }
    2 -> when (this) {
        OutdoorActivity.RUN -> "Si corres, vigila cómo te sientes. Si eres sensible a la contaminación, reduce la duración o la intensidad."
        OutdoorActivity.BIKE -> "Si vas en bicicleta, vigila cómo te sientes. Si eres sensible, elige un recorrido corto y suave."
        OutdoorActivity.WALK -> "Puedes caminar a ritmo suave. Si eres sensible, evita los paseos largos o enérgicos."
    }
    3 -> when (this) {
        OutdoorActivity.RUN -> "Acorta la carrera y baja el ritmo. Si eres sensible, plantéate hacerla en interiores."
        OutdoorActivity.BIKE -> "Evita las salidas largas o intensas. Si eres sensible, plantéate posponer la salida."
        OutdoorActivity.WALK -> "Si sales a caminar, haz un paseo corto y suave. Si eres sensible, plantéate posponerlo."
    }
    else -> "Conviene posponer esta actividad al aire libre o hacerla en interiores."
}
