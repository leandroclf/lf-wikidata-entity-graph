import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.api import (
    count_matches_above_threshold,
    get_matching_metrics,
    is_match_above_threshold,
)
from backend.src.ingest import (
    ingest_entities,
    process_entity_graph_pipeline,
    validate_entity_record,
)


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


def test_get_matching_metrics():
    metrics = get_matching_metrics()
    assert metrics["issue"] == "ISSUE-002"
    assert metrics["precisionTarget"] >= 0.9


def test_is_match_above_threshold():
    assert is_match_above_threshold(0.81) is True


def test_count_matches_above_threshold():
    assert count_matches_above_threshold([0.2, 0.8, 0.9])["passed"] == 2


def test_ingest_entities():
    test_records = [
        {"id": "e1", "name": "Test Entity"},
        {"id": "e2"},  # invalid - missing name
    ]
    result = ingest_entities(test_records)
    assert result["stats"]["total"] == 2
    assert result["stats"]["valid"] == 1
    assert result["stats"]["invalid"] == 1


def test_validate_entity_record():
    validation = validate_entity_record({"id": "test", "name": "Valid"})
    assert validation["valid"] is True


def test_process_entity_graph_pipeline():
    pipeline = process_entity_graph_pipeline(
        [{"id": "x1", "name": "ACME CORP"}, {"id": "x2", "name": "OpenAI"}],
        confidence_threshold=0.7,
    )
    assert pipeline["stats"]["raw_total"] == 2
    assert "baseline" in pipeline
    assert pipeline["graph"]["stats"]["entities"] == 2
    assert pipeline["graph"]["stats"]["wikidata"] == 2


def main():
    print("Starting smoke tests...")
    tests = [
        ("API: get_matching_metrics", test_get_matching_metrics),
        ("API: is_match_above_threshold", test_is_match_above_threshold),
        ("API: count_matches_above_threshold", test_count_matches_above_threshold),
        ("Ingest: ingest_entities", test_ingest_entities),
        ("Ingest: validate_entity_record", test_validate_entity_record),
        ("Pipeline: process_entity_graph_pipeline", test_process_entity_graph_pipeline),
    ]

    results = [run_test(name, fn) for name, fn in tests]
    passed_count = sum(results)
    total_count = len(results)

    if all(results):
        print(f"\nAll smoke tests passed! ({passed_count}/{total_count})")
        print("smoke-check:ok")
    else:
        print(f"\nSmoke tests failed! ({passed_count}/{total_count} passed)")
        sys.exit(1)


if __name__ == "__main__":
    main()
