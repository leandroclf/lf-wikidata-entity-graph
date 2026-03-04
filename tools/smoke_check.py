from backend.src.api import get_matching_metrics, is_match_above_threshold, count_matches_above_threshold
from backend.src.ingest import ingest_entities, validate_entity_record, process_entity_graph_pipeline

def run_test(name, func):
    try:
        func()
        print(f"[PASSED] {name}")
        return True
    except AssertionError as e:
        print(f"[FAILED] {name}: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] {name}: An unexpected error occurred - {e}")
        return False

def main():
    print("Starting smoke tests...")
    results = []

    # Test matching metrics
    results.append(run_test("API: get_matching_metrics", lambda: (
        metrics := get_matching_metrics(),
        assert metrics["issue"] == "ISSUE-002",
        assert metrics["precisionTarget"] >= 0.9
    )))
    results.append(run_test("API: is_match_above_threshold", lambda: (
        assert is_match_above_threshold(0.81) is True
    )))
    results.append(run_test("API: count_matches_above_threshold", lambda: (
        assert count_matches_above_threshold([0.2, 0.8, 0.9])["passed"] == 2
    )))
    
    # Test ingest module
    results.append(run_test("Ingest: ingest_entities", lambda: (
        test_records := [
            {"id": "e1", "name": "Test Entity"},
            {"id": "e2"}  # invalid - missing name
        ],
        result := ingest_entities(test_records),
        assert result["stats"]["total"] == 2,
        assert result["stats"]["valid"] == 1,
        assert result["stats"]["invalid"] == 1
    )))
    
    # Test validation
    results.append(run_test("Ingest: validate_entity_record", lambda: (
        validation := validate_entity_record({"id": "test", "name": "Valid"}),
        assert validation["valid"] is True
    )))

    # Test process_entity_graph_pipeline
    results.append(run_test("Pipeline: process_entity_graph_pipeline", lambda: (
        pipeline := process_entity_graph_pipeline(
            [{"id": "x1", "name": "ACME CORP"}, {"id": "x2", "name": "OpenAI"}],
            confidence_threshold=0.7,
        ),
        assert pipeline["stats"]["raw_total"] == 2,
        assert "baseline" in pipeline
    )))
    
    passed_count = sum(results)
    total_count = len(results)

    if all(results):
        print(f"\nAll smoke tests passed! ({passed_count}/{total_count})")
        print("smoke-check:ok")
    else:
        print(f"\nSmoke tests failed! ({passed_count}/{total_count} passed)")
        # Exit with a non-zero status code to indicate failure in CI
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
