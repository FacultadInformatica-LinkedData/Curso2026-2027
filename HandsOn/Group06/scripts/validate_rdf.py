"""Parse the generated graph and run every query in queries.sparql."""

from __future__ import annotations

import re
from pathlib import Path

from rdflib import Graph


GROUP_DIR = Path(__file__).resolve().parents[1]
RDF_FILE = GROUP_DIR / "rdf" / "madrid-culture.ttl"
QUERY_FILE = GROUP_DIR / "rdf" / "queries.sparql"


def main() -> None:
    graph = Graph().parse(RDF_FILE, format="turtle")
    query_text = QUERY_FILE.read_text(encoding="utf-8")
    prefix_block, *sections = re.split(r"(?=^# Q\d+\.)", query_text, flags=re.MULTILINE)

    expected_row_counts = {
        1: 5,
        2: 120,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
    }

    for number, section in enumerate(sections, start=1):
        rows = list(graph.query(prefix_block + section))
        expected = expected_row_counts.get(number)
        if expected is not None and len(rows) != expected:
            raise AssertionError(
                f"Q{number} returned {len(rows)} rows; expected {expected}."
            )
        print(f"Q{number}: {len(rows)} row(s)")

    print(f"Validation passed: {len(graph)} unique triples in valid Turtle syntax.")


if __name__ == "__main__":
    main()
