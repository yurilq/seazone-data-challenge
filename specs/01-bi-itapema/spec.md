# Spec: Análise de Investimento em Itapema (BI)

## 1. Hipóteses para as Perguntas de Negócio
1. **Melhor perfil de imóvel:** Imóveis compactos (1 a 2 quartos) geram maior giro e rentabilidade proporcional do que imóveis muito grandes.
2. **Melhor localização:** Bairros litorâneos centrais (ex: Meia Praia) concentram a maior receita bruta devido à alta demanda no verão.
3. **Características das melhores receitas:** Imóveis geridos por "Superhosts" (ou hosts profissionais) com alta taxa de resposta possuem um prêmio no preço e maior ocupação.
4. **Prédio de 50 apartamentos:** Deve ser posicionado no bairro de maior receita por m² e focado na tipologia que apresentou maior RevPAR (Revenue Per Available Room).
5. **ROI Projetado:** O cálculo assumirá a receita gerada na alta temporada (Jan-Abr 2025) extrapolada sazonalmente para 3 anos (2025, 2026, 2027), descontando custos operacionais padrão.

## 2. Métricas que Materializam as Respostas
* **Diárias Alugadas (Nights Booked):** Calculada pela ausência de um imóvel em um snapshot posterior para uma mesma data de estadia.
* **Receita Total Bruta:** Diárias alugadas multiplicadas pelo último preço capturado antes do sumiço.
* **Ocupação (%):** Proporção de dias alugados em relação à janela total (Jan-Abr).

## 3. Decisões de Modelagem
* **Stack:** Python gerenciado via `uv`. DuckDB para extração local rápida simulando Datalake (AWS Athena/BigQuery). Polars para wrangling em memória.
* **Tratamento de Preço (Crítico):** Em vez de tratar o arquivo `Price_AV_Itapema.csv` com um simples "preço atual" (o que causaria reprovação), usaremos CTEs com funções de janela (`ROW_NUMBER()`) no DuckDB para identificar a "dupla data" e rastrear os imóveis que estavam livres no snapshot de 07/01, mas sumiram no de 13/01 ou 20/01 para as mesmas datas de estadia.
* **Joins:** A tabela Fato (Receita) fará join com as dimensões `Details` (tipologia) e `Mesh` (geolocalização).

## 4. Riscos Mapeados
* **Alucinação de Schema:** Os CSVs podem ter nomes de colunas diferentes do esperado (ex: `airbnb_listing_id` vs `listing_id`). **Mitigação:** Fazer o agente IA ler o header antes de escrever queries em SQL.
* **Falso Positivo de Reserva:** Um imóvel sumir do scraper pode significar bloqueio do dono e não reserva real. **Mitigação:** Assumir o sumiço como proxy de reserva, conforme induzido pela regra de negócio do desafio.
