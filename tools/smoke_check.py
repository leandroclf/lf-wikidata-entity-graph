from backend.src.api import get_matching_metrics, is_match_above_threshold


def main():
    metrics = get_matching_metrics()
    assert metrics["issue"] == "ISSUE-002"
    assert metrics["precisionTarget"] >= 0.9
    assert is_match_above_threshold(0.81) is True
    print("smoke-check:ok")


if __name__ == "__main__":
    main()
