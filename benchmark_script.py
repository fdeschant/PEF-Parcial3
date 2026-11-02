import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache import QueryCache
from inverted_index import InvertedIndexEngine
from search_sequential import SequentialSearchEngine

DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

QUERIES = [
    "java concurrencia",
    "base datos sql",
    "algoritmo ordenamiento",
    "red tcp protocolo",
    "sistema operativo proceso",
]


def main():
    seq = SequentialSearchEngine(DOCS_DIR)
    seq.load_documents()

    idx = InvertedIndexEngine(DOCS_DIR)
    idx.build_index()

    cache = QueryCache()

    for q in QUERIES * 1000:
        seq.search(q)
        idx.search(q)

    for q in QUERIES[:3]:
        cache.put(q, idx.search(q))
        cache.get(q)


if __name__ == "__main__":
    main()
