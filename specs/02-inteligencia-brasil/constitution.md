# Constituição do Squad: Inteligência Brasil

Este documento define os princípios inegociáveis de engenharia de dados para o produto "Inteligência Brasil". Se um Pull Request ferir um destes princípios, ele será rejeitado automaticamente.

## 1. Spec-Driven Development (AI Builder)
* Nenhuma linha de código será escrita sem que `spec.md` e `plan.md` tenham sido aprovados e mergeados primeiro. 
* Agentes de IA (Claude/Cursor) são ferramentas de execução do spec, não tomadores de decisão arquitetural.

## 2. Idempotência e Reprocessamento
* Todos os pipelines (ETL/ELT) devem ser estritamente idempotentes. Rodar o mesmo pipeline para o mesmo particionamento (ex: `ds='2025-01-01'`) múltiplas vezes deve produzir o exato mesmo estado final, sem duplicar registros (uso de `MERGE` ou `INSERT OVERWRITE`).

## 3. Custo-Bound em Athena / BigQuery
* Nenhuma query analítica em produção no AWS Athena ou GCP BigQuery pode rodar sem limites de partição (Partition Pruning). 
* Dashboards não podem consultar a camada Silver diretamente; devem ler exclusivamente da camada Gold agregada para minimizar custos de scan.

## 4. Contratos de Dados e Versionamento
* O schema da camada Gold consumida por Revenue Management (RM) e Originação é uma API. Qualquer alteração (drop de coluna, mudança de tipo) exige versionamento da tabela (ex: `system_price_v2`) e notificação prévia de 30 dias aos consumidores.

## 5. Qualidade como Barreira (Circuit Breakers)
* Dados nulos em chaves de geolocalização ou anomalias de preço (>3 desvios padrões) devem travar a esteira na camada Silver e alertar o squad. Dados ruins não chegam na camada Gold.