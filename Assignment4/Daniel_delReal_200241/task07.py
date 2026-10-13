# -*- coding: utf-8 -*-
"""Task07_Querying_RDFs.ipynb

Task 07: Querying RDF(s)
"""

# !pip install rdflib
# !pip install oeg-sw-class

import urllib.request
github_storage = "https://raw.githubusercontent.com/FacultadInformatica-LinkedData/Curso2026-2027/master/Assignment4/course_materials"

from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS
from oeg_sw_class import Report

# Do not change the name of the variables
g = Graph()
g.namespace_manager.bind('ns', Namespace("http://somewhere#"), override=False)
g.parse(github_storage + "/rdf/data07.ttl", format="TTL")
report = Report()


# ==========================================
# TASK 7.1a
# ==========================================
# Spanish: Para todas las clases, enumera cada classURI. Si la clase pertenece a otra clase, indica su superclase. 
# Realiza el ejercicio en RDFLib devolviendo una lista de tuplas: (clase, superclase) denominada "result". 
# Si una clase no tiene superclase, devuelve None como superclase.
#
# English: For all classes, list each classURI. If the class belogs to another class, then list its superclass. 
# Do the exercise in RDFLib returning a list of Tuples: (class, superclass) called "result". 
# If a class does not have a super class, then return None as the superclass

result = []

# Obtener todas las clases explicitas e implicitas
classes = set(g.subjects(RDF.type, RDFS.Class))
classes.update(g.subjects(RDF.type, Namespace("http://www.w3.org/2002/07/owl#").Class))
classes.update(g.subjects(RDFS.subClassOf, None))
classes.update(g.objects(None, RDFS.subClassOf))

for c in classes:
    superclasses = list(g.objects(c, RDFS.subClassOf))
    if superclasses:
        for sc in superclasses:
            result.append((c, sc))
    else:
        result.append((c, None))

# Eliminar duplicados manteniendo tuplas
result = list(set(result))

# Visualize the results
for r in result:
    print(r)

## Validation: Do not remove
report.validate_07_1a(result)


# ==========================================
# TASK 7.1b
# ==========================================
# Spanish: Repite el mismo ejercicio en SPARQL, devolviendo las variables ?c (clase) y ?sc (superclase)
# English: Repeat the same exercise in SPARQL, returning the variables ?c (class) and ?sc (superclass)

query = """
SELECT DISTINCT ?c ?sc WHERE {
  { ?c a rdfs:Class } UNION { ?c rdfs:subClassOf ?x }
  OPTIONAL { ?c rdfs:subClassOf ?sc }
}
"""

for r in g.query(query):
    print(r.c, r.sc)

## Validation: Do not remove
report.validate_07_1b(query, g)


# ==========================================
# TASK 7.2a
# ==========================================
# Spanish: Enumera todos los individuos de "Person" con RDFLib (ten en cuenta las subclases). 
# Devuelve los URI de los individuos en una lista llamada "individuals".
#
# English: List all individuals of "Person" with RDFLib (remember the subClasses). 
# Return the individual URIs in a list called "individuals"

ns = Namespace("http://oeg.fi.upm.es/def/people#")

# Obtener todas las subclases de Person recursivamente
person_classes = {ns.Person}
added = True
while added:
    added = False
    for sub, _, obj in g.triples((None, RDFS.subClassOf, None)):
        if obj in person_classes and sub not in person_classes:
            person_classes.add(sub)
            added = True

individuals = []
for ind, _, cls in g.triples((None, RDF.type, None)):
    if cls in person_classes and ind not in individuals:
        individuals.append(ind)

# Visualize results
for i in individuals:
    print(i)

# Validation: Do not remove
report.validate_07_02a(individuals)


# ==========================================
# TASK 7.2b
# ==========================================
# Spanish: Repite el mismo ejercicio en SPARQL, devolviendo los URI individuales en una variable ?ind.
# English: Repeat the same exercise in SPARQL, returning the individual URIs in a variable ?ind

query = """
PREFIX ns: <http://oeg.fi.upm.es/def/people#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?ind WHERE {
  ?ind a ?type .
  ?type rdfs:subClassOf* ns:Person .
}
"""

for r in g.query(query):
    print(r.ind)

## Validation: Do not remove
report.validate_07_02b(g, query)


# ==========================================
# TASK 7.3
# ==========================================
# Spanish: Enumera el nombre y el tipo de quienes conocen a Curry (solo en SPARQL). 
# Utiliza el nombre y el tipo como variables en la consulta.
#
# English: List the name and type of those who know Curry (in SPARQL only). 
# Use name and type as variables in the query

query = """
PREFIX ns: <http://oeg.fi.upm.es/def/people#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?name ?type WHERE {
  ?person ns:knows ?curry .
  ?curry rdfs:label "Curry" .
  ?person rdfs:label ?name .
  ?person a ?type .
}
"""

for r in g.query(query):
    print(r.name, r.type)

## Validation: Do not remove
report.validate_07_03(g, query)


# ==========================================
# Task 7.4
# ==========================================
# Spanish: Enumera los nombres de aquellas entidades que tengan un companero de trabajo que tenga un perro, 
# o que tengan un companero de trabajo que tenga un companero de trabajo que tenga un perro (en SPARQL). 
# Devuelve los resultados en una variable llamada «name».
#
# English: List the name of those entities who have a colleague with a dog, or that have a collegue who has 
# a colleague who has a dog (in SPARQL). Return the results in a variable called name

query = """
PREFIX ns: <http://oeg.fi.upm.es/def/people#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?name WHERE {
  ?entity rdfs:label ?name .
  {
    ?entity ns:hasColleague ?colleague .
    ?colleague ns:ownsPet ?pet .
  }
  UNION
  {
    ?entity ns:hasColleague ?col1 .
    ?col1 ns:hasColleague ?col2 .
    ?col2 ns:ownsPet ?pet .
  }
}
"""

for r in g.query(query):
    print(r.name)

## Validation: Do not remove
report.validate_07_04(g, query)
report.save_report("_Task_07")