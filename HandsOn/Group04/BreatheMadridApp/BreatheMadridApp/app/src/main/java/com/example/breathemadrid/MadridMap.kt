package com.example.breathemadrid

import android.annotation.SuppressLint
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import org.json.JSONObject

private const val AssetHost = "appassets.androidplatform.net"
private const val MapUrl = "https://$AssetHost/index.html"

@SuppressLint("SetJavaScriptEnabled")
@Composable
internal fun MadridMap(
    state: JSONObject,
    onStationSelected: (String) -> Unit,
    onPointSelected: (MapPoint) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val currentSelection = rememberUpdatedState(onStationSelected)
    val currentPointSelection = rememberUpdatedState(onPointSelected)
    val mapView = remember(context) {
        WebView(context).apply {
            settings.javaScriptEnabled = true
            settings.allowFileAccess = false
            settings.allowContentAccess = false
            settings.userAgentString += " BreatheMadrid/1.0"
        }
    }
    val stateJson = state.toString()
    val currentState = rememberUpdatedState(stateJson)
    DisposableEffect(mapView) {
        mapView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? {
                val url = request.url
                if (url.scheme != "https" || url.host != AssetHost) return null
                if (url.path != "/districts.geojson") return null
                return WebResourceResponse("application/geo+json", "UTF-8", context.assets.open("map/districts.geojson"))
            }

            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url
                if (url.scheme == "https" && url.host == AssetHost &&
                    url.pathSegments.size == 2 && url.pathSegments.first() == "select"
                ) {
                    currentSelection.value(url.pathSegments.last())
                } else if (url.scheme == "https" && url.host == AssetHost &&
                    url.pathSegments.size == 3 && url.pathSegments.first() == "point"
                ) {
                    val lat = url.pathSegments[1].toDoubleOrNull()
                    val lon = url.pathSegments[2].toDoubleOrNull()
                    if (lat != null && lon != null && lat in -90.0..90.0 && lon in -180.0..180.0) {
                        currentPointSelection.value(MapPoint(lat, lon))
                    }
                } else if (url.toString() == "https://www.openstreetmap.org/copyright") {
                    val browser = android.content.Intent(android.content.Intent.ACTION_VIEW, url)
                    runCatching { context.startActivity(browser) }
                }
                return true
            }

            override fun onPageFinished(view: WebView, url: String) {
                view.renderStations(currentState.value)
            }
        }
        fun asset(name: String) = context.assets.open("map/$name").bufferedReader().use { it.readText() }
        val styles = "<style>" + asset("leaflet.css") + "\n" + asset("map.css") + "</style>"
        val scripts = "<script>" + asset("leaflet.js") + "\n" + asset("map.js") + "</script>"
        val page = asset("index.html").replace("<!-- styles -->", styles).replace("<!-- scripts -->", scripts)
        mapView.loadDataWithBaseURL(MapUrl, page, "text/html", "UTF-8", null)
        onDispose { mapView.destroy() }
    }
    AndroidView(factory = { mapView }, modifier = modifier, update = { it.renderStations(stateJson) })
}

private fun WebView.renderStations(state: String) {
    evaluateJavascript("window.renderStations?.($state)", null)
}
