import unittest

from backend.src.api import link_entities_to_wikidata


class TestIssue002WikidataLinking(unittest.TestCase):
    def test_link_entities_respects_threshold(self):
        result = link_entities_to_wikidata([{"name": "X"}], confidence_threshold=0.9)
        self.assertIsInstance(result["linked"], list)
        self.assertFalse(result["linked"][0]["_wikidata"]["linked"])
        self.assertIsNone(result["linked"][0]["_wikidata"]["qid"])

    def test_qid_is_deterministic_for_normalized_name(self):
        one = link_entities_to_wikidata([{"name": " ACME   CORP "}])["linked"][0]["_wikidata"]["qid"]
        two = link_entities_to_wikidata([{"name": "acme corp"}])["linked"][0]["_wikidata"]["qid"]
        self.assertIsNotNone(one)
        self.assertEqual(one, two)


if __name__ == "__main__":
    unittest.main()
