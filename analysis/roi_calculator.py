#!/usr/bin/env python3
"""
AI Builder - ROI Calculator for 50-Unit Building Project
Meia Praia, 4-Bedroom Apartments
Financial Projection: 2025-2027
"""

from pathlib import Path
from datetime import datetime

# ============================================================================
# PREMISSAS DESCOBERTAS NO DISCOVERY (Hardcoded)
# ============================================================================

# Configuracao do Projeto
TOTAL_APARTMENTS = 50
BEDROOMS_PER_UNIT = 4
LOCATION = "Meia Praia"

# Descobertas do Discovery Phase
RECEITA_MEDIA_POR_IMOVEL_2025 = 81_595.00  # R$ 81.595 (4 quartos)
CRESCIMENTO_ANUAL = 0.05  # 5% ao ano
PERCENTUAL_CUSTOS = 0.35  # 35% de custos operacionais
MARGEM_LUCRO_OPERACIONAL = 1 - PERCENTUAL_CUSTOS  # 65%

# ============================================================================
# CALCULO DE PROJECOES
# ============================================================================

def calcular_projecao(ano, receita_unitaria, quantidade_unidades):
    """
    Calcula receita, custos e lucro para um ano especifico
    
    Args:
        ano: Ano da projecao
        receita_unitaria: Receita media por unidade para aquele ano
        quantidade_unidades: Numero de apartamentos
    
    Returns:
        Dict com metricas financeiras
    """
    receita_bruta = receita_unitaria * quantidade_unidades
    custos_operacionais = receita_bruta * PERCENTUAL_CUSTOS
    lucro_operacional = receita_bruta * MARGEM_LUCRO_OPERACIONAL
    
    return {
        'ano': ano,
        'receita_unitaria': receita_unitaria,
        'receita_bruta': receita_bruta,
        'custos_operacionais': custos_operacionais,
        'lucro_operacional': lucro_operacional,
        'margem_lucro_pct': MARGEM_LUCRO_OPERACIONAL * 100
    }

# Calculo para cada ano
ano_2025 = calcular_projecao(
    ano=2025,
    receita_unitaria=RECEITA_MEDIA_POR_IMOVEL_2025,
    quantidade_unidades=TOTAL_APARTMENTS
)

ano_2026 = calcular_projecao(
    ano=2026,
    receita_unitaria=RECEITA_MEDIA_POR_IMOVEL_2025 * (1 + CRESCIMENTO_ANUAL),
    quantidade_unidades=TOTAL_APARTMENTS
)

ano_2027 = calcular_projecao(
    ano=2027,
    receita_unitaria=RECEITA_MEDIA_POR_IMOVEL_2025 * (1 + CRESCIMENTO_ANUAL) ** 2,
    quantidade_unidades=TOTAL_APARTMENTS
)

projecoes = [ano_2025, ano_2026, ano_2027]

# ============================================================================
# EXIBICAO DOS RESULTADOS
# ============================================================================

print("\n" + "=" * 100)
print("ROI CALCULATOR - PRÉDIO RESIDENCIAL MEIA PRAIA")
print("=" * 100)
print(f"\nProjeto: {TOTAL_APARTMENTS} Apartamentos | {BEDROOMS_PER_UNIT} Quartos | Localização: {LOCATION}")
print(f"Período de Análise: 2025-2027")
print(f"\nPremissas Descobertas:")
print(f"  • Receita Média por Imóvel (2025): R$ {RECEITA_MEDIA_POR_IMOVEL_2025:,.2f}")
print(f"  • Crescimento Anual: {CRESCIMENTO_ANUAL * 100:.1f}%")
print(f"  • Custos Operacionais: {PERCENTUAL_CUSTOS * 100:.0f}% da Receita Bruta")
print(f"  • Margem Operacional: {MARGEM_LUCRO_OPERACIONAL * 100:.0f}%")
print("\n" + "=" * 100)

# Tabela principal
print("\nPROJECAO FINANCEIRA (2025-2027)")
print("=" * 100)
print(f"{'Metrica':<35} {'2025':>20} {'2026':>20} {'2027':>20}")
print("-" * 100)

# Receita por Apartamento
line_receita_apt = "Receita por Apartamento"
for projecao in projecoes:
    print(f"{line_receita_apt:<35} R$ {projecao['receita_unitaria']:>18,.2f}", end="  ")
print()

# Receita Bruta Total
line_receita_bruta = "Receita Bruta Total"
for projecao in projecoes:
    print(f"{line_receita_bruta:<35} R$ {projecao['receita_bruta']:>18,.2f}", end="  ")
print()

# Custos Operacionais
line_custos = "Custos Operacionais (35%)"
for projecao in projecoes:
    print(f"{line_custos:<35} R$ {projecao['custos_operacionais']:>18,.2f}", end="  ")
print()

# Lucro Operacional
line_lucro = "Lucro Operacional"
for projecao in projecoes:
    print(f"{line_lucro:<35} R$ {projecao['lucro_operacional']:>18,.2f}", end="  ")
print()

print("=" * 100)

# Detalhe por ano
for projecao in projecoes:
    print(f"\nANO {projecao['ano']}")
    print("-" * 100)
    print(f"  Receita Bruta:        R$ {projecao['receita_bruta']:>15,.2f}")
    print(f"  Custos Operacionais:  R$ {projecao['custos_operacionais']:>15,.2f}  ({PERCENTUAL_CUSTOS * 100:.0f}%)")
    print(f"  Lucro Operacional:    R$ {projecao['lucro_operacional']:>15,.2f}  ({projecao['margem_lucro_pct']:.0f}% margem)")

# Resumo 3 anos
print("\n" + "=" * 100)
print("RESUMO ACUMULADO (3 ANOS)")
print("=" * 100)

receita_total_3anos = sum(p['receita_bruta'] for p in projecoes)
custos_total_3anos = sum(p['custos_operacionais'] for p in projecoes)
lucro_total_3anos = sum(p['lucro_operacional'] for p in projecoes)

print(f"\n  Receita Bruta Total (2025-2027):     R$ {receita_total_3anos:>15,.2f}")
print(f"  Custos Operacionais Total:           R$ {custos_total_3anos:>15,.2f}")
print(f"  Lucro Operacional Total:             R$ {lucro_total_3anos:>15,.2f}")
print(f"\n  Lucro Medio Anual:                   R$ {lucro_total_3anos / 3:>15,.2f}")
print(f"  Lucro Medio por Apartamento/Ano:     R$ {lucro_total_3anos / 3 / TOTAL_APARTMENTS:>15,.2f}")

print("\n" + "=" * 100)

# Calculo de ROI simples (assumindo investimento inicial)
# Nota: Para calcular ROI real, seria necessario saber o valor do investimento inicial
# Por enquanto, mostramos apenas payback baseado em lucro

print("\nINSIGHTS")
print("=" * 100)
print(f"  • Crescimento Acumulado de Receita (2025->2027): {((ano_2027['receita_bruta'] / ano_2025['receita_bruta'] - 1) * 100):.1f}%")
print(f"  • Lucro por Apartamento em 2025: R$ {ano_2025['lucro_operacional'] / TOTAL_APARTMENTS:,.2f}")
print(f"  • Lucro por Apartamento em 2027: R$ {ano_2027['lucro_operacional'] / TOTAL_APARTMENTS:,.2f}")
print(f"  • Evolucao da Margem: Mantem {MARGEM_LUCRO_OPERACIONAL * 100:.0f}% em todos os anos")

print("\n" + "=" * 100 + "\n")
