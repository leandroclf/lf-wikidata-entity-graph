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


def build_entity_graph(linked_entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a lightweight entity graph from linked entities.

    Graph structure:
    - entity nodes represent canonical entities grouped by Wikidata QID or normalized name
    - alias nodes represent observed aliases and source-provided alias lists
    - wikidata nodes represent linked QIDs
    - edges connect alias -> entity and entity -> wikidata
    """
    if not linked_entities:
        return {"nodes": [], "edges": [], "stats": {"entities": 0, "aliases": 0, "wikidata": 0, "edges": 0}}

    entity_groups: Dict[str, Dict[str, Any]] = {}
    alias_nodes: Dict[str, Dict[str, Any]] = {}
    wikidata_nodes: Dict[str, Dict[str, Any]] = {}
    edges = []
    seen_edges = set()

    for entity in linked_entities:
        name = entity.get("name", "")
        normalized_name = normalize_entity_name(name)
        wikidata = entity.get("_wikidata", {}) or {}
        qid = wikidata.get("qid")
        group_key = qid or normalized_name or str(entity.get("id", "unknown"))
        entity_node_id = f"entity:{group_key}"

        group = entity_groups.setdefault(
            group_key,
            {
                "id": entity_node_id,
                "type": "entity",
                "canonicalName": name,
                "normalizedName": normalized_name,
                "wikidataQid": qid,
                "linked": bool(wikidata.get("linked")),
                "sourceRecordIds": [],
                "aliases": [],
                "maxConfidence": 0.0,
            },
        )

        if entity.get("id") is not None:
            source_id = str(entity["id"])
            if source_id not in group["sourceRecordIds"]:
                group["sourceRecordIds"].append(source_id)

        confidence = float(wikidata.get("confidence", 0.0))
        if confidence > group["maxConfidence"]:
            group["maxConfidence"] = round(confidence, 3)
            group["canonicalName"] = name or group["canonicalName"]
            group["normalizedName"] = normalized_name or group["normalizedName"]

        if qid and not group.get("wikidataQid"):
            group["wikidataQid"] = qid
        if wikidata.get("linked"):
            group["linked"] = True

        raw_aliases = [name, *(entity.get("aliases") or [])]
        for alias in raw_aliases:
            normalized_alias = normalize_entity_name(alias)
            if not normalized_alias:
                continue
            if normalized_alias not in group["aliases"]:
                group["aliases"].append(normalized_alias)

            alias_node_id = f"alias:{normalized_alias}"
            alias_nodes.setdefault(
                alias_node_id,
                {
                    "id": alias_node_id,
                    "type": "alias",
                    "name": alias,
                    "normalizedName": normalized_alias,
                },
            )

            edge_key = (alias_node_id, entity_node_id, "alias_of")
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append(
                    {
                        "source": alias_node_id,
                        "target": entity_node_id,
                        "type": "alias_of",
                    }
                )

        if qid:
            wikidata_node_id = f"wikidata:{qid}"
            wikidata_nodes.setdefault(
                wikidata_node_id,
                {
                    "id": wikidata_node_id,
                    "type": "wikidata",
                    "qid": qid,
                },
            )
            edge_key = (entity_node_id, wikidata_node_id, "same_as")
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append(
                    {
                        "source": entity_node_id,
                        "target": wikidata_node_id,
                        "type": "same_as",
                    }
                )

    entity_nodes = []
    for group in entity_groups.values():
        entity_nodes.append({**group, "aliasCount": len(group["aliases"])})

    nodes = entity_nodes + list(alias_nodes.values()) + list(wikidata_nodes.values())
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "entities": len(entity_nodes),
            "aliases": len(alias_nodes),
            "wikidata": len(wikidata_nodes),
            "edges": len(edges),
        },
    }


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
    graph = build_entity_graph(linked_entities)

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
        "graph": graph,
        "errors": ingested.get("errors", []),
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
