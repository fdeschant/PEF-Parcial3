import os

from generator import (
    generate_documents,
    generate_large_documents,
    get_document_count,
)


class TestGenerator:
    def test_generate_documents_count_and_names(self, tmp_path):
        count = generate_documents(5, str(tmp_path), seed=42)
        files = sorted(os.listdir(tmp_path))
        assert count == 5
        assert files == [f"documento_{i}.txt" for i in range(1, 6)]

    def test_generate_documents_is_reproducible(self, tmp_path):
        first = tmp_path / "first"
        second = tmp_path / "second"
        generate_documents(3, str(first), seed=123)
        generate_documents(3, str(second), seed=123)
        for name in ("documento_1.txt", "documento_2.txt", "documento_3.txt"):
            assert (first / name).read_text() == (second / name).read_text()

    def test_generate_large_documents(self, tmp_path):
        count = generate_large_documents(2, str(tmp_path), words_per_doc=50, seed=7)
        files = sorted(os.listdir(tmp_path))
        assert count == 2
        assert files == ["documento_large_10001.txt", "documento_large_10002.txt"]
        assert len((tmp_path / files[0]).read_text().split()) == 50

    def test_get_document_count(self, tmp_path):
        generate_documents(4, str(tmp_path), seed=1)
        assert get_document_count(str(tmp_path)) == 4

    def test_get_document_count_missing_directory(self, tmp_path):
        assert get_document_count(str(tmp_path / "missing")) == 0
