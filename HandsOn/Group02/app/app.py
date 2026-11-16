"""Madrid Green Spaces: simple RDFLib + SPARQL browser application.
Run: python app.py ; visit http://127.0.0.1:5000
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import json
import unicodedata
from rdflib import Graph

ROOT = Path(__file__).resolve().parent
RDF = ROOT / 'parks-with-links-updated.ttl'
GRAPH = Graph()
GRAPH.parse(str(RDF), format='turtle')

PREFIXES = '''
PREFIX parks: <https://parques-jardines.madrid.data.es/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
'''

# SPARQL 1: search all parks with district and optional coordinates/Wikidata.
PARKS_QUERY = PREFIXES + '''
SELECT ?park ?name ?districtName ?lat ?lon ?wikidata ?url WHERE {
  ?park a parks:Park ; parks:parkName ?name .
  OPTIONAL { ?park parks:locatedInDistrict ?district .
             ?district rdfs:label ?districtName . }
  OPTIONAL { ?park parks:latitude ?lat . }
  OPTIONAL { ?park parks:longitude ?lon . }
  OPTIONAL { ?park owl:sameAs ?wikidata . }
  OPTIONAL { ?park parks:contentUrl ?url . }
} ORDER BY ?name
'''

# SPARQL 2: park totals grouped by district.
DISTRICT_QUERY = PREFIXES + '''
SELECT ?districtName (COUNT(DISTINCT ?park) AS ?total) WHERE {
  ?park a parks:Park ; parks:locatedInDistrict ?district .
  ?district rdfs:label ?districtName .
} GROUP BY ?districtName ORDER BY ?districtName
'''

# SPARQL 3: park-level Wikidata links.
WIKIDATA_QUERY = PREFIXES + '''
SELECT ?name ?wikidata WHERE {
  ?park a parks:Park ; parks:parkName ?name ; owl:sameAs ?wikidata .
  FILTER(STRSTARTS(STR(?wikidata), "http://www.wikidata.org/entity/"))
} ORDER BY ?name
'''


def normalized(text):
    decomposed = unicodedata.normalize('NFD', str(text))
    return ''.join(c for c in decomposed if unicodedata.category(c) != 'Mn').casefold().strip()


def value(v):
    return str(v) if v is not None else None


def decimal(v):
    try:
        return float(v) if v is not None else None
    except (ValueError, TypeError):
        return None


# Perform the three SPARQL queries against the actual RDF graph.
PARKS = []
seen = set()
for row in GRAPH.query(PARKS_QUERY):
    uri = str(row.park)
    if uri in seen:
        continue
    seen.add(uri)
    PARKS.append({
        'uri': uri,
        'name': value(row.name),
        'district': value(row.districtName) or 'Sin distrito',
        'lat': decimal(row.lat),
        'lon': decimal(row.lon),
        'wikidata': value(row.wikidata),
        'url': value(row.url),
    })
DISTRICTS = [{'name': str(r.districtName), 'total': int(r.total)} for r in GRAPH.query(DISTRICT_QUERY)]
WIKIDATA = [{'name': str(r.name), 'url': str(r.wikidata)} for r in GRAPH.query(WIKIDATA_QUERY)]

class Handler(BaseHTTPRequestHandler):
    def respond_json(self, obj):
        payload = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == '/api/parks':
            params = parse_qs(url.query)
            name = normalized(params.get('name', [''])[0])
            district = normalized(params.get('district', ['Todos'])[0])
            matches = [p for p in PARKS
                       if name in normalized(p['name'])
                       and (district in ('', 'todos') or normalized(p['district']) == district)]
            return self.respond_json({'total': len(matches), 'parks': matches})
        if url.path == '/api/districts':
            return self.respond_json({'districts': DISTRICTS})
        if url.path == '/api/wikidata':
            return self.respond_json({'total': len(WIKIDATA), 'links': WIKIDATA})
        if url.path == '/api/stats':
            return self.respond_json({'parks': len(PARKS), 'districts': len(DISTRICTS),
                                      'wikidata': len(WIKIDATA), 'triples': len(GRAPH)})
        paths = {'/': ROOT / 'static' / 'index.html',
                 '/static/style.css': ROOT / 'static' / 'style.css',
                 '/static/script.js': ROOT / 'static' / 'script.js'}
        filepath = paths.get(url.path)
        if filepath is None or not filepath.is_file():
            self.send_error(404, 'Not found')
            return
        content = filepath.read_bytes()
        typ = ('text/html' if filepath.suffix == '.html' else
               'text/css' if filepath.suffix == '.css' else 'text/javascript')
        self.send_response(200)
        self.send_header('Content-Type', typ + '; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

if __name__ == '__main__':
    print(f'Madrid Green Spaces: {len(GRAPH)} triples | {len(PARKS)} parques | {len(DISTRICTS)} distritos')
    print('Abre en tu navegador: http://127.0.0.1:5000')
    print('Salir: Ctrl + C')
    try:
        ThreadingHTTPServer(('127.0.0.1', 5000), Handler).serve_forever()
    except KeyboardInterrupt:
        print('\n Terminado')
