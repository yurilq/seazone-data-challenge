# Plano de Execução: Análise Itapema

## Passos de Execução
1. **Setup de Ambiente e Infra:**
   - Inicializar projeto Python com `uv`.
   - Criar diretórios de `data/` (raw data), `analysis/` (códigos) e `ai-sessions/` (logs de AI).

2. **Ingestão e Tratamento no DuckDB (Modelagem Principal):**
   - Ler dinamicamente os cabeçalhos dos arquivos CSVs.
   - Criar script `main.py` para carregar dados para o DuckDB em memória.
   - Escrever query SQL (CTE) aplicando a lógica de "sumiço" de anúncios nos snapshots para calcular diárias alugadas e receita.

3. **Joins Dimensionais (Enriquecimento):**
   - Relacionar o consolidado de receitas com `Details` (quartos), `Mesh` (bairro) e `Hosts` (perfil do dono).
   - Exportar o dataset final via Arrow para um DataFrame Polars.

4. **Análises Exploratórias e Respostas (Polars):**
   - Agrupar e ranquear os bairros pela soma de receita e receita média.
   - Analisar correlação de receita com número de quartos e reviews.
   - Definir a melhor tipologia e localização para o prédio de 50 apartamentos.

5. **Projeção de ROI:**
   - Montar a modelagem financeira do prédio para os anos 2025, 2026 e 2027 baseada nos resultados atuais multiplicados por sazonalidade.

## Dependências
- `uv` instalado localmente.
- Bibliotecas Python: `duckdb`, `polars`.
- Arquivos raw na pasta `data/`: `Details_Itapema.csv`, `Hosts_ids_Itapema.csv`, `Mesh_Ids_Data_Itapema.csv`, `Price_AV_Itapema.csv`, `VivaReal_Itapema.csv`.
- AI Builder agents (OpenCode / Antigravity Kit) configurados para auto-log.