import math
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool, cpu_count

from config import DEFAULT_WORKERS, DOCS_DIR
from inverted_index import InvertedIndex, InvertedIndexEngine, SearchResult
from search_common import list_doc_files


def _build_partial(args: tuple[str, list[str]]) -> InvertedIndex:
    """Construye un índice parcial en un worker separado.

    Args:
        args: Tupla (docs_dir, file_chunk).

    Returns:
        Índice invertido parcial.
    """
    docs_dir, file_chunk = args
    engine = InvertedIndexEngine(docs_dir)
    return engine.build_partial_index(file_chunk)


def _search_one(args: tuple[InvertedIndexEngine, str]) -> tuple[str, list[SearchResult]]:
    """Ejecuta una búsqueda en un worker separado.

    Args:
        args: Tupla (engine, query).

    Returns:
        Tupla (query, resultados).
    """
    engine, query = args
    return query, engine.search(query)


class ConcurrentSearcher:
    """Búsqueda concurrente usando multiprocessing.

    Ideal para consultas independientes en CPU-bound workloads.
    """

    def __init__(self, engine: InvertedIndexEngine, workers: int | None = None):
        self.engine = engine
        self.workers = min(workers or cpu_count(), cpu_count() or 4)

    def search_batch(self, queries: list[str]) -> dict[str, list[SearchResult]]:
        """Ejecuta múltiples consultas en paralelo.

        Args:
            queries: Lista de strings de consulta.

        Returns:
            Diccionario query -> resultados.
        """
        with Pool(processes=self.workers) as pool:
            args = [(self.engine, q) for q in queries]
            results = pool.map(_search_one, args)
        return dict(results)


class ConcurrentSearcherThreaded:
    """Búsqueda concurrente usando hilos (ThreadPoolExecutor).

    Limitado por el GIL para trabajo CPU-bound; incluido para comparación.
    """

    def __init__(self, engine: InvertedIndexEngine, workers: int | None = None):
        self.engine = engine
        self.workers = min(workers or cpu_count(), cpu_count() or 4)

    def search_batch(self, queries: list[str]) -> dict[str, list[SearchResult]]:
        """Ejecuta múltiples consultas con hilos.

        Args:
            queries: Lista de strings de consulta.

        Returns:
            Diccionario query -> resultados.
        """
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            results = list(executor.map(self.engine.search, queries))
        return dict(zip(queries, results, strict=False))


class ParallelIndexBuilder:
    """Constructor de índice invertido en paralelo.

    Divide los archivos en chunks, construye índices parciales en un Pool
    de procesos, y los fusiona en un único índice.
    """

    def __init__(self, docs_dir: str = DOCS_DIR, workers: int = DEFAULT_WORKERS):
        self.docs_dir = docs_dir
        self.workers = min(workers, cpu_count() or 4)

    def build(self, progress_callback: Callable[[int, int], None] | None = None) -> InvertedIndex:
        """Construye el índice en paralelo.

        Args:
            progress_callback: Función opcional(current, total).

        Returns:
            Índice invertido completo.
        """
        all_files = list_doc_files(self.docs_dir)

        chunk_size = math.ceil(len(all_files) / self.workers)
        chunks = [
            (self.docs_dir, all_files[i : i + chunk_size])
            for i in range(0, len(all_files), chunk_size)
        ]

        with Pool(processes=self.workers) as pool:
            partial_indexes = pool.map(_build_partial, chunks)

        merged = InvertedIndex()
        for partial in partial_indexes:
            merged.merge(partial)

        if progress_callback:
            progress_callback(len(all_files), len(all_files))

        return merged
