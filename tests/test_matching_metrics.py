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
