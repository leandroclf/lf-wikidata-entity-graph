import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from datetime import datetime, timezone
from backend.src.api import get_sample_payload, choose_best_match, build_match_decision, score_name_similarity, get_matching_metrics
from backend.src.ingest import process_entity_graph_pipeline

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self._send(200, {'status':'ok','service':'lf-wikidata-entity-graph'})
            return
        if self.path == '/sample':
            payload=get_sample_payload()
            payload['transport']='http'
            payload['generatedAtHttp']=datetime.now(timezone.utc).isoformat()
            self._send(200,payload)
            return
        if self.path == '/v1/entities/metrics':
            self._send(200, get_matching_metrics())
            return
        self._send(404, {'error':'not_found','path':self.path})

    def do_POST(self):
        body = self._read_body()
        if self.path == '/v1/entities/pipeline':
            records = body.get('records', [])
            threshold = float(body.get('confidence_threshold', 0.7))
            result = process_entity_graph_pipeline(records, confidence_threshold=threshold)
            self._send(200, result)
            return
        if self.path == '/v1/entities/match':
            entity_name = body.get('entity_name', '')
            candidates = body.get('candidates', [])
            best = choose_best_match(candidates)
            score = score_name_similarity(entity_name, best.get('name', '') if best else '')
            decision = build_match_decision(score)
            self._send(200, {'best_match': best, 'decision': decision})
            return
        self._send(404, {'error':'not_found','path':self.path})

    def log_message(self, format, *args):
        pass


def run(host="0.0.0.0", port=None):
    port = port or int(os.environ.get("PORT", 8000))
    server = HTTPServer((host, port), Handler)
    print(f'Starting lf-wikidata-entity-graph on {host}:{port}')
    server.serve_forever()

if __name__ == '__main__':
    run()
