from ranking import ResultRanker
from search_common import SearchResult


class TestResultRanker:
    def _make_results(self, scores):
        return [SearchResult(doc_id=i, doc_name=f"doc_{i}", score=s) for i, s in enumerate(scores)]

    def test_fewer_than_k(self):
        results = self._make_results([0.3, 0.1, 0.5])
        ranked = ResultRanker.rank(results, top_k=10)
        assert len(ranked) == 3
        assert ranked[0].score == 0.5

    def test_more_than_k(self):
        results = self._make_results([0.1, 0.5, 0.3, 0.9, 0.2, 0.8, 0.4, 0.7, 0.6, 0.0, 0.95])
        ranked = ResultRanker.rank(results, top_k=3)
        assert len(ranked) == 3
        assert ranked[0].score == 0.95
        assert ranked[1].score == 0.9
        assert ranked[2].score == 0.8

    def test_sorted_descending(self):
        scores = [0.5, 0.9, 0.1, 0.7, 0.3, 0.8, 0.2, 0.6, 0.4, 0.0, 0.95]
        results = self._make_results(scores)
        ranked = ResultRanker.rank(results, top_k=5)
        for i in range(len(ranked) - 1):
            assert ranked[i].score >= ranked[i + 1].score
