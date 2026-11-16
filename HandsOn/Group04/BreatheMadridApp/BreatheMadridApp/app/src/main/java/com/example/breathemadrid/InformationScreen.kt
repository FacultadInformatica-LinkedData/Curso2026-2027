package com.example.breathemadrid

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

@Composable
internal fun InformationScreen(snapshotDate: String, onClose: () -> Unit) {
    val links = LocalUriHandler.current
    Column(Modifier.fillMaxSize().background(Accent).safeDrawingPadding()) {
        Row(Modifier.fillMaxWidth().heightIn(min = 56.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onClose, modifier = Modifier.semantics { contentDescription = "Volver" }) {
                Text("‹", style = MaterialTheme.typography.headlineMedium, color = Color.White)
            }
            Text("Información y metodología", color = Color.White,
                style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        }
        Column(
            Modifier.weight(1f).fillMaxWidth().background(HomeBackground)
                .verticalScroll(rememberScrollState()).padding(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            InfoSection("Origen de los datos") {
                InfoText("Las mediciones proceden del Portal de Datos Abiertos del Ayuntamiento de Madrid. " +
                    "Esta versión usa una copia local de las observaciones del $snapshotDate.")
            }
            InfoSection("Índice Nacional de Calidad del Aire") {
                InfoText("Referencia del MITECO. El índice asigna a la estación la categoría menos favorable " +
                    "entre los contaminantes evaluados.")
                InfoText("Concentraciones en µg/m³")
                IndexTable()
                InfoText("NO₂ y SO₂ usan la media de 1 hora. O₃ usa la media móvil de 8 horas. " +
                    "PM10 y PM₂.₅ usan la media móvil de 24 horas. Estas bandas describen la calidad " +
                    "del aire a corto plazo y los límites legales se consultan por separado.")
                TextButton(
                    onClick = { links.openUri("https://www.boe.es/buscar/doc.php?id=BOE-A-2020-10426") },
                    contentPadding = PaddingValues(0.dp)
                ) { Text("Consultar la metodología del BOE", color = Accent) }
            }
            InfoSection("Recomendaciones y actividades") {
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    OutdoorActivity.entries.forEach { activity ->
                        Text(activity.label, color = Color(0xFF125F36), style = MaterialTheme.typography.labelMedium,
                            modifier = Modifier.background(Color(0xFFDDF1E4), RoundedCornerShape(20.dp))
                                .padding(horizontal = 9.dp, vertical = 5.dp))
                    }
                }
                InfoText("Inicio adapta el consejo a la actividad elegida y a la categoría menos favorable " +
                    "de los contaminantes que se pueden evaluar a la hora indicada. Usa ventanas completas " +
                    "para las medias móviles y muestra qué contaminantes entraron en la evaluación parcial.")
                InfoText("La orientación corresponde a la fecha y hora de la instantánea. Para saber cómo está " +
                    "el aire hoy, consulta las observaciones actuales.")
            }
            InfoSection("Cálculo de distancias") {
                InfoText("Las estaciones se ordenan por distancia en línea recta desde el punto elegido en el mapa " +
                    "o desde el punto de referencia de la zona. Cada lectura corresponde a su estación.")
            }
        }
        TextButton(onClick = onClose, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
            Text("Cerrar", color = Color.White, fontWeight = FontWeight.SemiBold)
        }
    }
}

@Composable
private fun InfoSection(title: String, content: @Composable ColumnScope.() -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(title, color = Ink, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        content()
    }
}

@Composable
private fun InfoText(text: String) {
    Text(text, color = Ink, style = MaterialTheme.typography.bodySmall)
}

@Composable
private fun IndexTable() {
    val bands = listOf(
        Triple("Buena", listOf("0–40", "0–20", "0–50"), Color(0xFFCEF0F3)),
        Triple("Razonablemente buena", listOf("41–90", "21–40", "51–100"), Color(0xFFDDF1E4)),
        Triple("Regular", listOf("91–120", "41–50", "101–130"), Color(0xFFFFF1BF)),
        Triple("Desfavorable", listOf("121–230", "51–100", "131–240"), Color(0xFFF9D9CB)),
        Triple("Muy desfavorable", listOf("231–340", "101–150", "241–380"), Color(0xFFF0C6CC)),
        Triple("Extremadamente desfavorable", listOf("341–1000", "151–1200", "381–800"), Color(0xFFE8D9F6))
    )
    Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(6.dp))) {
        IndexRow("Categoría", listOf("NO₂", "PM10", "O₃"), Accent, Color.White)
        bands.forEach { (label, ranges, color) -> IndexRow(label, ranges, color, Ink) }
    }
}

@Composable
private fun IndexRow(label: String, values: List<String>, background: Color, foreground: Color) {
    Row(Modifier.fillMaxWidth().background(background).padding(horizontal = 6.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically) {
        Text(label, modifier = Modifier.weight(1.8f), color = foreground,
            style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.SemiBold)
        values.forEach { value ->
            Text(value, modifier = Modifier.weight(1f), textAlign = TextAlign.Center,
                color = foreground, style = MaterialTheme.typography.labelSmall)
        }
    }
}
