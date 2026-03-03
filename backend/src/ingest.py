"""Data ingestion module for entity graph."""
from typing import List, Dict, Any
import json
from datetime import datetime, timezone

from backend.src.api import (
    link_entities_to_wikidata,
    normalize_entity_name,
    summarize_link_confidence,
)


def validate_entity_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that an entity record has required fields."""
    errors = []
    
    if not record.get("name"):
        errors.append("missing_name")
    
    if "id" not in record:
        errors.append("missing_id")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "record": record
    }


def ingest_entities(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ingest a batch of entity records.
    Returns validation results and stats.
    """
    if not records:
        return {
            "status": "empty",
            "stats": {"total": 0, "valid": 0, "invalid": 0},
            "valid_entities": [],
            "errors": []
        }
    
    valid_entities = []
    errors = []
    
    for idx, record in enumerate(records):
        validation = validate_entity_record(record)
        
        if validation["valid"]:
            valid_entities.append({
                **record,
                "_ingested_at": datetime.now(timezone.utc).isoformat(),
                "_source": "batch_ingest"
            })
        else:
            errors.append({
                "index": idx,
                "record_id": record.get("id", "unknown"),
                "errors": validation["errors"]
            })
    
    return {
        "status": "processed",
        "stats": {
            "total": len(records),
            "valid": len(valid_entities),
            "invalid": len(errors),
            "success_rate": round(len(valid_entities) / len(records), 4) if records else 0.0
        },
        "valid_entities": valid_entities,
        "errors": errors
    }


def load_entities_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load entity records from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "entities" in data:
                return data["entities"]
            else:
                return [data]
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def deduplicate_entities(entities: List[Dict[str, Any]], key: str = "id") -> List[Dict[str, Any]]:
    """Remove duplicate entities based on a key field."""
    seen = set()
    unique = []
    
    for entity in entities:
        value = entity.get(key)
        if value and value not in seen:
            seen.add(value)
            unique.append(entity)
    
    return unique


def deduplicate_linked_entities(linked_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate linked entities preferring Wikidata QID, then normalized name.
    """
    seen = set()
    unique = []

    for entity in linked_entities or []:
        wikidata = entity.get("_wikidata", {}) or {}
        qid = wikidata.get("qid")
        dedup_key = qid if qid else normalize_entity_name(entity.get("name", ""))
        if not dedup_key:
            dedup_key = f"row:{len(unique)}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        unique.append(entity)

    return unique


def process_entity_graph_pipeline(
    records: List[Dict[str, Any]],
    confidence_threshold: float = 0.7,
) -> Dict[str, Any]:
    """
    End-to-end ISSUE-002 pipeline:
    validate -> dedupe raw -> link Wikidata -> dedupe by QID/name -> baseline metrics.
    """
    ingested = ingest_entities(records)
    valid_entities = ingested.get("valid_entities", [])

    raw_dedup = deduplicate_entities(valid_entities, key="id")
    linked = link_entities_to_wikidata(raw_dedup, confidence_threshold=confidence_threshold)
    linked_entities = linked.get("linked", [])
    linked_dedup = deduplicate_linked_entities(linked_entities)
    link_summary = summarize_link_confidence(linked_dedup)

    total_raw = len(records or [])
    total_valid = len(valid_entities)
    total_linked = sum(1 for e in linked_dedup if e.get("_wikidata", {}).get("linked"))
    unique_rate = round(len(linked_dedup) / total_valid, 4) if total_valid else 0.0

    return {
        "status": "processed",
        "stats": {
            "raw_total": total_raw,
            "valid_total": total_valid,
            "raw_dedup_total": len(raw_dedup),
            "linked_total": len(linked_entities),
            "linked_dedup_total": len(linked_dedup),
            "linked_success_total": total_linked,
            "link_rate": round(total_linked / len(linked_dedup), 4) if linked_dedup else 0.0,
            "unique_entity_rate": unique_rate,
        },
        "baseline": {
            "matchingPrecisionTarget": 0.9,
            "linkConfidenceAvg": link_summary.get("avgConfidence", 0.0),
            "entityResolutionCoverage": unique_rate,
        },
        "entities": linked_dedup,
        "errors": ingested.get("errors", []),
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
