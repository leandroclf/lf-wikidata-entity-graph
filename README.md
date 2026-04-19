# lf-wikidata-entity-graph

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Production-brightgreen)
![API](https://img.shields.io/badge/API-REST%20JSON-orange)

Serviço de **resolução de entidades** que vincula registros de negócio (empresas, organizações, produtos) ao grafo de conhecimento do [Wikidata](https://www.wikidata.org), eliminando duplicatas e inconsistências de nomenclatura entre sistemas.

**URL de producao:** https://lf-wikidata-entity-graph.onrender.com

---

## Sumario

- [O que faz](#o-que-faz)
- [Como funciona o algoritmo Jaccard](#como-funciona-o-algoritmo-jaccard)
- [Endpoints](#endpoints)
- [Quick start local](#quick-start-local)
- [Exemplos curl](#exemplos-curl)
- [Integracao em codigo](#integracao-em-codigo)
- [Importar Postman Collection](#importar-postman-collection)
- [Casos de uso](#casos-de-uso)
- [Estrutura do projeto](#estrutura-do-projeto)

---

## O que faz

O `lf-wikidata-entity-graph` resolve o problema de **fragmentacao de entidades** entre sistemas distintos: a mesma empresa pode aparecer como "Microsoft Corp", "Microsoft Corporation" ou "MSFT" em diferentes bases de dados. Este servico:

1. Valida e ingere lotes de registros de entidades
2. Deduplica registros por identificador unico
3. Vincula cada entidade a um QID do Wikidata com score de confianca
4. Deduplica entidades vinculadas por QID ou nome normalizado
5. Constroi um grafo de relacionamentos (nos: entity, alias, wikidata; arestas: alias_of, same_as)
6. Retorna metricas de cobertura e precisao

---

## Como funciona o algoritmo Jaccard

A similaridade entre dois nomes e calculada pela **similaridade Jaccard sobre tokens de palavras**, apos normalizacao (lowercase, remocao de espacos extras):

```
Jaccard(A, B) = |tokens(A) ∩ tokens(B)| / |tokens(A) ∪ tokens(B)|
```

**Exemplo:**

| Nome A | Nome B | Tokens A | Tokens B | Intersecao | Uniao | Jaccard |
|--------|--------|----------|----------|------------|-------|---------|
| "Apple Inc" | "Apple Inc." | {apple, inc} | {apple, inc.} | {apple} | {apple, inc, inc.} | 0.33 |
| "Microsoft Corp" | "Microsoft Corp" | {microsoft, corp} | {microsoft, corp} | {microsoft, corp} | {microsoft, corp} | 1.00 |
| "Apple Records" | "Apple Inc" | {apple, records} | {apple, inc} | {apple} | {apple, records, inc} | 0.33 |

**Thresholds:**
- **Vinculacao Wikidata** (`confidence_threshold`): padrao `0.7` — configura-se por chamada
- **Decisao de match** (`/v1/entities/match`): fixo em `0.8` internamente

---

## Endpoints

| Metodo | Path | Descricao | Tags |
|--------|------|-----------|------|
| `GET` | `/health` | Status do servico | Health |
| `GET` | `/sample` | Payload de exemplo Wikidata | Health |
| `POST` | `/v1/entities/match` | Melhor candidato para uma entidade | Entity Matching |
| `POST` | `/v1/entities/pipeline` | Pipeline completo de resolucao | Pipeline |
| `GET` | `/v1/entities/metrics` | Metricas de qualidade do sistema | Metrics |

---

## Quick start local

**Pre-requisitos:** Python 3.10+

```bash
# 1. Clone o repositorio
git clone https://github.com/leandroclf/lf-wikidata-entity-graph.git
cd lf-wikidata-entity-graph

# 2. Instale as dependencias
pip install -r requirements.txt

# 3. Inicie o servidor (porta padrao: 8000)
PYTHONPATH=. python -m backend.src.http_server

# 4. Verifique o health
curl http://localhost:8000/health
# {"status": "ok", "service": "lf-wikidata-entity-graph"}
```

Para usar uma porta diferente:

```bash
PORT=9000 PYTHONPATH=. python -m backend.src.http_server
```

---

## Exemplos curl

### GET /health

```bash
curl https://lf-wikidata-entity-graph.onrender.com/health
```

Resposta:
```json
{"status": "ok", "service": "lf-wikidata-entity-graph"}
```

---

### GET /sample

```bash
curl https://lf-wikidata-entity-graph.onrender.com/sample
```

Resposta:
```json
{
  "component": "lf-wikidata-entity-graph",
  "source": "wikidata",
  "status": "ok",
  "generatedAt": "2026-04-18T12:00:00+00:00",
  "transport": "http",
  "generatedAtHttp": "2026-04-18T12:00:00+00:00"
}
```

---

### POST /v1/entities/match

```bash
curl -X POST https://lf-wikidata-entity-graph.onrender.com/v1/entities/match \
  -H "Content-Type: application/json" \
  -d '{
    "entity_name": "Apple Inc",
    "candidates": [
      {"name": "Apple Inc.", "id": "Q312", "score": 0.92},
      {"name": "Apple Records", "id": "Q193704", "score": 0.41}
    ]
  }'
```

Resposta:
```json
{
  "best_match": {"name": "Apple Inc.", "id": "Q312", "score": 0.92},
  "decision": {"score": 1.0, "threshold": 0.8, "match": true}
}
```

**Campos do request:**
| Campo | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| `entity_name` | string | sim | Nome da entidade a comparar |
| `candidates` | array | sim | Lista de candidatos com `name`, `id` e `score` |

---

### POST /v1/entities/pipeline

```bash
curl -X POST https://lf-wikidata-entity-graph.onrender.com/v1/entities/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"id": "r1", "name": "Microsoft Corp", "source": "crm"},
      {"id": "r2", "name": "Apple Inc", "source": "erp"}
    ],
    "confidence_threshold": 0.7
  }'
```

Resposta (resumida):
```json
{
  "status": "processed",
  "stats": {
    "raw_total": 2,
    "valid_total": 2,
    "raw_dedup_total": 2,
    "linked_total": 2,
    "linked_dedup_total": 2,
    "linked_success_total": 2,
    "link_rate": 1.0,
    "unique_entity_rate": 1.0
  },
  "baseline": {
    "matchingPrecisionTarget": 0.9,
    "linkConfidenceAvg": 0.875,
    "entityResolutionCoverage": 1.0
  },
  "entities": [...],
  "graph": {
    "nodes": [...],
    "edges": [...],
    "stats": {"entities": 2, "aliases": 2, "wikidata": 2, "edges": 4}
  },
  "errors": [],
  "processed_at": "2026-04-18T12:00:00+00:00"
}
```

**Campos do request:**
| Campo | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| `records` | array | sim | Lista de registros com `id` e `name` obrigatorios |
| `confidence_threshold` | float | nao | Threshold para vinculacao Wikidata (padrao: 0.7) |

---

### GET /v1/entities/metrics

```bash
curl https://lf-wikidata-entity-graph.onrender.com/v1/entities/metrics
```

Resposta:
```json
{
  "issue": "ISSUE-002",
  "precisionTarget": 0.90,
  "recallTarget": 0.85,
  "fprMax": 0.05
}
```

---

## Integracao em codigo

### Python

```python
import requests

BASE_URL = "https://lf-wikidata-entity-graph.onrender.com"

# Health check
resp = requests.get(f"{BASE_URL}/health")
print(resp.json())  # {"status": "ok", "service": "lf-wikidata-entity-graph"}

# Pipeline de resolucao
payload = {
    "records": [
        {"id": "r1", "name": "Microsoft Corp", "source": "crm"},
        {"id": "r2", "name": "Apple Inc", "source": "erp"},
    ],
    "confidence_threshold": 0.7,
}
resp = requests.post(f"{BASE_URL}/v1/entities/pipeline", json=payload)
result = resp.json()

print(f"Status: {result['status']}")
print(f"Entidades vinculadas: {result['stats']['linked_success_total']}")
print(f"Taxa de vinculacao: {result['stats']['link_rate']}")

for entity in result["entities"]:
    wikidata = entity.get("_wikidata", {})
    print(f"  {entity['name']} -> QID: {wikidata.get('qid')} (conf: {wikidata.get('confidence')})")
```

---

### JavaScript (fetch)

```javascript
const BASE_URL = "https://lf-wikidata-entity-graph.onrender.com";

// Matching de entidade
const response = await fetch(`${BASE_URL}/v1/entities/match`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    entity_name: "Apple Inc",
    candidates: [
      { name: "Apple Inc.", id: "Q312", score: 0.92 },
      { name: "Apple Records", id: "Q193704", score: 0.41 },
    ],
  }),
});

const data = await response.json();
console.log("Melhor match:", data.best_match);
console.log("Decisao:", data.decision);
// Decisao: { score: 1.0, threshold: 0.8, match: true }
```

---

### curl (pipeline completo com jq)

```bash
curl -s -X POST https://lf-wikidata-entity-graph.onrender.com/v1/entities/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"id": "c1", "name": "Petrobras", "source": "b3"},
      {"id": "c2", "name": "Petroleo Brasileiro", "source": "bloomberg"},
      {"id": "c3", "name": "Vale SA", "source": "b3"}
    ],
    "confidence_threshold": 0.7
  }' | jq '{
    status: .status,
    total: .stats.raw_total,
    vinculadas: .stats.linked_success_total,
    nos_grafo: .graph.stats
  }'
```

---

## Importar Postman Collection

### Passo a passo

1. Abra o **Postman** (desktop ou web)
2. Clique em **Import** (canto superior esquerdo)
3. Arraste ou selecione o arquivo `docs/postman_collection.json`
4. Clique novamente em **Import**
5. Para importar o environment:
   - Va em **Environments** > **Import**
   - Selecione `docs/postman_environment.json`
   - Ative o environment "lf-wikidata-entity-graph" no seletor superior direito
6. As variaveis `{{base_url}}` e `{{base_url_local}}` estao pre-configuradas
7. Para usar o servidor local, altere `{{base_url}}` para `{{base_url_local}}` nas requisicoes desejadas

**Variaveis de environment:**

| Variavel | Valor |
|----------|-------|
| `base_url` | `https://lf-wikidata-entity-graph.onrender.com` |
| `base_url_local` | `http://localhost:8000` |

---

## Casos de uso

### Deduplicacao de CRM

Um CRM acumula registros duplicados de clientes com nomes ligeiramente diferentes. O pipeline identifica que "Microsoft Corp", "Microsoft Corporation" e "MSFT" referem-se ao mesmo QID Wikidata e os agrupa em uma unica entidade canonica.

```bash
curl -X POST https://lf-wikidata-entity-graph.onrender.com/v1/entities/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"id": "crm-001", "name": "Microsoft Corp"},
      {"id": "crm-002", "name": "Microsoft Corporation"},
      {"id": "crm-003", "name": "MSFT"}
    ]
  }'
```

O grafo resultante mostra 1 no de entidade com 3 nos de alias, todos conectados ao mesmo QID Wikidata.

---

### Enriquecimento de dados

Dado um lote de empresas de um sistema legado, o pipeline vincula cada uma ao Wikidata e retorna o QID para uso em consultas SPARQL e enriquecimento com dados externos (setor, pais, ticker, fundacao).

```python
# Apos obter o QID, consulte o Wikidata SPARQL
qid = "Q82670"  # Microsoft
sparql_url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
```

---

### Integracao entre sistemas

Dois sistemas distintos (ERP e CRM) usam nomes diferentes para os mesmos fornecedores. O endpoint `/v1/entities/match` permite comparar registros em tempo real durante o processo de integracao ETL.

```python
# Durante ETL: para cada registro do ERP, buscar candidatos no CRM
def resolve_supplier(erp_name, crm_candidates):
    resp = requests.post(
        "https://lf-wikidata-entity-graph.onrender.com/v1/entities/match",
        json={"entity_name": erp_name, "candidates": crm_candidates}
    )
    result = resp.json()
    if result["decision"]["match"]:
        return result["best_match"]["id"]
    return None
```

---

## Estrutura do projeto

```
lf-wikidata-entity-graph/
├── backend/
│   └── src/
│       ├── api.py          # Logica de matching, Jaccard, vinculacao Wikidata
│       ├── http_server.py  # Servidor HTTP (stdlib), roteamento de endpoints
│       ├── ingest.py       # Pipeline: validacao, dedup, grafo
│       └── service.py      # Servicos auxiliares
├── docs/
│   ├── openapi.yaml              # Especificacao OpenAPI 3.0
│   ├── postman_collection.json   # Colecao Postman v2.1
│   └── postman_environment.json  # Environment Postman
├── tests/                  # Suite de testes pytest
├── tools/                  # Scripts auxiliares (smoke check, etc.)
├── requirements.txt
└── README.md
```

---

## Metricas de qualidade (ISSUE-002)

| Metrica | Meta |
|---------|------|
| Precisao (`precisionTarget`) | >= 90% |
| Recall (`recallTarget`) | >= 85% |
| Taxa de falsos positivos (`fprMax`) | <= 5% |

Consulte as metas atuais via `GET /v1/entities/metrics`.

---

## Documentacao adicional

- [OpenAPI Spec](docs/openapi.yaml) — Especificacao completa de todos os endpoints
- [Postman Collection](docs/postman_collection.json) — Colecao pronta para importar
- [ARCHITECTURE.md](ARCHITECTURE.md) — Decisoes de arquitetura e design
- [CHANGELOG.md](CHANGELOG.md) — Historico de versoes

---

_Ref.: ISSUE-002 — Grafo de entidades com Wikidata para normalizacao e matching_
