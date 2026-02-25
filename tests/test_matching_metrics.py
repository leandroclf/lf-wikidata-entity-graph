from backend.src.api import get_matching_metrics


def test_matching_metrics_targets():
    m=get_matching_metrics()
    assert m["precisionTarget"]>=0.9
    assert m["fprMax"]<=0.05
