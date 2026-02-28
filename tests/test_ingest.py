"""Tests for data ingestion module."""
from backend.src.ingest import (
    validate_entity_record,
    ingest_entities,
    deduplicate_entities
)


def test_validate_entity_record_valid():
    record = {"id": "e1", "name": "ACME Corp"}
    result = validate_entity_record(record)
    assert result["valid"] is True
    assert result["errors"] == []


def test_validate_entity_record_missing_name():
    record = {"id": "e1"}
    result = validate_entity_record(record)
    assert result["valid"] is False
    assert "missing_name" in result["errors"]


def test_validate_entity_record_missing_id():
    record = {"name": "ACME Corp"}
    result = validate_entity_record(record)
    assert result["valid"] is False
    assert "missing_id" in result["errors"]


def test_ingest_entities_empty():
    result = ingest_entities([])
    assert result["status"] == "empty"
    assert result["stats"]["total"] == 0


def test_ingest_entities_all_valid():
    records = [
        {"id": "e1", "name": "ACME Corp"},
        {"id": "e2", "name": "TechCo"}
    ]
    result = ingest_entities(records)
    
    assert result["status"] == "processed"
    assert result["stats"]["total"] == 2
    assert result["stats"]["valid"] == 2
    assert result["stats"]["invalid"] == 0
    assert result["stats"]["success_rate"] == 1.0
    assert len(result["valid_entities"]) == 2
    assert len(result["errors"]) == 0


def test_ingest_entities_mixed_validity():
    records = [
        {"id": "e1", "name": "ACME Corp"},
        {"id": "e2"},  # missing name
        {"name": "TechCo"}  # missing id
    ]
    result = ingest_entities(records)
    
    assert result["stats"]["total"] == 3
    assert result["stats"]["valid"] == 1
    assert result["stats"]["invalid"] == 2
    assert result["stats"]["success_rate"] == 0.3333
    assert len(result["errors"]) == 2


def test_ingest_entities_adds_metadata():
    records = [{"id": "e1", "name": "ACME Corp"}]
    result = ingest_entities(records)
    
    entity = result["valid_entities"][0]
    assert "_ingested_at" in entity
    assert "_source" in entity
    assert entity["_source"] == "batch_ingest"


def test_deduplicate_entities():
    entities = [
        {"id": "e1", "name": "ACME"},
        {"id": "e2", "name": "TechCo"},
        {"id": "e1", "name": "ACME Duplicate"}
    ]
    unique = deduplicate_entities(entities, key="id")
    
    assert len(unique) == 2
    assert unique[0]["id"] == "e1"
    assert unique[1]["id"] == "e2"


def test_deduplicate_entities_empty():
    assert deduplicate_entities([]) == []
