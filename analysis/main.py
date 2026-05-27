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

query = """
WITH snapshots_dates AS (
    -- Identificar as 3 datas de aquisição (snapshot)
    SELECT DISTINCT aquisition_date
    FROM read_csv_auto(?)
    ORDER BY aquisition_date
),

-- Para cada imóvel, data de estadia e snapshot, determinar se foi reservado
-- Um imóvel foi reservado se:
-- - Estava disponível no snapshot 07/01 para uma data de estadia
-- - NÃO aparece nos snapshots subsequentes (13/01 ou 20/01) para a MESMA data de estadia
item_level_analysis AS (
    SELECT 
        p.airbnb_listing_id,
        p.date as stay_date,
        p.price,
        p.aquisition_date,
        -- Identificar qual snapshot (1=primeiro, 2=segundo, 3=terceiro)
        ROW_NUMBER() OVER (ORDER BY p.aquisition_date) as snapshot_order
    FROM read_csv_auto(?) p
),

-- Identificar reservas: itens que sumiram em snapshots posteriores
reservations AS (
    SELECT 
        i1.airbnb_listing_id,
        i1.stay_date,
        i1.price as last_price_seen,
        i1.snapshot_order as first_snapshot_order
    FROM item_level_analysis i1
    WHERE NOT EXISTS (
        SELECT 1 
        FROM item_level_analysis i2 
        WHERE i2.airbnb_listing_id = i1.airbnb_listing_id
        AND i2.stay_date = i1.stay_date
        AND i2.snapshot_order > i1.snapshot_order
    )
    AND i1.snapshot_order = 1  -- Apenas considerar primeiro snapshot para evitar duplicatas
),

-- Calcular métricas por imóvel
revenue_metrics AS (
    SELECT 
        r.airbnb_listing_id,
        COUNT(r.stay_date) as diarias_alugadas,
        SUM(r.last_price_seen) as receita_total
    FROM reservations r
    GROUP BY r.airbnb_listing_id
)

-- JOIN com Details e Mesh
SELECT 
    rm.airbnb_listing_id,
    rm.diarias_alugadas,
    rm.receita_total,
    d.number_of_bedrooms,
    m.suburb as bairro
FROM revenue_metrics rm
LEFT JOIN read_csv_auto(?) d ON rm.airbnb_listing_id = d.airbnb_listing_id
LEFT JOIN read_csv_auto(?) m ON rm.airbnb_listing_id = m.airbnb_listing_id
""".strip()

# Executar com parâmetros dinâmicos
price_path = str(DATA_DIR / 'Price_AV_Itapema.csv')
details_path = str(DATA_DIR / 'Details_Itapema.csv')
mesh_path = str(DATA_DIR / 'Mesh_Ids_Data_Itapema.csv')

result_df = con.execute(query, [price_path, price_path, details_path, mesh_path]).fetch_arrow_table()

# ============================================================================
# PASSO 4: Converter para Polars e exibir
# ============================================================================
df = pl.from_arrow(result_df)

print("=" * 60)
print("RESULTADO DA MODELAGEM DE PREÇOS")
print("=" * 60)
print(df.head())
print("=" * 60)
print(f"Total de imóveis com reservas identificadas: {df.height}")