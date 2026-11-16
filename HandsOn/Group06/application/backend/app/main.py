
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.rdf.graph import load_graph
from app.api.routes.facilities import router as facilities_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida del grafo RDF."""

    # Inicio de la aplicación
    # Creamos el grafo que se podrá reutilizar luego
    app.state.rdf_graph = load_graph()

    print("Dataset RDF cargado correctamente.")

    yield

    # Cierre de la aplicación
    del app.state.rdf_graph

app = FastAPI(
    title="Madrid Culture API",
    description="API desarrollada con FastAPI",
    version="1.0.0", 
    lifespan=lifespan,
)

# Permitir peticiones desde React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar las rutas
app.include_router(facilities_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Backend funcionando correctamente"
    }

@app.get("/api/health")
async def health():
    return {
        "status": "ok"
    }
