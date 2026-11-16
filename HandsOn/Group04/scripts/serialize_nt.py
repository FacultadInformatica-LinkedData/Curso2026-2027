"""Serialize the RMLMapper-generated Turtle graphs as N-Triples (requires rdflib)."""
from pathlib import Path
from rdflib import Graph

ROOT = Path(__file__).resolve().parents[1]
for name in ('airquality', 'airquality-with-links'):
    source = ROOT / 'rdf' / f'{name}.ttl'
    target = ROOT / 'rdf' / f'{name}.nt'
    graph = Graph().parse(source, format='turtle')
    graph.serialize(destination=target, format='nt')
    print(f'{target.relative_to(ROOT)}: {len(graph)} triples')
