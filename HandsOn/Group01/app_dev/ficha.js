// Madrid Smart City - page of a single accommodation (ficha.html?id=<signatura>).

const params = new URLSearchParams(location.search);
const id = params.get("id") || "";
const backSearch = params.get("volver") || "";
$("back").href = "index.html" + backSearch;
$("logo").innerHTML = LOGO_STAR;

async function load() {
  if (!/^[A-Za-z0-9-]+$/.test(id)) return notFound();
  const uri = `<${ACC}${id}>`;
  const [r] = await graph(`SELECT ?label ?name ?type ?level ?street ?pc ?locality ?city ?cityName ?wd WHERE {
  ${uri} rdfs:label ?label ; sesame:directType ?type ; schema:address ?addr .
  OPTIONAL { ${uri} schema:name ?name }
  OPTIONAL { ${uri} vocab:categoryLevel ?level }
  OPTIONAL { ?addr schema:streetAddress ?street }
  OPTIONAL { ?addr schema:postalCode ?pc }
  OPTIONAL { ?addr schema:addressLocality ?locality }
  OPTIONAL { ?addr vocab:inCity ?city . ?city rdfs:label ?cityName . OPTIONAL { ?city owl:sameAs ?wd } }
}`, "Datos del alojamiento");
  if (!r) return notFound();
  document.title = `${r.label} · Madrid Smart City`;

  const [infoMap, others, total] = await Promise.all([
    r.wd ? cityInfo([r.wd], "Wikidata: datos del municipio (vía owl:sameAs)") : new Map(),
    r.city ? graph(`SELECT ?acc ?label ?type ?level ?street WHERE {
      ?acc schema:address ?a ; rdfs:label ?label ; sesame:directType ?type .
      ?a vocab:inCity <${r.city}> . OPTIONAL { ?a schema:streetAddress ?street }
      OPTIONAL { ?acc vocab:categoryLevel ?level }
      FILTER(?acc != ${uri})
    } ORDER BY DESC(?level) ?label LIMIT 6`, "Otros alojamientos del municipio") : [],
    r.city ? graph(`SELECT (COUNT(?acc) AS ?n) WHERE { ?acc schema:address/vocab:inCity <${r.city}> }`, "Alojamientos del municipio") : [{ n: 0 }],
  ]);
  const info = (r.wd && infoMap.get(r.wd)) || {};
  const cityTotal = total[0].n;
  const style = typeStyle(r.type);
  const address = [r.street, [r.pc, r.locality].filter(Boolean).join(" ")].filter(Boolean).join(", ");
  const back = encodeURIComponent(backSearch);

  $("content").innerHTML = `
  <section class="cover" style="--c:${style.color}${info.image ? `;--img:url('${esc(info.image)}?width=1400')` : ""}">
    <div class="cover-text">
      ${typeBadge(r.type)}
      <h1>${esc(r.label)}</h1>
      ${r.level ? `<p class="stars big" title="Categoría ${r.level}">${stars(r.level)}</p>` : '<p class="no-cat">Sin categoría oficial</p>'}
      ${address ? `<p class="cover-addr">${icon("pin", 18)} ${esc(address)}</p>` : ""}
    </div>
  </section>

  <div class="ficha">
    <section class="panel">
      <h2>Datos del alojamiento</h2>
      <dl class="facts">
        <dt>Tipo</dt><dd>${esc(typeName(r.type))}</dd>
        <dt>Categoría</dt><dd>${r.level ? `<span class="stars">${stars(r.level)}</span>` : "Sin categoría"}</dd>
        <dt>Dirección</dt><dd>${esc(r.street || "No disponible")}</dd>
        <dt>Código postal</dt><dd>${esc(r.pc || "No disponible")}</dd>
        <dt>Municipio</dt><dd>${esc(r.cityName || "No indicado en el registro")}</dd>
        <dt>Nº de registro</dt><dd>${esc(id)}</dd>
      </dl>
      ${!r.name ? '<p class="hint">Este alojamiento no tiene nombre comercial en el registro; se muestra su tipo y número de registro.</p>' : ""}
    </section>

    <section class="panel">
      ${r.city ? `
        <h2>Sobre ${esc(r.cityName)}</h2>
        <div class="stats">
          <div>${icon("people", 22)}<b>${info.population ? fmt(info.population) : "—"}</b><span>habitantes</span></div>
          <div>${icon("bed", 22)}<b>${fmt(cityTotal)}</b><span>alojamientos</span></div>
        </div>
        ${info.lat != null ? '<div id="minimap"></div><p class="hint">Ubicación del municipio (el registro no incluye la ubicación exacta del alojamiento).</p>' : ""}
        ${r.wd ? `<p><a class="pill-link" href="${esc(wikidataPage(r.wd))}" target="_blank" rel="noopener">Ver ${esc(r.cityName)} en Wikidata (${esc(localName(r.wd))}) →</a></p>
          <p class="hint">Población, imagen y ubicación vienen de Wikidata gracias al enlace <code>owl:sameAs</code> de nuestro grafo.</p>` : ""}
      ` : '<h2>Municipio</h2><p class="muted">El registro no indica el municipio de este alojamiento.</p>'}
    </section>
  </div>

  ${others.length ? `<section class="others">
    <div class="results-head"><h2>Otros alojamientos en ${esc(r.cityName)}</h2>
      <a href="index.html?municipio=${encodeURIComponent(localName(r.city))}">Ver los ${fmt(cityTotal)} →</a></div>
    <div class="cards">${others.map((o) => `<a class="card" style="--c:${typeStyle(o.type).color}"
        href="ficha.html?id=${encodeURIComponent(localName(o.acc))}&volver=${back}">
        <div class="card-top">${typeBadge(o.type)}${o.level ? `<span class="stars">${stars(o.level)}</span>` : ""}</div>
        <h3>${esc(o.label)}</h3>${o.street ? `<p class="addr">${esc(o.street)}</p>` : ""}</a>`).join("")}</div>
  </section>` : ""}`;

  if (info.lat != null) {
    const m = L.map("minimap", { scrollWheelZoom: false }).setView([info.lat, info.lon], 12);
    osmLayer().addTo(m);
    L.circleMarker([info.lat, info.lon], { radius: 10, color: "#fff", weight: 2, fillColor: style.color, fillOpacity: 0.9 })
      .bindTooltip(r.cityName).addTo(m);
  }
}

function notFound() {
  $("content").innerHTML = '<div class="panel"><h2>Alojamiento no encontrado</h2><p>Revisa el enlace o vuelve a los resultados.</p></div>';
}

load().catch((e) => {
  console.error(e);
  $("content").innerHTML = '<div class="panel"><p class="error">No se han podido cargar los datos. Comprueba que el servidor de datos está en marcha.</p></div>';
});
