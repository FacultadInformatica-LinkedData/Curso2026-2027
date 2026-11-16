package com.example.breathemadrid

import android.Manifest.permission.ACCESS_COARSE_LOCATION
import android.Manifest.permission.ACCESS_FINE_LOCATION
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Looper
import android.os.SystemClock
import androidx.activity.ComponentActivity
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.rememberUpdatedState
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver

internal val mapLocationPermissions = arrayOf(ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION)

internal fun Context.canShowLocation() = mapLocationPermissions.any {
    checkSelfPermission(it) == PackageManager.PERMISSION_GRANTED
}

@Composable
internal fun ObserveMapLocation(
    activity: ComponentActivity,
    granted: Boolean,
    onLocation: (Location?) -> Unit
) {
    val callback = rememberUpdatedState(onLocation)
    DisposableEffect(activity, granted) {
        val manager = activity.getSystemService(LocationManager::class.java)
        var best: Location? = null
        fun accept(location: Location) {
            val current = best
            val age = SystemClock.elapsedRealtimeNanos() - location.elapsedRealtimeNanos
            if (age > 60_000_000_000L) return
            if (current != null && location.elapsedRealtimeNanos - current.elapsedRealtimeNanos < 15_000_000_000L &&
                location.accuracy > current.accuracy
            ) return
            best = location
            callback.value(location)
        }
        val listener = object : LocationListener {
            override fun onLocationChanged(location: Location) = accept(location)
            override fun onProviderDisabled(provider: String) {
                if (!manager.isLocationEnabled) {
                    best = null
                    callback.value(null)
                }
            }
        }
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_START -> if (granted && activity.canShowLocation()) {
                    val precise = activity.checkSelfPermission(ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                    val providers = if (LocationManager.FUSED_PROVIDER in manager.allProviders) {
                        listOf(LocationManager.FUSED_PROVIDER)
                    } else if (precise) {
                        listOf(LocationManager.NETWORK_PROVIDER, LocationManager.GPS_PROVIDER)
                    } else listOf(LocationManager.NETWORK_PROVIDER)
                    providers.filter { it in manager.allProviders }.forEach { provider ->
                        try {
                            manager.requestLocationUpdates(provider, 3_000L, 3f, listener, Looper.getMainLooper())
                        } catch (_: SecurityException) {
                            callback.value(null)
                        }
                    }
                }
                Lifecycle.Event.ON_STOP -> {
                    manager.removeUpdates(listener)
                    best = null
                    callback.value(null)
                }
                else -> Unit
            }
        }
        activity.lifecycle.addObserver(observer)
        onDispose {
            activity.lifecycle.removeObserver(observer)
            manager.removeUpdates(listener)
        }
    }
}
