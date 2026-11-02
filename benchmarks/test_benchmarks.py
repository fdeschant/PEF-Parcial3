"""Benchmarks reproducibles de las operaciones representativas."""

from pathlib import Path

import pytest

from cache import QueryCache
from generator import generate_documents, generate_large_documents
from inverted_index import InvertedIndexEngine
from large_file_handler import read_file_buffered
from search_common import tokenize
from search_sequential import SequentialSearchEngine


@pytest.fixture(scope="session")
def corpus_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("benchmark-corpus")
    generate_documents(200, str(path), seed=42)
    generate_large_documents(1, str(path), words_per_doc=10000, seed=42)
    return str(path)


@pytest.fixture(scope="session")
def sequential_engine(corpus_dir):
    engine = SequentialSearchEngine(corpus_dir)
    engine.load_documents()
    return engine


@pytest.fixture(scope="session")
def indexed_engine(corpus_dir):
    engine = InvertedIndexEngine(corpus_dir)
    engine.build_index()
    return engine


def test_benchmark_tokenize(benchmark):
    text = "python java algoritmo " * 5000
    benchmark(tokenize, text)


def test_benchmark_index_build(benchmark, corpus_dir):
    benchmark(lambda: InvertedIndexEngine(corpus_dir).build_index())


def test_benchmark_sequential_search(benchmark, sequential_engine):
    benchmark(sequential_engine.search, "python java")


def test_benchmark_indexed_search(benchmark, indexed_engine):
    benchmark(indexed_engine.search, "python java")


def test_benchmark_cached_search(benchmark, indexed_engine):
    cache = QueryCache()
    results = indexed_engine.search("python java")
    cache.put("python java", results)
    benchmark(cache.get, "python java")


def test_benchmark_buffered_read(benchmark, corpus_dir):
    large_file = next(Path(corpus_dir).glob("documento_large_*.txt"))
    benchmark(read_file_buffered, str(large_file))
