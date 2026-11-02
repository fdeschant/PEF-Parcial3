class TestInvertedIndex:
    def test_add_document(self, indexed_engine):
        assert len(indexed_engine.index.get_all_doc_ids()) == 3

    def test_posting_list(self, indexed_engine):
        posting = indexed_engine.index.get_posting_list("python")
        assert len(posting) == 2

    def test_term_freq(self, indexed_engine):
        doc_id = next(iter(indexed_engine.index.get_all_doc_ids()))
        tf = indexed_engine.index.get_term_freq("python", doc_id)
        assert tf >= 0

    def test_merge(self, indexed_engine):
        from inverted_index import InvertedIndex

        other = InvertedIndex()
        other.add_document(99, "documento_99.txt", ["test", "merge"])
        indexed_engine.index.merge(other)
        assert 99 in indexed_engine.index.get_all_doc_ids()

    def test_doc_length(self, indexed_engine):
        for doc_id in indexed_engine.index.get_all_doc_ids():
            assert indexed_engine.index.get_doc_length(doc_id) > 0


class TestInvertedIndexEngine:
    def test_build_index(self, indexed_engine):
        assert len(indexed_engine.index.get_all_doc_ids()) == 3

    def test_search_finds_matching_doc(self, indexed_engine):
        results = indexed_engine.search("python")
        assert len(results) == 2

    def test_search_no_results(self, indexed_engine):
        results = indexed_engine.search("nonexistent")
        assert len(results) == 0

    def test_search_empty_query(self, indexed_engine):
        results = indexed_engine.search("")
        assert len(results) == 0

    def test_search_all_terms_required(self, indexed_engine):
        results = indexed_engine.search("python red")
        assert len(results) == 0

    def test_results_have_required_fields(self, indexed_engine):
        results = indexed_engine.search("python")
        for r in results:
            assert r.doc_id > 0
            assert r.doc_name.startswith("documento_")
            assert r.score > 0
            assert len(r.snippet) > 0

    def test_top_k_limits_results(self, indexed_engine):
        results = indexed_engine.search("python", top_k=1)
        assert len(results) == 1

    def test_build_partial_index(self, indexed_engine):
        partial = indexed_engine.build_partial_index(["documento_1.txt"])
        assert len(partial.get_all_doc_ids()) == 1
