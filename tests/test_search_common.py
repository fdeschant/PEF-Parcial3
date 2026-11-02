import os

import pytest

from search_common import (
    build_snippet,
    list_doc_files,
    parse_doc_id,
    read_tokens,
    tokenize,
)


class TestSearchCommon:
    def test_tokenize(self):
        assert tokenize("Hola, Mundo! Python 3") == ["hola", "mundo", "python", "3"]

    def test_tokenize_empty(self):
        assert tokenize("") == []

    def test_build_snippet_with_match(self):
        snippet = build_snippet(["a", "b", "python", "c", "d"], ["python"], context=1)
        assert "python" in snippet
        assert snippet == "b python c"

    def test_build_snippet_without_match(self):
        snippet = build_snippet(["a", "b", "c"], ["python"])
        assert snippet == "a b c"

    def test_parse_doc_id(self):
        assert parse_doc_id("documento_12.txt") == 12
        assert parse_doc_id("documento_large_10001.txt") == 10001

    def test_parse_doc_id_invalid(self):
        with pytest.raises(ValueError):
            parse_doc_id("documento.txt")

    def test_list_doc_files_filters_and_sorts(self, tmp_path):
        for name in ("documento_2.txt", "documento_10.txt", "otro.txt"):
            (tmp_path / name).write_text("python")
        assert list_doc_files(str(tmp_path)) == ["documento_10.txt", "documento_2.txt"]

    def test_list_doc_files_missing_directory(self, tmp_path):
        assert list_doc_files(str(tmp_path / "missing")) == []

    def test_read_tokens(self, tmp_path):
        path = tmp_path / "documento_1.txt"
        path.write_text("Python Java", encoding="utf-8")
        assert read_tokens(str(path)) == ["python", "java"]
        assert os.path.exists(path)
