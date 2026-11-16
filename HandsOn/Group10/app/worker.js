// SPARQL engine for the Group 10 knowledge graph.
// Runs Oxigraph (WebAssembly) in a worker, loads kg.ttl and answers queries.
import init, { Store } from "./oxigraph/web.js";

let store = null;

async function boot() {
  const t0 = performance.now();
  const wasm = await (await fetch(new URL("./oxigraph/web_bg.wasm", import.meta.url))).arrayBuffer();
  await init({ module_or_path: wasm });
  postMessage({ type: "progress", step: "engine" });
  const res = await fetch(new URL("./kg.ttl.txt", import.meta.url));
  if (!res.ok) throw new Error("kg.ttl " + res.status);
  const ttl = await res.text();
  postMessage({ type: "progress", step: "parsing" });
  store = new Store();
  store.load(ttl, { format: "text/turtle", no_transaction: true });
  postMessage({ type: "ready", size: store.size, ms: Math.round(performance.now() - t0) });
}

onmessage = (e) => {
  const { id, query } = e.data;
  if (!store) {
    postMessage({ type: "result", id, error: "El motor todavía se está cargando." });
    return;
  }
  const t0 = performance.now();
  try {
    const json = store.query(query, { results_format: "application/sparql-results+json" });
    postMessage({ type: "result", id, json, ms: performance.now() - t0 });
  } catch (err) {
    postMessage({ type: "result", id, error: String(err && err.message ? err.message : err) });
  }
};

boot().catch((err) => postMessage({ type: "failed", error: String(err && err.message ? err.message : err) }));
