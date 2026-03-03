import unittest

from backend.src.ingest import (
    deduplicate_linked_entities,
    process_entity_graph_pipeline,
)


class TestIssue002Pipeline(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
