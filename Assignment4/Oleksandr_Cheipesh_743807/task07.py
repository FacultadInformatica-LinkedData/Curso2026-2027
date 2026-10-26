# Task 07: Querying RDF(s)
# !pip install rdflib
# !pip install oeg-sw-class
github_storage = "https://raw.githubusercontent.com/FacultadInformatica-LinkedData/Curso2026-2027/master/Assignment4/course_materials"

from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS
from oeg_sw_class import Report
# Do not change the name of the variables
g = Graph()
g.namespace_manager.bind('ns', Namespace("http://somewhere#"), override=False)
g.parse(github_storage+"/rdf/data07.ttl", format="TTL")
report = Report()

# TASK 7.1a
result = []
for c in g.subjects(RDF.type, RDFS.Class):
  supers = list(g.objects(c, RDFS.subClassOf))
  if supers:
    for sc in supers:
      result.append((c, sc))
  else:
    result.append((c, None))

for r in result:
  print(r)

report.validate_07_1a(result)

# TASK 7.1b
query = """ SELECT ?c ?sc WHERE {
  ?c a rdfs:Class .
  OPTIONAL { ?c rdfs:subClassOf ?sc }
}
"""

for r in g.query(query):
  print(r.c, r.sc)

report.validate_07_1b(query,g)

# TASK 7.2a
ns = Namespace("http://oeg.fi.upm.es/def/people#")

individuals = []
for cls in g.transitive_subjects(RDFS.subClassOf, ns.Person):
  for ind in g.subjects(RDF.type, cls):
    if ind not in individuals:
      individuals.append(ind)

for i in individuals:
  print(i)

report.validate_07_02a(individuals)

# TASK 7.2b
query = """PREFIX ns: <http://oeg.fi.upm.es/def/people#>
SELECT DISTINCT ?ind WHERE {
  ?ind a ?c .
  ?c rdfs:subClassOf* ns:Person .
}
"""

for r in g.query(query):
  print(r.ind)

report.validate_07_02b(g, query)

# TASK 7.3
query =  """
PREFIX ns:  <http://oeg.fi.upm.es/def/people#>
SELECT ?name ?type WHERE {
  ?x ns:knows ns:Curry ;
     rdfs:label ?name ;
     a ?type .
}
"""

for r in g.query(query):
  print(r.name, r.type)

report.validate_07_03(g, query)

# Task 7.4
query =  """
PREFIX ns:  <http://oeg.fi.upm.es/def/people#>
SELECT DISTINCT ?name WHERE {
  ?x rdfs:label ?name .
  { ?x ns:hasColleague ?c1 . ?c1 ns:ownsPet ?pet }
  UNION
  { ?x ns:hasColleague ?c1 . ?c1 ns:hasColleague ?c2 . ?c2 ns:ownsPet ?pet }
}
"""

for r in g.query(query):
  print(r.name)

report.validate_07_04(g,query)
report.save_report("_Task_07")
