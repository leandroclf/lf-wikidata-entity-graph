import unittest

from backend.src.ingest import (
    build_entity_graph,
    deduplicate_linked_entities,
    process_entity_graph_pipeline,
)


class TestIssue002Pipeline(unittest.TestCase):
    def test_build_entity_graph_groups_by_qid_and_preserves_aliases(self):
        linked = [
            {
                "id": "1",
                "name": "International Business Machines",
                "aliases": ["IBM", "Big Blue"],
                "_wikidata": {"qid": "Q37156", "linked": True, "confidence": 0.9},
            },
            {
                "id": "2",
                "name": "IBM",
                "_wikidata": {"qid": "Q37156", "linked": True, "confidence": 0.8},
            },
            {
                "id": "3",
                "name": "Other Co",
                "_wikidata": {"qid": None, "linked": False, "confidence": 0.2},
            },
        ]

        out = build_entity_graph(linked)
        entity_nodes = [node for node in out["nodes"] if node["type"] == "entity"]
        alias_nodes = [node for node in out["nodes"] if node["type"] == "alias"]
        wikidata_nodes = [node for node in out["nodes"] if node["type"] == "wikidata"]

        self.assertEqual(out["stats"]["entities"], 2)
        self.assertEqual(len(entity_nodes), 2)
        self.assertEqual(out["stats"]["wikidata"], 1)
        self.assertEqual(len(wikidata_nodes), 1)
        self.assertEqual(out["stats"]["aliases"], 4)
        self.assertEqual(len(alias_nodes), 4)
        self.assertIn(
            {"source": "entity:Q37156", "target": "wikidata:Q37156", "type": "same_as"},
            out["edges"],
        )
        ibm_node = next(node for node in entity_nodes if node["id"] == "entity:Q37156")
        self.assertEqual(ibm_node["aliasCount"], 3)
        self.assertEqual(sorted(ibm_node["sourceRecordIds"]), ["1", "2"])

    def test_deduplicate_linked_entities_prefers_qid(self):
        linked = [
            {"id": "1", "name": "ACME CORP", "_wikidata": {"qid": "Q123", "linked": True, "confidence": 0.9}},
            {"id": "2", "name": "Acme Corp", "_wikidata": {"qid": "Q123", "linked": True, "confidence": 0.8}},
            {"id": "3", "name": "Other Co", "_wikidata": {"qid": None, "linked": False, "confidence": 0.3}},
            {"id": "4", "name": " other  co ", "_wikidata": {"qid": None, "linked": False, "confidence": 0.2}},
        ]
        out = deduplicate_linked_entities(linked)
        self.assertEqual(len(out), 2)

    def test_process_entity_graph_pipeline_returns_baseline_and_dedup_stats(self):
        records = [
            {"id": "a1", "name": "ACME CORP"},
            {"id": "a1", "name": "Acme Corp Duplicate ID"},
            {"id": "a2", "name": "OpenAI"},
            {"id": "a3"},  # invalid
        ]
        out = process_entity_graph_pipeline(records, confidence_threshold=0.7)
        stats = out["stats"]

        self.assertEqual(out["status"], "processed")
        self.assertEqual(stats["raw_total"], 4)
        self.assertEqual(stats["valid_total"], 3)
        self.assertEqual(stats["raw_dedup_total"], 2)
        self.assertIn("link_rate", stats)
        self.assertIn("unique_entity_rate", stats)
        self.assertIn("baseline", out)
        self.assertIn("matchingPrecisionTarget", out["baseline"])
        self.assertIn("graph", out)
        self.assertEqual(out["graph"]["stats"]["entities"], 2)
        self.assertEqual(out["graph"]["stats"]["wikidata"], 2)
        self.assertGreaterEqual(out["graph"]["stats"]["edges"], 4)


if __name__ == "__main__":
    unittest.main()
