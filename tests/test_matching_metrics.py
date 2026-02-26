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
