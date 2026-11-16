"use strict";

const SOURCES = {
  bicimad: "BiciMAD",
  callejero: "Callejero",
  wikidata: "Wikidata",
  osrm: "OSRM",
  user: "Tú",
  local: "RDF local",
};
const GROUPS = { street: "Calles · Callejero", place: "Lugares · Wikidata", station: "Estaciones · BiciMAD" };
const SOL = [40.416775, -3.70379];
const EXAMPLES = ["Bravo Murillo 120", "Museo del Prado", "un parque", "Agustín de Foxá"];
const EXPLORE_EXAMPLES = ["Museo del Prado", "Alcalá", "un parque", "Metro Sol"];

// mode: "route" (origen y destino) o "explore" (estaciones cerca de un lugar, FR2).
// center es el lugar elegido en el campo de Explorar; explore, la última respuesta de
// /api/explore junto con el lugar que se pidió (explore.place).
const state = {
  mode: "route", from: null, to: null, plan: null, shown: null, whyOpen: false,
  center: null, radius: 500, explore: null,
};

const $ = (selector, root = document) => root.querySelector(selector);
const results = $("#results");

// ---------- utilidades ----------

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

// HTML ya construido por html`…`: es lo único que una plantilla inserta sin escapar.
class SafeHtml {
  constructor(text) { this.text = text; }
  toString() { return this.text; }
}

// Plantilla que escapa por defecto: html`<b>${nombre}</b>` escapa nombre. Para insertar HTML hay
// que construirlo con otra plantilla html`…` (por ejemplo, badge()). Las listas se insertan
// seguidas y null o undefined no insertan nada.
function html(strings, ...values) {
  const insert = (value) => {
    if (value instanceof SafeHtml) return value.text;
    if (Array.isArray(value)) return value.map(insert).join("");
    return esc(value);
  };
  return new SafeHtml(strings.reduce((out, text, i) => out + insert(values[i - 1]) + text));
}

function badge(source, text) {
  return html`<span class="badge ${source}">${text ?? SOURCES[source] ?? source}</span>`;
}

function minutes(seconds) {
  const m = Math.round(seconds / 60);
  if (m < 1) return "<1 min";
  return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${m % 60} min`;
}

// Única función de formato de distancias del frontend: «1,2 km» o, por debajo del kilómetro, en
// metros redondeados a la decena. Es la misma regla que geocode._distance_label en Python, que la
// usa en los textos que monta el servidor (las sugerencias de «un parque»).
function distanceLabel(meters) {
  return meters >= 1000 ? `${(meters / 1000).toFixed(1).replace(".", ",")} km` : `${Math.round(meters / 10) * 10} m`;
}

function https(url) {
  return url ? url.replace(/^http:\/\//, "https://") : url;
}

async function api(path, params = {}) {
  const url = new URL(path, location.origin);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) url.searchParams.set(key, value);
  }
  let response;
  try {
    response = await fetch(url);
  } catch {
    throw new Error("No se ha podido conectar con el servidor. Comprueba que BiciSmart sigue en marcha.");
  }
  // Un fallo inesperado del servidor (un 500 en texto plano, por ejemplo) no trae JSON.
  const json = response.headers.get("content-type")?.includes("application/json");
  const body = json ? await response.json().catch(() => undefined) : undefined;
  if (!response.ok) {
    const detail = typeof body?.detail === "string" ? body.detail : null;
    throw new Error(detail ?? `El servidor no ha podido atender la petición (error ${response.status}).`);
  }
  if (body === undefined) throw new Error("La respuesta del servidor no tiene el formato esperado.");
  return body;
}

// Avisos bajo el formulario. El de las estaciones del mapa (slot "stations") se queda fijo delante
// de los demás (descarga de Wikidata, ubicación), que se sustituyen unos a otros.
const statusMessages = { stations: "", current: "" };

function showStatus(text, slot = "current") {
  statusMessages[slot] = text;
  const status = $("#status");
  status.textContent = Object.values(statusMessages).filter(Boolean).join(" ");
  status.hidden = !status.textContent;
}

// La ruta, Explorar y la ficha de una estación piden datos y los pintan en el panel de resultados.
// Para que una respuesta lenta no tape lo que el usuario ha pedido después, cada petición reclama
// el panel al empezar y, al llegar la respuesta, solo la pinta si el panel sigue siendo suyo (como
// `sequence` en el autocompletado). Cambiar de pestaña y «Volver» también lo reclaman. La ruta y
// Explorar lo reclaman con su nombre ("route", "explore"): si se vuelve a ellas mientras su
// petición está en camino, la respuesta se pinta al llegar. Cada ficha usa un objeto nuevo.
let resultsOwner = null;

function claimResults(owner = {}) {
  resultsOwner = owner;
  return () => resultsOwner === owner;
}

// ---------- mapa ----------

const map = L.map("map", { preferCanvas: true }).setView(SOL, 14);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);
const stationLayer = L.layerGroup().addTo(map);
const routeLayer = L.layerGroup().addTo(map);
// Explorar: círculos del radio y lugar buscado. Los círculos van en un panel por debajo de las
// estaciones (overlayPane, 400) para no taparlas.
map.createPane("explore-area").style.zIndex = 350;
const exploreLayer = L.layerGroup().addTo(map);

// Colores de lo que se dibuja en el mapa. Salen de las variables de style.css, el único sitio
// donde se definen; la hoja de estilos ya está cargada cuando se ejecuta este script.
const COLORS = (() => {
  const css = getComputedStyle(document.documentElement);
  const color = (name) => css.getPropertyValue(`--${name}`).trim();
  return {
    station: color("bicimad"), // estación en servicio
    stationOff: color("station-off"), // fuera de servicio
    edge: color("paper"), // borde de las estaciones y relleno de las de la ruta
    onStreet: color("callejero"), // Explorar: estación de la calle buscada
    inRadius: color("ink"), // Explorar: otra estación del radio
    explore: color("explore"), // Explorar: círculo del radio
    bike: color("bike"),
    walk: color("walk"),
  };
})();

// Botones para usar un sitio: «Salir de aquí» e «Ir aquí» (modo Ruta) y, en Explorar, «Explorar aquí».
// extra añade otros botones, como { act: "card", label: "Ver ficha" }. Cada botón lleva su acción
// en data-act.
function placeActions(extra = []) {
  const buttons = [
    ...(state.mode === "explore" ? [{ act: "explore", label: "Explorar aquí" }] : []),
    { act: "from", label: "Salir de aquí" },
    { act: "to", label: "Ir aquí" },
    ...extra,
  ];
  return html`<div class="actions">${buttons.map(({ act, label }) => html`<button type="button" data-act="${act}">${label}</button>`)}</div>`;
}

// Los botones de placeActions para un popup del mapa. Los popups quedan fuera de #results, así que
// escuchan por su cuenta.
function actions(onChoose, extra = []) {
  const template = document.createElement("template");
  template.innerHTML = placeActions(extra);
  const div = template.content.firstElementChild;
  div.addEventListener("click", (event) => {
    const act = event.target.dataset.act;
    if (!act) return;
    map.closePopup();
    onChoose(act);
  });
  return div;
}

// Filtros de estaciones: solo deciden qué marcadores se ven; el cálculo de rutas no los usa.
const stationMarkers = [];
const MIN_CAPACITY_OPTIONS = [10, 20, 25, 30];

const stationFilter = L.control({ position: "topright" });
stationFilter.onAdd = () => {
  const form = L.DomUtil.create("form", "station-filter");
  // En pantallas estrechas el recuadro empieza plegado para no tapar el mapa (style.css) y el botón
  // .filter-toggle, que hace de título, lo despliega. En las anchas el botón no se ve.
  form.innerHTML = html`<button type="button" class="filter-toggle" aria-expanded="false" aria-controls="filter-fields">Estaciones ${badge("bicimad")}</button><fieldset id="filter-fields">
    <legend>Estaciones ${badge("bicimad")}</legend>
    <label><input type="checkbox" id="filter-usable"> Solo en servicio</label>
    <label>Mínimo de bases
      <select id="filter-capacity">
        <option value="0">Cualquiera</option>
        ${MIN_CAPACITY_OPTIONS.map((n) => html`<option value="${n}">${n} o más</option>`)}
      </select>
    </label>
    <p class="count" id="filter-count" aria-live="polite">Cargando estaciones…</p>
  </fieldset>`;
  L.DomEvent.disableClickPropagation(form);
  L.DomEvent.disableScrollPropagation(form);
  form.addEventListener("submit", (event) => event.preventDefault());
  form.addEventListener("change", applyStationFilters);
  const toggle = $(".filter-toggle", form);
  toggle.addEventListener("click", () => toggle.setAttribute("aria-expanded", form.classList.toggle("open")));
  return form;
};
stationFilter.addTo(map);

// Si una estación pasa los filtros del mapa. La lista de Explorar usa los mismos.
function passesFilters(station) {
  const onlyUsable = $("#filter-usable").checked;
  const minCapacity = Number($("#filter-capacity").value);
  return !(onlyUsable && !station.usable) && station.capacity >= minCapacity;
}

function applyStationFilters() {
  let visible = 0;
  for (const { station, marker } of stationMarkers) {
    if (passesFilters(station)) {
      stationLayer.addLayer(marker);
      visible += 1;
    } else {
      stationLayer.removeLayer(marker);
    }
  }
  $("#filter-count").textContent = `${visible} de ${stationMarkers.length} estaciones`;
  const list = $("#explore-stations");
  if (list && state.mode === "explore" && state.explore) list.outerHTML = exploreStationsCard(state.explore);
}

// Estaciones dentro del radio de Explorar (id → estación), o null si no se está explorando.
function exploreInside() {
  if (state.mode !== "explore" || !state.explore) return null;
  return new Map(state.explore.stations.map((s) => [s.id, s]));
}

// Estilo de un marcador de estación. En Explorar, las del radio se resaltan (con borde naranja,
// del Callejero, si están en la calle buscada) y las demás se atenúan, sin ocultarse.
function stationStyle(station, inside = null) {
  const style = {
    radius: 4.5, weight: 1, color: COLORS.edge, opacity: 1,
    fillColor: station.usable ? COLORS.station : COLORS.stationOff, fillOpacity: 0.95,
  };
  if (!inside) return style;
  const hit = inside.get(station.id);
  if (hit) return { ...style, radius: 7, weight: 2.5, color: hit.onStreet ? COLORS.onStreet : COLORS.inRadius, fillOpacity: 1 };
  return { ...style, radius: 4, opacity: 0.6, fillOpacity: 0.4 };
}

function styleStations() {
  const inside = exploreInside();
  for (const { station, marker } of stationMarkers) {
    marker.setStyle(stationStyle(station, inside));
    if (inside?.has(station.id)) marker.bringToFront();
  }
}

async function loadStations() {
  let stations;
  try {
    stations = await api("/api/stations");
  } catch (error) {
    // Sin estaciones en el mapa siguen funcionando las rutas, Explorar y las fichas. Los filtros se
    // desactivan para que el recuento no pase a «0 de 0 estaciones».
    $("#filter-count").textContent = "No se han podido cargar las estaciones.";
    $(".station-filter fieldset").disabled = true;
    showStatus(`No se han podido cargar las estaciones del mapa. ${error.message} Recarga la página para volver a intentarlo.`, "stations");
    return;
  }
  for (const s of stations) {
    const marker = L.circleMarker([s.lat, s.lon], stationStyle(s))
      .bindPopup(() => {
        const div = document.createElement("div");
        div.innerHTML = html`<strong>${s.name}</strong><br>${s.capacity} bases · ${s.usable ? "en servicio" : "fuera de servicio"}`;
        div.append(actions((act) => {
          if (act === "card") showStation(s.id);
          else usePlace(act, { ref: `station:${s.id}`, label: s.name });
        }, [{ act: "card", label: "Ver ficha" }]));
        return div;
      });
    marker.on("click", () => { if (state.mode === "explore") showStation(s.id); });
    stationMarkers.push({ station: s, marker });
  }
  applyStationFilters();
  styleStations();
}

map.on("click", (event) => {
  const { lat, lng } = event.latlng;
  const div = document.createElement("div");
  div.innerHTML = "<strong>Punto del mapa</strong>";
  const labels = { from: "Punto de salida", to: "Punto de llegada", explore: "Punto del mapa" };
  div.append(actions((act) => usePlace(act, {
    ref: `pt:${lat.toFixed(6)},${lng.toFixed(6)}`,
    label: labels[act],
    lat,
    lon: lng,
  })));
  L.popup().setLatLng(event.latlng).setContent(div).openOn(map);
});

function pin(latlng, letter, role, label) {
  L.marker(latlng, {
    icon: L.divIcon({ className: "", html: String(html`<div class="pin ${role}">${letter}</div>`), iconSize: [26, 26], iconAnchor: [13, 13] }),
    zIndexOffset: 1000,
  }).bindTooltip(esc(label)).addTo(routeLayer);
}

// Círculos del radio (uno por centro: varios si es una calle con estaciones), el lugar buscado
// y las estaciones resaltadas. Encuadra los círculos.
function drawExplore() {
  exploreLayer.clearLayers();
  const data = state.explore;
  const bounds = L.latLngBounds([]);
  for (const [lat, lon] of data.centers) {
    L.circle([lat, lon], {
      pane: "explore-area", radius: data.radius, interactive: false,
      color: COLORS.explore, weight: 2, opacity: 0.8, fillColor: COLORS.explore, fillOpacity: 0.06,
    }).addTo(exploreLayer);
    bounds.extend(L.latLng(lat, lon).toBounds(data.radius * 2));
  }
  // Una calle con estaciones se ve por ellas (borde naranja): no tiene un punto propio.
  if (!data.stations.some((s) => s.onStreet)) {
    const { lat, lon, label, source } = data.center;
    L.marker([lat, lon], {
      icon: L.divIcon({ className: "", html: String(html`<div class="pin here" style="background: var(--${source})"></div>`), iconSize: [20, 20], iconAnchor: [10, 10] }),
      zIndexOffset: 1000,
      keyboard: false,
    }).bindTooltip(esc(label)).addTo(exploreLayer);
  }
  styleStations();
  map.fitBounds(bounds, { padding: [24, 24] });
}

// Deja el mapa como fuera de Explorar.
function clearExplore() {
  exploreLayer.clearLayers();
  styleStations();
}

function drawPlan() {
  routeLayer.clearLayers();
  const plan = state.plan;
  const showBike = state.shown === "bike" && plan.bike;
  const bounds = [];

  const draw = (leg, faded) => {
    const style = leg.mode === "bike"
      ? { color: COLORS.bike, weight: 5, opacity: faded ? 0.25 : 0.9 }
      : { color: COLORS.walk, weight: 4, dashArray: "1 8", lineCap: "round", opacity: faded ? 0.3 : 0.95 };
    L.polyline(leg.geometry, style).addTo(routeLayer);
    if (!faded) bounds.push(...leg.geometry);
  };
  if (plan.bike) plan.bike.legs.forEach((leg) => draw(leg, !showBike));
  draw(plan.walk, showBike);

  if (showBike) {
    for (const s of [plan.bike.fromStation, plan.bike.toStation]) {
      L.circleMarker([s.lat, s.lon], { radius: 8, color: COLORS.bike, weight: 3, fillColor: COLORS.edge, fillOpacity: 1 })
        .bindTooltip(esc(s.name))
        .addTo(routeLayer);
    }
  }
  const legs = showBike ? plan.bike.legs : [plan.walk];
  const start = plan.origin.fixedStations ? legs[0].geometry[0] : [plan.origin.lat, plan.origin.lon];
  const end = plan.destination.fixedStations ? legs.at(-1).geometry.at(-1) : [plan.destination.lat, plan.destination.lon];
  pin(start, "A", "from", plan.origin.label);
  pin(end, "B", "to", plan.destination.label);
  bounds.push(start, end);
  map.fitBounds(L.latLngBounds(bounds), { padding: [40, 40] });
}

// ---------- modos: Ruta y Explorar ----------

const tabs = [...document.querySelectorAll('.tabs [role="tab"]')];

function setMode(mode) {
  if (state.mode === mode) return;
  state.mode = mode;
  claimResults(mode);
  for (const tab of tabs) {
    const selected = tab.dataset.mode === mode;
    tab.setAttribute("aria-selected", selected);
    tab.tabIndex = selected ? 0 : -1;
    $(`#${tab.getAttribute("aria-controls")}`).hidden = !selected;
  }
  map.closePopup();
  if (mode === "explore") {
    routeLayer.clearLayers();
    if (state.explore) showExplore();
    else exploreWelcome();
    return;
  }
  clearExplore();
  if (state.plan) showPlan();
  else welcome();
}

tabs.forEach((tab, i) => {
  tab.addEventListener("click", () => setMode(tab.dataset.mode));
  // Patrón de pestañas: las flechas pasan de una a otra.
  tab.addEventListener("keydown", (event) => {
    const step = { ArrowLeft: -1, ArrowRight: 1 }[event.key];
    if (!step) return;
    const next = tabs[(i + step + tabs.length) % tabs.length];
    next.focus();
    setMode(next.dataset.mode);
  });
});

// Usar un sitio elegido en el mapa o en una ficha: como origen, destino o centro de Explorar.
function usePlace(act, place) {
  if (act === "explore") setCenter(place);
  else setEndpoint(act, place);
}

// ---------- origen y destino ----------

function setEndpoint(role, value) {
  setMode("route");
  state[role] = value;
  $(`#${role}-input`).value = value.label;
  if (state.from && state.to) computeRoute();
}

// Campo con autocompletado (/api/search). Al elegir una opción se llama a onChoose; por defecto,
// la opción pasa a ser el origen o el destino.
function setupField(role, onChoose = (item) => setEndpoint(role, { ref: item.ref, label: item.label })) {
  const field = $(`.field[data-role="${role}"]`);
  const input = $("input", field);
  const list = $(".suggestions", field);
  let items = [];
  let active = -1;
  let timer;
  let sequence = 0;

  const close = () => { list.hidden = true; };

  const render = () => {
    if (!items.length) {
      list.innerHTML = '<li class="empty">Sin resultados</li>';
      list.hidden = false;
      return;
    }
    const seen = new Set();
    const rows = [];
    let last = null;
    items.forEach((item, i) => {
      if (item.kind !== last) {
        rows.push(html`<li class="group">${seen.has(item.kind) ? "Más " : ""}${GROUPS[item.kind]}</li>`);
        seen.add(item.kind);
        last = item.kind;
      }
      rows.push(html`<li class="option" role="option" data-i="${i}" aria-selected="${i === active}">
        <strong>${item.label}</strong><span>${item.detail}</span></li>`);
    });
    list.innerHTML = html`${rows}`;
    list.hidden = false;
  };

  const suggest = async () => {
    const q = input.value.trim();
    if (q.length < 2) return close();
    const mine = ++sequence;
    const near = role === "to" && state.from && state.from.lat !== undefined ? state.from : null;
    try {
      const data = await api("/api/search", { q, lat: near?.lat, lon: near?.lon });
      if (mine !== sequence) return;
      items = data.results;
      active = -1;
      render();
    } catch (error) {
      list.innerHTML = html`<li class="empty error">${error.message}</li>`;
      list.hidden = false;
    }
  };

  const choose = (item) => {
    // Descarta las sugerencias que aún estén en camino, para que no vuelvan a abrir la lista.
    clearTimeout(timer);
    sequence += 1;
    close();
    onChoose(item);
  };

  input.addEventListener("input", () => {
    state[role] = null;
    clearTimeout(timer);
    timer = setTimeout(suggest, 200);
  });
  input.addEventListener("focus", () => { if (input.value.trim().length >= 2 && !state[role]) suggest(); });
  input.addEventListener("blur", () => setTimeout(close, 150));
  input.addEventListener("keydown", (event) => {
    if (list.hidden || !items.length) return;
    if (event.key === "ArrowDown") active = Math.min(active + 1, items.length - 1);
    else if (event.key === "ArrowUp") active = Math.max(active - 1, 0);
    else if (event.key === "Enter") return choose(items[Math.max(active, 0)]);
    else if (event.key === "Escape") return close();
    else return;
    event.preventDefault();
    render();
  });
  list.addEventListener("mousedown", (event) => {
    const option = event.target.closest(".option");
    if (!option) return;
    event.preventDefault();
    choose(items[Number(option.dataset.i)]);
  });
}

$("#locate").addEventListener("click", () => {
  if (!navigator.geolocation) return showStatus("Tu navegador no permite obtener la ubicación.");
  showStatus("Buscando tu ubicación…");
  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude: lat, longitude: lon } = position.coords;
      if (map.distance([lat, lon], SOL) > 20000) {
        return showStatus("Tu ubicación está fuera de Madrid: haz clic en el mapa para elegir el origen.");
      }
      showStatus("");
      setEndpoint("from", { ref: `pt:${lat.toFixed(6)},${lon.toFixed(6)}`, label: "Tu ubicación", lat, lon });
    },
    () => showStatus("No se ha podido obtener tu ubicación: haz clic en el mapa para elegir el origen."),
    { enableHighAccuracy: true, timeout: 10000 },
  );
});

$("#swap").addEventListener("click", () => {
  [state.from, state.to] = [state.to, state.from];
  $("#from-input").value = state.from?.label ?? "";
  $("#to-input").value = state.to?.label ?? "";
  if (state.from && state.to) computeRoute();
});

// ---------- resultados ----------

// Mensaje en el panel de resultados: "loading" mientras llega una respuesta, o "error".
function showMessage(kind, text) {
  results.innerHTML = html`<p class="${kind}">${text}</p>`;
}

// Tarjeta del panel con su título y, si se indica, la etiqueta de la fuente de sus datos.
function card(title, source, body, id = null) {
  return html`<div class="card"${id ? html` id="${id}"` : ""}><h2>${title}${source ? html` ${badge(source)}` : ""}</h2>${body}</div>`;
}

function optionCard(mode, title, option, recommended) {
  return html`<button type="button" class="option-card ${state.shown === mode ? "active" : ""}" data-action="option" data-mode="${mode}">
    <div class="mode">${title}</div>
    <div class="time">${minutes(option.duration)}</div>
    <div class="meta">${distanceLabel(option.distance)}${option.estimated ? html` · ${badge("warn", "estimado")}` : ""}</div>
    ${recommended ? html`<span class="best">Más rápido</span>` : ""}
  </button>`;
}

function endpointLine(role, endpoint) {
  return html`<div class="endpoint"><b>${role}</b><div>
    <strong>${endpoint.label}</strong> ${badge(endpoint.source)}
    ${endpoint.approximate ? badge("warn", "aproximado") : ""}
    <p>${endpoint.note}</p></div></div>`;
}

// Distancia de un tramo, marcada si es una estimación en línea recta (sin OSRM).
function legDistance(leg) {
  return `${distanceLabel(leg.distance)}${leg.estimated ? " · estimado" : ""}`;
}

// Paso «Camina…» de un tramo a pie, hasta leg.to.
function walkStep(leg) {
  return html`<li class="walk">Camina ${minutes(leg.duration)} hasta <strong>${leg.to}</strong>
    <span class="sub">${legDistance(leg)}</span></li>`;
}

// Pasos de un tramo en bici: coger la bici, pedalear y dejarla. dock es el tiempo de cada maniobra.
function bikeSteps(leg, dock) {
  return html`<li class="dock">Coge una bici en <strong>${leg.from}</strong><span class="sub">${dock} para desanclarla</span></li>
    <li class="bike">Pedalea ${minutes(leg.duration)} hasta <strong>${leg.to}</strong>
    <span class="sub">${legDistance(leg)}</span></li>
    <li class="dock">Deja la bici en <strong>${leg.to}</strong><span class="sub">${dock} para anclarla</span></li>`;
}

function stepsCard(bike) {
  // bike.dock es el tiempo de sacar la bici y de dejarla: la mitad para cada paso.
  const dock = minutes(bike.dock / 2);
  const steps = bike.legs.map((leg) => (leg.mode === "walk" ? walkStep(leg) : bikeSteps(leg, dock)));
  return card("Itinerario", "osrm", html`<ol class="steps">${steps}</ol>`);
}

function walkCard(plan) {
  const faster = plan.recommended === "walk" && plan.bike
    ? html`<p class="sub">Para este trayecto es más rápido ir andando que coger y dejar una bici.</p>`
    : "";
  return card("Itinerario", "osrm", html`<ol class="steps">${walkStep(plan.walk)}</ol>${faster}`);
}

// Un bloque de la ficha de una estación, con el color y la etiqueta de su fuente.
function stationBlock(block) {
  const people = (block.namedAfter ?? []).map((person) => html`<div class="person">${person.image ? html`<img src="${https(person.image)}" alt="" loading="lazy">` : ""}
        <div>Homenajea a <a href="${person.link}" target="_blank" rel="noopener">${person.label}</a>
        ${person.description ? html`<br><span class="sub">${person.description}</span>` : ""}</div></div>`);
  return html`<div class="block ${block.source}"><div class="head"><span>${block.title}</span>${badge(block.source)}</div>${[
    block.items ? html`<dl>${block.items.map(([key, value]) => html`<dt>${key}</dt><dd>${value}</dd>`)}</dl>` : "",
    block.description ? html`<p>${block.description}</p>` : "",
    block.image ? html`<img src="${https(block.image)}" alt="${block.title}" loading="lazy">` : "",
    people,
    block.link ? html`<p><a href="${block.link}" target="_blank" rel="noopener">Ver en Wikidata ↗</a></p>` : "",
  ]}</div>`;
}

function stationCard(station, title) {
  return card(`${title}: ${station.name}`, null, station.blocks.map(stationBlock));
}

function nearbyCard(places, title) {
  const items = places.map((p) => html`<li><a href="${p.link}" target="_blank" rel="noopener">${p.label}</a>
    <span>${p.categories.join(", ")} · ${distanceLabel(p.distance)}</span></li>`);
  return card(title, "wikidata", html`<ul class="list">${items}</ul>`);
}

// Una estación en una lista: enlace a su ficha, estado, bases y distancia. En Explorar, las
// estaciones de la calle buscada (bm:locatedOnStreet) se marcan «en la calle».
function stationItem(s) {
  const where = s.onStreet ? badge("callejero", "en la calle") : distanceLabel(s.distance);
  return html`<li><a href="#" data-action="station" data-station="${s.id}">${s.name}</a>
    <span>${s.usable ? "" : html`${badge("muted", "fuera de servicio")} · `}${s.capacity} bases · ${where}</span></li>`;
}

function nearestStationsCard(stations, title = "Estaciones más cercanas") {
  return card(title, "bicimad", html`<ul class="list">${stations.map(stationItem)}</ul>`);
}

function queryItem(q) {
  const meta = [`${q.rows ?? 0} filas`, `${q.ms} ms`];
  if (q.cached) meta.push("caché");
  if (q.error) meta.push("error → estimación");
  return html`<details class="query"><summary>${badge(q.source)}<code>${q.name}</code>
      <span class="meta">${meta.join(" · ")}</span></summary>
      <pre>${q.text}${q.error ? `\n\n# ${q.error}` : ""}</pre></details>`;
}

function whyPanel(contributions, queries) {
  const table = contributions
    ? html`<p class="sub">Qué aporta cada fuente a esta respuesta y qué se podría hacer solo con el CSV de BiciMAD.</p>
      <table><thead><tr><th>Dato</th><th>Fuente</th><th>Solo con el CSV</th></tr></thead><tbody>
      ${contributions.map((c) => html`<tr><td>${c.what}<br><span class="sub">${c.how}</span></td>
        <td>${badge(c.source)}</td><td class="${c.csv.verdict}">${c.csv.text}</td></tr>`)}
      </tbody></table>`
    : "";
  return html`<details class="why" ${state.whyOpen ? "open" : ""}><summary>¿Por qué ontología?</summary><div>${table}<h3>Consultas ejecutadas (${queries.length})</h3>${queries.map(queryItem)}</div></details>`;
}

function renderPlan() {
  const plan = state.plan;
  const cards = plan.cards.map((station, i) => [
    stationCard(station, i ? "Llegada" : "Salida"),
    station.nearestStations?.length
      ? nearestStationsCard(station.nearestStations, i ? "Alternativas a la llegada" : "Alternativas a la salida")
      : "",
  ]);
  results.innerHTML = html`<div class="options">
      ${plan.bike ? optionCard("bike", "En BiciMAD", plan.bike, plan.recommended === "bike") : ""}
      ${optionCard("walk", "Andando", plan.walk, plan.recommended === "walk")}
    </div>
    <div class="card">${endpointLine("Desde", plan.origin)}${endpointLine("Hasta", plan.destination)}</div>
    ${state.shown === "bike" && plan.bike ? stepsCard(plan.bike) : walkCard(plan)}
    ${cards}
    ${plan.nearby.length ? nearbyCard(plan.nearby, "Cerca del destino") : ""}
    ${whyPanel(plan.contributions, plan.queries)}`;
}

// Pinta la ruta guardada en el panel y en el mapa.
function showPlan() {
  renderPlan();
  drawPlan();
}

let routeSequence = 0;

async function computeRoute() {
  const mine = ++routeSequence;
  const ownsPanel = claimResults("route");
  // El origen pedido: mientras llega la respuesta, el usuario puede estar cambiando state.from.
  const from = state.from;
  showMessage("loading", "Calculando la ruta…");
  try {
    const plan = await api("/api/route", {
      from: state.from.ref,
      to: state.to.ref,
      fromLabel: state.from.label,
      toLabel: state.to.label,
    });
    if (mine !== routeSequence) return;
    state.plan = plan;
    state.shown = plan.recommended;
    from.lat = plan.origin.lat;
    from.lon = plan.origin.lon;
    // Si entretanto se ha pedido otra cosa, la ruta se guarda para «Volver a la ruta» o la
    // pestaña Ruta, pero no se pinta.
    if (ownsPanel()) showPlan();
  } catch (error) {
    if (mine !== routeSequence || !ownsPanel()) return;
    routeLayer.clearLayers();
    showMessage("error", error.message);
  }
}

// Botón para volver de una ficha a lo que había: la lista de Explorar o la ruta (ver goBack).
function backButton() {
  if (state.mode === "explore" && state.explore) {
    return html`<button type="button" class="back" data-action="back">← Volver a la lista</button>`;
  }
  if (state.mode === "route" && state.plan) {
    return html`<button type="button" class="back" data-action="back">← Volver a la ruta</button>`;
  }
  return "";
}

function goBack() {
  claimResults(state.mode);
  if (state.mode === "route") showPlan();
  // Si la última búsqueda de Explorar falla mientras se ve la ficha, state.explore queda vacío.
  else if (state.explore) showExplore();
  else exploreWelcome();
}

async function showStation(id) {
  const ownsPanel = claimResults();
  showMessage("loading", "Cargando la estación…");
  try {
    const data = await api(`/api/station/${encodeURIComponent(id)}`);
    if (!ownsPanel()) return;
    const s = data.station;
    results.innerHTML = html`${backButton()}
      ${stationCard(s, "Estación")}
      <div class="card" id="station-actions" data-action="place" data-ref="station:${s.id}" data-label="${s.name}">${placeActions()}</div>
      ${s.nearestStations.length ? nearestStationsCard(s.nearestStations) : ""}
      ${data.nearby.length ? nearbyCard(data.nearby, "Lugares cercanos") : ""}
      ${whyPanel(null, data.queries)}`;
    map.setView([s.lat, s.lon], Math.max(map.getZoom(), 16));
  } catch (error) {
    if (ownsPanel()) showMessage("error", error.message);
  }
}

function exampleButtons(examples) {
  return html`<div class="actions">${examples.map((e) => html`<button type="button" data-action="example" data-example="${e}">${e}</button>`)}</div>`;
}

function welcome() {
  results.innerHTML = card("¿A dónde vas?", null, html`
    <p class="sub">Elige el origen con tu ubicación o haciendo clic en el mapa, y escribe el destino:
    una calle (el número se ignora), un lugar, un tipo de lugar o una estación.</p>
    <p class="sub">Ejemplos desde la Puerta del Sol:</p>${exampleButtons(EXAMPLES)}`);
}

function exploreWelcome() {
  results.innerHTML = card("¿Qué estaciones hay cerca?", null, html`
    <p class="sub">Escribe una calle, un lugar, un tipo de lugar o una estación, o haz clic en el mapa,
    y verás las estaciones BiciMAD que tiene alrededor, de la más cercana a la más lejana.</p>
    <p class="sub">Ejemplos:</p>${exampleButtons(EXPLORE_EXAMPLES)}`);
}

// Los ejemplos escriben en el campo del modo activo y muestran sus sugerencias.
function useExample(example) {
  let input = $("#center-input");
  if (state.mode === "route") {
    state.from = { ref: `pt:${SOL[0]},${SOL[1]}`, label: "Puerta del Sol", lat: SOL[0], lon: SOL[1] };
    $("#from-input").value = state.from.label;
    input = $("#to-input");
  }
  input.value = example;
  input.focus();
  input.dispatchEvent(new Event("input"));
}

// ---------- eventos del panel ----------

// Lo que se pinta en #results dice con data-action qué hace al pulsarlo, y con otros data-*, sobre
// qué. Un solo listener atiende todo el panel: no hay que enlazar nada en cada pintado y sigue
// funcionando cuando se vuelve a pintar solo una parte (la lista de Explorar al cambiar los filtros).
const resultActions = {
  station: (el) => showStation(el.dataset.station),
  option: (el) => {
    state.shown = el.dataset.mode;
    showPlan();
  },
  back: () => goBack(),
  example: (el) => useExample(el.dataset.example),
  // Botones de placeActions en la ficha: el sitio va en el contenedor y la acción en cada botón.
  place: (el, event) => {
    const act = event.target.closest("[data-act]")?.dataset.act;
    if (act) usePlace(act, { ref: el.dataset.ref, label: el.dataset.label });
  },
};

results.addEventListener("click", (event) => {
  const el = event.target.closest("[data-action]");
  if (!el) return;
  event.preventDefault();
  resultActions[el.dataset.action](el, event);
});

// El panel «¿Por qué ontología?» se queda abierto o cerrado al volver a pintar. toggle no burbujea,
// así que se escucha en la fase de captura.
results.addEventListener("toggle", (event) => {
  if (event.target.matches("details.why")) state.whyOpen = event.target.open;
}, true);

// ---------- Explorar ----------

let exploreSequence = 0;

function setCenter(place) {
  setMode("explore");
  state.center = place;
  $("#center-input").value = place.label;
  exploreAround(place);
}

// Pide las estaciones alrededor de place con el radio elegido. Al cambiar solo el radio
// (loading = false) se deja la lista anterior hasta que llega la nueva.
async function exploreAround(place, loading = true) {
  const mine = ++exploreSequence;
  const ownsPanel = claimResults("explore");
  if (loading) showMessage("loading", "Buscando estaciones…");
  try {
    const data = await api("/api/explore", { ref: place.ref, label: place.label, radius: state.radius });
    if (mine !== exploreSequence) return;
    // Como en la ruta: si entretanto se ha abierto una ficha o cambiado de pestaña, se guarda
    // para «Volver a la lista» o la pestaña Explorar, pero no se pinta.
    state.explore = { ...data, place };
    if (ownsPanel()) showExplore();
  } catch (error) {
    if (mine !== exploreSequence) return;
    state.explore = null;
    clearExplore();
    if (ownsPanel()) showMessage("error", error.message);
  }
}

$("#explore-form").addEventListener("change", (event) => {
  if (event.target.name !== "radius") return;
  state.radius = Number(event.target.value);
  const place = state.explore?.place ?? state.center;
  if (place) exploreAround(place, false);
});

function centerCard(center, place) {
  const [kind, id] = place.ref.split(":");
  const link = kind === "station" ? html`<p class="sub"><a href="#" data-action="station" data-station="${id}">Ver la ficha de la estación</a></p>` : "";
  return html`<div class="card center-card"><p class="kicker">Lugar</p>
    <h2>${center.label} ${badge(center.source)} ${center.approximate ? badge("warn", "aproximado") : ""}</h2>
    <p class="sub">${center.note}</p>${link}</div>`;
}

function stationsLabel(count) {
  return count === 1 ? "1 estación" : `${count} estaciones`;
}

// Nombre de un radio de Explorar: el texto de su botón en el formulario («300 m», «1 km»).
function radiusLabel(radius) {
  return $(`#explore-form input[name="radius"][value="${radius}"] + span`).textContent;
}

// Lista de estaciones del radio, con los filtros del mapa aplicados y su recuento.
function exploreStationsCard(data) {
  const radius = radiusLabel(data.radius);
  const total = data.stations.length;
  const shown = data.stations.filter(passesFilters);
  let count;
  if (!total) {
    count = `No hay ninguna estación a ${radius} o menos.${data.radius < 1000 ? " Prueba con un radio mayor." : ""}`;
  } else if (shown.length === total) {
    count = `${stationsLabel(total)}, de la más cercana a la más lejana en línea recta.`;
  } else if (!shown.length) {
    count = `Los filtros del mapa ocultan ${total === 1 ? "la estación" : `las ${total} estaciones`} del radio.`;
  } else {
    count = `${shown.length} de ${stationsLabel(total)}, de la más cercana a la más lejana en línea recta. Los filtros del mapa ocultan el resto.`;
  }
  const list = shown.length ? html`<ul class="list">${shown.map(stationItem)}</ul>` : "";
  return card(`Estaciones a ${radius} o menos`, "bicimad", html`<p class="sub">${count}</p>${list}`, "explore-stations");
}

function renderExplore() {
  const data = state.explore;
  results.innerHTML = html`${centerCard(data.center, data.place)}${exploreStationsCard(data)}${whyPanel(data.contributions, data.queries)}`;
}

function showExplore() {
  renderExplore();
  drawExplore();
}

async function checkStatus() {
  try {
    const status = await api("/api/status");
    if (status.places === "ready") return showStatus("");
    if (status.places === "error") {
      return showStatus("No se han podido descargar los lugares de Wikidata: la búsqueda de lugares no está disponible.");
    }
    showStatus("Descargando lugares de Wikidata…");
    setTimeout(checkStatus, 3000);
  } catch {
    setTimeout(checkStatus, 3000);
  }
}

// Los formularios de Ruta y Explorar no se envían: cada campo actúa al elegir una sugerencia.
document.querySelectorAll("form.trip").forEach((form) => {
  form.addEventListener("submit", (event) => event.preventDefault());
});
setupField("from");
setupField("to");
setupField("center", (item) => setCenter({ ref: item.ref, label: item.label }));
welcome();
loadStations();
checkStatus();
