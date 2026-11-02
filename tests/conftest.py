import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache import QueryCache
from inverted_index import InvertedIndexEngine
from search_sequential import SequentialSearchEngine


@pytest.fixture
def sample_docs_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        words_alpha = ["python", "java", "algoritmo", "programacion", "eficiente"]
        words_beta = ["python", "base", "datos", "sql", "consulta"]
        words_gamma = ["java", "red", "tcp", "protocolo", "paquete"]

        for i, words in enumerate([words_alpha, words_beta, words_gamma], 1):
            with open(os.path.join(tmpdir, f"documento_{i}.txt"), "w") as f:
                f.write(" ".join(words))

        yield tmpdir


@pytest.fixture
def sequential_engine(sample_docs_dir):
    engine = SequentialSearchEngine(sample_docs_dir)
    engine.load_documents()
    return engine


@pytest.fixture
def indexed_engine(sample_docs_dir):
    engine = InvertedIndexEngine(sample_docs_dir)
    engine.build_index()
    return engine


@pytest.fixture
def cache():
    return QueryCache()
