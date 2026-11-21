# Global Seismic Analytics Lakehouse

## Como rodar

1. Crie o catálogo, os schemas e os volumes com a **parte 2** do [SQL de configuração do Unity Catalog](notebooks/00_setup_and_delta_fundamentals.sql).
2. Antes de baixar o histórico, confirme que o workspace consegue acessar a API com o [teste de conectividade do USGS](notebooks/00_validate_usgs_api.py).
3. Rode a extração uma vez para `usgs` e outra para `emsc`, com `ano=2025`. Confira a saída dos 12 meses no [notebook de extração](notebooks/01_extract_usgs_landing.py).
4. Carregue a Bronze para cada fonte. Em uma tabela vazia, a carga de 2025 deve gerar 12 linhas por catálogo. [Notebook de carga](notebooks/02_bronze_autoloader.py)
5. Confira as contagens mensais e o histórico Delta no [notebook de evidências](notebooks/evidencias_desafio_02.py).

Os caminhos de armazenamento, as consultas SQL e os prints estão no [guia da Aula 2](docs/parte_1_ingestao_bronze.md). O primeiro teste de ingestão está registrado no [notebook inicial do USGS](notebooks/ingestao_inicial_usgs.ipynb).

## Sobre o projeto

Projeto da trilha de Engenharia de Dados Pleno da EmpregaDados. O pipeline consulta os catálogos sísmicos do USGS e do EMSC e carrega os dados na camada Bronze do Databricks Free Edition. O recorte da Aula 2 vai de janeiro a dezembro de 2025, com magnitude mínima de 2,5.

## Tecnologias usadas

| Tecnologia | Uso no projeto |
|---|---|
| Databricks Free Edition | Execução dos notebooks e consultas ao histórico Delta. |
| Python e Requests | Consumo das APIs FDSN, conferência das contagens e gravação dos arquivos mensais. |
| Unity Catalog e Volumes | Organização do catálogo `sismos`, da Landing e dos checkpoints. |
| Auto Loader e Spark | Leitura incremental dos arquivos e validação das contagens por fonte e mês. |
| Delta Lake | Persistência das tabelas Bronze e registro das operações de carga. |
| SQL | Comparação mensal dos catálogos e consulta ao histórico das tabelas. |

## Como os dados chegam à Bronze

A extração consulta cada mês em UTC e compara o total informado por `/count` com o número de eventos em `features`. Quando as contagens batem, a resposta da API é gravada na Landing, na pasta da fonte.

O Auto Loader lê os arquivos mensais e grava em `sismos.bronze.terremotos_raw` ou `sismos.bronze.emsc_raw`. Cada linha da Bronze representa um arquivo mensal inteiro e preserva seu array `features`. Cada tabela tem seu próprio checkpoint para retomar a carga a partir dos arquivos já processados.

A Silver está prevista para a Aula 3, com tipagem e deduplicação no nível de evento. A Gold reunirá as agregações para análise de risco sísmico nas Aulas 3 e 4.

## Resultados da execução de 20/11/2026

| Fonte | Arquivos | Eventos na Bronze | Meses conferidos |
|---|---:|---:|---:|
| USGS | 12 | 29.312 | 12 de 12 |
| EMSC | 12 | 79.492 | 12 de 12 |

Nos 24 pares de fonte e mês, a Bronze tinha um arquivo e a mesma contagem de eventos registrada na extração. Ao rodar a carga do EMSC novamente com o mesmo checkpoint, o Auto Loader gravou **zero linhas novas** e a tabela Delta permaneceu na **versão 2**. [Entrega do Desafio 2](https://github.com/ckoliveiraa/lakehouse-sismico/issues/3)

## Fontes

- [USGS Earthquake Hazards Program](https://earthquake.usgs.gov/fdsnws/event/1/)
- [EMSC SeismicPortal, CC BY 4.0](https://seismicportal.eu/fdsn-wsevent.html)
- [Guia da Aula 2](https://ckoliveiraa.github.io/lakehouse-sismico/aula-2.html)

## Padrão de commits

Use `tipo(escopo): descrição curta`, em português, com um verbo no presente. Mantenha uma mudança por commit. Por exemplo, `fix(bronze): corrige a leitura dos arquivos mensais`.

| Tipo | Uso |
|---|---|
| `feat` | Nova funcionalidade |
| `fix` | Correção de comportamento |
| `docs` | Documentação |
| `test` | Testes |
| `chore` | Manutenção do repositório |

## Autora

[Nayane Oliveira](https://github.com/Nayanearaujo)
