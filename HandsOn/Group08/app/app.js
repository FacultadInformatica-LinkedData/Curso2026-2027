// Madrid Sports Finder: reads the RDF (Turtle) published by Group 08 and shows it on a map.
// No server or SPARQL endpoint is needed: the Turtle file is parsed in the browser with N3.js.

const DATA_URL = "data/madridsports-with-links.ttl";
const MS = "http://madridsports.example.org/ontology/madridsports#";
const RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";
const RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label";
const OWL_SAMEAS = "http://www.w3.org/2002/07/owl#sameAs";
const DCT_SOURCE = "http://purl.org/dc/terms/source";

const $ = (id) => document.getElementById(id);
const state = { facilities: [], districts: new Map(), types: new Map(), levels: new Map(), features: new Map(), selected: null, user: null };
let map, layer;
const markers = new Map();

// ---------- loading ----------

async function load() {
  const text = await (await fetch(DATA_URL)).text();
  const store = new N3.Store(new N3.Parser().parse(text));
  buildModel(store);
  initUI();
  render();
  $("status").textContent = `${state.facilities.length} facilities from ${store.size.toLocaleString()} RDF triples`;
}

function buildModel(store) {
  // all quads grouped by subject: { predicateIRI: [object values] }
  const by = new Map();
  for (const q of store) {
    if (!by.has(q.subject.value)) by.set(q.subject.value, {});
    const props = by.get(q.subject.value);
    (props[q.predicate.value] ||= []).push(q.object);
  }
  const first = (p, k) => (p[k] && p[k][0] ? p[k][0].value : null);
  const label = (iri) => first(by.get(iri) || {}, RDFS_LABEL) || iri.split("/").pop();

  for (const [iri, p] of by) {
    const types = (p[RDF_TYPE] || []).map((o) => o.value);
    if (types.includes(MS + "District")) {
      state.districts.set(iri, { iri, name: first(p, RDFS_LABEL), wikidata: (p[OWL_SAMEAS] || []).map((o) => o.value)[0] });
    } else if (types.includes(MS + "FacilityType")) {
      state.types.set(iri, humanize(first(p, RDFS_LABEL)));
    } else if (types.includes(MS + "AccessibilityLevel")) {
      state.levels.set(iri, first(p, RDFS_LABEL));
    } else if (types.includes(MS + "AccessibilityFeature")) {
      state.features.set(iri, first(p, RDFS_LABEL));
    }
  }

  for (const [iri, p] of by) {
    const types = (p[RDF_TYPE] || []).map((o) => o.value);
    const isCentre = types.includes(MS + "SportsCentre");
    if (!isCentre && !types.includes(MS + "BasicSportsFacility")) continue;
    const lat = parseFloat(first(p, MS + "latitude"));
    const lon = parseFloat(first(p, MS + "longitude"));
    if (Number.isNaN(lat) || Number.isNaN(lon)) continue;
    const street = [first(p, MS + "streetType"), first(p, MS + "streetName"), first(p, MS + "streetNumber")].filter(Boolean).join(" ");
    state.facilities.push({
      iri,
      key: first(p, MS + "sourceKey"),
      name: first(p, RDFS_LABEL) || "(no name)",
      centre: isCentre,
      lat, lon,
      district: first(p, MS + "locatedInDistrict"),
      type: first(p, MS + "hasFacilityType"),
      level: first(p, MS + "hasAccessibilityLevel"),
      features: (p[MS + "hasAccessibilityFeature"] || []).map((o) => o.value),
      pool: first(p, MS + "hasSwimmingPool") === "true",
      address: [street, first(p, MS + "postalCode")].filter(Boolean).join(", "),
      hours: first(p, MS + "openingHours"),
      equipment: first(p, MS + "equipment"),
      transport: first(p, MS + "transport"),
      phone: first(p, MS + "phone"),
      email: first(p, MS + "email"),
      web: first(p, MS + "webPage"),
      source: first(p, DCT_SOURCE),
    });
  }
  state.facilities.sort((a, b) => a.name.localeCompare(b.name, "es"));
}

function humanize(s) {
  return s.replace(/([a-z])([A-Z])/g, "$1 $2");
}

// ---------- UI ----------

function fillSelect(sel, entries) {
  entries.sort((a, b) => a[1].localeCompare(b[1], "es"));
  for (const [value, text] of entries) {
    const o = document.createElement("option");
    o.value = value;
    o.textContent = text;
    sel.appendChild(o);
  }
}

function initUI() {
  map = L.map("map").setView([40.4168, -3.7038], 11);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
  layer = L.layerGroup().addTo(map);

  fillSelect($("f-district"), [...state.districts.values()].map((d) => [d.iri, titleCase(d.name)]));
  fillSelect($("f-type"), [...state.types.entries()]);
  const levels = [...state.levels.entries()];
  fillSelect($("f-access"), levels);
  for (const [iri, text] of state.features) {
    const o = document.createElement("option");
    o.value = "feature:" + iri;
    o.textContent = "With feature: " + text;
    $("f-access").appendChild(o);
  }

  for (const id of ["f-text", "f-basic", "f-centre", "f-district", "f-type", "f-access", "f-pool"]) {
    $(id).addEventListener("input", render);
  }
  $("reset").addEventListener("click", () => {
    $("f-text").value = "";
    $("f-basic").checked = $("f-centre").checked = true;
    $("f-district").value = $("f-type").value = $("f-access").value = "";
    $("f-pool").checked = false;
    render();
  });
  $("locate").addEventListener("click", locate);
}

function titleCase(s) {
  return s.toLowerCase().replace(/(^|[\s-])(\p{L})/gu, (m, a, b) => a + b.toUpperCase());
}

function currentFilters() {
  return {
    text: $("f-text").value.trim().toLowerCase(),
    basic: $("f-basic").checked,
    centre: $("f-centre").checked,
    district: $("f-district").value,
    type: $("f-type").value,
    access: $("f-access").value,
    pool: $("f-pool").checked,
  };
}

function matches(f, c, ignoreDistrict = false) {
  if (f.centre ? !c.centre : !c.basic) return false;
  if (!ignoreDistrict && c.district && f.district !== c.district) return false;
  if (c.type && f.type !== c.type) return false;
  if (c.access) {
    if (c.access.startsWith("feature:")) {
      if (!f.features.includes(c.access.slice(8))) return false;
    } else if (f.level !== c.access) return false;
  }
  if (c.pool && !f.pool) return false;
  if (c.text && !f.name.toLowerCase().includes(c.text)) return false;
  return true;
}

// ---------- rendering ----------

function render() {
  const c = currentFilters();
  const visible = state.facilities.filter((f) => matches(f, c));

  layer.clearLayers();
  markers.clear();
  for (const f of visible) {
    const m = L.circleMarker([f.lat, f.lon], {
      radius: f.centre ? 8 : 6,
      color: "#fff",
      weight: 1.5,
      fillColor: f.centre ? "#2f6fdb" : "#2e9e5b",
      fillOpacity: 0.9,
    }).addTo(layer);
    m.bindTooltip(f.name);
    m.on("click", () => select(f));
    markers.set(f.iri, m);
  }
  if (state.selected && !visible.includes(state.selected)) closeDetail();
  drawChart(c);
  drawNearest(visible);
  $("status").textContent = `${visible.length} of ${state.facilities.length} facilities shown`;
}

function drawChart(c) {
  const counts = new Map([...state.districts.keys()].map((d) => [d, 0]));
  for (const f of state.facilities) {
    if (f.district && matches(f, c, true)) counts.set(f.district, (counts.get(f.district) || 0) + 1);
  }
  const rows = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...rows.map((r) => r[1]));
  const box = $("chart");
  box.innerHTML = "";
  for (const [iri, n] of rows) {
    const row = document.createElement("div");
    row.className = "bar-row" + (c.district === iri ? " sel" : "");
    row.innerHTML = `<span class="name"></span><span class="bar-track"><span class="bar-fill" style="width:${(n / max) * 100}%"></span></span><span class="n">${n}</span>`;
    row.querySelector(".name").textContent = titleCase(state.districts.get(iri).name);
    row.addEventListener("click", () => {
      $("f-district").value = c.district === iri ? "" : iri;
      render();
    });
    box.appendChild(row);
  }
}

// ---------- nearest ----------

function distanceKm(lat1, lon1, lat2, lon2) {
  const rad = Math.PI / 180;
  const a = Math.sin(((lat2 - lat1) * rad) / 2) ** 2 +
    Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(((lon2 - lon1) * rad) / 2) ** 2;
  return 12742 * Math.asin(Math.sqrt(a));
}

function locate() {
  if (!navigator.geolocation) {
    $("nearest").innerHTML = "<li>Geolocation is not available in this browser.</li>";
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      state.user = { lat: pos.coords.latitude, lon: pos.coords.longitude };
      L.circleMarker([state.user.lat, state.user.lon], { radius: 7, color: "#c0392b", fillColor: "#c0392b", fillOpacity: 1 })
        .addTo(map).bindTooltip("You are here");
      map.setView([state.user.lat, state.user.lon], 14);
      render();
    },
    () => { $("nearest").innerHTML = "<li>Could not get your location.</li>"; }
  );
}

function drawNearest(visible) {
  const list = $("nearest");
  if (!state.user) { list.innerHTML = ""; return; }
  const top = visible
    .map((f) => ({ f, d: distanceKm(state.user.lat, state.user.lon, f.lat, f.lon) }))
    .sort((a, b) => a.d - b.d)
    .slice(0, 5);
  list.innerHTML = "";
  for (const { f, d } of top) {
    const li = document.createElement("li");
    li.innerHTML = `<span></span> <span class="km">(${d.toFixed(1)} km)</span>`;
    li.firstChild.textContent = f.name;
    li.addEventListener("click", () => { map.setView([f.lat, f.lon], 16); select(f); });
    list.appendChild(li);
  }
}

// ---------- detail card ----------

function select(f) {
  state.selected = f;
  const d = state.districts.get(f.district);
  const na = '<span class="na">Not available</span>';
  const row = (k, v) => `<dt>${k}</dt><dd>${v || na}</dd>`;
  const features = f.features.map((i) => state.features.get(i)).filter(Boolean).join(", ");
  const access = [state.levels.get(f.level), features].filter(Boolean).join(" · ");
  const link = (url, text) => (url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(text)}</a>` : "");

  const box = $("detail");
  box.hidden = false;
  box.innerHTML = `
    <button class="close" type="button" aria-label="Close">×</button>
    <h3>${esc(f.name)}</h3>
    <span class="tag ${f.centre ? "centre" : "basic"}">${f.centre ? "Sports centre" : "Basic facility"}</span>
    ${f.pool ? ' <span class="tag centre">Swimming pool</span>' : ""}
    <dl>
      ${row("Type", esc(state.types.get(f.type) || ""))}
      ${row("Address", esc(f.address))}
      ${row("District", d ? esc(titleCase(d.name)) + (d.wikidata ? " · " + link(d.wikidata, "Wikidata") : "") : "")}
      ${row("Opening hours", esc(f.hours || ""))}
      ${row("Accessibility", esc(access))}
      ${row("Equipment", esc(shorten(f.equipment, 300)))}
      ${row("Transport", esc(f.transport || ""))}
      ${row("Phone", esc(f.phone || ""))}
      ${row("Email", f.email ? `<a href="mailto:${esc(f.email)}">${esc(f.email)}</a>` : "")}
      ${row("Original source", link(f.source || f.web, "madrid.es"))}
      ${row("RDF resource", `<code>${esc(f.iri)}</code>`)}
    </dl>`;
  box.querySelector(".close").addEventListener("click", closeDetail);
  const m = markers.get(f.iri);
  if (m) m.bringToFront();
}

function closeDetail() {
  state.selected = null;
  $("detail").hidden = true;
}

function shorten(s, n) {
  if (!s) return s;
  return s.length > n ? s.slice(0, n).trimEnd() + "…" : s;
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

load().catch((err) => {
  $("status").textContent = "Could not load the data. Serve this folder over HTTP (see README).";
  console.error(err);
});
