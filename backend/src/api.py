from datetime import datetime, timezone

def get_sample_payload():
    return {
        "component": "lf-wikidata-entity-graph",
        "source": "wikidata",
        "status": "ok",
        "generatedAt": datetime.now(timezone.utc).isoformat()
    }


def get_matching_metrics():
    return {"issue": "ISSUE-002", "precisionTarget": 0.90, "recallTarget": 0.85, "fprMax": 0.05}



def evaluate_match_quality(tp, fp, fn):
    """Compute precision/recall/f1 with safe zero division."""
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}
