class TestSequentialSearchEngine:
    def test_load_documents(self, sequential_engine):
        assert sequential_engine.get_doc_count() == 3

    def test_search_finds_matching_doc(self, sequential_engine):
        results = sequential_engine.search("python")
        assert len(results) == 2

    def test_search_no_results(self, sequential_engine):
        results = sequential_engine.search("nonexistent")
        assert len(results) == 0

    def test_search_empty_query(self, sequential_engine):
        results = sequential_engine.search("")
        assert len(results) == 0

    def test_search_all_terms_required(self, sequential_engine):
        results = sequential_engine.search("python red")
        assert len(results) == 0

    def test_results_have_required_fields(self, sequential_engine):
        results = sequential_engine.search("python")
        for r in results:
            assert r.doc_id > 0
            assert r.doc_name.startswith("documento_")
            assert r.score > 0
            assert len(r.snippet) > 0

    def test_top_k_limits_results(self, sequential_engine):
        results = sequential_engine.search("python", top_k=1)
        assert len(results) == 1


class TestSequentialTokenize:
    def test_lowercase(self, sequential_engine):
        from search_common import tokenize

        assert tokenize("Hello World") == ["hello", "world"]

    def test_empty(self, sequential_engine):
        from search_common import tokenize

        assert tokenize("") == []
