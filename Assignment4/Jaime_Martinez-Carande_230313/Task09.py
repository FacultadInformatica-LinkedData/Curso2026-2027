# %% [markdown]
# **Task 09: Data linking**

# %%
#!pip install rdflib
github_storage = "https://raw.githubusercontent.com/FacultadInformatica-LinkedData/Curso2021-2022/master/Assignment4/course_materials/"

# %%
from rdflib import Graph, Namespace, Literal, URIRef
g1 = Graph()
g2 = Graph()
g3 = Graph()
g1.parse(github_storage+"rdf/data03.rdf", format="xml")
g2.parse(github_storage+"rdf/data04.rdf", format="xml")

# %% [markdown]
# Spanish: Busca individuos en los dos grafos y enlázalos mediante la propiedad OWL:sameAs, inserta estas coincidencias en g3. Consideramos dos individuos iguales si tienen el mismo apodo y nombre de familia. Ten en cuenta que las URI no tienen por qué ser iguales para un mismo individuo en los dos grafos.
# 
# English: Search for individuals in both graphs and link them using the OWL:sameAs property; insert these matches into g3. We consider two individuals to be the same if they have the same first name and surname. Please note that the URIs do not necessarily have to be the same for the same individual in both graphs.

# %%
from rdflib.namespace import RDF, OWL

VCARD = Namespace("http://www.w3.org/2001/vcard-rdf/3.0#")
g3.bind("owl", OWL)

def personas(g):
    d = {}
    for s in g.subjects(RDF.type, None):
        given, family = g.value(s, VCARD.Given), g.value(s, VCARD.Family)
        if given is not None and family is not None:
            d[(str(given), str(family))] = s
    return d

p1, p2 = personas(g1), personas(g2)

for clave, s1 in p1.items():
    if clave in p2:
        g3.add((s1, OWL.sameAs, p2[clave]))

for s, p, o in g3:
    print(s, p, o)


