"""Data ingestion module for entity graph."""
from typing import List, Dict, Any
import json
from datetime import datetime, timezone


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
