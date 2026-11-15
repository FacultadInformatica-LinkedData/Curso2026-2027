
from rdflib import Graph

from app.core.config import DATASET_PATH


DATASET = DATASET_PATH / "madrid-culture-with-links.ttl"


def load_graph() -> Graph:
    """
    Carga el dataset RDF de bibliotecas y museos.
    """
    if not DATASET.exists():
        raise FileNotFoundError(
            f"No se ha encontrado el dataset: {DATASET}"
        )

    graph = Graph()
    graph.parse(str(DATASET), format="turtle")

    return graph