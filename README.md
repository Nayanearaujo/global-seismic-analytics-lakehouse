# Global Seismic Analytics Lakehouse

Pipeline de dados sísmicos do USGS e do EMSC no Databricks Free Edition. A Aula 2 cobre o histórico de janeiro a dezembro de 2025, com magnitude mínima de 2,5, da API FDSN até a Bronze.

## Como executar

| Ordem | Arquivo | O que fazer |
|---|---|---|
| 1 | [Setup do Unity Catalog](notebooks/00_setup_and_delta_fundamentals.sql) | Execute a parte 2 do SQL para criar o catálogo, os schemas e os volumes. As outras partes são demonstrações da Aula 1. |
| 2 | [Teste de conectividade do USGS](notebooks/00_validate_usgs_api.py) | Execute a consulta de contagem antes de carregar o histórico. |
| 3 | [Extração](notebooks/01_extract_usgs_landing.py) | Execute para `usgs` e `emsc`, com `ano=2025`. A saída registra a contagem conferida de cada mês. |
| 4 | [Carga Bronze](notebooks/02_bronze_autoloader.py) | Execute para as duas fontes. Na primeira carga, espere 12 linhas por fonte. |
| 5 | [Evidências do Desafio 2](notebooks/03_desafio_02_evidencias.py) | Consulte as contagens mensais, a reconciliação e o histórico Delta. |

O [guia da Aula 2](docs/parte_1_ingestao_bronze.md) detalha os caminhos, as consultas SQL e a execução registrada. A pasta [`notebooks/exploratory`](notebooks/exploratory) guarda a exploração inicial do USGS. O notebook de evidências pertence à Aula 2. O arquivo da Silver pertence à Aula 3.

## Arquitetura

| Camada | Conteúdo | Estado |
|---|---|---|
| Landing | Respostas das APIs em arquivos mensais, separadas por fonte. | Validada |
| Bronze | `sismos.bronze.terremotos_raw` e `sismos.bronze.emsc_raw`. Cada linha representa um documento mensal e preserva o array `features`. | Validada |
| Silver | Tipagem e deduplicação no grão de evento, com `MERGE`. | Prevista para a Aula 3 |
| Gold | Agregações para análise de risco sísmico. | Prevista para as Aulas 3 e 4 |

A extração usa janelas mensais em UTC e compara `/count` com o tamanho de `features` antes de gravar. O Auto Loader usa um checkpoint por tabela, com o schema inferido em um subdiretório próprio. A carga é retomada com o checkpoint da mesma fonte.

## Validação de 20/11/2026

| Fonte | Arquivos mensais | Eventos na Bronze | Meses aprovados |
|---|---:|---:|---:|
| USGS | 12 | 29.312 | 12 de 12 |
| EMSC | 12 | 79.492 | 12 de 12 |

As 24 combinações de fonte e mês bateram com as contagens registradas na extração. Na reexecução da Bronze do EMSC com o mesmo checkpoint, foram gravadas zero linhas novas e o histórico Delta permaneceu na versão 2. [Entrega e prints](https://github.com/ckoliveiraa/lakehouse-sismico/issues/3)

## Fontes

- [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/fdsnws/event/1/)
- [EMSC SeismicPortal, CC BY 4.0](https://seismicportal.eu/fdsn-wsevent.html)
- [Guia da Aula 2](https://ckoliveiraa.github.io/lakehouse-sismico/aula-2.html)

## Padrão de commits

Use `tipo(escopo): descrição curta`, em português, com um verbo no presente. Faça um commit por mudança lógica. Se precisar explicar a motivação ou registrar uma validação, use o corpo do commit.

| Tipo | Quando usar | Exemplo |
|---|---|---|
| `feat` | Nova funcionalidade | `feat(bronze): ingere eventos com Auto Loader` |
| `fix` | Correção de comportamento | `fix(silver): corrige deduplicação por ID do USGS` |
| `docs` | Alteração na documentação | `docs(readme): documenta as camadas do lakehouse` |
| `test` | Adição ou ajuste de testes | `test(ingestao): cobre respostas vazias do USGS` |
| `chore` | Manutenção do repositório | `chore(git): atualiza arquivos ignorados` |
