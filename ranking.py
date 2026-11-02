import heapq

from search_common import SearchResult


class ResultRanker:
    """Rankeador de resultados usando heap de tamaño K.

    Si los resultados caben en K: ordenamiento completo O(N log N).
    Si exceden K: mantiene un min-heap de tamaño K -> O(N log K).
    """

    @staticmethod
    def rank(results: list[SearchResult], top_k: int = 10) -> list[SearchResult]:
        """Retorna los top_k resultados con mayor score.

        Args:
            results: Lista de resultados con atributo .score.
            top_k: Número máximo de resultados a retornar.

        Returns:
            Lista ordenada por score descendente.
        """
        if len(results) <= top_k:
            results.sort(key=lambda r: r.score, reverse=True)
            return results

        heap: list[tuple[float, int, SearchResult]] = []
        for r in results:
            if len(heap) < top_k:
                heapq.heappush(heap, (r.score, id(r), r))
            elif r.score > heap[0][0]:
                heapq.heapreplace(heap, (r.score, id(r), r))

        ranked = [item[2] for item in heap]
        ranked.sort(key=lambda r: r.score, reverse=True)
        return ranked
