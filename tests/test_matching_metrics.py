from backend.src.api import get_matching_metrics


def test_matching_metrics_targets():
    m=get_matching_metrics()
    assert m["precisionTarget"]>=0.9
    assert m["fprMax"]<=0.05


from backend.src.api import evaluate_match_quality


def test_evaluate_match_quality():
    m = evaluate_match_quality(tp=18, fp=2, fn=4)
    assert m["precision"] == 0.9
    assert m["recall"] == 0.8182
    assert m["f1"] == 0.8571


from backend.src.api import normalize_entity_name


def test_normalize_entity_name():
    assert normalize_entity_name("  ACME   Corp ") == "acme corp"


from backend.src.api import choose_best_match


def test_choose_best_match():
    c = [{"id":"a","score":0.71},{"id":"b","score":0.89}]
    best = choose_best_match(c)
    assert best["id"] == "b"


from backend.src.api import score_name_similarity


def test_score_name_similarity():
    assert score_name_similarity("ACME Corp", "Acme Corporation") > 0.3
    assert score_name_similarity("Foo", "Bar") == 0.0


from backend.src.api import is_match_above_threshold


def test_is_match_above_threshold():
    assert is_match_above_threshold(0.81) is True
    assert is_match_above_threshold(0.79) is False


from backend.src.api import build_match_decision
from backend.src.api import summarize_threshold_outcomes
from backend.src.api import summarize_best_match_coverage
from backend.src.api import summarize_similarity_scores
from backend.src.api import count_matches_above_threshold
from backend.src.api import estimate_match_rate
from backend.src.api import calculate_precision_delta


def test_build_match_decision():
    d = build_match_decision(0.82, 0.8)
    assert d["match"] is True
    assert d["threshold"] == 0.8


def test_summarize_threshold_outcomes():
    out = summarize_threshold_outcomes([0.79, 0.8, 0.91, 0.1], threshold=0.8)
    assert out == {
        "threshold": 0.8,
        "total": 4,
        "passed": 2,
        "failed": 2,
        "passRate": 0.5,
    }


def test_summarize_threshold_outcomes_empty():
    out = summarize_threshold_outcomes([], threshold=0.8)
    assert out["total"] == 0
    assert out["passRate"] == 0.0


def test_summarize_best_match_coverage():
    out = summarize_best_match_coverage([
        {"candidates": [{"id": "a", "score": 0.7}, {"id": "b", "score": 0.9}]},
        {"candidates": []},
        {"candidates": [{"id": "c", "score": 0.6}]},
    ])
    assert out == {"total": 3, "matched": 2, "coverage": 0.6667}


def test_summarize_best_match_coverage_empty():
    assert summarize_best_match_coverage([]) == {"total": 0, "matched": 0, "coverage": 0.0}


def test_summarize_similarity_scores():
    out = summarize_similarity_scores([
        ("ACME Corp", "Acme Corporation"),
        ("Foo", "Bar"),
    ])
    assert out["total"] == 2
    assert out["avgSimilarity"] == 0.1666
    assert out["maxSimilarity"] == 0.3333


def test_summarize_similarity_scores_empty():
    assert summarize_similarity_scores([]) == {"total": 0, "avgSimilarity": 0.0, "maxSimilarity": 0.0}


def test_count_matches_above_threshold():
    out = count_matches_above_threshold([0.2, 0.8, 0.91], threshold=0.8)
    assert out == {"threshold": 0.8, "total": 3, "passed": 2}


def test_count_matches_above_threshold_empty():
    assert count_matches_above_threshold([], threshold=0.8) == {"threshold": 0.8, "total": 0, "passed": 0}


def test_estimate_match_rate():
    out = estimate_match_rate([
        {"candidates": [{"id": "a", "score": 0.9}]},
        {"candidates": [{"id": "b", "score": 0.6}]},
        {"candidates": []},
        {"candidates": [{"id": "c", "score": 0.85}]},
    ])
    assert out == 0.5


def test_estimate_match_rate_empty():
    assert estimate_match_rate([]) == 0.0


def test_calculate_precision_delta():
    delta = calculate_precision_delta(tp=18, fp=2, fn=4, baseline_precision=0.85)
    assert delta == 5.0


def test_calculate_precision_delta_zero_baseline():
    assert calculate_precision_delta(tp=10, fp=0, fn=0, baseline_precision=0) == 0.0


def test_link_entities_empty():
    from backend.src.api import link_entities_to_wikidata
    result = link_entities_to_wikidata([])
    assert result["stats"]["total"] == 0


def test_link_entities_with_data():
    from backend.src.api import link_entities_to_wikidata
    entities = [{"name": "Microsoft Corporation"}, {"name": "X"}]
    result = link_entities_to_wikidata(entities)
    assert result["stats"]["total"] == 2
    assert result["linked"][0]["_wikidata"]["linked"] == True


def test_link_entities_respects_threshold_and_keeps_list_shape():
    from backend.src.api import link_entities_to_wikidata

    result = link_entities_to_wikidata([{"name": "X"}], confidence_threshold=0.9)
    assert isinstance(result["linked"], list)
    assert result["linked"][0]["_wikidata"]["linked"] is False
    assert result["linked"][0]["_wikidata"]["qid"] is None


def test_link_entities_qid_is_deterministic_and_normalized():
    from backend.src.api import link_entities_to_wikidata

    one = link_entities_to_wikidata([{"name": " ACME   CORP "}])["linked"][0]["_wikidata"]["qid"]
    two = link_entities_to_wikidata([{"name": "acme corp"}])["linked"][0]["_wikidata"]["qid"]

    assert one is not None
    assert one == two


def test_resolve_entity_aliases():
    from backend.src.api import resolve_entity_aliases
    aliases = {"IBM": ["International Business Machines"]}
    resolved = resolve_entity_aliases("International Business Machines", aliases)
    assert resolved["canonical"] == "IBM"


def test_summarize_link_confidence():
    from backend.src.api import summarize_link_confidence

    payload = [
        {"name": "A", "_wikidata": {"linked": True, "confidence": 0.9}},
        {"name": "B", "_wikidata": {"linked": False, "confidence": 0.6}},
        {"name": "C", "_wikidata": {"linked": True, "confidence": 0.8}},
    ]

    out = summarize_link_confidence(payload)
    assert out == {"total": 3, "avgConfidence": 0.7667, "linkedCount": 2}


def test_summarize_link_confidence_empty():
    from backend.src.api import summarize_link_confidence
    assert summarize_link_confidence([]) == {"total": 0, "avgConfidence": 0.0, "linkedCount": 0}
