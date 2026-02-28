from backend.src.api import get_matching_metrics, is_match_above_threshold, count_matches_above_threshold
from backend.src.ingest import ingest_entities, validate_entity_record


def main():
    # Test matching metrics
    metrics = get_matching_metrics()
    assert metrics["issue"] == "ISSUE-002"
    assert metrics["precisionTarget"] >= 0.9
    assert is_match_above_threshold(0.81) is True
    assert count_matches_above_threshold([0.2, 0.8, 0.9])["passed"] == 2
    
    # Test ingest module
    test_records = [
        {"id": "e1", "name": "Test Entity"},
        {"id": "e2"}  # invalid - missing name
    ]
    result = ingest_entities(test_records)
    assert result["stats"]["total"] == 2
    assert result["stats"]["valid"] == 1
    assert result["stats"]["invalid"] == 1
    
    # Test validation
    validation = validate_entity_record({"id": "test", "name": "Valid"})
    assert validation["valid"] is True
    
    print("smoke-check:ok")


if __name__ == "__main__":
    main()
