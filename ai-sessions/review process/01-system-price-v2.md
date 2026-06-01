# Code Review: PR feature-system-price-v2

**Revisor**: Yuri Queiroz (AI Builder - Data Lead)  
**Data**: 2026-06-01  
**Branch**: `pr-review/feature-system-price-v2`  
**Autor**: Junior (Squad Data Edge)  
**AI Co-author**: Claude Sonnet 4.5 (anthropic.claude-sonnet-4-5-20250929-v1:0) via OpenCode

---

> **Nota sobre AI Co-authorship**: Este code review foi desenvolvido com auxílio de IA agentic (Claude Sonnet 4.5) seguindo metodologia spec-driven da Seazone. A IA foi utilizada para análise sistemática do código, identificação de padrões de bugs, e estruturação do feedback. Todas as decisões técnicas e recomendações foram validadas por revisão humana.

---

## Veredito: ❌ CHANGES REQUESTED

Este PR não pode ser mergeado no estado atual. Contém **erros críticos de segurança, lógica de dados incorreta e violação de princípios fundamentais** da engenharia de dados da Seazone.

---

## Top 3 Problemas Mais Críticos

### 🔴 1. CREDENCIAIS HARDCODED NO CÓDIGO (CRÍTICO DE SEGURANÇA)

**Localização**: `pipelines/system_price_v2.py:15-16`

```python
DB_USER = "sz_data_edge"
DB_PASSWORD = "Sz!DataEdge2025"
```

**Problema**:
- Senha em texto claro commitada no repositório
- Violação direta da política de segurança da empresa
- Expõe credenciais de produção em repositório que pode se tornar público
- Se este código chegar em produção, precisaremos rotacionar credenciais e auditar acessos

**Impacto**: **BLOQUEADOR** - Risco de segurança imediato

**Correção**:
```python
# Usar variáveis de ambiente
import os
DB_USER = os.getenv("SEAZONE_DB_USER")
DB_PASSWORD = os.getenv("SEAZONE_DB_PASSWORD")

if not DB_USER or not DB_PASSWORD:
    raise ValueError("Credenciais não configuradas. Configure SEAZONE_DB_USER e SEAZONE_DB_PASSWORD")
```

**Nota adicional**: Essas variáveis são declaradas mas **nunca usadas** no código. Se não são necessárias, devem ser removidas. Se são necessárias, falta implementação.

---

### 🔴 2. NÃO TRATA A ESTRUTURA DE DUPLA DATA DO PRICE_AV (ERRO CONCEITUAL GRAVE)

**Localização**: `pipelines/system_price_v2.py:37-42` (função `filter_last_quarter`)

**Problema**:
O arquivo `Price_AV_Itapema.csv` tem **duas dimensões temporais**:
- **Data de aquisição** (snapshot): 2025-01-07, 2025-01-13, 2025-01-20
- **Data de estadia** (stay): Janeiro a Abril 2025

Segundo o PDF do desafio (página 2):
> "Atenção: Price_AV_Itapema.csv tem dupla data (aquisição × estadia) — 3 snapshots de aquisição capturando o mesmo período de estadia (alta temporada de verão SC). **Tratar como simples "preço atual" é o tipo de erro que reprova.**"

**O que o código faz ERRADO**:
```python
def filter_last_quarter(prices_df):
    """Filtra o ultimo trimestre."""
    today = datetime.now()  # ← Hoje é 2026-06-01
    cutoff = today - timedelta(days=QUARTER_DAYS)  # ← 2026-03-03
    prices_df["date"] = pd.to_datetime(prices_df["date"])
    return prices_df[prices_df["date"] >= cutoff]  # ← Retorna VAZIO!
```

**Consequências**:
1. Se rodar hoje (Jun 2026), o filtro busca datas >= Mar 2026
2. Os dados vão de Jan-Abr **2025** → dataset filtrado fica **VAZIO**
3. Ignora completamente os 3 snapshots de aquisição
4. Perde a capacidade de detectar mudanças de preço ao longo do tempo
5. A gold table vai estar vazia ou com dados inconsistentes

**Impacto**: **BLOQUEADOR** - Lógica de negócio fundamentalmente quebrada

**Correção necessária**:
```python
def prepare_price_data(prices_df):
    """
    Trata a estrutura de dupla data do Price_AV.
    
    Estratégia: usar o snapshot mais recente (2025-01-20) como referência
    de preço atual, mantendo a granularidade por data de estadia.
    """
    # Converter colunas de data
    prices_df['acquisition_date'] = pd.to_datetime(prices_df['acquisition_date'])
    prices_df['stay_date'] = pd.to_datetime(prices_df['stay_date'])
    
    # Usar snapshot mais recente
    latest_snapshot = prices_df['acquisition_date'].max()
    df_latest = prices_df[prices_df['acquisition_date'] == latest_snapshot].copy()
    
    # Filtrar apenas alta temporada (Jan-Abr 2025 conforme spec)
    df_latest = df_latest[
        (df_latest['stay_date'] >= '2025-01-01') & 
        (df_latest['stay_date'] <= '2025-04-30')
    ]
    
    return df_latest
```

**Alternativa avançada**: Calcular delta de preço entre snapshots para detectar tendências de ocupação (preço que "sumiu" = reserva confirmada).

---

### 🔴 3. MISTURA INCORRETA DE MERCADOS: SHORT-STAY (AIRBNB) + LONG-TERM (VIVAREAL)

**Localização**: `pipelines/system_price_v2.py:76-99` (funções `normalize_vivareal` e `build_stage`)

**Problema**:
O código combina duas fontes de dados de **mercados completamente diferentes**:

```python
# Linha 79: VivaReal → aluguel mensal / 30 = "diária"
vivareal_df["price"] = vivareal_df["rental_price"] / 30

# Linhas 95-98: Combina tudo numa média única
combined = pd.concat(
    [short_term[["suburb", "price"]], vivareal_norm],
    ignore_index=True,
)
```

**Por que isso é errado**:

| Dimensão | Airbnb (short-stay) | VivaReal (long-term) |
|----------|---------------------|----------------------|
| **Período** | 1-7 noites | 30+ dias (contrato) |
| **Precificação** | Dinâmica, sazonal | Fixa mensal |
| **Target** | Turistas | Residentes |
| **Markup** | 2-4x maior | Menor |
| **Custos inclusos** | Limpeza, utilidades | Separados |

**Exemplo numérico do erro**:
- Airbnb: R$ 500/noite (short-stay premium)
- VivaReal: R$ 3000/mês ÷ 30 = R$ 100/noite (long-term convertido)
- **Média final: R$ 300/noite** ← Não representa NENHUM dos mercados!

**Impacto**: **BLOQUEADOR** - A métrica "System Price" perde significado analítico

**Correção**:
```python
# OPÇÃO 1: Separar as métricas
def build_stage_separated(prices_df, mesh_df, vivareal_df):
    """Calcula métricas separadas por tipo de mercado."""
    # Short-term (Airbnb)
    airbnb_prices = enrich_with_bairro(prices_df, mesh_df)
    airbnb_summary = airbnb_prices.groupby('suburb').agg({
        'price': 'mean',
        'airbnb_listing_id': 'count'
    }).rename(columns={'price': 'avg_price_short_term', 'airbnb_listing_id': 'n_listings'})
    
    # Long-term (VivaReal) - SEM dividir por 30
    vivareal_summary = vivareal_df.groupby('suburb').agg({
        'rental_price': 'mean'
    }).rename(columns={'rental_price': 'avg_price_long_term_monthly'})
    
    # JOIN preservando a separação
    return airbnb_summary.join(vivareal_summary, how='outer')

# OPÇÃO 2: Se realmente precisa combinar, usar como sinal secundário
# com peso ponderado explícito e documentado
```

**Nota para o 1:1**: Este é um erro conceitual que sugere falta de entendimento do domínio de negócio da Seazone. Nosso core é short-stay; VivaReal pode ser sinal complementar de mercado imobiliário, mas não pode ser averaged diretamente.

---

## Outros Problemas Críticos

### 🔴 4. EXCEPTION HANDLING SILENCIOSO

**Localização**: `pipelines/system_price_v2.py:31-32`

```python
def load_csvs():
    try:
        details = pd.read_csv(f"{DATA_DIR}/Details_Itapema.csv")
        hosts = pd.read_csv(f"{DATA_DIR}/Hosts_ids_Itapema.csv")
        mesh = pd.read_csv(f"{DATA_DIR}/Mesh_Ids_Data_Itapema.csv")
        prices = pd.read_csv(f"{DATA_DIR}/Price_AV_Itapema.csv")
        vivareal = pd.read_csv(f"{DATA_DIR}/VivaReal_Itapema.csv")
    except Exception:
        pass  # ← ENGOLE TODOS OS ERROS!

    return details, hosts, mesh, prices, vivareal  # ← VARIÁVEIS INDEFINIDAS SE FALHAR
```

**Problemas**:
1. `except Exception: pass` engole TODOS os erros sem logging
2. Se qualquer CSV falhar, as variáveis ficam **indefinidas**
3. O `return` referencia variáveis que podem não existir → `NameError` na linha 128
4. Pipeline continua rodando silenciosamente com dados incorretos
5. Impossível debugar em produção

**Correção**:
```python
import logging

def load_csvs():
    """Carrega os 5 CSVs em DataFrames com validação."""
    required_files = {
        'details': 'Details_Itapema.csv',
        'hosts': 'Hosts_ids_Itapema.csv',
        'mesh': 'Mesh_Ids_Data_Itapema.csv',
        'prices': 'Price_AV_Itapema.csv',
        'vivareal': 'VivaReal_Itapema.csv'
    }
    
    dataframes = {}
    
    for key, filename in required_files.items():
        filepath = f"{DATA_DIR}/{filename}"
        try:
            df = pd.read_csv(filepath)
            logging.info(f"✓ Carregado {filename}: {len(df)} linhas")
            dataframes[key] = df
        except FileNotFoundError:
            logging.error(f"✗ Arquivo não encontrado: {filepath}")
            raise
        except pd.errors.ParserError as e:
            logging.error(f"✗ Erro ao parsear {filename}: {e}")
            raise
    
    return (
        dataframes['details'],
        dataframes['hosts'],
        dataframes['mesh'],
        dataframes['prices'],
        dataframes['vivareal']
    )
```

---

### 🔴 5. PIPELINE NÃO É IDEMPOTENTE

**Localização**: `pipelines/gold_system_price_itapema.sql:14`

```sql
INSERT INTO gold_system_price_itapema
SELECT
    suburb AS bairro,
    AVG(price) AS system_price_avg,
    COUNT(*) AS n_amostras
FROM stage
GROUP BY suburb
ORDER BY system_price_avg DESC;
```

**Problema**:
- Usa `INSERT INTO` sem antes limpar dados anteriores
- Se rodar 2x o pipeline → dados **duplicados** na tabela gold
- Viola princípio de **idempotência** (executar N vezes ≠ executar 1 vez)

**Impacto**:
- Em produção com Airflow, re-runs vão corromper dados
- Impossível garantir integridade das análises de RM

**Correção**:
```sql
-- OPÇÃO 1: Usar TRUNCATE + INSERT
DELETE FROM gold_system_price_itapema;  -- ou TRUNCATE TABLE

INSERT INTO gold_system_price_itapema
SELECT ...

-- OPÇÃO 2: DROP + CREATE (mais seguro)
DROP TABLE IF EXISTS gold_system_price_itapema;

CREATE TABLE gold_system_price_itapema AS
SELECT
    suburb AS bairro,
    AVG(price) AS system_price_avg,
    COUNT(*) AS n_amostras
FROM stage
GROUP BY suburb
ORDER BY system_price_avg DESC;

-- OPÇÃO 3: Usar MERGE/UPSERT com particionamento por data de processamento
```

---

### 🟡 6. CÓDIGO INÚTIL E INEFICIENTE

**Localização**: `pipelines/system_price_v2.py:58-61`

```python
details_df = details_df.copy()
details_df["bairro_lower"] = ""
for idx, row in details_df.iterrows():
    details_df.at[idx, "bairro_lower"] = str(row.get("ad_name", "")).lower()
```

**Problemas**:
1. `iterrows()` é O(n²) em pandas - extremamente lento
2. Cria coluna `bairro_lower` mas **NUNCA USA** ela no resto do código
3. Processa campo `ad_name` que não está sendo usado

**Correção**: **DELETAR** este bloco inteiro (linhas 58-61). Se for necessário no futuro:
```python
# Vetorizado, O(n)
details_df['bairro_lower'] = details_df['ad_name'].str.lower()
```

---

### 🟡 7. VALIDAÇÃO INEXISTENTE

**Problema**: PR_DESCRIPTION diz:
> "Validei batendo o olho no count de linhas no log"

**O que está faltando**:
1. Nenhum teste unitário
2. Nenhuma validação de schema
3. Nenhuma métrica de qualidade de dados
4. Nenhuma comparação com baseline
5. Nenhuma verificação de valores nulos/outliers

**Exemplo de validação mínima**:
```python
def validate_gold_output(con):
    """Validações básicas de qualidade."""
    checks = {
        'total_rows': "SELECT COUNT(*) FROM gold_system_price_itapema",
        'null_bairros': "SELECT COUNT(*) FROM gold_system_price_itapema WHERE bairro IS NULL",
        'zero_prices': "SELECT COUNT(*) FROM gold_system_price_itapema WHERE system_price_avg <= 0",
        'low_samples': "SELECT COUNT(*) FROM gold_system_price_itapema WHERE n_amostras < 5"
    }
    
    issues = []
    for check_name, query in checks.items():
        result = con.execute(query).fetchone()[0]
        logging.info(f"Check {check_name}: {result}")
        
        if check_name == 'null_bairros' and result > 0:
            issues.append(f"{result} bairros nulos encontrados")
        if check_name == 'zero_prices' and result > 0:
            issues.append(f"{result} preços <= 0 encontrados")
    
    if issues:
        raise ValueError(f"Validação falhou: {'; '.join(issues)}")
```

---

### 🟡 8. NOME DE COLUNA INCONSISTENTE NO SQL

**Localização**: `pipelines/system_price_v2.py:56` vs `gold_system_price_itapema.sql:16`

Python usa:
```python
hosts_df['owner']  # ← Coluna 'owner'
```

Mas SQL espera:
```sql
SELECT ... FROM stage  -- onde 'stage' vem do combined_df
```

**Problema potencial**: Se `hosts_df` tem coluna `owner` (linha 56) mas o merge usa `owner_id`, pode haver inconsistência.

---

## O que Falhou Upstream

Este PR não deveria ter chegado em review nesse estado. Identifico 3 falhas no processo:

### 1. **Spec insuficiente ou não seguido**
O PR menciona "spec combinado com a Anna no dia 22/04", mas:
- Não há spec escrito em `specs/`
- Não há validação de que o código segue o spec
- Não há definição clara de "System Price" (inclui VivaReal? Como?)

**Ação corretiva**: Exigir `specs/{feature}/spec.md` commitado ANTES de iniciar código, conforme metodologia spec-driven da Seazone.

### 2. **Falta de revisão interna antes de abrir PR**
Problemas triviais que deveriam ser pegos antes de review formal:
- Credenciais hardcoded
- Exception handling silencioso
- Código morto (variáveis não usadas)

**Ação corretiva**: 
- Instalar pre-commit hooks para detectar credenciais
- Checklist obrigatório antes de abrir PR:
  - [ ] Código roda localmente sem erros
  - [ ] Sem credenciais hardcoded
  - [ ] Logging adequado
  - [ ] Validações básicas implementadas

### 3. **Falta de entendimento do domínio de dados**
A mistura de Airbnb + VivaReal e o erro da dupla data sugerem gap de conhecimento sobre:
- Estrutura dos dados de scrapers da Seazone
- Diferença entre mercados short-stay vs long-term
- Importância de idempotência em pipelines

**Ação corretiva**:
- Onboarding técnico reforçado sobre arquitetura de dados
- Shadowing em pipelines existentes antes de criar novos
- Pair programming em features de dados complexas

---

## Como Conduziria o 1:1 com o Júnior

### Estrutura da Conversa (30-40 minutos)

**1. Contexto Positivo (5 min)**
- "Primeiro, obrigado por abrir o PR. Sei que você se dedicou nisso."
- "Vejo que você seguiu a estrutura que combinamos: Python + DuckDB, SQL separado, documentação no PR."
- "A arquitetura geral (load → stage → gold) está no caminho certo."

**2. Apresentar os Problemas Críticos (15 min)**
- Compartilhar tela com o código aberto
- **Começar pelo mais didático** (não pelo mais grave):

**"Vou te mostrar 3 problemas que bloqueiam o merge, em ordem crescente de complexidade:"**

**a) Credenciais Hardcoded (5 min)**
- "Olha aqui nas linhas 15-16. O que você vê de problemático?"
- [Deixar ele responder, guiar se necessário]
- "Exato. Se isso chegar em produção, vamos ter que rotacionar senha e auditar acessos. Como você corrigiria?"
- [Explicar variáveis de ambiente, mostrar exemplo]

**b) Pipeline Não Idempotente (5 min)**
- "Agora olha o SQL. O que acontece se rodarmos 2x o pipeline?"
- [Deixar ele pensar]
- "Isso! Dados duplicados. Em produção com Airflow, re-runs vão corromper análises. Familiar com o conceito de idempotência?"
- [Se não: explicar brevemente, mostrar correção com DROP+CREATE]

**c) Dupla Data do Price_AV (5 min)**
- "Esse é o mais sutil, mas é o mais crítico. Vou te mostrar a estrutura do Price_AV."
- [Abrir CSV, mostrar colunas de aquisição vs estadia]
- "Vê que temos 3 snapshots de **aquisição** para mesmas datas de **estadia**? O que isso significa?"
- [Guiar: permite detectar quando preço 'sumiu' = reserva confirmada]
- "Olha o que seu código faz: usa `datetime.now()` para filtrar. Se eu rodar hoje, o que acontece?"
- [Fazer ele perceber: dataset vazio]
- "Esse erro é citado explicitamente no desafio como reprovador. Vamos pensar juntos numa correção?"

**3. Problema Conceitual: Airbnb + VivaReal (10 min)**
- "Agora quero entender sua decisão de combinar Airbnb e VivaReal. Me explica o raciocínio?"
- [OUVIR ativamente, sem interromper]
- "Entendo a intenção de ter sinal de mercado mais amplo. Mas vamos pensar juntos: qual a diferença entre esses mercados?"
- [Discussão socrática: duração da estadia, target, precificação]
- "Se a gente faz média direta, o número final representa qual mercado? Nenhum dos dois, certo?"
- "Como você acha que poderíamos usar VivaReal como sinal **complementar** sem distorcer o System Price?"
- [Guiar para: métricas separadas ou peso ponderado explícito]

**4. Caminho para Correção (5-10 min)**
- "Vou marcar o PR como 'Changes Requested'. Aqui está o que precisa ser corrigido por ordem de prioridade:"
  1. **IMEDIATO**: Remover credenciais, usar env vars
  2. **CRÍTICO**: Corrigir lógica da dupla data
  3. **CRÍTICO**: Separar métricas Airbnb vs VivaReal OU justificar combinação com peso explícito
  4. **IMPORTANTE**: Tornar pipeline idempotente
  5. **IMPORTANTE**: Adicionar logging e exception handling adequados
  6. **BÔNUS**: Adicionar validações básicas de qualidade

- "Eu vou deixar comentários inline no PR com sugestões de código. Sinta-se à vontade pra me chamar pra pair programming se quiser destrinchar qualquer um desses pontos."

**5. Processo e Crescimento (5 min)**
- "Esses erros não são sobre capacidade, são sobre processo e contexto. Vamos ajustar algumas coisas:"
  1. **Specs obrigatórios**: A partir de agora, todo PR de dados precisa ter `specs/{feature}/spec.md` commitado antes
  2. **Pair programming**: Nas próximas 2-3 features de dados, vamos fazer pair pra você pegar o contexto dos scrapers e estrutura dos dados
  3. **Pre-commit hooks**: Vou configurar hooks que bloqueiam credenciais e código com problemas óbvios

- "Uma coisa que você faz bem: organização do código em funções, separação Python/SQL. Continue nisso."

**6. Próximos Passos Concretos**
- "Pra essa semana: foca em corrigir itens 1-4. Me mostra a correção da dupla data antes de commitar, quero validar contigo."
- "Sexta a gente faz um quick review do PR atualizado. Se tiver 80% correto, eu aprovo e a gente ajusta o resto em PR incremental."
- "Alguma dúvida ou algo que não ficou claro?"

**Tom geral**:
- ✅ Direto e honesto sobre os problemas
- ✅ Educativo, não punitivo
- ✅ Foca em correção E em prevenir recorrência
- ✅ Oferece suporte concreto (pair programming, review parcial)
- ❌ Sem jargões desnecessários
- ❌ Sem minimizar a gravidade ("só uns detalhezinhos")
- ❌ Sem assumir má-fé ou falta de esforço

---

## Comentários Inline a Serem Adicionados no PR

Vou adicionar os seguintes comentários inline no GitHub:

### `pipelines/system_price_v2.py:15-16`
```
🔴 BLOQUEADOR: Credenciais hardcoded

Senha em texto claro no código é violação crítica de segurança.

Correção:
```python
import os
DB_USER = os.getenv("SEAZONE_DB_USER")
DB_PASSWORD = os.getenv("SEAZONE_DB_PASSWORD")

if not DB_USER or not DB_PASSWORD:
    raise ValueError("Configure SEAZONE_DB_USER e SEAZONE_DB_PASSWORD")
```

Nota: Essas variáveis não são usadas no resto do código. Se não são necessárias, remova.
```

### `pipelines/system_price_v2.py:31-32`
```
🔴 CRÍTICO: Exception handling silencioso

`except Exception: pass` engole TODOS os erros sem logging.
Se qualquer CSV falhar, as variáveis ficam indefinidas e o pipeline continua com erro.

Correção: Ver sugestão completa no review summary.
```

### `pipelines/system_price_v2.py:37-42`
```
🔴 BLOQUEADOR: Lógica incorreta para Price_AV

Price_AV tem DUPLA DATA (aquisição × estadia). Este código:
1. Usa `datetime.now()` (Jun 2026) pra filtrar dados de Jan-Abr 2025 → retorna VAZIO
2. Ignora os 3 snapshots de aquisição (essência da detecção de reservas)

Segundo o PDF do desafio (pág 2):
> "Tratar como simples 'preço atual' é o tipo de erro que reprova."

Correção: Ver sugestão completa no review summary.
```

### `pipelines/system_price_v2.py:76-99`
```
🔴 CRÍTICO: Mistura incorreta de mercados

Combinar Airbnb (short-stay, R$500/noite) com VivaReal (long-term, R$3000/mês ÷ 30) numa média única:
- Não representa nenhum dos mercados
- VivaReal/30 não é equivalente a diária de short-stay (markup, custos, target diferentes)

Sugestões:
1. Métricas SEPARADAS: `avg_price_short_term` vs `avg_price_long_term_monthly`
2. OU: VivaReal como sinal secundário com peso ponderado explícito e documentado

Vamos discutir no 1:1 qual abordagem faz mais sentido pro dashboard de RM.
```

### `pipelines/system_price_v2.py:58-61`
```
🟡 Código inútil e ineficiente

1. `iterrows()` é O(n²) - extremamente lento
2. Coluna `bairro_lower` é criada mas nunca usada

Sugestão: DELETAR este bloco inteiro.

Se for necessário no futuro:
```python
details_df['bairro_lower'] = details_df['ad_name'].str.lower()
```
```

### `pipelines/gold_system_price_itapema.sql:14`
```
🔴 CRÍTICO: Pipeline não é idempotente

`INSERT INTO` sem limpar dados anteriores = dados duplicados se rodar 2x.

Correção:
```sql
DROP TABLE IF EXISTS gold_system_price_itapema;

CREATE TABLE gold_system_price_itapema AS
SELECT ...
```

Ou usar DELETE antes do INSERT.
```

---

## Resumo Executivo

**Veredito**: ❌ **CHANGES REQUESTED**

**Problemas bloqueadores**:
1. Credenciais hardcoded (segurança)
2. Lógica de dupla data incorreta (dataset vazio)
3. Mistura de mercados incompatíveis (métrica sem significado)
4. Pipeline não idempotente (corrupção de dados)
5. Exception handling silencioso (impossível debugar)

**Tempo estimado de correção**: 1-2 dias de desenvolvimento + pair programming

**Recomendação**: 
- Pair programming na correção da dupla data (item mais complexo)
- Revisão parcial na sexta-feira
- Instalar pre-commit hooks para prevenir credenciais hardcoded

**Nível de urgência**: Não é urgente mergear. Melhor investir tempo corrigindo bem do que ter débito técnico em produção.

---

## Aprendizados para o Time

Este PR revela gaps que afetam o squad como um todo:

1. **Processo**: Specs não estão sendo escritos antes do código
2. **Técnico**: Falta documentação interna sobre estrutura dos scrapers (dupla data, snapshots)
3. **Segurança**: Pre-commit hooks não estão configurados

**Ações para as próximas sprints**:
- [ ] Criar template de spec obrigatório em `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] Documentar estrutura dos datasets de scrapers em `docs/data-sources.md`
- [ ] Configurar pre-commit hooks (secrets detection, linting)
- [ ] Session de knowledge sharing: "Anatomia dos dados de scraping da Seazone"

---

## AI Co-author Log

### Modelo Utilizado
**LLM**: Claude Sonnet 4.5 (anthropic.claude-sonnet-4-5-20250929-v1:0)  
**Interface**: OpenCode (AI Builder IDE)  
**Metodologia**: Spec-driven development + AI agentic review

### O que foi Entregue à IA
1. **Contexto do Desafio**: PDF completo do desafio Seazone (9 páginas)
2. **Código do PR**: 
   - `system_price_v2.py` (138 linhas)
   - `gold_system_price_itapema.sql` (21 linhas)
   - `PR_DESCRIPTION.md` (descrição do Júnior)
3. **Prompt Estruturado**: 
   - "Analise este PR como um líder técnico de dados"
   - "Identifique bugs críticos, problemas de segurança, e erros conceituais"
   - "Forneça feedback acionável e educativo, não punitivo"
   - "Prepare estrutura de 1:1 para discussão com o desenvolvedor"

### Onde a IA Acelerou Bem

**1. Análise Sistemática Multi-camada** (Speedup estimado: 3x)
- A IA percorreu o código de forma estruturada identificando simultaneamente:
  - Segurança (credenciais hardcoded)
  - Lógica de negócio (dupla data, mistura de mercados)
  - Qualidade de código (exception handling, idempotência)
  - Performance (iterrows ineficiente)
- **Exemplo concreto**: Em ~2 minutos, a IA mapeou 8 problemas críticos que manualmente levariam 15-20 minutos de análise linha por linha

**2. Cruzamento com Requisitos do Desafio**
- A IA cruzou automaticamente o código com o texto do PDF:
  > "Price_AV_Itapema.csv tem dupla data... Tratar como simples 'preço atual' é o tipo de erro que reprova."
- Identificou que o `filter_last_quarter()` comete exatamente esse erro
- Sem IA: eu precisaria reler o PDF enquanto analiso o código (context switching)

**3. Geração de Exemplos de Correção**
- Para cada problema, a IA gerou código corrigido imediatamente
- Exemplos com comentários explicativos prontos para copiar
- **Speedup estimado: 4x** - Escrever correções manualmente levaria 30-40 min

### Onde a IA Errou ou Desviou

**1. Falso Positivo Inicial: Nomes de Colunas** (Corrigido)
- A IA inicialmente sinalizou inconsistência entre `hosts_df['owner']` (linha 56) e `owner_id` usado em merges
- **Correção humana**: Revisei o CSV original - a coluna é `owner_id`, não `owner`
- A linha 56 usa `.head(5).tolist()` apenas para logging, não afeta lógica
- **Mantive como problema menor** no review, mas menos crítico que inicialmente sugerido

**2. Over-engineering na Solução de Validação**
- A IA sugeriu inicialmente um framework completo de validação com Great Expectations
- **Correção humana**: Simplifiquei para validações básicas com SQL direto no DuckDB
- Contexto: estamos em fase de MVP, validação sofisticada vem depois

**3. Tom Excessivamente Técnico no 1:1**
- Primeira versão do script de 1:1 usava muito jargão ("dimensional modeling", "SCD Type 2")
- **Correção humana**: Reescrevi com linguagem mais acessível e socrática
- Exemplo: Mudei "violação de SCD Type 2" para "o que acontece se rodarmos 2x o pipeline?"

### Sub-agentes / Skills / MCPs Utilizados

**Skills Nativos do OpenCode**:
1. **Read**: Leitura estruturada de código e documentos (PDF, Python, SQL)
2. **Grep**: Busca por padrões (ex: credenciais, imports, uso de variáveis)
3. **Bash/Git**: Análise de histórico de commits e diffs
4. **TodoWrite**: Organização do trabalho de review em etapas (6 tasks)

**Não utilizei MCP servers customizados** para este review, apenas ferramentas nativas.

### Estimativa Honesta de Speedup

**Tempo com IA**: ~45 minutos
- 5 min: Leitura do código e PDF
- 10 min: Análise sistemática guiada por IA
- 15 min: Validação humana dos achados e correção de falsos positivos
- 15 min: Estruturação do documento final e script de 1:1

**Tempo sem IA (estimado)**: ~2h30
- 15 min: Leitura inicial
- 40 min: Análise manual linha por linha com context switching para PDF
- 30 min: Escrever exemplos de correção
- 45 min: Estruturar documento e 1:1
- 20 min: Revisar consistência

**Speedup**: **~3.3x**

### Decisões que Permaneceram 100% Humanas

1. **Veredito final**: "Changes Requested" (não "Close PR")
2. **Priorização dos Top 3**: Escolhi destacar dupla data sobre idempotência por ser erro explicitamente citado no desafio
3. **Tom do 1:1**: Estrutura de conversa socrática, não expositiva
4. **Ações de squad**: Definir pre-commit hooks, knowledge sharing sessions
5. **Nível de urgência**: Decisão de não apressar o merge

---

**Nota final**: Junior, agradeço pela dedicação no PR. Os erros aqui são oportunidade de crescimento, não reflexo de capacidade. Vamos trabalhar juntos pra corrigir e pra você dominar esse contexto de dados. Marca um tempo comigo essa semana pra destrincharmos juntos. 🤝
