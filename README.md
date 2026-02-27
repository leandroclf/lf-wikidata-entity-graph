# lf-wikidata-entity-graph: Grafo de Entidades e Matching (ISSUE-002)

## Visão Geral

Este repositório contém o Mínimo Produto Viável (MVP) do componente de Grafo de Entidades e Matching, focado em utilizar dados do Wikidata para normalização e resolução de entidades. O objetivo é criar uma base consistente de entidades, permitindo a identificação e o matching precisos de empresas e indivíduos, mesmo com variações de nomenclatura.

## Contexto e Issue

Desenvolvido sob a **ISSUE-002: Grafo de entidades com Wikidata para normalização e matching**, este componente é crucial para resolver problemas de fragmentação e inconsistência de dados, que dificultam a análise integrada e a tomada de decisão.

## Problema Resolvido

A inconsistência na representação de entidades (empresas, pessoas) em diferentes fontes de dados é um desafio comum. Nomes variados, abreviações ou erros de digitação impedem a conexão e análise holística. Este componente resolve isso, fornecendo mecanismos para padronizar e linkar entidades a uma referência comum (Wikidata).

## Objetivo do MVP

O MVP visa estabelecer uma base para a normalização e matching de entidades, com foco nas seguintes capacidades:

*   **Scoring de Similaridade:** Calcular e sumarizar scores de similaridade entre nomes de entidades.
*   **Métricas de Matching:** Avaliar a qualidade dos matches com métricas como cobertura e precisão delta.
*   **Ligação de Entidades:** Conectar entidades a identificadores únicos do Wikidata, com base em confiança.
*   **Resolução de Aliases:** Padronizar nomes de entidades usando aliases conhecidos para melhorar a acurácia do matching.
*   **Gate de Decisão:** Implementar um gate de decisão para determinar se um match é válido, usando thresholds configuráveis.

## Objetivo Final em Produção (Visão Estratégica)

Quando em produção, o `lf-wikidata-entity-graph` será um serviço robusto e automatizado, capaz de:

*   **Grafo de Conhecimento Centralizado:** Manter um grafo de conhecimento atualizado com todas as entidades relevantes e seus relacionamentos.
*   **Resolução de Entidades em Tempo Real:** Fornecer um serviço de resolução de entidades que padroniza e linka dados em tempo real para aplicações downstream.
*   **Melhora da Qualidade de Dados:** Ser a espinha dorsal para garantir a consistência e qualidade dos dados em todos os sistemas da empresa.
*   **Descoberta de Insights:** Facilitar a descoberta de novas conexões e insights através da exploração do grafo de entidades.

## Funcionalidades Chave Implementadas (MVP)

*   `summarize_threshold_outcomes()`: Sumariza resultados de gates de threshold.
*   `summarize_best_match_coverage()`: Calcula a cobertura dos melhores matches.
*   `summarize_similarity_scores()`: Sumariza scores de similaridade.
*   `calculate_precision_delta()`: Calcula a variação da precisão de matching.
*   `link_entities_to_wikidata()`: Liga entidades a IDs do Wikidata.
*   `resolve_entity_aliases()`: Resolve aliases para nomes canônicos.

## Estratégia e Abordagem

O desenvolvimento segue uma abordagem iterativa, com foco na precisão (precision) e recuperação (recall) do matching de entidades. A validação contínua contra dados reais e a calibração de thresholds são essenciais para aprimorar a qualidade do grafo e dos resultados de matching.

## Stack Técnica

*   **Linguagem:** Python
*   **Ferramentas:** Git, GitHub Actions (CI/CD)
*   **Dados:** Wikidata (fonte primária), fontes de dados internas.

## Como Começar

Para configurar e executar o projeto localmente:

1.  **Clone o repositório:**
    `git clone https://github.com/leandroclf/lf-wikidata-entity-graph.git`
    `cd lf-wikidata-entity-graph`
2.  **Instale as dependências:**
    `pip install -r requirements.txt` (se houver, ou adicione conforme necessário)
3.  **Execute testes:**
    `PYTHONPATH=. python3 -c "from backend.src.api import link_entities_to_wikidata; ..."` (Exemplo de execução de função)
    `# Ou se pytest estiver configurado: pytest`
    `PYTHONPATH=. python3 tools/smoke_check.py` (para smoke tests)

## Diretrizes de Contribuição

Este projeto adota um fluxo de trabalho de desenvolvimento que permite **commit direto na branch `main`**. Pull Requests são opcionais e encorajados para revisão colaborativa, mas não são obrigatórios para a integração de código.

## Governança

*   **Proprietário Primário (`ownerPrimary`):** Builder-repo
*   **Categoria Primária (`categoryPrimary`):** Engenharia-Arquitetura
*   **KPI de Valor (`valueKpi`):** (+/-) % de entidades únicas resolvidas; (+/-) % de tempo na análise de dados fragmentados.

---
_Gerado por Stephen (agente) em 2026-02-27. Ref.: ISSUE-002._
