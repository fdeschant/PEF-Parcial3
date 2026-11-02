from collections.abc import Callable

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


class InvertedIndex:
    """Índice invertido: mapea términos a listas de postings (IDs de documentos).

    Estructuras:
        index: term -> set de doc_ids
        term_freqs: term -> {doc_id: frecuencia}
        doc_lengths: doc_id -> número de tokens
        doc_names: doc_id -> nombre de archivo
    """

    def __init__(self) -> None:
        self.index: dict[str, set[int]] = {}
        self.doc_lengths: dict[int, int] = {}
        self.term_freqs: dict[str, dict[int, int]] = {}
        self.doc_names: dict[int, str] = {}
        self._doc_tokens: dict[int, list[str]] = {}

    def add_document(self, doc_id: int, doc_name: str, tokens: list[str]) -> None:
        """Agrega un documento al índice en una sola pasada.

        Args:
            doc_id: Identificador único del documento.
            doc_name: Nombre del archivo.
            tokens: Lista de tokens del documento.
        """
        self.doc_lengths[doc_id] = len(tokens)
        self.doc_names[doc_id] = doc_name
        self._doc_tokens[doc_id] = tokens

        term_counts: dict[str, int] = {}
        for token in tokens:
            term_counts[token] = term_counts.get(token, 0) + 1

        for term, count in term_counts.items():
            if term not in self.index:
                self.index[term] = set()
                self.term_freqs[term] = {}
            self.index[term].add(doc_id)
            self.term_freqs[term][doc_id] = count

    def get_posting_list(self, term: str) -> set[int]:
        """Retorna el conjunto de IDs de documentos que contienen el término."""
        return self.index.get(term, set())

    def get_term_freq(self, term: str, doc_id: int) -> int:
        """Retorna la frecuencia del término en el documento."""
        return self.term_freqs.get(term, {}).get(doc_id, 0)

    def get_doc_length(self, doc_id: int) -> int:
        """Retorna la longitud (en tokens) del documento."""
        return self.doc_lengths.get(doc_id, 0)

    def get_all_doc_ids(self) -> set[int]:
        """Retorna el conjunto de todos los IDs de documentos indexados."""
        return set(self.doc_lengths.keys())

    def get_doc_tokens(self, doc_id: int) -> list[str]:
        """Retorna los tokens del documento."""
        return self._doc_tokens.get(doc_id, [])

    def merge(self, other: "InvertedIndex") -> None:
        """Fusiona otro índice invertido en este (usado en construcción paralela).

        Args:
            other: Índice parcial a fusionar.
        """
        for doc_id, length in other.doc_lengths.items():
            self.doc_lengths[doc_id] = length
            self.doc_names[doc_id] = other.doc_names[doc_id]
            self._doc_tokens[doc_id] = other._doc_tokens[doc_id]

        for term, postings in other.index.items():
            if term not in self.index:
                self.index[term] = set()
                self.term_freqs[term] = {}
            self.index[term].update(postings)
            self.term_freqs[term].update(other.term_freqs[term])


class InvertedIndexEngine:
    """Motor de búsqueda con índice invertido.

    Construye el índice una vez y responde consultas en O(k * L_min)
    donde k = términos de la consulta y L_min = posting list más corta.
    """

    def __init__(self, docs_dir: str = DOCS_DIR):
        self.docs_dir = docs_dir
        self.index = InvertedIndex()

    def build_index(self, progress_callback: Callable[[int, int], None] | None = None) -> int:
        """Construye el índice invertido completo.

        Args:
            progress_callback: Función opcional(current, total) para reportar progreso.

        Returns:
            Número de documentos indexados.
        """
        self.index = InvertedIndex()
        files = list_doc_files(self.docs_dir)
        for filename in files:
            doc_id = parse_doc_id(filename)
            tokens = read_tokens(f"{self.docs_dir}/{filename}")
            self.index.add_document(doc_id, filename, tokens)
            if progress_callback:
                progress_callback(len(self.index.get_all_doc_ids()), len(files))
        return len(self.index.get_all_doc_ids())

    def get_doc_count(self) -> int:
        return len(self.index.get_all_doc_ids())

    def build_partial_index(self, file_list: list[str]) -> InvertedIndex:
        """Construye un índice parcial a partir de un subconjunto de archivos.

        Usado por el constructor paralelo para procesar chunks independientes.

        Args:
            file_list: Lista de nombres de archivo a indexar.

        Returns:
            Índice invertido parcial.
        """
        partial = InvertedIndex()
        for filename in file_list:
            doc_id = parse_doc_id(filename)
            tokens = read_tokens(f"{self.docs_dir}/{filename}")
            partial.add_document(doc_id, filename, tokens)
        return partial

    def search(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[SearchResult]:
        """Busca documentos usando intersección de posting lists.

        Args:
            query: Texto de la búsqueda.
            top_k: Número máximo de resultados.

        Returns:
            Lista de resultados ordenados por score descendente.
        """
        query_terms = tokenize(query)
        if not query_terms:
            return []

        candidate_ids: set[int] | None = None
        for term in query_terms:
            posting = self.index.get_posting_list(term)
            if candidate_ids is None:
                candidate_ids = posting.copy()
            else:
                candidate_ids &= posting

        if not candidate_ids:
            return []

        scored: list[SearchResult] = []
        for doc_id in candidate_ids:
            score = 0.0
            doc_len = self.index.get_doc_length(doc_id)
            if doc_len == 0:
                continue
            for term in query_terms:
                tf = self.index.get_term_freq(term, doc_id)
                score += tf / doc_len

            tokens = self.index.get_doc_tokens(doc_id)
            snippet = build_snippet(tokens, query_terms)
            scored.append(
                SearchResult(
                    doc_id=doc_id,
                    doc_name=self.index.doc_names[doc_id],
                    score=score,
                    snippet=snippet,
                )
            )

        return ResultRanker.rank(scored, top_k)
