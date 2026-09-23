from app.services.knowledge_base import retrieve


def test_retrieve_finds_relevant_pool_snippet():
    results = retrieve("Does the hotel have a swimming pool?")
    assert len(results) > 0
    assert any("pool" in r["text"].lower() for r in results)


def test_retrieve_finds_relevant_breakfast_snippet():
    results = retrieve("Is breakfast included?")
    assert len(results) > 0
    assert any("breakfast" in r["text"].lower() for r in results)


def test_retrieve_returns_empty_for_irrelevant_query():
    results = retrieve("Do you sell airline tickets?")
    assert results == []


def test_retrieve_respects_top_k_limit():
    results = retrieve("room", top_k=2)
    assert len(results) <= 2


def test_retrieve_results_sorted_by_score_descending():
    results = retrieve("family suite room capacity")
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_retrieve_handles_plural_policy_query():
    """
    Regression test: "policies" (plural) must match knowledge base
    entries tagged/keyed "policy" (singular). Previously this returned
    nothing because scoring used exact word/substring matching with no
    singular/plural normalization.
    """
    results = retrieve("what are the policies")
    assert len(results) > 0


def test_retrieve_handles_plural_room_query():
    """Regression test for the same normalization, on 'rooms' -> 'room'."""
    results = retrieve("tell me about your rooms")
    assert len(results) > 0
