from backend.src.api import get_matching_metrics, is_match_above_threshold, count_matches_above_threshold


def main():
    metrics = get_matching_metrics()
    assert metrics["issue"] == "ISSUE-002"
    assert metrics["precisionTarget"] >= 0.9
    assert is_match_above_threshold(0.81) is True
    assert count_matches_above_threshold([0.2, 0.8, 0.9])["passed"] == 2
    print("smoke-check:ok")


if __name__ == "__main__":
    main()
