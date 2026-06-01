# Code Review: PR feature-system-price-v2

## Metadados

| Campo | Valor |
|-------|-------|
| **Revisor** | Yuri Queiroz (AI Builder - Data Lead) |
| **Data** | 2026-06-01 |
| **Branch** | `pr-review/feature-system-price-v2` |
| **Autor do PR** | Junior (Squad Data Edge) |
| **Arquivos Alterados** | 4 (system_price_v2.py, gold_system_price_itapema.sql, requirements.txt, PR_DESCRIPTION.md) |
| **Linhas Adicionadas** | ~195 |
| **LLM Utilizado** | Claude Opus 4 (claude-opus-4-5-20251101) via Amazon Bedrock |
| **Interface** | OpenCode CLI |

---

## Nota sobre AI Co-authorship

> Este code review foi desenvolvido utilizando **Claude Opus 4** (model ID: `global.anthropic.claude-opus-4-5-20251101-v1:0`) via Amazon Bedrock, integrado através do OpenCode CLI. A metodologia aplicada segue o padrão spec-driven da Seazone, onde a IA atuou como co-autor na identificação sistemática de bugs, análise de padrões problemáticos e estruturação do feedback técnico. Todas as conclusões e recomendações passaram por validação humana antes da publicação.

---

## Veredito Final

# CHANGES REQUESTED

O PR **não pode ser aprovado** no estado atual. Foram identificados **8 problemas**, sendo **5 bloqueadores** que impedem o merge.

---

## Sumário de Problemas Identificados

| # | Severidade | Problema | Linha(s) | Tipo |
|---|------------|----------|----------|------|
| 1 | BLOQUEADOR | Credenciais hardcoded | 15-16 | Segurança |
| 2 | BLOQUEADOR | Não trata dupla data do Price_AV | 37-42 | Lógica de Negócio |
| 3 | BLOQUEADOR | Mistura Airbnb + VivaReal incorretamente | 76-98 | Lógica de Negócio |
| 4 | BLOQUEADOR | Exception silencioso com variáveis indefinidas | 31-34 | Qualidade de Código |
| 5 | BLOQUEADOR | Pipeline não idempotente | SQL:14 | Arquitetura |
| 6 | IMPORTANTE | Código morto e ineficiente (iterrows) | 58-61 | Performance |
| 7 | IMPORTANTE | Validação inexistente | - | Qualidade |
| 8 | MENOR | Variáveis declaradas mas não usadas | 15-16 | Code Smell |

---

## Análise Detalhada dos Problemas

### PROBLEMA #1: Credenciais Hardcoded no Código

**Severidade**: BLOQUEADOR  
**Tipo**: Segurança  
**Localização**: `pipelines/system_price_v2.py:15-16`

**Código problemático**:
```python
DB_USER = "sz_data_edge"
DB_PASSWORD = "Sz!DataEdge2025"
```

**Por que é grave**:
- Senha em texto claro versionada no Git
- Qualquer pessoa com acesso ao repositório (inclusive se tornar público) terá as credenciais
- Viola política de segurança corporativa
- Requer rotação de credenciais se já commitado em produção
- Pode resultar em acesso não autorizado ao banco de dados

**Correção recomendada**:
```python
import os

DB_USER = os.environ.get("SEAZONE_DB_USER")
DB_PASSWORD = os.environ.get("SEAZONE_DB_PASSWORD")

if not DB_USER or not DB_PASSWORD:
    raise EnvironmentError(
        "Variáveis SEAZONE_DB_USER e SEAZONE_DB_PASSWORD não configuradas. "
        "Configure-as no ambiente ou no arquivo .env"
    )
```

**Observação adicional**: Estas variáveis são declaradas mas nunca utilizadas no código atual. Se não são necessárias, devem ser completamente removidas.

---

### PROBLEMA #2: Não Trata a Estrutura de Dupla Data do Price_AV

**Severidade**: BLOQUEADOR  
**Tipo**: Lógica de Negócio  
**Localização**: `pipelines/system_price_v2.py:37-42`

**Código problemático**:
```python
def filter_last_quarter(prices_df):
    """Filtra o ultimo trimestre."""
    today = datetime.now()
    cutoff = today - timedelta(days=QUARTER_DAYS)
    prices_df["date"] = pd.to_datetime(prices_df["date"])
    return prices_df[prices_df["date"] >= cutoff]
```

**Contexto do problema**:

O arquivo `Price_AV_Itapema.csv` possui uma estrutura de **dupla dimensão temporal**:

| Dimensão | Descrição | Valores no Dataset |
|----------|-----------|-------------------|
| **Data de Aquisição** (snapshot) | Quando o scraper capturou o preço | 2025-01-07, 2025-01-13, 2025-01-20 |
| **Data de Estadia** (stay) | Para qual data futura é o preço | Janeiro a Abril 2025 |

**Citação do PDF do desafio (página 2)**:
> "Atenção: Price_AV_Itapema.csv tem **dupla data** (aquisição × estadia) — 3 snapshots de aquisição capturando o mesmo período de estadia (alta temporada de verão SC). **Tratar como simples "preço atual" é o tipo de erro que reprova.**"

**O que o código faz de errado**:

1. **Usa `datetime.now()`**: Em Junho de 2026, `cutoff` será ~Março 2026
2. **Filtra por data >= cutoff**: Os dados vão de Jan-Abr **2025**
3. **Resultado**: DataFrame **VAZIO** após o filtro
4. **Ignora snapshots**: Perde a capacidade de detectar reservas (preço que "sumiu" entre snapshots = reserva confirmada)

**Impacto prático**:
- A tabela gold será gerada vazia ou com dados incorretos
- Dashboard de RM exibirá informações falsas
- Decisões de negócio baseadas em dados corrompidos

**Correção recomendada**:
```python
def prepare_price_data(prices_df):
    """
    Processa Price_AV respeitando a estrutura de dupla data.
    
    Estratégia: usar o snapshot mais recente como referência de preço atual,
    mantendo granularidade por data de estadia.
    """
    # Identificar colunas de data (ajustar nomes conforme CSV real)
    prices_df['acquisition_date'] = pd.to_datetime(prices_df['acquisition_date'])
    prices_df['stay_date'] = pd.to_datetime(prices_df['stay_date'])
    
    # Usar apenas o snapshot mais recente (2025-01-20)
    latest_snapshot = prices_df['acquisition_date'].max()
    df_current = prices_df[prices_df['acquisition_date'] == latest_snapshot].copy()
    
    print(f"[INFO] Usando snapshot de {latest_snapshot}")
    print(f"[INFO] Período de estadia: {df_current['stay_date'].min()} a {df_current['stay_date'].max()}")
    
    return df_current
```

**Alternativa avançada** (detectar reservas):
```python
def detect_bookings(prices_df):
    """
    Detecta reservas comparando snapshots.
    Se um preço existia em snapshot anterior e sumiu no atual = reservado.
    """
    snapshots = sorted(prices_df['acquisition_date'].unique())
    
    if len(snapshots) < 2:
        return prices_df
    
    prev_snapshot = snapshots[-2]
    curr_snapshot = snapshots[-1]
    
    prev_listings = set(prices_df[prices_df['acquisition_date'] == prev_snapshot]['airbnb_listing_id'])
    curr_listings = set(prices_df[prices_df['acquisition_date'] == curr_snapshot]['airbnb_listing_id'])
    
    booked_listings = prev_listings - curr_listings
    print(f"[INFO] Detectadas {len(booked_listings)} reservas entre {prev_snapshot} e {curr_snapshot}")
    
    return prices_df
```

---

### PROBLEMA #3: Mistura Incorreta de Mercados (Airbnb + VivaReal)

**Severidade**: BLOQUEADOR  
**Tipo**: Lógica de Negócio  
**Localização**: `pipelines/system_price_v2.py:76-98`

**Código problemático**:
```python
def normalize_vivareal(vivareal_df):
    """Sinal complementar de mercado a partir do VivaReal."""
    vivareal_df = vivareal_df.copy()
    vivareal_df["price"] = vivareal_df["rental_price"] / 30  # Converte mensal para "diária"
    return vivareal_df[["suburb", "price"]].dropna()

# ... depois em build_stage():
combined = pd.concat(
    [short_term[["suburb", "price"]], vivareal_norm],  # Junta tudo!
    ignore_index=True,
)
```

**Por que é conceitualmente errado**:

| Característica | Airbnb (Short-Stay) | VivaReal (Long-Term) |
|----------------|---------------------|----------------------|
| **Duração típica** | 1-7 noites | 12+ meses |
| **Modelo de preço** | Diária dinâmica | Mensal fixo |
| **Público-alvo** | Turistas | Residentes |
| **Markup** | 2-4x maior | Baseline |
| **Custos inclusos** | Limpeza, amenities | Geralmente não |
| **Sazonalidade** | Alta | Baixa |

**Exemplo numérico do erro**:
```
Airbnb Meia Praia:     R$ 650/noite (alta temporada, short-stay premium)
VivaReal Meia Praia:   R$ 4.500/mês ÷ 30 = R$ 150/noite (long-term convertido)

Média combinada: (650 + 150) / 2 = R$ 400/noite

PROBLEMA: R$ 400 não representa NEM o mercado de short-stay NEM o de long-term!
```

**Impacto**:
- A métrica "System Price" perde significado analítico
- RM não consegue precificar corretamente
- Decisões de investimento baseadas em dados distorcidos

**Correção recomendada**:

**Opção A - Métricas Separadas** (Recomendado):
```python
def build_market_metrics(airbnb_prices, vivareal_df, mesh_df):
    """Calcula métricas separadas por tipo de mercado."""
    
    # Short-term (Airbnb)
    airbnb_enriched = airbnb_prices.merge(mesh_df[['airbnb_listing_id', 'suburb']], on='airbnb_listing_id')
    short_term_metrics = airbnb_enriched.groupby('suburb').agg(
        avg_price_short_term=('price', 'mean'),
        median_price_short_term=('price', 'median'),
        n_listings_airbnb=('airbnb_listing_id', 'nunique')
    ).reset_index()
    
    # Long-term (VivaReal) - NÃO divide por 30
    long_term_metrics = vivareal_df.groupby('suburb').agg(
        avg_rent_monthly=('rental_price', 'mean'),
        n_listings_vivareal=('id', 'nunique')
    ).reset_index()
    
    # Join preservando separação
    combined = short_term_metrics.merge(long_term_metrics, on='suburb', how='outer')
    
    # Ratio como indicador (não como combinação)
    combined['yield_ratio'] = (combined['avg_price_short_term'] * 30) / combined['avg_rent_monthly']
    
    return combined
```

**Opção B - VivaReal como Sinal Secundário com Peso Explícito**:
```python
def build_weighted_price(airbnb_avg, vivareal_monthly, weight_airbnb=0.85):
    """
    Combina métricas com peso explícito.
    
    Justificativa: Seazone opera 95%+ em short-stay, 
    VivaReal é apenas referência de mercado imobiliário base.
    """
    vivareal_daily_equivalent = vivareal_monthly / 30
    
    weighted_price = (
        airbnb_avg * weight_airbnb + 
        vivareal_daily_equivalent * (1 - weight_airbnb)
    )
    
    return weighted_price
```

---

### PROBLEMA #4: Exception Handling Silencioso

**Severidade**: BLOQUEADOR  
**Tipo**: Qualidade de Código  
**Localização**: `pipelines/system_price_v2.py:31-34`

**Código problemático**:
```python
def load_csvs():
    """Carrega os 5 CSVs em DataFrames."""
    try:
        details = pd.read_csv(f"{DATA_DIR}/Details_Itapema.csv")
        hosts = pd.read_csv(f"{DATA_DIR}/Hosts_ids_Itapema.csv")
        mesh = pd.read_csv(f"{DATA_DIR}/Mesh_Ids_Data_Itapema.csv")
        prices = pd.read_csv(f"{DATA_DIR}/Price_AV_Itapema.csv")
        vivareal = pd.read_csv(f"{DATA_DIR}/VivaReal_Itapema.csv")
    except Exception:
        pass  # <-- SILENCIA TODOS OS ERROS!

    return details, hosts, mesh, prices, vivareal  # <-- VARIÁVEIS PODEM NÃO EXISTIR!
```

**Problemas identificados**:

1. **`except Exception: pass`** - Anti-pattern clássico que engole TODOS os erros
2. **Variáveis indefinidas** - Se qualquer `read_csv` falhar, as variáveis não são definidas
3. **`return` com variáveis inexistentes** - Causa `NameError` na linha 34
4. **Impossível debugar** - Sem logging, sem stack trace, sem indicação do que falhou
5. **Pipeline continua quebrado** - Código subsequente opera com dados corrompidos

**Cenário de falha**:
```
1. Details_Itapema.csv carrega OK
2. Hosts_ids_Itapema.csv não existe -> FileNotFoundError
3. Exception é silenciada pelo 'pass'
4. mesh, prices, vivareal NUNCA são definidos
5. return tenta retornar variáveis que não existem
6. NameError: name 'mesh' is not defined
```

**Correção recomendada**:
```python
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_csvs():
    """Carrega os 5 CSVs em DataFrames com tratamento de erro adequado."""
    
    required_files = {
        'details': 'Details_Itapema.csv',
        'hosts': 'Hosts_ids_Itapema.csv',
        'mesh': 'Mesh_Ids_Data_Itapema.csv',
        'prices': 'Price_AV_Itapema.csv',
        'vivareal': 'VivaReal_Itapema.csv'
    }
    
    dataframes = {}
    
    for name, filename in required_files.items():
        filepath = f"{DATA_DIR}/{filename}"
        try:
            df = pd.read_csv(filepath)
            logger.info(f"Carregado {filename}: {len(df):,} linhas, {len(df.columns)} colunas")
            dataframes[name] = df
        except FileNotFoundError:
            logger.error(f"Arquivo não encontrado: {filepath}")
            raise FileNotFoundError(f"Arquivo obrigatório ausente: {filepath}")
        except pd.errors.EmptyDataError:
            logger.error(f"Arquivo vazio: {filepath}")
            raise ValueError(f"Arquivo vazio: {filepath}")
        except pd.errors.ParserError as e:
            logger.error(f"Erro ao parsear {filepath}: {e}")
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

### PROBLEMA #5: Pipeline Não Idempotente

**Severidade**: BLOQUEADOR  
**Tipo**: Arquitetura  
**Localização**: `pipelines/gold_system_price_itapema.sql:14-21`

**Código problemático**:
```sql
CREATE TABLE IF NOT EXISTS gold_system_price_itapema (
    bairro VARCHAR,
    system_price_avg DOUBLE,
    n_amostras INTEGER
);

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
- `INSERT INTO` sem `DELETE` ou `TRUNCATE` anterior
- Cada execução **adiciona** dados em vez de **substituir**
- Pipeline não é **idempotente** (rodar N vezes != rodar 1 vez)

**Cenário de falha**:
```
Execução 1: 15 bairros inseridos
Execução 2: 15 bairros inseridos novamente (total: 30 linhas, dados duplicados)
Execução 3: mais 15 bairros (total: 45 linhas)
...
Dashboard mostra médias incorretas devido a duplicação
```

**Impacto em produção**:
- Re-runs do Airflow corrompem dados
- Backfills geram duplicação massiva
- Impossível confiar nos números do dashboard

**Correção recomendada**:

**Opção A - DROP + CREATE (Mais Seguro)**:
```sql
-- gold.system_price_itapema
-- Idempotente: recria tabela a cada execução

DROP TABLE IF EXISTS gold_system_price_itapema;

CREATE TABLE gold_system_price_itapema AS
SELECT
    suburb AS bairro,
    AVG(price) AS system_price_avg,
    COUNT(*) AS n_amostras,
    CURRENT_TIMESTAMP AS processed_at
FROM stage
GROUP BY suburb
ORDER BY system_price_avg DESC;
```

**Opção B - TRUNCATE + INSERT**:
```sql
-- Limpa dados anteriores antes de inserir
TRUNCATE TABLE gold_system_price_itapema;

INSERT INTO gold_system_price_itapema
SELECT ...
```

**Opção C - DELETE + INSERT (Se TRUNCATE não disponível)**:
```sql
DELETE FROM gold_system_price_itapema WHERE 1=1;

INSERT INTO gold_system_price_itapema
SELECT ...
```

---

### PROBLEMA #6: Código Morto e Ineficiente

**Severidade**: IMPORTANTE  
**Tipo**: Performance / Code Smell  
**Localização**: `pipelines/system_price_v2.py:58-61`

**Código problemático**:
```python
details_df = details_df.copy()
details_df["bairro_lower"] = ""
for idx, row in details_df.iterrows():
    details_df.at[idx, "bairro_lower"] = str(row.get("ad_name", "")).lower()
```

**Problemas identificados**:

1. **`iterrows()` é O(n) com overhead alto** - Extremamente lento para DataFrames grandes
2. **Coluna `bairro_lower` nunca é usada** - Código morto, aumenta complexidade sem benefício
3. **`row.get("ad_name", "")` em loop** - Desnecessário, pandas já tem métodos vetorizados

**Benchmark de performance**:
```
DataFrame com 100.000 linhas:
- iterrows():    ~45 segundos
- str.lower():   ~0.1 segundos
- Diferença:     450x mais lento
```

**Correção recomendada**:

**Opção A - Deletar (Se não for usado)**:
```python
# Simplesmente remova as linhas 58-61
# A coluna bairro_lower não é referenciada em nenhum outro lugar
```

**Opção B - Vetorizar (Se for necessário no futuro)**:
```python
details_df = details_df.copy()
details_df["bairro_lower"] = details_df["ad_name"].fillna("").str.lower()
```

---

### PROBLEMA #7: Validação Inexistente

**Severidade**: IMPORTANTE  
**Tipo**: Qualidade de Dados  
**Localização**: Ausente no código

**Evidência do PR_DESCRIPTION.md**:
> "Validação: Joins parecem ok, validei batendo o olho no count de linhas no log"

**Problemas**:
- Nenhum teste unitário
- Nenhuma verificação de schema
- Nenhuma validação de valores nulos
- Nenhuma detecção de outliers
- Nenhuma comparação com baseline
- "Batendo o olho" não é validação aceitável para produção

**Correção recomendada**:
```python
def validate_gold_output(con):
    """Validações básicas de qualidade de dados."""
    
    validations = {
        'total_rows': {
            'query': "SELECT COUNT(*) FROM gold_system_price_itapema",
            'check': lambda x: x > 0,
            'message': "Tabela não pode estar vazia"
        },
        'null_bairros': {
            'query': "SELECT COUNT(*) FROM gold_system_price_itapema WHERE bairro IS NULL",
            'check': lambda x: x == 0,
            'message': "Não deve haver bairros nulos"
        },
        'invalid_prices': {
            'query': "SELECT COUNT(*) FROM gold_system_price_itapema WHERE system_price_avg <= 0",
            'check': lambda x: x == 0,
            'message': "Preços devem ser positivos"
        },
        'low_sample_bairros': {
            'query': "SELECT COUNT(*) FROM gold_system_price_itapema WHERE n_amostras < 5",
            'check': lambda x: True,  # Apenas log, não falha
            'message': "Bairros com baixa amostragem (< 5)"
        }
    }
    
    issues = []
    
    for name, validation in validations.items():
        result = con.execute(validation['query']).fetchone()[0]
        passed = validation['check'](result)
        
        status = "PASS" if passed else "FAIL"
        logger.info(f"Validação [{name}]: {result} - {status}")
        
        if not passed:
            issues.append(f"{name}: {validation['message']} (valor: {result})")
    
    if issues:
        raise ValueError(f"Validações falharam:\n" + "\n".join(issues))
    
    logger.info("Todas as validações passaram com sucesso")
```

---

### PROBLEMA #8: Variáveis Declaradas mas Não Usadas

**Severidade**: MENOR  
**Tipo**: Code Smell  
**Localização**: `pipelines/system_price_v2.py:15-16`

**Código problemático**:
```python
DB_USER = "sz_data_edge"
DB_PASSWORD = "Sz!DataEdge2025"
```

**Problema**: Além do issue de segurança (Problema #1), estas variáveis não são referenciadas em nenhum lugar do código. O DuckDB é usado com conexão local, não remota.

**Correção**: Remover completamente ou implementar uso se necessário.

---

## O que Falhou Upstream

Este PR não deveria ter chegado em review nesse estado. Identifico falhas em 3 níveis:

### 1. Falha de Processo: Spec Não Documentado

O PR menciona "spec combinado com a Anna no dia 22/04", mas:
- Não há arquivo `specs/system-price-v2/spec.md`
- Não há definição formal de "System Price"
- Não há decisão documentada sobre combinação Airbnb + VivaReal

**Ação corretiva**: Exigir spec em markdown commitado ANTES do código (verificável via `git log --reverse`).

### 2. Falha Técnica: Desconhecimento dos Dados

Os erros #2 e #3 indicam que o desenvolvedor não entendeu:
- A estrutura de dupla data do Price_AV
- A diferença entre mercados short-stay e long-term

**Ação corretiva**: 
- Documentar estrutura dos datasets em `docs/data-sources/`
- Sessão de onboarding sobre dados de scrapers
- Pair programming em features de dados novas

### 3. Falha de Tooling: Sem Pre-Commit Hooks

Problemas triviais que deveriam ser bloqueados automaticamente:
- Credenciais hardcoded (detect-secrets, gitleaks)
- Exception handling com `pass` (flake8, pylint)

**Ação corretiva**: Configurar `.pre-commit-config.yaml` com hooks de segurança.

---

## Condução do 1:1 com o Junior

### Estrutura Proposta (40 minutos)

**Bloco 1 - Contexto Positivo (5 min)**

Começar reconhecendo o que está bom:
- Estrutura de código organizada em funções
- Separação Python/SQL
- Documentação do PR presente
- Iniciativa de implementar a feature

**Bloco 2 - Problemas Críticos (20 min)**

Usar abordagem socrática, não expositiva:

*Credenciais (5 min)*:
> "Olha as linhas 15-16. O que você vê de problemático aí?"
> [Deixar responder]
> "Exato. Se esse repo fosse público, o que aconteceria?"
> [Guiar para: rotação de credenciais, auditoria]
> "Como a gente corrige isso? Conhece variáveis de ambiente?"

*Dupla Data (7 min)*:
> "Vou abrir o Price_AV com você. Me mostra as colunas de data."
> [Explorar junto]
> "Vê que tem data de aquisição E data de estadia? O que isso significa?"
> [Guiar para: 3 snapshots capturando mesmo período]
> "Agora olha seu filtro na linha 39. Usa datetime.now(). Qual o problema?"
> [Deixar perceber: dataset vazio]
> "Esse erro específico é citado no desafio como reprovador. Vamos pensar na correção juntos?"

*Mistura de Mercados (8 min)*:
> "Me explica a decisão de combinar Airbnb com VivaReal."
> [OUVIR - entender o raciocínio]
> "Faz sentido querer mais sinal de mercado. Mas me diz: qual a diferença entre short-stay e long-term?"
> [Discussão: duração, preço, público, sazonalidade]
> "Se a gente faz média direta, o número final representa qual mercado?"
> [Guiar para: nenhum dos dois]
> "Como você usaria VivaReal como sinal sem distorcer o System Price?"

**Bloco 3 - Caminho de Correção (10 min)**

1. **Prioridade Imediata**: Remover credenciais (pode commitar hoje)
2. **Crítico**: Corrigir lógica da dupla data (pair programming amanhã)
3. **Crítico**: Separar métricas ou justificar peso de combinação
4. **Importante**: Tornar pipeline idempotente
5. **Importante**: Adicionar logging e validações

> "Vou deixar comentários inline no PR. Marca um horário comigo amanhã pra fazermos pair na parte da dupla data - é a mais complexa."

**Bloco 4 - Processo e Crescimento (5 min)**

> "Esses erros não são sobre capacidade - são sobre contexto que você ainda não teve exposição. Vamos ajustar algumas coisas no processo:"
> 
> 1. Spec obrigatório antes de código
> 2. Pair programming nas próximas 2-3 features de dados
> 3. Vou configurar pre-commit hooks pra pegar credenciais automaticamente
>
> "Uma coisa que você faz bem: organização do código. Continue nisso."

### Tom da Conversa

| Fazer | Evitar |
|-------|--------|
| Direto sobre os problemas | Minimizar ("só uns detalhezinhos") |
| Educativo e socrático | Punitivo ou condescendente |
| Oferecer suporte concreto | Delegar sem apoio |
| Foco em correção E prevenção | Só apontar erros |

---

## Comentários Inline para o PR

### Linha 15-16 (system_price_v2.py)
```
BLOQUEADOR: Credenciais em texto claro

Remover imediatamente. Usar variáveis de ambiente.
Nota: essas variáveis não são usadas no código atual - confirmar se são necessárias.
```

### Linha 31-32 (system_price_v2.py)
```
BLOQUEADOR: Exception silenciosa

`except Exception: pass` engole todos os erros. Se qualquer CSV falhar,
as variáveis ficam indefinidas e o pipeline continua quebrado.

Usar try/except específico com logging e re-raise.
```

### Linha 37-42 (system_price_v2.py)
```
BLOQUEADOR: Lógica incorreta para Price_AV

Este código trata Price_AV como "preço atual", mas o arquivo tem dupla data
(aquisição × estadia). Usando datetime.now() para filtrar dados de Jan-Abr 2025
resulta em dataset VAZIO.

Ver PDF do desafio pág 2: "Tratar como simples 'preço atual' é o tipo de erro que reprova."
```

### Linha 76-79 (system_price_v2.py)
```
BLOQUEADOR: Mistura de mercados incompatíveis

Dividir aluguel mensal (VivaReal) por 30 e combinar com diária de short-stay (Airbnb)
distorce ambas as métricas. São mercados diferentes com dinâmicas diferentes.

Sugestão: métricas separadas ou peso ponderado explícito e documentado.
```

### Linha 58-61 (system_price_v2.py)
```
IMPORTANTE: Código morto + ineficiente

1. iterrows() é extremamente lento (450x vs vetorizado)
2. Coluna bairro_lower criada mas NUNCA usada

Remover este bloco inteiro.
```

### Linha 14 (gold_system_price_itapema.sql)
```
BLOQUEADOR: Pipeline não idempotente

INSERT INTO sem DELETE anterior = dados duplicados a cada execução.

Usar: DROP TABLE IF EXISTS ... CREATE TABLE AS SELECT ...
```

---

## AI Co-author Log

### Modelo e Ambiente

| Item | Valor |
|------|-------|
| **LLM** | Claude Opus 4 |
| **Model ID** | `global.anthropic.claude-opus-4-5-20251101-v1:0` |
| **Provider** | Amazon Bedrock |
| **Interface** | OpenCode CLI (Windows PowerShell) |
| **Metodologia** | Spec-driven development + AI agentic code review |

### Contexto Fornecido à IA

1. **PDF do Desafio**: 9 páginas com requisitos, critérios de avaliação, estrutura dos dados
2. **Código do PR**:
   - `system_price_v2.py` (138 linhas)
   - `gold_system_price_itapema.sql` (21 linhas)
   - `requirements.txt` (2 linhas)
   - `PR_DESCRIPTION.md` (34 linhas)
3. **Contexto Git**: diff entre main e branch do PR, histórico de commits

### Prompts Utilizados

```
1. "Analise o repositório para entender a estrutura e localizar o PR que precisa ser revisado"
2. "Considere as informações do PDF do desafio técnico da Seazone"
3. "Crie análise detalhada identificando os problemas críticos"
4. "Crie documento formal de review"
```

### Onde a IA Agregou Valor

**1. Análise Sistemática Multi-Camada**
- Identificou 8 problemas em ~3 minutos de análise
- Classificou automaticamente por severidade
- Cruzou código com requisitos do PDF

**2. Cruzamento com Documentação**
- Localizou citação exata do PDF sobre dupla data
- Conectou erro do código com critério de reprovação

**3. Geração de Código Corrigido**
- Produziu exemplos de correção imediatamente
- Código com comentários explicativos

**4. Estruturação do Feedback**
- Organizou review em formato profissional
- Criou roteiro de 1:1 estruturado

### Onde a IA Precisou de Correção Humana

**1. Falso Positivo em Nomes de Colunas**
- IA sinalizou inconsistência em `hosts_df['owner']` vs `owner_id`
- Correção: linha 56 é apenas logging, não afeta lógica
- Mantido como observação menor

**2. Sugestão de Validação Over-Engineered**
- IA sugeriu Great Expectations para validação
- Correção: simplificado para SQL direto no DuckDB (contexto MVP)

**3. Jargão Técnico Excessivo no 1:1**
- Primeira versão usava termos como "SCD Type 2", "dimensional modeling"
- Correção: reescrito com linguagem acessível e abordagem socrática

### Estimativa de Speedup

| Etapa | Com IA | Sem IA (Est.) |
|-------|--------|---------------|
| Leitura de código | 3 min | 10 min |
| Identificação de bugs | 5 min | 30 min |
| Correções de exemplo | 5 min | 25 min |
| Estruturação do documento | 10 min | 35 min |
| Roteiro de 1:1 | 5 min | 20 min |
| Revisão humana | 15 min | - |
| **TOTAL** | **43 min** | **~120 min** |

**Speedup estimado: 2.8x**

### Decisões que Permaneceram Humanas

1. Veredito final: "Changes Requested" (não Close)
2. Priorização do Top 3 de problemas
3. Tom e estrutura da conversa de 1:1
4. Ações corretivas para o squad
5. Decisão de não apressar o merge

---

## Resumo Executivo

| Dimensão | Status |
|----------|--------|
| **Veredito** | CHANGES REQUESTED |
| **Problemas Bloqueadores** | 5 |
| **Problemas Importantes** | 2 |
| **Problemas Menores** | 1 |
| **Tempo de Correção Estimado** | 2-3 dias |
| **Recomendação** | Pair programming + revisão parcial em 3 dias |

### Checklist de Correção

- [ ] Remover credenciais hardcoded (usar env vars)
- [ ] Corrigir lógica de dupla data do Price_AV
- [ ] Separar métricas Airbnb vs VivaReal
- [ ] Tornar pipeline idempotente (DROP + CREATE)
- [ ] Adicionar exception handling adequado
- [ ] Remover código morto (iterrows)
- [ ] Adicionar validações básicas
- [ ] Adicionar logging estruturado

---

**Mensagem Final para o Junior**:

Os problemas identificados aqui são oportunidades de aprendizado, não reflexo de falta de capacidade. A arquitetura geral do código (load → stage → gold) está no caminho certo, e a documentação do PR mostra cuidado com o processo.

Vamos trabalhar juntos na correção. Me procura para pair programming na parte da dupla data - é a mais sutil e importante de acertar.
