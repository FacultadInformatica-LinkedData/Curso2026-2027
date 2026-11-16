const mapElement = document.getElementById('map');
function sizeMap() {
    mapElement.style.height = window.innerHeight + 'px';
}
sizeMap();
const map = L.map('map', { zoomControl: false, minZoom: 7, maxZoom: 19 })
    .setView([40.431, -3.689], 10);
window.addEventListener('resize', () => {
    sizeMap();
    map.invalidateSize({ pan: false });
});
L.control.zoom({ position: 'bottomright', zoomInTitle: 'Acercar', zoomOutTitle: 'Alejar' }).addTo(map);
const regionControl = L.control({ position: 'bottomleft' });
regionControl.onAdd = () => {
    const button = L.DomUtil.create('button', 'region-control');
    button.type = 'button';
    button.textContent = 'Ver la Comunidad';
    L.DomEvent.disableClickPropagation(button);
    button.addEventListener('click', () => map.fitBounds([[39.88, -4.58], [41.17, -3.04]]));
    return button;
};
regionControl.addTo(map);

const tileStatus = document.getElementById('tile-status');
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19
}).on('tileerror', () => { tileStatus.hidden = false; })
  .on('tileload', () => { tileStatus.hidden = true; })
  .addTo(map);

const districts = L.geoJSON(null, {
    interactive: false,
    style: { color: '#476f7e', opacity: .55, weight: 1, fillOpacity: .03 }
}).addTo(map);
fetch('districts.geojson').then(response => response.json()).then(data => districts.addData(data))
    .catch(error => console.warn('No se pudieron cargar los límites municipales', error));

const markerLayer = L.layerGroup().addTo(map);
const deviceLayer = L.layerGroup().addTo(map);
let renderedStations = '';
let centeredRequest = 0;
let initialized = false;
map.on('click', ({ latlng }) => {
    window.location.href = '/point/' + latlng.lat + '/' + L.Util.wrapNum(latlng.lng, [-180, 180]);
});

window.renderStations = function ({ stationState, device, centerRequest }) {
    const stationKey = JSON.stringify(stationState);
    if (stationKey !== renderedStations) {
        renderStationMarkers(stationState);
        renderedStations = stationKey;
    }
    deviceLayer.clearLayers();
    if (device) {
        const point = [device.lat, device.lon];
        if (device.accuracy > 0) {
            L.circle(point, {
                radius: device.accuracy, stroke: false, fillColor: '#1686eb',
                fillOpacity: 0.14, interactive: false
            }).addTo(deviceLayer);
        }
        L.circleMarker(point, {
            radius: 8, color: 'white', weight: 3, fillColor: '#1686eb',
            fillOpacity: 1, interactive: false
        }).addTo(deviceLayer).bringToFront();
        if (centerRequest !== centeredRequest) {
            centeredRequest = centerRequest;
            map.setView(point, Math.max(13, map.getZoom()));
        }
    }
};

function renderStationMarkers(state) {
    markerLayer.clearLayers();
    state.stations.forEach(station => {
        const badge = document.createElement('span');
        badge.textContent = state.showStationNumbers ? station.id : (station.value ?? '—');
        const icon = L.divIcon({
            className: 'station-marker' + (station.id === state.selected ? ' is-selected' : '')
                + (!state.showStationNumbers && station.value === null ? ' no-reading' : ''),
            html: badge,
            iconSize: station.value === null ? [30, 28] : [76, 28],
            iconAnchor: station.value === null ? [15, 14] : [38, 14]
        });
        const label = station.name + ', ' + station.label;
        const marker = L.marker([station.lat, station.lon], {
            icon, title: label, alt: label, zIndexOffset: station.id === state.selected ? 1000 : 0
        }).addTo(markerLayer);
        marker.getElement().setAttribute('aria-label', label);
        marker.on('click', () => { window.location.href = '/select/' + encodeURIComponent(station.id); });
    });
    if (state.pin) {
        L.circleMarker(state.pin, {
            radius: 7, color: 'white', weight: 3, fillColor: '#874be0', fillOpacity: 1, interactive: false
        }).bindTooltip('Punto elegido', { permanent: true, direction: 'bottom' }).addTo(markerLayer);
    }
    if (!initialized) {
        initialized = true;
        map.setView(state.center, 12);
    }
}
