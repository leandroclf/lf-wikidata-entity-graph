from datetime import datetime, timezone
import hashlib

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



def normalize_entity_name(name):
    return " ".join(str(name).strip().lower().split())



def choose_best_match(candidates):
    """Return candidate with highest score; None for empty list."""
    if not candidates:
        return None
    return max(candidates, key=lambda c: c.get("score", 0))



def score_name_similarity(a, b):
    na = normalize_entity_name(a)
    nb = normalize_entity_name(b)
    if not na or not nb:
        return 0.0
    aset, bset = set(na.split()), set(nb.split())
    inter = len(aset & bset)
    union = len(aset | bset)
    return round(inter / union, 4) if union else 0.0



def is_match_above_threshold(score, threshold=0.8):
    return float(score) >= float(threshold)



def build_match_decision(score, threshold=0.8):
    ok = is_match_above_threshold(score, threshold)
    return {"score": float(score), "threshold": float(threshold), "match": ok}


def summarize_threshold_outcomes(scores, threshold=0.8):
    """Aggregate pass/fail counts for a threshold decision."""
    if not scores:
        return {"threshold": float(threshold), "total": 0, "passed": 0, "failed": 0, "passRate": 0.0}

    total = len(scores)
    passed = sum(1 for s in scores if is_match_above_threshold(s, threshold))
    failed = total - passed
    return {
        "threshold": float(threshold),
        "total": total,
        "passed": passed,
        "failed": failed,
        "passRate": round(passed / total, 4),
    }


def summarize_best_match_coverage(records):
    """Share of records with an automatic best-match candidate."""
    if not records:
        return {"total": 0, "matched": 0, "coverage": 0.0}

    matched = 0
    for r in records:
        best = choose_best_match(r.get("candidates", []))
        if best is not None:
            matched += 1

    total = len(records)
    return {"total": total, "matched": matched, "coverage": round(matched / total, 4)}


def summarize_similarity_scores(pairs):
    """Average and max similarity for name pairs."""
    if not pairs:
        return {"total": 0, "avgSimilarity": 0.0, "maxSimilarity": 0.0}
    scores = [score_name_similarity(a, b) for a, b in pairs]
    return {
        "total": len(scores),
        "avgSimilarity": round(sum(scores) / len(scores), 4),
        "maxSimilarity": max(scores),
    }


def count_matches_above_threshold(scores, threshold=0.8):
    """Count how many similarity scores pass the match threshold."""
    total = len(scores or [])
    passed = sum(1 for s in (scores or []) if is_match_above_threshold(s, threshold))
    return {"threshold": float(threshold), "total": total, "passed": passed}


def estimate_match_rate(records):
    """Estimate share of records with a qualifying best match (score >= 0.8)."""
    if not records:
        return 0.0
    matched = 0
    for r in records:
        best = choose_best_match(r.get("candidates", []))
        if best and is_match_above_threshold(best.get("score", 0)):
            matched += 1
    return round(matched / len(records), 4)


def calculate_precision_delta(tp, fp, fn, baseline_precision):
    """Return percentage-point delta vs baseline precision."""
    if baseline_precision <= 0:
        return 0.0
    current = evaluate_match_quality(tp, fp, fn)["precision"]
    return round((current - baseline_precision) * 100, 2)


def _deterministic_qid_from_name(name):
    """Build a stable pseudo-QID from a normalized entity name."""
    normalized = normalize_entity_name(name)
    if not normalized:
        return None
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()
    return f"Q{int(digest[:10], 16) % 1000000}"


def link_entities_to_wikidata(entities, confidence_threshold=0.7):
    """
    Link business entities to Wikidata IDs based on name matching.
    Returns linked entities with confidence scores.
    """
    if not entities:
        return {"linked": [], "stats": {"total": 0, "linked_count": 0, "link_rate": 0.0}}
    
    linked = []
    linked_count = 0

    for entity in entities:
        name = entity.get("name", "")
        # Simulate Wikidata lookup with confidence scoring
        confidence = 0.0 if not name else min(0.9, len(name.strip()) / 20 + 0.5)

        is_linked = confidence >= confidence_threshold
        linked_entity = {
            **entity,
            "_wikidata": {
                "linked": is_linked,
                "confidence": round(confidence, 3),
                "qid": _deterministic_qid_from_name(name) if is_linked else None,
            },
        }
        linked.append(linked_entity)
        if is_linked:
            linked_count += 1
    
    return {
        "linked": linked,
        "stats": {
            "total": len(entities),
            "linked_count": linked_count,
            "link_rate": round(linked_count / len(entities), 4) if entities else 0.0
        }
    }


def resolve_entity_aliases(entity_name, known_aliases=None):
    """
    Resolve entity name to canonical form using known aliases.
    Useful for matching variations like 'IBM' vs 'International Business Machines'.
    """
    aliases = known_aliases or {}
    normalized_input = "" if entity_name is None else str(entity_name).strip().lower()
    
    for canonical, alias_list in aliases.items():
        canonical_text = "" if canonical is None else str(canonical).strip()
        if not canonical_text:
            continue

        if normalized_input == canonical_text.lower():
            return {"canonical": canonical, "input": entity_name, "matched": True}

        aliases_iterable = alias_list
        if isinstance(aliases_iterable, str):
            aliases_iterable = [aliases_iterable]

        for alias in aliases_iterable or []:
            if alias is None:
                continue
            if normalized_input == str(alias).strip().lower():
                return {"canonical": canonical, "input": entity_name, "matched": True}
    
    return {"canonical": entity_name, "input": entity_name, "matched": False}



def summarize_link_confidence(linked_entities):
    """Summarize confidence stats from linked entities payload."""
    if not linked_entities:
        return {"total": 0, "avgConfidence": 0.0, "linkedCount": 0}

    confidences = []
    linked_count = 0
    for entity in linked_entities:
        meta = entity.get("_wikidata", {})
        conf = float(meta.get("confidence", 0.0))
        confidences.append(conf)
        if meta.get("linked") is True:
            linked_count += 1

    return {
        "total": len(linked_entities),
        "avgConfidence": round(sum(confidences) / len(confidences), 4),
        "linkedCount": linked_count,
    }
