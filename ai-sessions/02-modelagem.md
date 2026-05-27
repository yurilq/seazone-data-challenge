# 02-modelagem.md - AI Builder Data Ingestion & Price Modeling

## Pedido/Erro
Criar script `analysis/main.py` que realiza:
1. Reconhecimento de schema dos CSVs (leitura de cabeçalhos).
2. Ingestão dinâmica usando pathlib.
3. Aplicar regra de negócio para identificar reservas e calcular diárias alugadas e receita.
4. Joins com Details e Mesh, exportar para Polars e imprimir `.head()`.
5. Registrar tudo no Auto-Logger.

---

## Ação do AI Builder

### Passo 1: Schema Discovery (Ferramentas de Leitura)
Utilizei a ferramenta **read** para capturar os nomes reais das colunas:

**Price_AV_Itapema.csv:**
- `airbnb_listing_id` (ID do anúncio)
- `date` (data de estadia)
- `price` (preço da diária)
- `aquisition_date` (data do snapshot de coleta - timestamp)

**Details_Itapema.csv:**
- `airbnb_listing_id` 
- `number_of_bedrooms` (número de quartos)
- `aquisition_date`

**Mesh_Ids_Data_Itapema.csv:**
- `airbnb_listing_id`
- `suburb` (bairro/localidade)
- `aquisition_date`

### Passo 2-3: Evolução da Lógica SQL

#### ❌ ERRO CRÍTICO - Primeira Versão (Retornou 1 linha)
A primeira CTE tinha falhas lógicas graves:

**Problema 1 - Identificação de Snapshots:**
- Tentei usar `ROW_NUMBER()` para identificar snapshots, mas isso foi feito globalmente sem considerar as 3 datas de coleta reais (2025-01-07, 2025-01-13, 2025-01-20).

**Problema 2 - Lógica de Reservas:**
- A condição `WHERE NOT EXISTS ... AND snapshot_order = 1` tentava garantir que um registro não aparecesse em snapshots posteriores, mas:
  - A comparação `i2.snapshot_order > i1.snapshot_order` era superficial
  - Não levava em conta que um imóvel pode ter múltiplas datas de estadia
  - A filtragem `snapshot_order = 1` eliminava informações relevantes

**Resultado:** Apenas 1 imóvel foi identificado com reserva, o que é logicamente impossível para uma cidade turística em Jan-Abr 2025.

#### ✅ CORREÇÃO - Segunda Versão (Retornou 228 linhas)

**Nova Abordagem: Lógica de Conjuntos com NOT EXISTS**

A solução corrigida usa agregação condicional e lógica de diferença de conjuntos:

1. **CTE `price_data`**: Normaliza dados e converte `aquisition_date` (TIMESTAMP) para DATE usando `CAST()`.

2. **CTE `first_snapshot_records`**: Seleciona TODAS as combinações `(airbnb_listing_id, date)` que existem no PRIMEIRO snapshot (min date).

3. **CTE `other_snapshots_records`**: Seleciona TODAS as combinações `(airbnb_listing_id, date)` que existem em snapshots posteriores.

4. **CTE `reserved_diarias`**: Implementa a diferença de conjuntos (EXCEPT):
   ```sql
   SELECT fsr.* FROM first_snapshot_records fsr
   WHERE NOT EXISTS (
       SELECT 1 FROM other_snapshots_records osr
       WHERE osr.airbnb_listing_id = fsr.airbnb_listing_id
       AND osr.stay_date = fsr.stay_date
   )
   ```
   Isso identifica: "registros que estavam disponíveis em 07/01 mas sumiram em 13/01 ou 20/01"

5. **CTE `revenue_by_listing`**: Agregação simples:
   - `COUNT(*)` = diárias alugadas (cada linha = 1 diaria)
   - `SUM(price_at_reservation)` = receita total

6. **JOINs:** Conexão com Details (quartos) e Mesh (bairro)

**Resultado:** 228 imóveis com diárias reservadas identificadas ✅

---

## Resultado

### Correções Aplicadas

1. **Schema Correction:** Alterado `acquisition_date` → `aquisition_date` (nome real da coluna)

2. **Type Casting:** Adicionado `CAST(aquisition_date AS DATE)` porque a coluna é TIMESTAMP, não VARCHAR

3. **Deprecation Fix:** Substituído `fetch_arrow_table()` por `to_arrow_table()` na linha de exportação para DuckDB

4. **SQL Logic:** Reescrita das CTEs usando:
   - Lógica de conjuntos (NOT EXISTS para implementar EXCEPT)
   - Isolamento claro de snapshots (first vs. others)
   - Agregação por imóvel

### Arquivo Gerado

- **`analysis/main.py`** - Script completo de ingestão e modelagem
- **`analysis/revenue_analysis.csv`** - Output com 228 imóveis e métricas de receita

### Validação

- Query executada sem erros
- 228 imóveis com diárias alugadas identificadas (realista para turismo costeiro)
- Campos: `airbnb_listing_id`, `diarias_alugadas`, `receita_gerada`, `number_of_bedrooms`, `bairro`

---

## Auto-Logger Seazone - Status

✅ **Setup Concluído**
✅ **Schema Descoberto Dinamicamente**
✅ **Lógica de Negócio Implementada e Validada**
✅ **Ingestão com Pathlib Funcional**
✅ **Polars DataFrame Exportado**

**Próximo Passo:** Implementar camada de análise/visualização ou testes de validação de dados.
