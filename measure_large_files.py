"""Medición de escritura/lectura de archivos grandes.

Compara el indexado secuencial contra el indexado por batches con
multiprocessing.Pool, y mide el efecto del buffering en la lectura.

Uso:
    python measure_large_files.py
"""

import glob
import os
import statistics
import time

from config import DOCS_DIR
from inverted_index import InvertedIndex
from large_file_handler import (
    build_index_large_files,
    get_total_tokens_large_files,
    read_file_buffered,
    tokens_from_large_file,
)
from search_common import list_doc_files

REPEATS = 3


def build_sequential(files):
    """Construye un indice invertido leyendo los archivos uno a uno."""
    index = InvertedIndex()
    for filename in files:
        path = os.path.join(DOCS_DIR, filename)
        doc_id = int(filename.rsplit(".", 1)[0].split("_")[-1])
        tokens = tokens_from_large_file(path)
        index.add_document(doc_id, filename, tokens)
    return index


def measure_median(build_fn):
    """Retorna la mediana del tiempo de construccion sobre varias corridas."""
    times = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        build_fn()
        times.append(time.perf_counter() - start)
    return statistics.median(times)


def main():
    """Ejecuta la medicion y muestra los resultados en consola."""
    large_files = sorted(glob.glob(os.path.join(DOCS_DIR, "documento_large_*.txt")))
    if not large_files:
        print("No hay archivos grandes. Ejecute la opcion 2 del menu primero.")
        return

    all_files = [name for name in list_doc_files(DOCS_DIR) if name.startswith("documento_")]

    sizes = [os.path.getsize(path) for path in large_files]
    total_mb = sum(sizes) / 1024 / 1024
    avg_kb = sum(sizes) / len(sizes) / 1024

    print("=" * 62)
    print(" MEDICION DE ARCHIVOS GRANDES")
    print("=" * 62)
    print(f"Documentos grandes : {len(large_files)} archivos")
    print(f"Documentos totales : {len(all_files)}")
    print(f"Tamano total       : {total_mb:.2f} MB (promedio {avg_kb:.1f} KB)")

    sample = large_files[0]
    sample_kb = os.path.getsize(sample) / 1024

    start = time.perf_counter()
    with open(sample, encoding="utf-8") as handle:
        _ = handle.read()
    plain_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    _ = read_file_buffered(sample)
    buffered_ms = (time.perf_counter() - start) * 1000

    print(f"\n[Buffering] 1 archivo ({sample_kb:.0f} KB)")
    print(f"  read() simple  : {plain_ms:.2f} ms")
    print(f"  read 8KB x N   : {buffered_ms:.2f} ms")

    seq_median = measure_median(lambda: build_sequential(all_files))
    par_median = measure_median(lambda: build_index_large_files(DOCS_DIR))

    print(f"\n[Indexado] mediana de {REPEATS} corridas")
    print(f"  Secuencial          : {seq_median:.3f} s")
    print(f"  Batch + multiprocess: {par_median:.3f} s")
    print(f"  Speedup             : {seq_median / par_median:.2f}x")

    total_tokens = get_total_tokens_large_files(DOCS_DIR)
    print(f"\n[Tokens] total en archivos grandes: {total_tokens:,}")
    print("=" * 62)


if __name__ == "__main__":
    main()
