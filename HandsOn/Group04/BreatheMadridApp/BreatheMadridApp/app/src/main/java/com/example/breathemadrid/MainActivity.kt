package com.example.breathemadrid

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.saveable.rememberSaveableStateHolder
import androidx.compose.runtime.setValue
import androidx.activity.enableEdgeToEdge
import com.example.breathemadrid.ui.theme.BreatheMadridTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.light(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT),
            navigationBarStyle = SystemBarStyle.light(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT)
        )
        setContent {
            BreatheMadridTheme(darkTheme = false, dynamicColor = false) {
                val snapshot = rememberAirSnapshot()
                var showMap by rememberSaveable { mutableStateOf(false) }
                var showInfo by rememberSaveable { mutableStateOf(false) }
                var showKnowledgeGraph by rememberSaveable { mutableStateOf(false) }
                var targetStationCode by rememberSaveable { mutableStateOf<String?>(null) }
                var selected by rememberSaveable { mutableStateOf("4") }
                var zoneId by rememberSaveable { mutableStateOf("49") }
                var homeStationId by rememberSaveable { mutableStateOf<String?>(null) }
                var location by rememberSaveable { mutableStateOf<MapPoint?>(null) }
                var activity by rememberSaveable { mutableStateOf(OutdoorActivity.RUN) }
                var detailId by rememberSaveable { mutableStateOf<String?>(null) }
                var detailPollutant by rememberSaveable { mutableStateOf("14") }
                val screenState = rememberSaveableStateHolder()
                val detailStation = snapshot.stations.firstOrNull { it.id == detailId }
                val zone = snapshot.stations.firstOrNull { it.id == zoneId } ?: snapshot.stations.first()
                val reference = location ?: MapPoint(zone.lat, zone.lon)
                BackHandler(enabled = showInfo || showKnowledgeGraph || showMap || detailStation != null) {
                    when {
                        showKnowledgeGraph -> { showKnowledgeGraph = false; targetStationCode = null }
                        showInfo -> showInfo = false
                        detailId != null -> detailId = null
                        else -> showMap = false
                    }
                }
                if (showKnowledgeGraph) {
                    KnowledgeGraphScreen(targetStationCode) {
                        showKnowledgeGraph = false
                        targetStationCode = null
                    }
                } else if (showInfo) {
                    InformationScreen(snapshot.date) { showInfo = false }
                } else if (detailStation != null) {
                    StationDetailScreen(detailStation, snapshot.date, detailPollutant) { detailId = null }
                } else if (showMap) {
                    screenState.SaveableStateProvider("map") {
                        StationMapScreen(snapshot, selected, reference, location, { selected = it }, { showMap = false }, {
                            location = it
                            homeStationId = null
                            showMap = false
                        }, onInfo = { showInfo = true }, onAnalyzeRdf = { id ->
                            targetStationCode = officialStationCode(id) ?: id
                            showKnowledgeGraph = true
                        }) { id, code ->
                            selected = id
                            detailPollutant = code
                            detailId = id
                        }
                    }
                } else {
                    screenState.SaveableStateProvider("home") {
                        HomeScreen(snapshot, zone, location, activity, homeStationId, {
                            zoneId = it
                            location = null
                            homeStationId = null
                        }, { activity = it }, {
                            selected = snapshot.stations.minBy { reference.distanceTo(it) }.id
                            showMap = true
                        }, onInfo = { showInfo = true }, onKnowledgeGraph = {
                            targetStationCode = null
                            showKnowledgeGraph = true
                        }) { id ->
                            zoneId = id
                            location = null
                            homeStationId = id
                        }
                    }
                }
            }
        }
    }
}
