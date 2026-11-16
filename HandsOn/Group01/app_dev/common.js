// Shared code for the Madrid Smart City pages: SPARQL access, Spanish labels and small helpers.

const PREFIXES = `PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX schema: <http://schema.org/>
PREFIX vocab: <http://smartcity.linkeddata.es/touristaccommodation/ontology/>
PREFIX sesame: <http://www.openrdf.org/schema/sesame#>
`;
const BASE = "http://smartcity.linkeddata.es/touristaccommodation/";
const ACC = BASE + "resource/Accommodation/";
const CITY = BASE + "resource/City/";

// User-facing names (Spanish) of the ontology classes; the ontology only has English labels.
const TYPE_NAMES = {
  ApartHotel: "Hotel-apartamento", BoardingHouse: "Casa de huéspedes", Camping: "Camping",
  Hostel: "Hostal", Hotel: "Hotel", Inn: "Hostería", Pension: "Pensión",
  RuralApartment: "Apartamento rural", RuralHotel: "Hotel rural", RuralHouse: "Casa rural",
  TouristApartment: "Apartamento turístico", TouristHome: "Vivienda de uso turístico",
};
// Visual family of each type: colour + icon (cards, badges, map legend).
const ICONS = {
  bed: '<path d="M3 18v-6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v6M3 18v2M21 18v2M3 15h18M7 10V7a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v3"/>',
  house: '<path d="M3 11l9-7 9 7M5 10v10h14V10M10 20v-6h4v6"/>',
  building: '<path d="M5 21V4a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v17M15 9h3a1 1 0 0 1 1 1v11M3 21h18M8 7h1M11 7h1M8 11h1M11 11h1M8 15h1M11 15h1"/>',
  tent: '<path d="M3 20L12 4l9 16M12 4v16M8 20l4-7 4 7M2 20h20"/>',
  pin: '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
  people: '<circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0M16 11a3 3 0 1 0 0-6M21 20a6 6 0 0 0-4-5.6"/>',
};
const FAMILIES = {
  hotel: { color: "#c8102e", icon: "bed" },
  hostal: { color: "#2563a8", icon: "bed" },
  rural: { color: "#2e8b57", icon: "house" },
  apartamento: { color: "#0f8b8d", icon: "building" },
  vivienda: { color: "#7b4fb3", icon: "house" },
  camping: { color: "#d97706", icon: "tent" },
};
const TYPE_FAMILY = {
  Hotel: "hotel", ApartHotel: "hotel", Hostel: "hostal", Pension: "hostal", BoardingHouse: "hostal", Inn: "hostal",
  RuralHouse: "rural", RuralApartment: "rural", RuralHotel: "rural", TouristApartment: "apartamento",
  TouristHome: "vivienda", Camping: "camping",
};
const icon = (name, size = 16) =>
  `<svg class="icon" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name]}</svg>`;
const typeStyle = (uri) => FAMILIES[TYPE_FAMILY[localName(uri)]] || FAMILIES.hotel;
const typeBadge = (uri) => {
  const s = typeStyle(uri);
  return `<span class="badge" style="--c:${s.color}">${icon(s.icon, 14)} ${esc(typeName(uri))}</span>`;
};
// 7-pointed star of the Madrid flag, used in the logo
const LOGO_STAR = `<svg class="logo-star" viewBox="0 0 100 100" aria-hidden="true"><polygon fill="currentColor" points="${
  Array.from({ length: 14 }, (_, i) => { const r = i % 2 ? 20 : 48, a = (Math.PI / 7) * i - Math.PI / 2;
    return `${50 + r * Math.cos(a)},${50 + r * Math.sin(a)}`; }).join(" ")}"/></svg>`;

// Groups in the type filter. They work thanks to the RDFS inference of GraphDB:
// "hoteles" = schema:Hotel = Hotel + ApartHotel + RuralHotel (aligned in ontology-updated.ttl).
const TYPE_GROUPS = {
  todos: ["vocab:Accommodation", "Todos los alojamientos"],
  rurales: ["vocab:RuralAccommodation", "Alojamientos rurales"],
  hoteles: ["schema:Hotel", "Todos los hoteles (incluye hoteles-apartamento y rurales)"],
};

const $ = (id) => document.getElementById(id);
const localName = (uri) => String(uri).split("/").pop();
const typeName = (uri) => TYPE_NAMES[localName(uri)] || localName(uri);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const lit = (s) => '"' + String(s).replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"';
const fmt = (n) => Number(n).toLocaleString("es-ES");
const stars = (n) => (n ? "★".repeat(Number(n)) : "Sin categoría");

// Every query the page runs is recorded (by label) and shown in the "SPARQL" panel.
const queryLog = new Map();
async function sparql(endpoint, query, label = "Consulta") {
  queryLog.set(label, { endpoint, query });
  renderQueryPanel();
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/sparql-results+json" },
    body: new URLSearchParams({ query }),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.error || res.statusText);
  return json.results.bindings.map((b) => Object.fromEntries(Object.entries(b).map(([k, v]) => [k, v.value])));
}
const graph = (q, label) => sparql("/sparql", PREFIXES + q, label);

// Wikidata page of an entity reached through owl:sameAs (http://www.wikidata.org/entity/Q... -> /wiki/Q...)
const wikidataPage = (uri) => "https://www.wikidata.org/wiki/" + localName(uri);

// Municipality context from Wikidata, following the owl:sameAs links of our City resources:
// coordinates (P625), population (P1082) and image (P18).
async function cityInfo(wikidataUris, label = "Wikidata: datos de los municipios (vía owl:sameAs)") {
  const info = new Map();
  if (!wikidataUris.length) return info;
  const values = wikidataUris.map((u) => "wd:" + localName(u)).join(" ");
  const rows = await sparql("/wikidata", `PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?item (SAMPLE(?coord) AS ?c) (MAX(?pop) AS ?p) (SAMPLE(?img) AS ?i) WHERE {
  VALUES ?item { ${values} }
  OPTIONAL { ?item wdt:P625 ?coord }   # coordenadas
  OPTIONAL { ?item wdt:P1082 ?pop }    # población
  OPTIONAL { ?item wdt:P18 ?img }      # imagen
} GROUP BY ?item`, label).catch((e) => { console.warn("Wikidata no disponible", e); return []; });
  rows.forEach((r) => {
    const m = /Point\(([-\d.]+) ([-\d.]+)\)/.exec(r.c || "");
    info.set(r.item, { lon: m ? +m[1] : null, lat: m ? +m[2] : null, population: r.p, image: r.i });
  });
  return info;
}

// ---------- "SPARQL" button + side panel with the queries of the current page ----------
const SPARQL_KEYWORDS = /^(SELECT|ASK|CONSTRUCT|DESCRIBE|WHERE|PREFIX|OPTIONAL|FILTER|UNION|VALUES|GROUP|BY|ORDER|DESC|ASC|LIMIT|OFFSET|DISTINCT|AS|COUNT|SAMPLE|MAX|MIN|BOUND|IN|NOT|EXISTS|CONTAINS|LCASE|STRSTARTS|SERVICE)$/i;
function highlightSparql(q) {
  return q.replace(/(<[^>\s]*>)|("(?:[^"\\]|\\.)*")|(#[^\n]*)|(\?\w+)|([A-Za-z]+)(:\w*)?|([^<"#?A-Za-z]+|.)/g,
    (t, iri, str, com, v, word, local) => {
      if (iri) return `<span class="q-iri">${esc(iri)}</span>`;
      if (str) return `<span class="q-str">${esc(str)}</span>`;
      if (com) return `<span class="q-com">${esc(com)}</span>`;
      if (v) return `<span class="q-var">${esc(v)}</span>`;
      if (word && local !== undefined) return `<span class="q-pfx">${esc(word)}:</span>${esc(local.slice(1))}`;
      if (word && SPARQL_KEYWORDS.test(word)) return `<span class="q-kw">${esc(word)}</span>`;
      return esc(t);
    });
}

function setupQueryPanel() {
  document.body.insertAdjacentHTML("beforeend", `
    <button id="sparql-fab" class="sparql-fab" type="button" aria-controls="sparql-panel" aria-expanded="false"
            title="Ver las consultas SPARQL de esta página">
      <span aria-hidden="true">{ }</span> SPARQL <b id="sparql-count">0</b></button>
    <div id="sparql-backdrop" class="sparql-backdrop" hidden></div>
    <aside id="sparql-panel" class="sparql-panel" aria-label="Consultas SPARQL" aria-hidden="true">
      <header>
        <div><h2>Consultas SPARQL</h2>
          <p>Lo que la aplicación pregunta para mostrar esta pantalla: a nuestro grafo en <b>GraphDB</b> y,
             siguiendo los enlaces <code>owl:sameAs</code>, a <b>Wikidata</b>. </p></div>
        <button id="sparql-close" type="button" class="sparql-close" aria-label="Cerrar">×</button>
      </header>
      <div id="sparql-list" class="sparql-list"></div>
    </aside>`);
  const open = (yes) => {
    $("sparql-panel").classList.toggle("open", yes);
    $("sparql-panel").setAttribute("aria-hidden", String(!yes));
    $("sparql-fab").setAttribute("aria-expanded", String(yes));
    $("sparql-backdrop").hidden = !yes;
  };
  $("sparql-fab").addEventListener("click", () => open(!$("sparql-panel").classList.contains("open")));
  $("sparql-close").addEventListener("click", () => open(false));
  $("sparql-backdrop").addEventListener("click", () => open(false));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") open(false); });
  $("sparql-list").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-copy]");
    if (!b) return;
    navigator.clipboard.writeText(queryLog.get(b.dataset.copy).query)
      .then(() => { b.textContent = "¡Copiada!"; setTimeout(() => (b.textContent = "Copiar"), 1500); });
  });
}

function renderQueryPanel() {
  if (!$("sparql-list")) return;
  $("sparql-count").textContent = queryLog.size;
  const openNow = new Set([...document.querySelectorAll("#sparql-list details[open]")].map((d) => d.dataset.label));
  // The main query of each page goes first and opens by default.
  const MAIN = ["Resultados (página actual)", "Datos del alojamiento"];
  const entries = [...queryLog].sort((a, b) => MAIN.includes(b[0]) - MAIN.includes(a[0]));
  let i = 0;
  $("sparql-list").innerHTML = entries.map(([label, { endpoint, query }]) => {
    const wd = endpoint === "/wikidata";
    const isOpen = openNow.size ? openNow.has(label) : i++ === 0;
    return `<details data-label="${esc(label)}" ${isOpen ? "open" : ""}>
      <summary><span class="q-src ${wd ? "wd" : "gdb"}">${wd ? "Wikidata" : "GraphDB"}</span> ${esc(label)}</summary>
      <div class="q-actions"><button type="button" data-copy="${esc(label)}">Copiar</button>
        ${wd ? `<a href="https://query.wikidata.org/#${encodeURIComponent(query)}" target="_blank" rel="noopener">Abrir en Wikidata Query Service ↗</a>` : ""}</div>
      <pre class="sparql">${highlightSparql(query)}</pre></details>`;
  }).join("") || '<p class="muted">Todavía no se ha lanzado ninguna consulta.</p>';
}
setupQueryPanel();

function osmLayer() {
  return L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  });
}
