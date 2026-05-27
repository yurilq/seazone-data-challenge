# 01-discovery.md - AI Builder Data Discovery & EDA

## Pedido/Erro
Realizar Discovery (Exploração de Dados) usando Polars para responder às duas primeiras perguntas de negócio:
1. **Melhor Localização:** Agregação por bairro (receita total, média e quantidade de imóveis)
2. **Melhor Perfil de Imóvel:** Agregação por número de quartos (receita total, média e média de diárias alugadas)

---

## Ação do AI Builder

### Ferramenta Utilizada
- **Polars** (DataFrames de alto desempenho, sem Pandas/Jupyter)
- Script: `analysis/discovery.py`
- Entrada: `analysis/revenue_analysis.csv` (228 imóveis com métricas de reserva)

### Processo de Exploração

1. **Leitura de Dados:** `pl.read_csv()` carregou o arquivo consolidado de 228 imóveis
2. **Agregação Q1:** `group_by('bairro').agg([sum, mean, count])` → 5 bairros principais
3. **Agregação Q2:** `group_by('number_of_bedrooms').agg([sum, mean, mean])` → 6 perfis de imóvel
4. **Ordenação:** `.sort('receita_total', descending=True)` para identificar topo
5. **Output:** Salvos em CSV (`discovery_localizacao.csv`, `discovery_perfil.csv`)

---

## Resultado - DESCOBERTAS PRINCIPAIS

### PERGUNTA 1: MELHOR LOCALIZACAO (TOP 5 BAIRROS)

| Rank | Bairro | Receita Total | Receita Media/Imovel | Qtd Imoveis |
|------|--------|---------------|--------------------|------------|
| 🥇 1 | **Meia Praia** | R$ 3.350.800,47 | R$ 25.578,63 | **131** |
| 🥈 2 | Centro | R$ 607.075,76 | R$ 12.141,52 | 50 |
| 🥉 3 | Morretes | R$ 365.066,83 | R$ 16.593,95 | 22 |
| 4 | Casa Branca | R$ 135.367,67 | R$ 16.920,96 | 8 |
| 5 | Sem Bairro | R$ 124.524,50 | R$ 41.508,17 | 3 |

**Insights:**
- **Meia Praia domina:** 82% da receita total (R$ 3.35M de R$ 4.1M)
- **Concentração extrema:** 131 dos 228 imóveis (57%) localizados em Meia Praia
- **Estratégia:** Investimento em Meia Praia é claramente prioridade máxima
- **Oportunidade:** Centro tem potencial (50 imóveis) mas receita média é 47% menor

### PERGUNTA 2: MELHOR PERFIL DE IMOVEL (POR NUMERO DE QUARTOS)

| Quartos | Receita Total | Receita Media | Media Diarias Alugadas |
|---------|---------------|--------------|-----------------------|
| **3** | **R$ 1.712.552,00** | R$ 20.633,16 | 25,3 |
| **4** | **R$ 1.387.120,00** | **R$ 81.595,29** ⭐ | **36,6** |
| **2** | R$ 1.145.588,57 | R$ 15.073,53 | 28,2 |
| 1 | R$ 434.320,37 | R$ 9.651,56 | 25,8 |
| 5 | R$ 164.674,00 | R$ 54.891,33 | 33,0 |

**Insights:**
- **Imóveis de 3 quartos:** Maior receita TOTAL (R$ 1.71M) - volume
- **Imóveis de 4 quartos:** Maior receita MEDIA (R$ 81.595) - margem 🌟
  - 4 quartos geram 4x mais receita média que imóveis com 2 quartos
  - Média de 36,6 diárias alugadas (maior ocupação)
- **Imóveis de 2 quartos:** Volume intermediário, receita baixa (sweet spot de quantidade)
- **Imóveis de 1 quarto:** Baixa performance (menor receita média)

### CORRELACAO: Meia Praia + 3-4 Quartos = Melhor Performance

Combinando os dados:
- Meia Praia: 57% dos imóveis, 82% da receita
- 3-4 quartos: 65% da receita total
- **Estratégia:** Focar em imóveis de 3-4 quartos em Meia Praia

---

## Recomendacoes Estrategicas

1. **Investimento Prioritário:**
   - Aumentar inventário de imóveis de 4 quartos em Meia Praia
   - ROI médio de R$ 81.595 por imóvel

2. **Diversificação Moderada:**
   - Explorar Centro (50 imóveis existentes) com foco em 3-4 quartos
   - Potencial subutilizado em bairros secundários

3. **Otimização Operacional:**
   - Imóveis de 4 quartos têm maior ocupação (36,6 diárias) → priorizar gestão
   - Revisar listagens de 1-2 quartos em bairros pequenos

---

## Auto-Logger Seazone - Status

✅ **Discovery Concluído com Polars**
✅ **Duas Perguntas de Negócio Respondidas**
✅ **Arquivos de Saida Gerados**
✅ **Insights Extraídos e Documentados**

**Stack Utilizado:** Polars (sem Pandas/Jupyter)
**Método:** Aggregation + Sorting (SQL-like com API funcional)
**Próximo Passo:** Machine Learning para previsão de demanda ou clustering de imóveis
