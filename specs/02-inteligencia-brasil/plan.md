# Plano de Execução: Inteligência Brasil

Este projeto será executado em 3 fases sequenciais, dividindo o escopo entre os squads Data Core, Data Acquisition e Data Edge.

## Fase 1: Fundação e Ingestão Escalável (Semanas 1-2)
* **Squad Responsável:** Data Acquisition e Data Core.
* **Execução:** 
  * *Acquisition:* Escalar os scrapers proprietários (Airbnb/VivaReal) para varredura em malha nacional baseada nas cidades alvo.
  * *Core:* Provisionar infraestrutura base (buckets S3/GCP) e configurar as pipelines de ingestão raw (Camada Bronze).
* **Marco de Validação:** Volume de dados fluindo para o datalake em D+1 sem gargalos e com logs de erro de scrap monitorados.
* **Risco e Mitigação:** Risco de bloqueio dos scrapers (IP ban). *Mitigação:* Rotação de proxies e randomização de requisições gerenciada pelo Acquisition.

## Fase 2: Motor de Tratamento e Geometria (Semanas 3-4)
* **Squad Responsável:** Data Core.
* **Execução:**
  * Desenvolver pipelines ELT idempotentes usando DBT ou Spark para processar Bronze -> Silver.
  * Aplicar resolução de `stay_date` vs `snapshot_date` (regra do sumiço) e converter coordenadas de latitude/longitude no mapeamento universal H3.
* **Marco de Validação:** Qualidade de dados garantida por testes de pipeline (ex: sem chaves H3 nulas, sem faturamento negativo).
* **Risco e Mitigação:** Explosão de custos de processamento no BigQuery/Athena. *Mitigação:* Implementar partições rigorosas por data e clusterização por H3 index.

## Fase 3: Regras de Negócio e Consumo (Semanas 5-6)
* **Squad Responsável:** Data Edge.
* **Execução:**
  * Consolidar camada Gold com os KPIs de negócio (Receita por Hexágono, Cap Rate de aquisição).
  * Criar o MCP de consulta de viabilidade para os Agentes de IA internos.
  * Lançar as visões no Lovable para Originação e RM.
* **Marco de Validação:** Homologação visual e aprovação do dado final por 2 usuários-chave (um de Originação, um de RM).
* **Risco e Mitigação:** Divergência conceitual de cálculo (ex: RM definir "Receita" diferente da Engenharia). *Mitigação:* Assinatura formal do contrato de dados e métricas no início da Fase 3.
