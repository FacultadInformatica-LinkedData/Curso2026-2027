# %% [markdown]
# **Task 07: Querying RDF(s)**

# %%
#!pip install rdflib
#!pip install oeg-sw-class
github_storage = "https://raw.githubusercontent.com/FacultadInformatica-LinkedData/Curso2026-2027/master/Assignment4/course_materials"

# %% [markdown]
# Spanish: Primero leemos los ficheros RDF
# 
# English: First let's read the RDF file

# %%
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS
from oeg_sw_class import Report
# Do not change the name of the variables
g = Graph()
g.namespace_manager.bind('ns', Namespace("http://somewhere#"), override=False)
g.parse(github_storage+"/rdf/data07.ttl", format="TTL")
report = Report()

# %% [markdown]
# **TASK 7.1a:**
# 
# Spanish: Para todas las clases, enumera cada classURI. Si la clase pertenece a otra clase, indica su superclase. Realiza el ejercicio en RDFLib devolviendo una lista de tuplas: (clase, superclase) denominada "result". Si una clase no tiene superclase, devuelve None como superclase.
# 
# English: For all classes, list each classURI. If the class belogs to another class, then list its superclass. Do the exercise in RDFLib returning a list of Tuples: (class, superclass) called "result". If a class does not have a super class, then return None as the superclass

# %%
from rdflib.namespace import OWL

#TODO
result = [] #list of tuples

classes = set(g.subjects(RDF.type, RDFS.Class)).union(set(g.subjects(RDF.type, OWL.Class)))

for c in classes:
    super_classes = list(g.objects(c, RDFS.subClassOf))
    if super_classes:
        for sc in super_classes:
            result.append((c, sc))
    else:
        result.append((c, None))

# Visualize the results
for r in result:
  print(r)

# %%
## Validation: Do not remove
report.validate_07_1a(result)

# %% [markdown]
# **TASK 7.1b:**
# 
# Spanish: Repite el mismo ejercicio en SPARQL, devolviendo las variables ?c (clase) y ?sc (superclase)
# 
# English: Repeat the same exercise in SPARQL, returning the variables ?c (class) and ?sc (superclass)

# %%
query = """ 
SELECT DISTINCT ?c ?sc WHERE {
  { ?c a <http://www.w3.org/2000/01/rdf-schema#Class> . } 
  UNION 
  { ?c a <http://www.w3.org/2002/07/owl#Class> . }
  
  OPTIONAL { ?c <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?sc . }
}
"""

for r in g.query(query):
  print(r.c, r.sc)


# %%
## Validation: Do not remove
report.validate_07_1b(query,g)

# %% [markdown]
# **TASK 7.2a:**
# 
# Spanish: Enumera todos los individuos de "Person" con RDFLib (ten en cuenta las subclases). Devuelve los URI de los individuos en una lista llamada "individuals".
# 
# English: List all individuals of "Person" with RDFLib (remember the subClasses). Return the individual URIs in a list called "individuals"
# 

# %%
ns = Namespace("http://oeg.fi.upm.es/def/people#")

# variable to return
individuals = []

def get_subclasses(cls):
    subclasses = {cls}
    for s in g.subjects(RDFS.subClassOf, cls):
        subclasses.update(get_subclasses(s))
    return subclasses
person_classes = get_subclasses(ns.Person)

for c in person_classes:
    for ind in g.subjects(RDF.type, c):
        individuals.append(ind)

# visualize results
for i in individuals:
  print(i)

# %%
# validation. Do not remove
report.validate_07_02a(individuals)

# %% [markdown]
# **TASK 7.2b:**
# 
# Spanish: Repite el mismo ejercicio en SPARQL, devolviendo los URI individuales en una variable ?ind.
# 
# English: Repeat the same exercise in SPARQL, returning the individual URIs in a variable ?ind

# %%
query = """
PREFIX ns: <http://oeg.fi.upm.es/def/people#>

SELECT DISTINCT ?ind WHERE {
  ?type <http://www.w3.org/2000/01/rdf-schema#subClassOf>* ns:Person .
  ?ind a ?type .
}
"""

for r in g.query(query):
  print(r.ind)
# Visualize the results

# %%
## Validation: Do not remove
report.validate_07_02b(g, query)

# %% [markdown]
# **TASK 7.3:**
# 
# Spanish: Enumera el nombre y el tipo de quienes conocen a Curry (solo en SPARQL). Utiliza el nombre y el tipo como variables en la consulta.
# 
# English: List the name and type of those who know Curry (in SPARQL only). Use name and type as variables in the query

# %%
query =  """
PREFIX ns:  <http://oeg.fi.upm.es/def/people#>
SELECT ?name ?type
WHERE{
  ?person ns:knows ns:Curry .
  ?person rdfs:label ?name .
  ?person rdf:type ?type .
}
"""

# Visualize the results
for r in g.query(query):
  print(r.name, r.type)


# %%
## Validation: Do not remove
report.validate_07_03(g, query)

# %% [markdown]
# **Task 7.4:**
# 
# Spanish: Enumera los nombres de aquellas entidades que tengan un compañero de trabajo que tenga un perro, o que tengan un compañero de trabajo que tenga un compañero de trabajo que tenga un perro (en SPARQL). Devuelve los resultados en una variable llamada «name».
# 
# English: List the name of those entities who have a colleague with a dog, or that have a collegue who has a colleague who has a dog (in SPARQL). Return the results in a variable called name

# %%
query =  """
PREFIX ns: <http://oeg.fi.upm.es/def/people#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?name WHERE {
  ?person rdfs:label ?name .
  
  {
    # Compañero directo con perro
    ?person ns:hasColleague ?colleague .
    ?colleague ns:ownsPet ?dog .
  }
  UNION
  {
    # Compañero del compañero con perro
    ?person ns:hasColleague ?colleague .
    ?colleague ns:hasColleague ?colleague2 .
    ?colleague2 ns:ownsPet ?dog .
  }
}
"""

for r in g.query(query):
  print(r.name)

# TO DO
# Visualize the results

# %%
## Validation: Do not remove
report.validate_07_04(g,query)
report.save_report("_Task_07")


