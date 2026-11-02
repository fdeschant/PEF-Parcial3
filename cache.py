from collections import OrderedDict

from config import CACHE_MAX_SIZE
from search_common import SearchResult


class QueryCache:
    """Caché LRU para resultados de consultas.

    Normaliza las consultas (minúsculas, orden canónico de términos)
    para que "java concurrencia" y "concurrencia java" compartan entrada.
    Desaloja la entrada menos recientemente usada cuando excede el máximo.
    """

    def __init__(self, max_size: int = CACHE_MAX_SIZE) -> None:
        self.max_size = max_size
        self._cache: OrderedDict[str, list[SearchResult]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def _normalize(query: str) -> str:
        """Normaliza una consulta a su forma canónica.

        Args:
            query: Texto original de la consulta.

        Returns:
            Cadena normalizada (minúsculas, términos ordenados).
        """
        terms = sorted(query.lower().split())
        return " ".join(terms)

    def get(self, query: str) -> list[SearchResult] | None:
        """Recupera los resultados de la caché si existen.

        Args:
            query: Texto de la consulta.

        Returns:
            Lista de resultados o None si no está en caché.
        """
        key = self._normalize(query)
        if key in self._cache:
            self._cache.move_to_end(key)
            self.hits += 1
            return self._cache[key]
        self.misses += 1
        return None

    def put(self, query: str, results: list[SearchResult]) -> None:
        """Almacena los resultados de una consulta en caché.

        Args:
            query: Texto de la consulta.
            results: Lista de resultados a cachear.
        """
        key = self._normalize(query)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = results
        if len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Limpia la caché y reinicia los contadores."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    def size(self) -> int:
        """Retorna el número de entradas en caché."""
        return len(self._cache)

    def hit_rate(self) -> float:
        """Retorna la tasa de aciertos (hits / total)."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
