#!/usr/bin/env python3
"""Demo script showing entity ingestion workflow."""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.src.ingest import (
    build_entity_graph,
    deduplicate_entities,
    ingest_entities,
    load_entities_from_json,
)
from backend.src.api import link_entities_to_wikidata


def main():
    print("=== Entity Ingestion Demo ===\n")
    
    # Load sample entities
    data_file = Path(__file__).parent.parent / "data" / "sample-entities.json"
    print(f"1. Loading entities from: {data_file}")
    entities = load_entities_from_json(str(data_file))
    print(f"   Loaded {len(entities)} entity records\n")
    
    # Ingest and validate
    print("2. Ingesting entities...")
    result = ingest_entities(entities)
    print(f"   Status: {result['status']}")
    print(f"   Total: {result['stats']['total']}")
    print(f"   Valid: {result['stats']['valid']}")
    print(f"   Invalid: {result['stats']['invalid']}")
    print(f"   Success Rate: {result['stats']['success_rate'] * 100}%\n")
    
    if result['errors']:
        print("   Errors found:")
        for error in result['errors']:
            print(f"   - Record {error['index']}: {', '.join(error['errors'])}")
        print()
    
    # Deduplicate (demo with artificial duplicates)
    print("3. Deduplication test...")
    with_dupes = result['valid_entities'] + [result['valid_entities'][0]]  # Add duplicate
    print(f"   Before: {len(with_dupes)} entities")
    unique = deduplicate_entities(with_dupes, key="id")
    print(f"   After: {len(unique)} entities\n")
    
    # Link to Wikidata
    print("4. Linking to Wikidata...")
    linked_result = link_entities_to_wikidata(unique[:3])  # Demo with first 3
    print(f"   Linked: {linked_result['stats']['linked_count']}/{linked_result['stats']['total']}")
    print(f"   Link Rate: {linked_result['stats']['link_rate'] * 100}%\n")

    graph = build_entity_graph(linked_result["linked"])
    print("5. Entity graph summary...")
    print(f"   Entity nodes: {graph['stats']['entities']}")
    print(f"   Alias nodes: {graph['stats']['aliases']}")
    print(f"   Wikidata nodes: {graph['stats']['wikidata']}")
    print(f"   Edges: {graph['stats']['edges']}\n")
    
    # Show example linked entity
    if linked_result['linked']:
        example = linked_result['linked'][0]
        print("   Example linked entity:")
        print(f"   - Name: {example['name']}")
        print(f"   - Wikidata QID: {example['_wikidata']['qid']}")
        print(f"   - Confidence: {example['_wikidata']['confidence']}")
        print(f"   - Linked: {example['_wikidata']['linked']}\n")
    
    print("=== Demo Complete ===")


if __name__ == "__main__":
    main()
