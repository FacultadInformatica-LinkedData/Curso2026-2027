"""Registro de las consultas hechas durante una petición, para el panel «¿por qué ontología?»."""

import time
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_entries: ContextVar[list[dict] | None] = ContextVar("trace", default=None)


def start() -> list[dict]:
    """Empieza un registro nuevo para la petición en curso y lo devuelve."""
    entries: list[dict] = []
    _entries.set(entries)
    return entries


@contextmanager
def record(
    source: str, name: str, text: str, cached: bool = False, note: str | None = None
) -> Iterator[dict]:
    """Mide una consulta y la añade al registro de la petición (si hay uno abierto).

    `source` es "local" (grafo RDF del grupo), "wikidata" u "osrm". Quien llama rellena
    `entry["rows"]` con el número de resultados. `note` explica qué se hace con las filas: se
    añade al final del texto como comentario (`# …`), tanto si la consulta se ejecuta como si
    su resultado está en caché.
    """
    if note:
        text = text.rstrip() + "\n\n" + "\n".join(f"# {line}" for line in note.splitlines())
    entry = {
        "source": source, "name": name, "text": text, "rows": None, "ms": 0.0, "cached": cached,
    }
    began = time.perf_counter()
    try:
        yield entry
    finally:
        entry["ms"] = round((time.perf_counter() - began) * 1000, 1)
        entries = _entries.get()
        if entries is not None:
            entries.append(entry)
