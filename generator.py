import os
import random

from config import (
    DOCS_DIR,
    MAX_WORDS_PER_DOC,
    MIN_WORDS_PER_DOC,
    NOISE_WORDS,
    NUM_DOCUMENTS,
    TOPICS,
)


def generate_documents(
    num_docs: int = NUM_DOCUMENTS,
    output_dir: str = DOCS_DIR,
    min_words: int = MIN_WORDS_PER_DOC,
    max_words: int = MAX_WORDS_PER_DOC,
    seed: int | None = None,
) -> int:
    """Genera documentos sintéticos pequeños.

    Cada documento tiene entre min_words y max_words tokens,
    60% del vocabulario del tema y 40% de palabras de ruido.

    Args:
        num_docs: Cantidad de documentos a generar.
        output_dir: Directorio de salida.
        min_words: Mínimo de palabras por documento.
        max_words: Máximo de palabras por documento.
        seed: Semilla opcional para generar un corpus reproducible.

    Returns:
        Número de documentos generados.
    """
    os.makedirs(output_dir, exist_ok=True)

    rng = random.Random(seed)  # nosec B311
    topic_names = list(TOPICS.keys())
    for i in range(1, num_docs + 1):
        topic = rng.choice(topic_names)
        vocabulary = TOPICS[topic]
        num_words = rng.randint(min_words, max_words)

        words = []
        for _ in range(num_words):
            # Dato sintetico: no se usa para fines criptograficos.
            if rng.random() < 0.6:  # nosec
                words.append(rng.choice(vocabulary))
            else:
                words.append(rng.choice(NOISE_WORDS))

        filename = os.path.join(output_dir, f"documento_{i}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(" ".join(words))

    return num_docs


def generate_large_documents(
    num_docs: int = 50,
    output_dir: str = DOCS_DIR,
    words_per_doc: int = 10000,
    seed: int | None = None,
) -> int:
    """Genera documentos grandes (10k+ palabras) para pruebas de I/O eficiente.

    Args:
        num_docs: Cantidad de documentos grandes a generar.
        output_dir: Directorio de salida.
        words_per_doc: Cantidad de palabras por documento.
        seed: Semilla opcional para generar un corpus reproducible.

    Returns:
        Número de documentos generados.
    """
    os.makedirs(output_dir, exist_ok=True)

    rng = random.Random(seed)  # nosec B311
    topic_names = list(TOPICS.keys())
    base_id = 10000
    for i in range(1, num_docs + 1):
        topic = rng.choice(topic_names)
        vocabulary = TOPICS[topic]

        words = []
        for _ in range(words_per_doc):
            # Dato sintetico: no se usa para fines criptograficos.
            if rng.random() < 0.6:  # nosec
                words.append(rng.choice(vocabulary))
            else:
                words.append(rng.choice(NOISE_WORDS))

        filename = os.path.join(output_dir, f"documento_large_{base_id + i}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(" ".join(words))

    return num_docs


def get_document_count(output_dir: str = DOCS_DIR) -> int:
    """Cuenta los documentos existentes en el directorio.

    Args:
        output_dir: Directorio a examinar.

    Returns:
        Número de documentos encontrados.
    """
    if not os.path.isdir(output_dir):
        return 0
    return len(
        [f for f in os.listdir(output_dir) if f.startswith("documento_") and f.endswith(".txt")]
    )
