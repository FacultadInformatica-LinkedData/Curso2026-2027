# %% [markdown]
# **Task 08: Completing missing data**

# %%
#!pip install rdflib
github_storage = "https://raw.githubusercontent.com/FacultadInformatica-LinkedData/Curso2021-2022/master/Assignment4/course_materials"

# %%
from rdflib import Graph, Namespace, Literal, URIRef
g1 = Graph()
g2 = Graph()
g1.parse(github_storage+"/rdf/data01.rdf", format="xml")
g2.parse(github_storage+"/rdf/data02.rdf", format="xml")

# %% [markdown]
# Spanish: Lista todos los elementos de la clase Person en el primer grafo (data01.rdf) y completa los campos (given name, family name y email) que puedan faltar con los datos del segundo grafo (data02.rdf). Puedes usar consultas SPARQL o iterar el grafo, o ambas cosas.
# 
# English: List all the elements of the Person class in the first graph (data01.rdf) and fill in any missing fields (given name, family name and email) using the data from the second graph (data02.rdf). You can use SPARQL queries or iterate through the graph, or both.

# %%
from rdflib.namespace import RDF

VCARD = Namespace("http://www.w3.org/2001/vcard-rdf/3.0#")
PERSON = URIRef("http://data.org#Person")

for p in g1.subjects(RDF.type, PERSON):
    for prop in (VCARD.Given, VCARD.Family, VCARD.EMAIL):
        if (p, prop, None) not in g1:          # falta en g1
            for o in g2.objects(p, prop):      # lo busco en g2
                g1.add((p, prop, o))

# Visualizar el resultado
for p in g1.subjects(RDF.type, PERSON):
    print(p, g1.value(p, VCARD.Given), g1.value(p, VCARD.Family), g1.value(p, VCARD.EMAIL))


