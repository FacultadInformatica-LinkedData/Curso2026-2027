"""Materialize the RML mappings with Morph-KGC and write Turtle output."""

from __future__ import annotations

import os
from pathlib import Path

import morph_kgc


GROUP_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = GROUP_DIR / "rdf" / "madrid-culture.ttl"


def main() -> None:
    os.chdir(GROUP_DIR)
    graph = morph_kgc.materialize("configuration.ini")
    graph.bind("mc", "https://w3id.org/madrid-culture/ontology/")
    graph.bind("mcr", "https://w3id.org/madrid-culture/resource/")
    graph.bind("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
    graph.bind("schema", "http://schema.org/")
    graph.bind("xsd", "http://www.w3.org/2001/XMLSchema#")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    turtle = graph.serialize(format="turtle")
    OUTPUT_FILE.write_text(turtle.rstrip() + "\n", encoding="utf-8", newline="\n")
    print(f"Generated {len(graph)} unique triples in {OUTPUT_FILE.relative_to(GROUP_DIR)}.")


if __name__ == "__main__":
    main()
