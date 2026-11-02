import os

from concurrency import (
    ConcurrentSearcher,
    ConcurrentSearcherThreaded,
    ParallelIndexBuilder,
)
from inverted_index import InvertedIndexEngine


def _write_corpus(directory: str) -> None:
    documents = {
        "documento_1.txt": "python java algoritmo programacion",
        "documento_2.txt": "python base datos sql",
        "documento_3.txt": "java red tcp protocolo",
        "documento_4.txt": "python java eficiente",
    }
    for name, content in documents.items():
        with open(os.path.join(directory, name), "w", encoding="utf-8") as file:
            file.write(content)


class TestConcurrency:
    def test_parallel_index_builder(self, tmp_path):
        _write_corpus(str(tmp_path))
        index = ParallelIndexBuilder(str(tmp_path), workers=2).build()
        assert len(index.get_all_doc_ids()) == 4

    def test_concurrent_searcher(self, tmp_path):
        _write_corpus(str(tmp_path))
        engine = InvertedIndexEngine(str(tmp_path))
        engine.build_index()
        results = ConcurrentSearcher(engine, workers=2).search_batch(["python", "java"])
        assert set(results) == {"python", "java"}
        assert len(results["python"]) == 3
        assert len(results["java"]) == 3

    def test_threaded_searcher(self, tmp_path):
        _write_corpus(str(tmp_path))
        engine = InvertedIndexEngine(str(tmp_path))
        engine.build_index()
        results = ConcurrentSearcherThreaded(engine, workers=2).search_batch(
            ["python", "inexistente"]
        )
        assert len(results["python"]) == 3
        assert results["inexistente"] == []
