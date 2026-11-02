class TestQueryCache:
    def test_get_miss(self, cache):
        result = cache.get("python java")
        assert result is None
        assert cache.misses == 1

    def test_put_and_get(self, cache):
        results = [{"doc_id": 1, "score": 0.5}]
        cache.put("python java", results)
        assert cache.get("python java") == results
        assert cache.hits == 1

    def test_normalization_order_independent(self, cache):
        results = [{"doc_id": 1}]
        cache.put("java python", results)
        assert cache.get("python java") == results

    def test_normalization_case_insensitive(self, cache):
        results = [{"doc_id": 1}]
        cache.put("Python Java", results)
        assert cache.get("python java") == results

    def test_lru_eviction(self, cache):
        cache.max_size = 2
        cache.put("a", [1])
        cache.put("b", [2])
        cache.get("a")
        cache.put("c", [3])
        assert cache.get("b") is None
        assert cache.get("a") is not None

    def test_hit_rate(self, cache):
        cache.put("python", [1])
        cache.get("python")
        cache.get("java")
        assert cache.hit_rate() == 0.5

    def test_clear(self, cache):
        cache.put("python", [1])
        cache.get("python")
        cache.clear()
        assert cache.size() == 0
        assert cache.hits == 0
        assert cache.misses == 0
