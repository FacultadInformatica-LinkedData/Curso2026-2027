// Madrid Smart City - search page. Builds SPARQL queries from the filters, runs them on
// GraphDB and draws the map (municipality coordinates come from Wikidata via owl:sameAs).
// The filters live in the URL, so "back" from an accommodation page restores them.

const PAGE_SIZE = 50;
const state = { cities: new Map(), info: new Map(), map: null, markers: null, page: 1 };

// ---------- Filters <-> URL ----------
function readFilters() {
  return {
    type: $("f-type").value,
    stars: [...document.querySelectorAll("#f-stars input:checked")].map((c) => c.value),
    city: $("f-city").value,
    pc: $("f-pc").value.trim(),
    name: $("f-name").value.trim(),
  };
}

function saveToUrl() {
  const f = readFilters(), p = new URLSearchParams();
  if (f.type !== "todos") p.set("tipo", f.type);
  if (f.stars.length) p.set("cat", f.stars.join(","));
  if (f.city) p.set("municipio", f.city);
  if (f.pc) p.set("cp", f.pc);
  if (f.name) p.set("nombre", f.name);
  if (state.page > 1) p.set("pag", state.page);
  history.replaceState(null, "", "?" + p.toString());
}

function loadFromUrl() {
  const p = new URLSearchParams(location.search);
  $("f-type").value = p.get("tipo") || "todos";
  if (!$("f-type").value) $("f-type").value = "todos";
  const cat = (p.get("cat") || "").split(",");
  document.querySelectorAll("#f-stars input").forEach((c) => (c.checked = cat.includes(c.value)));
  $("f-city").value = p.get("municipio") || "";
  $("f-pc").value = p.get("cp") || "";
  $("f-name").value = p.get("nombre") || "";
  state.page = Math.max(1, Number(p.get("pag")) || 1);
}

// ---------- Filters -> SPARQL ----------
function typeClass(key) {
  return TYPE_GROUPS[key] ? TYPE_GROUPS[key][0] : `<${BASE}ontology/${key}>`;
}

function filterPattern({ ignoreCity = false } = {}) {
  const f = readFilters();
  const p = [`  ?acc a ${typeClass(f.type)} ;\n       rdfs:label ?label ;\n       schema:address ?addr .`];
  if (f.stars.length) {
    const levels = f.stars.filter((s) => s !== "none").map(Number);
    const conds = [];
    if (levels.length) conds.push(`(BOUND(?lvlf) && ?lvlf IN (${levels.join(", ")}))`);
    if (f.stars.includes("none")) conds.push("!BOUND(?lvlf)");
    p.push(`  OPTIONAL { ?acc vocab:categoryLevel ?lvlf }\n  FILTER(${conds.join(" || ")})`);
  }
  if (f.city && !ignoreCity) p.push(`  ?addr vocab:inCity <${CITY}${f.city}> .`);
  if (f.pc) p.push(`  ?addr schema:postalCode ?pcf . FILTER(STRSTARTS(?pcf, ${lit(f.pc)}))`);
  if (f.name) p.push(`  FILTER(CONTAINS(LCASE(?label), ${lit(f.name.toLowerCase())}))`);
  return p.join("\n");
}

const resultsQuery = () => `SELECT ?acc ?label ?type ?level ?street ?pc ?cityName WHERE {
${filterPattern()}
  ?acc sesame:directType ?type .          # most specific class (GraphDB)
  OPTIONAL { ?acc vocab:categoryLevel ?level }
  OPTIONAL { ?addr schema:streetAddress ?street }
  OPTIONAL { ?addr schema:postalCode ?pc }
  OPTIONAL { ?addr vocab:inCity/rdfs:label ?cityName }
}
ORDER BY DESC(?level) ?label ?acc
LIMIT ${PAGE_SIZE} OFFSET ${(state.page - 1) * PAGE_SIZE}`;

const countQuery = () => `SELECT (COUNT(DISTINCT ?acc) AS ?n) WHERE {\n${filterPattern()}\n}`;
const mapQuery = () => `SELECT ?city (COUNT(DISTINCT ?acc) AS ?n) WHERE {
${filterPattern({ ignoreCity: true })}
  ?addr vocab:inCity ?city .
} GROUP BY ?city`;

// ---------- Initial load ----------
async function init() {
  const sel = $("f-type");
  const g1 = document.createElement("optgroup"); g1.label = "Agrupaciones";
  Object.entries(TYPE_GROUPS).forEach(([k, [, label]]) => g1.append(new Option(label, k)));
  const g2 = document.createElement("optgroup"); g2.label = "Tipo concreto";
  Object.entries(TYPE_NAMES).sort((a, b) => a[1].localeCompare(b[1], "es"))
    .forEach(([k, label]) => g2.append(new Option(label, k)));
  sel.append(g1, g2);

  const [cities, kpi] = await Promise.all([
    graph(`SELECT ?city ?name ?wd WHERE { ?city a schema:City ; rdfs:label ?name . OPTIONAL { ?city owl:sameAs ?wd } } ORDER BY ?name`,
          "Lista de municipios y su enlace owl:sameAs"),
    graph(`SELECT (COUNT(DISTINCT ?a) AS ?acc) (COUNT(DISTINCT ?c) AS ?cities) (COUNT(DISTINCT ?h) AS ?hotels) WHERE {
             { ?a a schema:LodgingBusiness } UNION { ?c a schema:City } UNION { ?h a schema:Hotel } }`, "Cifras de la cabecera"),
  ]);
  cities.forEach((c) => {
    const slug = localName(c.city);
    state.cities.set(slug, c);
    $("f-city").append(new Option(c.name, slug));
  });
  const k = kpi[0];
  $("logo").innerHTML = LOGO_STAR;
  $("kpis").innerHTML = [[k.acc, "alojamientos", "bed"], [k.hotels, "hoteles", "building"], [k.cities, "municipios", "pin"]]
    .map(([n, l, i]) => `<div class="kpi">${icon(i, 22)}<div><b>${fmt(n)}</b><span>${l}</span></div></div>`).join("");
  renderLegend();

  loadFromUrl();
  state.map = L.map("map").setView([40.5, -3.7], 8);
  osmLayer().addTo(state.map);
  state.markers = L.layerGroup().addTo(state.map);
  state.info = await cityInfo(cities.filter((c) => c.wd).map((c) => c.wd));

  const onChange = () => { state.page = 1; refresh(); };
  ["f-type", "f-city"].forEach((id) => $(id).addEventListener("change", onChange));
  $("f-stars").addEventListener("change", onChange);
  ["f-pc", "f-name"].forEach((id) => $(id).addEventListener("input", debounce(onChange, 350)));
  $("f-reset").addEventListener("click", () => {
    $("f-type").value = "todos";
    document.querySelectorAll("#f-stars input").forEach((c) => (c.checked = false));
    ["f-city", "f-pc", "f-name"].forEach((id) => ($(id).value = ""));
    onChange();
  });
  refresh();
}

// ---------- Refresh results, pager, map ----------
async function refresh() {
  saveToUrl();
  const q = resultsQuery();
  $("status").textContent = "Cargando…";
  try {
    const [rows, count, counts] = await Promise.all([graph(q, "Resultados (página actual)"),
      graph(countQuery(), "Número total de resultados"), graph(mapQuery(), "Resultados por municipio (mapa)")]);
    const total = Number(count[0].n);
    $("results-title").textContent = `${fmt(total)} alojamientos`;
    $("status").textContent = "";
    renderTable(rows);
    renderPager(total);
    drawMap(counts);
    renderCityBanner();
  } catch (e) {
    $("status").innerHTML = `<span class="error">No se han podido cargar los datos. Comprueba que el servidor de datos está en marcha.</span>`;
    console.error(e);
  }
}

function renderTable(rows) {
  const back = encodeURIComponent(location.search);
  $("results").innerHTML = rows.map((r) => {
    const href = `ficha.html?id=${encodeURIComponent(localName(r.acc))}&volver=${back}`;
    const place = [r.pc, r.cityName].filter(Boolean).join(" · ");
    return `<a class="card" href="${esc(href)}" style="--c:${typeStyle(r.type).color}">
      <div class="card-top">${typeBadge(r.type)}${r.level ? `<span class="stars">${stars(r.level)}</span>` : ""}</div>
      <h3>${esc(r.label)}</h3>
      ${r.street ? `<p class="addr">${esc(r.street)}</p>` : ""}
      ${place ? `<p class="place">${icon("pin", 14)} ${esc(place)}</p>` : ""}
    </a>`;
  }).join("") || `<p class="empty">Ningún alojamiento cumple los filtros. Prueba a quitar alguno.</p>`;
}

function renderLegend() {
  const names = { hotel: "Hoteles", hostal: "Hostales y pensiones", rural: "Rural", apartamento: "Apartamentos",
                  vivienda: "Viviendas turísticas", camping: "Campings" };
  $("legend").innerHTML = Object.entries(FAMILIES).map(([k, f]) =>
    `<span style="--c:${f.color}">${icon(f.icon, 13)} ${names[k]}</span>`).join("");
}

function renderPager(total) {
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  if (state.page > pages) state.page = pages;
  const from = total ? (state.page - 1) * PAGE_SIZE + 1 : 0, to = Math.min(state.page * PAGE_SIZE, total);
  const btn = (label, page, disabled, title) =>
    `<button type="button" class="secondary" data-page="${page}" ${disabled ? "disabled" : ""} title="${title}">${label}</button>`;
  $("pager").innerHTML = pages <= 1 ? (total ? `<span>${fmt(total)} resultados</span>` : "") :
    btn("«", 1, state.page === 1, "Primera página") +
    btn("‹ Anterior", state.page - 1, state.page === 1, "Página anterior") +
    `<span>${fmt(from)}–${fmt(to)} de ${fmt(total)} · página ${state.page} de ${pages}</span>` +
    btn("Siguiente ›", state.page + 1, state.page === pages, "Página siguiente") +
    btn("»", pages, state.page === pages, "Última página");
  $("pager").querySelectorAll("button[data-page]").forEach((b) => b.addEventListener("click", () => {
    state.page = Number(b.dataset.page);
    refresh();
    $("results-title").scrollIntoView({ behavior: "smooth", block: "start" });
  }));
}

function drawMap(counts) {
  state.markers.clearLayers();
  const selected = $("f-city").value;
  counts.forEach((c) => {
    const slug = localName(c.city), city = state.cities.get(slug);
    const info = city && city.wd && state.info.get(city.wd);
    if (!info || info.lat == null) return;
    const n = Number(c.n), isSel = slug === selected;
    L.circleMarker([info.lat, info.lon], {
      radius: Math.min(4 + Math.sqrt(n) * 1.6, 34), weight: isSel ? 3 : 1.5,
      color: isSel ? "#1b2a4a" : "#ffffff", fillColor: isSel ? "#f2a900" : "#c8102e", fillOpacity: 0.75,
    }).bindTooltip(`${esc(city.name)}: ${fmt(n)} alojamientos`)
      .on("click", () => { $("f-city").value = slug; state.page = 1; refresh(); })
      .addTo(state.markers);
  });
}

function renderCityBanner() {
  const slug = $("f-city").value, city = slug && state.cities.get(slug);
  if (!city) { $("city-banner").innerHTML = ""; return; }
  const info = (city.wd && state.info.get(city.wd)) || {};
  $("city-banner").innerHTML = `<div class="city-banner">
    ${info.image ? `<img src="${esc(info.image)}?width=480" alt="${esc(city.name)}">` : ""}
    <div><p class="eyebrow">Municipio seleccionado</p><h3>${esc(city.name)}</h3>
      ${info.population ? `<p>${icon("people", 15)} ${fmt(info.population)} habitantes</p>` : ""}
      <p>${city.wd ? `<a href="${esc(wikidataPage(city.wd))}" target="_blank" rel="noopener">Ver en Wikidata (${esc(localName(city.wd))})</a> · ` : ""}
      <button type="button" class="linklike" id="clear-city">Ver todos los municipios</button></p></div></div>`;
  $("clear-city").addEventListener("click", () => { $("f-city").value = ""; state.page = 1; refresh(); });
}

function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

init().catch((e) => {
  $("status").innerHTML = `<span class="error">No se han podido cargar los datos. Comprueba que el servidor de datos está en marcha.</span>`;
  console.error(e);
});
