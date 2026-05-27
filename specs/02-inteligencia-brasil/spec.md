# Spec do Produto: Inteligência Brasil

## 1. Visão Geral
* **Quem usa:** Times de Revenue Management (RM), Originação de Novos Prédios e Aquisição de Proprietários.
* **Decisão que substitui:** Análises manuais pontuais por cidade. Passaremos a ter uma visão contínua e automatizada da rentabilidade e demanda em escala nacional (polígonos × stratas × demanda).
* **Frequência de atualização:** Diária (D+1) para a camada de preços/ocupação e Semanal para malha urbana e características estáticas.

## 2. Inputs e Outputs
* **Inputs:** 
  * Datalake (AWS S3/GCP): Dados crus diários de scrapers proprietários (Airbnb, VivaReal).
  * Manual/Estático: Polígonos de exclusão de risco ou áreas de interesse definidas por negócios.
* **Outputs:** 
  * Tabelas Gold consolidadas no Athena/BigQuery.
  * APIs / MCPs (Model Context Protocol) para agentes de IA internos consultarem rentabilidade de uma coordenada em tempo real.
  * Dashboards operacionais (Lovable/Metabase) para consumo tático do time de RM.

## 3. Granularidade Espacial e Temporal
* **Espacial:** Índice H3 (Resolução 8 ou 9 da Uber). **Justificativa:** Diferente de CEPs (que variam de tamanho e mudam) ou Bairros (que têm limites subjetivos), o H3 cria hexágonos perfeitos e unificados, essenciais para cruzar demanda de short-stay litorânea com precisão matemática.
* **Temporal:** Janela de estadia estendida (rolling de 180 dias futuros) agregada semanalmente, para prever sazonalidades de demanda de curto e médio prazo.

## 4. Modelo de Dados (Medallion Architecture)
* **Bronze (Raw):** Dados brutos dos scrapers em Parquet particionados por data de ingestão.
* **Silver (Cleansed):** Deduplicação (resolução da dupla data aquisição x estadia), padronização de moedas, tipologias e enriquecimento com o índice H3 a partir de Lat/Lon.
* **Gold (Business):** 
  * `gold_market_demand_h3`: Diárias alugadas, receita média, ocupação por hexágono H3 e tipo de quarto.
  * `gold_investment_roi`: Cruzamento de preço VivaReal (venda) com a receita Airbnb projetada para cálculo do Cap Rate por região.

## 5. SLA / SLO e Fora de Escopo
* **SLO Mínimo Viável:** Dados D+1 disponíveis até às 09:00 BRT com 95% de precisão nos preços.
* **Fora de Escopo:** O sistema **não** executa a precificação dinâmica (não altera os preços na ponta). Ele é um produto de inteligência passiva para tomada de decisão.
