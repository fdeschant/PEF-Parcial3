import os

from fastapi.testclient import TestClient

from api import create_app


def _write_corpus(directory: str) -> None:
    documents = {
        "documento_1.txt": "python java algoritmo programacion eficiente",
        "documento_2.txt": "python base datos sql consulta",
        "documento_3.txt": "java red tcp protocolo paquete",
    }
    for name, content in documents.items():
        with open(os.path.join(directory, name), "w", encoding="utf-8") as file:
            file.write(content)


class TestApi:
    def test_health(self, tmp_path):
        _write_corpus(str(tmp_path))
        with TestClient(create_app(str(tmp_path))) as client:
            response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["indexed_docs"] == 3

    def test_sequential_search(self, tmp_path):
        _write_corpus(str(tmp_path))
        with TestClient(create_app(str(tmp_path))) as client:
            response = client.get("/search/sequential", params={"q": "python"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["engine"] == "sequential"
        assert payload["query"] == "python"
        assert len(payload["results"]) == 2
        assert payload["elapsed_seconds"] >= 0

    def test_indexed_search_and_cache(self, tmp_path):
        _write_corpus(str(tmp_path))
        with TestClient(create_app(str(tmp_path))) as client:
            first = client.get("/search/indexed", params={"q": "python"})
            second = client.get("/search/indexed", params={"q": "python"})
            stats = client.get("/cache/stats")
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["engine"] == "indexed"
        assert stats.json()["hits"] == 1
        assert stats.json()["misses"] == 1
        assert stats.json()["size"] == 1

    def test_empty_query_is_rejected(self, tmp_path):
        _write_corpus(str(tmp_path))
        with TestClient(create_app(str(tmp_path))) as client:
            response = client.get("/search/indexed", params={"q": ""})
        assert response.status_code == 422

    def test_query_too_long_is_rejected(self, tmp_path):
        _write_corpus(str(tmp_path))
        with TestClient(create_app(str(tmp_path))) as client:
            response = client.get("/search/indexed", params={"q": "x" * 201})
        assert response.status_code == 422

    def test_no_results(self, tmp_path):
        _write_corpus(str(tmp_path))
        with TestClient(create_app(str(tmp_path))) as client:
            response = client.get("/search/indexed", params={"q": "inexistente"})
        assert response.status_code == 200
        assert response.json()["results"] == []
