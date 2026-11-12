# Task 06: Modifying RDF(s)
# !pip install rdflib
# !pip install oeg-sw-class

from rdflib import Graph, Namespace, Literal, XSD
from rdflib.namespace import RDF, RDFS
from oeg_sw_class import Report
# Do not change the name of the variables
g = Graph()
g.namespace_manager.bind('ns', Namespace("http://somewhere#"), override=False)
r = Report()

ns = Namespace("http://mydomain.org#")
g.add((ns.Researcher, RDF.type, RDFS.Class))
for s, p, o in g:
  print(s,p,o)

# Task 6.0
person = Namespace("http://oeg.fi.upm.es/resource/person/")
organization = Namespace("http://oeg.fi.upm.es/resource/organization/")
ontology = Namespace("http://oeg.fi.upm.es/def/people#")
university = Namespace("http://oeg.fi.upm.es/resource/university/")
g.bind("person", person)
g.bind("organization", organization)
g.bind("ontology", ontology)
g.bind("university", university)

# Task 6.1
def add_class(cls, label, parent=None):
  g.add((cls, RDF.type, RDFS.Class))
  g.add((cls, RDFS.label, Literal(label, datatype=XSD.string)))
  if parent is not None:
    g.add((cls, RDFS.subClassOf, parent))

add_class(ontology.Person, "Person")
add_class(ontology.Professor, "Professor", ontology.Person)
add_class(ontology.FullProfessor, "FullProfessor", ontology.Professor)
add_class(ontology.AssistantProfessor, "AssistantProfessor", ontology.Professor)
add_class(ontology.AssociateProfessor, "AssociateProfessor", ontology.Professor)
add_class(ontology.InterimAssociateProfessor, "InterimAssociateProfessor", ontology.AssociateProfessor)

for s, p, o in g:
  print(s,p,o)

r.validate_task_06_01(g)

# Task 6.2
add_class(ontology.University, "University")

for s, p, o in g:
  print(s,p,o)

r.validate_task_06_02(g)

# Task 6.3
def add_property(prop, label, domain, range_):
  g.add((prop, RDF.type, RDF.Property))
  g.add((prop, RDFS.label, Literal(label, datatype=XSD.string)))
  g.add((prop, RDFS.domain, domain))
  g.add((prop, RDFS.range, range_))

add_property(ontology.hasName, "hasName", ontology.Person, RDFS.Literal)
add_property(ontology.hasColleague, "hasColleague", ontology.Person, ontology.Person)
add_property(ontology.hasHomePage, "hasHomePage", ontology.FullProfessor, RDFS.Literal)
add_property(ontology.affiliatedWith, "affiliatedWith", ontology.Person, ontology.University)

for s, p, o in g:
  print(s,p,o)

r.validate_task_06_03(g)

# Task 6.4
g.add((person.Raul, RDF.type, ontology.FullProfessor))
g.add((person.Juan, RDF.type, ontology.AssistantProfessor))
g.add((person.Sven, RDF.type, ontology.Person))
g.add((person.Raul, RDFS.label, Literal("Raúl", datatype=XSD.string)))
g.add((person.Juan, RDFS.label, Literal("Juan", datatype=XSD.string)))
g.add((person.Sven, RDFS.label, Literal("Sven", datatype=XSD.string)))
g.add((person.Raul, ontology.hasColleague, person.Juan))
g.add((person.Juan, ontology.hasColleague, person.Sven))
g.add((person.Sven, ontology.affiliatedWith, university.Mannheim))
g.add((person.Raul, ontology.hasHomePage, Literal("http://oeg.fi.upm.es", datatype=XSD.string)))
g.add((person.Juan, ontology.hasName, Literal("Juan Cano de Benito", datatype=XSD.string)))

for s, p, o in g:
  print(s,p,o)

r.validate_task_06_04(g)

# Task 6.5
foaf = Namespace("http://xmlns.com/foaf/0.1/")
g.bind("foaf", foaf)

g.add((person.Juan, foaf.mbox, Literal("juan.cano@upm.es", datatype=XSD.string)))
g.add((person.Juan, foaf.givenName, Literal("Juan", datatype=XSD.string)))
g.add((person.Juan, foaf.familyName, Literal("Cano de Benito", datatype=XSD.string)))

for s, p, o in g:
  print(s,p,o)

r.validate_task_06_05(g)

# Task 6.6
g.add((person.Juan, ontology.affiliatedWith, university.UPM))
g.add((person.Raul, ontology.affiliatedWith, university.UPM))
g.add((person.Sven, RDF.type, ontology.InterimAssociateProfessor))

for s, p, o in g:
  print(s,p,o)

r.validate_task_06_06(g)

# Task 6.7
g.add((university.UPM, RDF.type, ontology.University))
g.add((university.Mannheim, RDF.type, ontology.University))

for s, p, o in g:
  print(s,p,o)

r.validate_task_06_07(g)
r.save_report("_Task_06")
