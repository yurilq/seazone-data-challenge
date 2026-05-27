#!/usr/bin/env python3
"""
AI Builder - Data Ingestion & Price Modeling
Stack: Python/uv, DuckDB, Polars
Proibido: Jupyter Notebooks, Pandas
"""

from pathlib import Path
import duckdb
import polars as pl

# ============================================================================
# PASSO 2: Caminhos Dinâmicos (pathlib)
# ============================================================================
DATA_DIR = Path(__file__).parent.parent / 'data'

# ============================================================================
# PASSO 1 + 3: Schema descoberto + Regra de Negócio - DuckDB CTEs
# ============================================================================
con = duckdb.connect()

# Execute with parameters dynamically
price_path = str(DATA_DIR / 'Price_AV_Itapema.csv')
details_path = str(DATA_DIR / 'Details_Itapema.csv')
mesh_path = str(DATA_DIR / 'Mesh_Ids_Data_Itapema.csv')

# Rewrite query using EXCEPT for set difference logic
final_query = """
WITH price_data AS (
    SELECT 
        airbnb_listing_id,
        date as stay_date,
        price,
        aquisition_date,
        CAST(aquisition_date AS DATE) as acq_date_part
    FROM read_csv_auto(?)
),

-- Extrair os 3 snapshots distintos (datas de aquisição)
snapshots AS (
    SELECT DISTINCT CAST(aquisition_date AS DATE) as snapshot_date
    FROM price_data
    ORDER BY snapshot_date
),

-- Primeiro snapshot (a data mais antiga)
first_snapshot_date AS (
    SELECT MIN(CAST(aquisition_date AS DATE)) as first_date
    FROM price_data
),

-- Todos os outros snapshots (segundo e terceiro)
other_snapshots AS (
    SELECT CAST(aquisition_date AS DATE) as other_date
    FROM price_data
    WHERE CAST(aquisition_date AS DATE) <> (SELECT first_date FROM first_snapshot_date)
    GROUP BY CAST(aquisition_date AS DATE)
),

-- Registros disponíveis no primeiro snapshot (airbnb_listing_id, stay_date)
first_snapshot_records AS (
    SELECT 
        airbnb_listing_id,
        stay_date,
        price
    FROM price_data
    WHERE acq_date_part = (SELECT first_date FROM first_snapshot_date)
),

-- Registros disponíveis em QUALQUER outro snapshot (segundo ou terceiro)
other_snapshots_records AS (
    SELECT DISTINCT
        airbnb_listing_id,
        stay_date
    FROM price_data
    WHERE acq_date_part <> (SELECT first_date FROM first_snapshot_date)
),

-- Aplicar EXCEPT: registros que estavam no primeiro snapshot mas não existem nos outros
-- Isso identifica as diárias efetivamente alugadas (reservadas)
reserved_diarias AS (
    SELECT 
        fsr.airbnb_listing_id,
        fsr.stay_date,
        fsr.price as price_at_reservation
    FROM first_snapshot_records fsr
    WHERE NOT EXISTS (
        SELECT 1
        FROM other_snapshots_records osr
        WHERE osr.airbnb_listing_id = fsr.airbnb_listing_id
        AND osr.stay_date = fsr.stay_date
    )
),

-- Agregar por imóvel: contar diárias alugadas e calcular receita
revenue_by_listing AS (
    SELECT 
        airbnb_listing_id,
        COUNT(*) as diarias_alugadas,
        SUM(price_at_reservation) as receita_gerada
    FROM reserved_diarias
    GROUP BY airbnb_listing_id
),

-- Fazer JOIN com Details para número de quartos
with_details AS (
    SELECT 
        rbl.airbnb_listing_id,
        rbl.diarias_alugadas,
        rbl.receita_gerada,
        d.number_of_bedrooms
    FROM revenue_by_listing rbl
    LEFT JOIN read_csv_auto(?) d 
        ON rbl.airbnb_listing_id = d.airbnb_listing_id
),

-- Fazer JOIN final com Mesh para bairro
final_output AS (
    SELECT 
        wd.airbnb_listing_id,
        wd.diarias_alugadas,
        wd.receita_gerada,
        wd.number_of_bedrooms,
        m.suburb as bairro
    FROM with_details wd
    LEFT JOIN read_csv_auto(?) m 
        ON wd.airbnb_listing_id = m.airbnb_listing_id
)

SELECT * FROM final_output
""".strip()

# Execute query with dynamic file paths (3 times for the 3 CSV reads)
result_df = con.execute(final_query, [
    price_path, 
    details_path, 
    mesh_path
]).to_arrow_table()  # CORRIGIDO: usando to_arrow_table() em vez de fetch_arrow_table()

# ============================================================================
# PASSO 4: Converter para Polars e exibir
# ============================================================================
df = pl.from_arrow(result_df)

# ============================================================================
# PASSO 4: Converter para Polars e exibir
# ============================================================================
df = pl.from_arrow(result_df)

print("=" * 80)
print("RESULTADO DA MODELAGEM DE PRECOS - RESERVAS IDENTIFICADAS")
print("=" * 80)
print(f"Total de imoveis com diarias alugadas identificadas: {df.height}")
print("=" * 80)

# Salvar resultado em arquivo para visualizacao
output_file = Path(__file__).parent / 'revenue_analysis.csv'
df.write_csv(str(output_file))
print(f"Resultado salvo em: {output_file}")
