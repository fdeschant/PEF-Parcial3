"""Integración de herramientas de profiling cProfile y SnakeViz.

Provee funciones para generar perfiles de CPU y memoria,
y visualizarlos con SnakeViz.

Uso:
    python profiling_integration.py
"""

import cProfile
import io
import pstats
import sys

from cache import QueryCache
from config import DOCS_DIR
from inverted_index import InvertedIndexEngine
from search_sequential import SequentialSearchEngine


def profile_with_cprofile(func, *args, **kwargs):
    """Perfila una función usando cProfile.

    Args:
        func: Función a perfilar.
        *args: Argumentos posicionales.
        **kwargs: Argumentos con nombre.

    Returns:
        Tupla (resultados, string_stats).
    """
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(20)
    return result, s.getvalue()


def run_profile_benchmark(docs_dir: str = DOCS_DIR):
    """Ejecuta un benchmark de profiling completo.

    Args:
        docs_dir: Directorio de documentos.
    """
    print("=" * 60)
    print("PROFILING CON cProfile")
    print("=" * 60)

    print("\n[1] Perfilando carga secuencial...")
    seq_engine = SequentialSearchEngine(docs_dir)
    _, seq_stats = profile_with_cprofile(seq_engine.load_documents)
    print(seq_stats[:2000])

    print("\n[2] Perfilando construcción de índice invertido...")
    inv_engine = InvertedIndexEngine(docs_dir)
    _, inv_stats = profile_with_cprofile(inv_engine.build_index)
    print(inv_stats[:2000])

    print("\n[3] Perfilando búsquedas...")
    query = "python java"
    _, search_stats = profile_with_cprofile(inv_engine.search, query)
    print(search_stats[:2000])

    print("\n[4] Perfilando caché LRU...")
    cache = QueryCache()

    def cache_operations():
        for _ in range(1000):
            cache.put("python java", [1, 2, 3])
            cache.get("python java")
            cache.get("nonexistent query")

    _, cache_stats = profile_with_cprofile(cache_operations)
    print(cache_stats[:2000])


def generate_snakeviz_compatible_profile(output_path: str = "profile.prof"):
    """Genera un perfil compatible con SnakeViz.

    Args:
        output_path: Ruta del archivo .prof de salida.
    """
    from config import DOCS_DIR

    inv_engine = InvertedIndexEngine(DOCS_DIR)
    inv_engine.build_index()

    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(100):
        inv_engine.search("python")
        inv_engine.search("java")
        inv_engine.search("algoritmo")
    profiler.disable()
    profiler.dump_stats(output_path)
    print(f"Perfil guardado en {output_path}")
    print(f"Visualizar con: {sys.executable} -m snakeviz {output_path}")


def main():
    """Punto de entrada principal."""
    run_profile_benchmark()
    print("\n" + "=" * 60)
    print("GENERANDO PERFIL COMPATIBLE CON SNAKEVIZ")
    print("=" * 60)
    generate_snakeviz_compatible_profile()


if __name__ == "__main__":
    main()
