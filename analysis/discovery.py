#!/usr/bin/env python3
"""
AI Builder - Data Discovery & Exploratory Analysis
Stack: Polars (no Pandas, no Jupyter)
Objetivo: Responder as duas primeiras perguntas de negocio
"""

from pathlib import Path
import polars as pl

# ============================================================================
# LEITURA DO ARQUIVO CONSOLIDADO
# ============================================================================
DATA_FILE = Path(__file__).parent / 'revenue_analysis.csv'

# Ler CSV com Polars
df = pl.read_csv(str(DATA_FILE))

print("Dataset carregado com sucesso")
print(f"Total de imoveis: {df.height}")

# ============================================================================
# PERGUNTA 1: MELHOR LOCALIZACAO
# ============================================================================

localizacao = (
    df
    .group_by('bairro')
    .agg([
        pl.col('receita_gerada').sum().alias('receita_total'),
        pl.col('receita_gerada').mean().alias('receita_media_por_imovel'),
        pl.col('airbnb_listing_id').count().alias('quantidade_imoveis')
    ])
    .sort('receita_total', descending=True)
    .head(5)
)

# ============================================================================
# PERGUNTA 2: MELHOR PERFIL DE IMOVEL
# ============================================================================

perfil_imovel = (
    df
    .group_by('number_of_bedrooms')
    .agg([
        pl.col('receita_gerada').sum().alias('receita_total'),
        pl.col('receita_gerada').mean().alias('receita_media'),
        pl.col('diarias_alugadas').mean().alias('media_diarias_alugadas')
    ])
    .sort('receita_total', descending=True)
)

# ============================================================================
# SALVAR RESULTADOS E EXIBIR RESUMO
# ============================================================================

# Salvar em arquivo
localizacao_file = Path(__file__).parent / 'discovery_localizacao.csv'
perfil_file = Path(__file__).parent / 'discovery_perfil.csv'

localizacao.write_csv(str(localizacao_file))
perfil_imovel.write_csv(str(perfil_file))

print("\n" + "=" * 80)
print("PERGUNTA 1: TOP 5 BAIRROS POR RECEITA")
print("=" * 80)
for i, row in enumerate(localizacao.to_dicts(), 1):
    print(f"{i}. {row['bairro']}")
    print(f"   Receita Total: R$ {row['receita_total']:,.2f}")
    print(f"   Receita Media por Imovel: R$ {row['receita_media_por_imovel']:,.2f}")
    print(f"   Quantidade de Imoveis: {int(row['quantidade_imoveis'])}")
    print()

print("=" * 80)
print("PERGUNTA 2: MELHOR PERFIL DE IMOVEL (POR NUMERO DE QUARTOS)")
print("=" * 80)
for row in perfil_imovel.to_dicts():
    quartos = int(row['number_of_bedrooms']) if row['number_of_bedrooms'] else 0
    print(f"Imovel com {quartos} quartos:")
    print(f"  Receita Total: R$ {row['receita_total']:,.2f}")
    print(f"  Receita Media: R$ {row['receita_media']:,.2f}")
    print(f"  Media de Diarias Alugadas: {row['media_diarias_alugadas']:.1f}")
    print()

print("=" * 80)
print("Arquivos de saida:")
print(f"  - {localizacao_file}")
print(f"  - {perfil_file}")
print("=" * 80)

