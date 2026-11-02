"""API REST para el Buscador Eficiente de Información.

La API está aislada del núcleo: ningún módulo de búsqueda la importa.
Para eliminarla basta con borrar este archivo y la dependencia FastAPI.

Ejecución local:
    uvicorn api:app --reload --host 127.0.0.1 --port 8000
"""

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from pydantic import BaseModel

from cache import QueryCache
from config import DOCS_DIR
from inverted_index import InvertedIndexEngine
from search_common import SearchResult as CoreSearchResult
from search_sequential import SequentialSearchEngine


class SearchResponse(BaseModel):
    """Resultado individual de una búsqueda."""

    doc_id: int
    doc_name: str
    score: float
    snippet: str


class SearchResult(BaseModel):
    """Respuesta completa de una búsqueda."""

    query: str
    engine: str
    elapsed_seconds: float
    results: list[SearchResponse]


def _to_response(results: list[CoreSearchResult]) -> list[SearchResponse]:
    """Convierte resultados del núcleo al modelo de la API."""
    return [
        SearchResponse(
            doc_id=result.doc_id,
            doc_name=result.doc_name,
            score=result.score,
            snippet=result.snippet,
        )
        for result in results
    ]


def create_app(docs_dir: str | None = None) -> FastAPI:
    """Crea y configura la aplicación FastAPI.

    Args:
        docs_dir: Directorio de documentos. Si es None se usa ``config.DOCS_DIR``.

    Returns:
        Instancia de FastAPI configurada.
    """
    directory = docs_dir or DOCS_DIR
    indexed_engine = InvertedIndexEngine(directory)
    sequential_engine = SequentialSearchEngine(directory)
    query_cache = QueryCache()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        """Carga los documentos al iniciar y libera recursos al cerrar."""
        sequential_engine.load_documents()
        indexed_engine.build_index()
        yield

    application = FastAPI(
        title="Buscador Eficiente de Información",
        description="API REST para búsqueda secuencial e indexada con caché LRU",
        version="3.0",
        lifespan=lifespan,
    )

    @application.get("/health")
    def health() -> dict[str, int | str]:
        """Retorna el estado del servicio y la cantidad de documentos indexados."""
        return {
            "status": "ok",
            "indexed_docs": len(indexed_engine.index.get_all_doc_ids()),
        }

    @application.get("/search/sequential", response_model=SearchResult)
    def search_sequential(
        q: str = Query(..., min_length=1, max_length=200),
    ) -> SearchResult:
        """Ejecuta una búsqueda secuencial sobre el corpus."""
        start = time.perf_counter()
        results = sequential_engine.search(q)
        elapsed = time.perf_counter() - start
        return SearchResult(
            query=q,
            engine="sequential",
            elapsed_seconds=elapsed,
            results=_to_response(results),
        )

    @application.get("/search/indexed", response_model=SearchResult)
    def search_indexed(
        q: str = Query(..., min_length=1, max_length=200),
    ) -> SearchResult:
        """Ejecuta una búsqueda indexada usando la caché LRU."""
        start = time.perf_counter()
        cached = query_cache.get(q)
        if cached is None:
            cached = indexed_engine.search(q)
            query_cache.put(q, cached)
        elapsed = time.perf_counter() - start
        return SearchResult(
            query=q,
            engine="indexed",
            elapsed_seconds=elapsed,
            results=_to_response(cached),
        )

    @application.get("/cache/stats")
    def cache_stats() -> dict[str, float | int]:
        """Retorna las estadísticas de la caché de consultas."""
        return {
            "hits": query_cache.hits,
            "misses": query_cache.misses,
            "hit_rate": query_cache.hit_rate(),
            "size": query_cache.size(),
        }

    return application


app = create_app()
