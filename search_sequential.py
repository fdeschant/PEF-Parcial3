from config import DEFAULT_TOP_K, DOCS_DIR
from ranking import ResultRanker
from search_common import (
    SearchResult,
    build_snippet,
    list_doc_files,
    parse_doc_id,
    read_tokens,
    tokenize,
)


class SequentialSearchEngine:
    """Motor de búsqueda secuencial (baseline).

    Carga todos los documentos en memoria y los escanea en cada consulta.
    Complejidad por consulta: O(D * W) donde D = documentos, W = tokens por documento.
    """

    def __init__(self, docs_dir: str = DOCS_DIR):
        self.docs_dir = docs_dir
        self._documents: dict[int, list[str]] = {}
        self._doc_names: dict[int, str] = {}

    def load_documents(self) -> int:
        """Carga todos los documentos del directorio en memoria.

        Returns:
            Número de documentos cargados.
        """
        self._documents.clear()
        self._doc_names.clear()
        for filename in list_doc_files(self.docs_dir):
            doc_id = parse_doc_id(filename)
            tokens = read_tokens(f"{self.docs_dir}/{filename}")
            self._documents[doc_id] = tokens
            self._doc_names[doc_id] = filename
        return len(self._documents)

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[SearchResult]:
        """Busca documentos que contengan todos los términos de la consulta.

        Args:
            query: Texto de la búsqueda.
            top_k: Número máximo de resultados a retornar.

        Returns:
            Lista de resultados ordenados por score descendente.
        """
        query_terms = tokenize(query)
        if not query_terms:
            return []

        query_set = set(query_terms)
        scored: list[SearchResult] = []

        for doc_id, tokens in self._documents.items():
            token_set = set(tokens)
            if not query_set.issubset(token_set):
                continue

            count = sum(tokens.count(t) for t in query_terms)
            score = count / len(tokens) if tokens else 0.0

            snippet = build_snippet(tokens, query_terms)
            scored.append(
                SearchResult(
                    doc_id=doc_id,
                    doc_name=self._doc_names[doc_id],
                    score=score,
                    snippet=snippet,
                )
            )

        return ResultRanker.rank(scored, top_k)

    def get_doc_count(self) -> int:
        """Retorna el número de documentos cargados."""
        return len(self._documents)
