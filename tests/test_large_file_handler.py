import os
import tempfile

from large_file_handler import (
    get_total_tokens_large_files,
    read_file_buffered,
    tokens_from_large_file,
)


class TestLargeFileHandler:
    def test_read_file_buffered(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world test")
            f.flush()
            result = read_file_buffered(f.name)
            os.unlink(f.name)
        assert "hello" in result
        assert "world" in result

    def test_tokens_from_large_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Python Java Algoritmo Programacion")
            f.flush()
            tokens = tokens_from_large_file(f.name)
            os.unlink(f.name)
        assert "python" in tokens
        assert "java" in tokens

    def test_get_total_tokens(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "documento_1.txt"), "w") as f:
                f.write("python java algoritmo")
            with open(os.path.join(tmpdir, "documento_2.txt"), "w") as f:
                f.write("base datos sql")
            total = get_total_tokens_large_files(tmpdir)
        assert total == 6

    def test_read_file_buffered_small_buffer(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("python java algoritmo")
            f.flush()
            result = read_file_buffered(f.name, buffer_size=4)
            os.unlink(f.name)
        assert result == "python java algoritmo"

    def test_build_index_large_files(self):
        from large_file_handler import build_index_large_files

        with tempfile.TemporaryDirectory() as tmpdir:
            for doc_id in (10001, 10002, 10003):
                with open(os.path.join(tmpdir, f"documento_large_{doc_id}.txt"), "w") as f:
                    f.write("python java algoritmo")
            index = build_index_large_files(tmpdir, batch_size=2, workers=2)
        assert index.get_all_doc_ids() == {10001, 10002, 10003}
