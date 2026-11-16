"""Madrid Smart City - local server.

Serves the web application and acts as a small proxy so the browser does not
need CORS:
  /sparql?query=...    -> GraphDB repository (our knowledge graph)
  /wikidata?query=...  -> Wikidata Query Service (sent with an identifying User-Agent)

Usage:  python server.py        then open http://localhost:8000
Only standard library is required (certifi is used if installed).
"""
import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HOST, PORT = "127.0.0.1", 8000
GRAPHDB = os.environ.get("GRAPHDB_ENDPOINT", "http://localhost:7200/repositories/alojamientos-turisticos")
WIKIDATA = "https://query.wikidata.org/sparql"
USER_AGENT = "MadridSmartCity/1.0 (UPM Semantic Web course project; local demo)"
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

try:  # some Windows Python installs have an outdated certificate store
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

_wikidata_cache = {}


def run_sparql(endpoint, query, extra_headers=None):
    data = urllib.parse.urlencode({"query": query}).encode()
    headers = {"Accept": "application/sparql-results+json",
               "Content-Type": "application/x-www-form-urlencoded",
               "User-Agent": USER_AGENT}
    headers.update(extra_headers or {})
    req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")
    ctx = SSL_CTX if endpoint.startswith("https") else None
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        return resp.read()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send(self, status, body, ctype="application/sparql-results+json"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _proxy(self, query):
        path = urllib.parse.urlparse(self.path).path
        try:
            if path == "/sparql":
                body = run_sparql(GRAPHDB, query)
            else:  # /wikidata, cached because the same municipalities are asked again and again
                if query not in _wikidata_cache:
                    _wikidata_cache[query] = run_sparql(WIKIDATA, query)
                body = _wikidata_cache[query]
            self._send(200, body)
        except urllib.error.HTTPError as e:
            self._send(e.code, json.dumps({"error": e.read().decode(errors="replace")[:500]}).encode(), "application/json")
        except Exception as e:  # GraphDB stopped, no internet...
            self._send(502, json.dumps({"error": str(e)}).encode(), "application/json")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/sparql", "/wikidata"):
            query = urllib.parse.parse_qs(parsed.query).get("query", [""])[0]
            return self._proxy(query)
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path not in ("/sparql", "/wikidata"):
            return self._send(404, b"{}", "application/json")
        length = int(self.headers.get("Content-Length", 0))
        form = urllib.parse.parse_qs(self.rfile.read(length).decode())
        return self._proxy(form.get("query", [""])[0])

    def log_message(self, fmt, *args):  # keep the console readable
        if "/sparql" not in self.path and "/wikidata" not in self.path:
            super().log_message(fmt, *args)


if __name__ == "__main__":
    print(f"GraphDB endpoint: {GRAPHDB}")
    print(f"Madrid Smart City running at http://localhost:{PORT}  (Ctrl+C to stop)")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
