"""Core service bootstrap for lf-wikidata-entity-graph."""

def healthcheck():
    return {"status": "ok", "component": "lf-wikidata-entity-graph"}


def roadmap_items():
    return [
        "ingest",
        "normalize",
        "publish-metrics"
    ]
