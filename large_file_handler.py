import os
from multiprocessing import Pool

from config import DEFAULT_WORKERS
from inverted_index import InvertedIndex
from search_common import list_doc_files, tokenize

BUFFER_SIZE = 8192
BATCH_SIZE = 10


def read_file_buffered(filepath: str, buffer_size: int = BUFFER_SIZE) -> str:
    """Lee un archivo en bloques de buffer_size bytes.

    Args:
        filepath: Ruta al archivo.
        buffer_size: Tamaño del buffer en bytes.

    Returns:
        Contenido completo del archivo como string.
    """
    chunks = []
    with open(filepath, encoding="utf-8") as f:
        while True:
            chunk = f.read(buffer_size)
            if not chunk:
                break
            chunks.append(chunk)
    return "".join(chunks)


def tokens_from_large_file(filepath: str) -> list[str]:
    """Tokeniza un archivo grande usando lectura por buffer.

    Args:
        filepath: Ruta al archivo grande.

    Returns:
        Lista de tokens.
    """
    content = read_file_buffered(filepath)
    return tokenize(content)


def _process_batch(args: tuple[str, list[str]]) -> InvertedIndex:
    """Procesa un batch de documentos en un worker.

    Args:
        args: Tupla (docs_dir, file_batch).

    Returns:
        Índice parcial del batch.
    """
    docs_dir, file_batch = args
    partial = InvertedIndex()
    for filename in file_batch:
        doc_id = int(filename.split("_")[-1].split(".")[0])
        filepath = os.path.join(docs_dir, filename)
        tokens = tokens_from_large_file(filepath)
        partial.add_document(doc_id, filename, tokens)
    return partial


def build_index_large_files(
    docs_dir: str,
    batch_size: int = BATCH_SIZE,
    workers: int = DEFAULT_WORKERS,
) -> InvertedIndex:
    """Construye el índice invertido para archivos grandes.

    Strategy:
        1. Divide los archivos en batches de batch_size.
        2. Procesa cada batch en un worker del Pool.
        3. Fusiona los índices parciales.

    Args:
        docs_dir: Directorio con los documentos grandes.
        batch_size: Cantidad de documentos por batch.
        workers: Número de procesos workers.

    Returns:
        Índice invertido completo.
    """
    all_files = [
        f for f in list_doc_files(docs_dir) if f.startswith(("documento_large_", "documento_"))
    ]

    batches = [
        (docs_dir, all_files[i : i + batch_size]) for i in range(0, len(all_files), batch_size)
    ]

    with Pool(processes=workers) as pool:
        partial_indexes = pool.map(_process_batch, batches)

    merged = InvertedIndex()
    for partial in partial_indexes:
        merged.merge(partial)

    return merged


def get_total_tokens_large_files(docs_dir: str) -> int:
    """Cuenta el total de tokens en todos los archivos grandes.

    Args:
        docs_dir: Directorio con los documentos.

    Returns:
        Total de tokens.
    """
    total = 0
    for filename in list_doc_files(docs_dir):
        filepath = os.path.join(docs_dir, filename)
        total += len(tokens_from_large_file(filepath))
    return total
