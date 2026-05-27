# Desafio Prático AI Builder - Seazone

Este repositório contém a solução completa para o Desafio Prático AI Builder da Seazone. O projeto foi desenvolvido seguindo rigorosamente a metodologia Spec-Driven Development utilizando IA Agentic (AI Builder) e as melhores práticas de Engenharia de Dados.

## Tecnologias Utilizadas

Conforme os requisitos inegociáveis do desafio, as seguintes tecnologias foram utilizadas:

- **Gerenciador de Pacotes e Ambiente**: uv
- **Linguagem**: Python
- **Processamento SQL/Datalake Local**: DuckDB
- **Wrangling e EDA**: Polars

## Preparação do Ambiente

### Pré-requisitos

Para que o código funcione corretamente, os arquivos CSV originais da cidade de Itapema devem ser colocados dentro de uma pasta chamada `data/` na raiz deste projeto.

### Instalação

Certifique-se de ter o `uv` instalado em sua máquina. Caso não tenha, instale seguindo a documentação oficial ou via pip:

```bash
pip install uv
```

Na raiz do projeto, instale as dependências isoladas lendo o arquivo `pyproject.toml`:

```bash
uv sync
```

## Execução do Projeto

A arquitetura foi dividida em três etapas lógicas. Execute os comandos abaixo estritamente nesta ordem:

### A. Ingestão e Modelagem Principal (DuckDB)

Lê os CSVs simulando um datalake, aplica a lógica de "sumiço" nos snapshots para identificar reservas reais e consolida o faturamento.

```bash
uv run analysis/main.py
```

### B. Análise Exploratória e Discovery (Polars)

Lê os dados modelados da etapa anterior e responde às perguntas de negócio (melhor localização e melhor perfil de imóvel).

```bash
uv run analysis/discovery.py
```

### C. Projeção Financeira e ROI

Calcula a viabilidade financeira e o lucro projetado para a construção de um prédio de 50 apartamentos (2025-2027).

```bash
uv run analysis/roi_calculator.py
```

## Estrutura do Repositório

- **specs/**: Contém os arquivos `spec.md`, `plan.md` e `constitution.md` das Partes 1 e 2, atestando o planejamento antes do código.
- **analysis/**: Scripts Python gerenciados pelo uv (`main.py`, `discovery.py`, `roi_calculator.py`) e os .csv de output gerados.
- **ai-sessions/**: Logs obrigatórios das sessões da IA (Discovery, Modelagem e ROI), demonstrando coautoria e correções.
- **reviews/**: Veredito e feedback de Code Review do squad (Parte 3).
- **plano-squad/**: Diagnóstico e planejamento de liderança técnica (30/60/90 dias) e plano de ação de underperformance (Parte 4).
- **report/**: PDF final consolidando todas as etapas e defesas arquiteturais.
