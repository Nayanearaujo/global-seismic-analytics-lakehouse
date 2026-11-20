# Aula 2 — USGS e EMSC na Bronze

O ano de 2025 é extraído em 12 janelas mensais UTC com magnitude mínima de 2,5. As duas fontes passam pelas mesmas funções e preservam o array `features` para a Silver.

| Fonte | Formato da API | Landing | Tabela Bronze e nome do checkpoint |
|---|---|---|---|
| USGS | `geojson` | `terremotos/ano=2025/mes=MM.geojson` | `terremotos_raw` |
| EMSC | `json` | `emsc/ano=2025/mes=MM.geojson` | `emsc_raw` |

1. No Databricks, crie o catálogo `sismos`, o schema `bronze` e os volumes `landing` e `checkpoints` com o setup da Aula 1.
2. Execute `01_extract_usgs_landing.py` para cada fonte pelo widget `fonte`, com `ano=2025`. O notebook compara o `/count` com o número de eventos do `/query` em cada mês usando os mesmos filtros e encerra com erro se algum mês falhar. As janelas terminam no último milissegundo do mês para respeitar o limite inclusivo documentado pelo USGS. O código preserva os arquivos existentes e sinaliza revisões que alterem o conteúdo já publicado.
3. Execute `02_bronze_autoloader.py` para cada fonte. Cada execução processa os arquivos disponíveis, grava uma linha por documento e termina. Rode a Bronze do EMSC pela segunda vez com o mesmo checkpoint. A saída esperada é `0 linhas novas`.
4. Se o Databricks bloquear o USGS, o `landing_2025.zip` do professor pode ser extraído no volume landing, mantendo o caminho `terremotos/ano=2025/mes=MM.geojson`. Se o domínio do EMSC retornar `ConnectionError`, avise no grupo da turma conforme o guia.

## Evidências do desafio

A consulta compara os eventos mensais das duas fontes e mostra meses ausentes ou repetidos. Compare também os totais com o `/count` impresso pela extração. Os 29.265 eventos do USGS são a referência do snapshot da aula. Uma nova extração pode variar com as revisões do catálogo.

```sql
WITH meses AS (
    SELECT explode(sequence(1, 12)) AS mes
),
documentos AS (
    SELECT 'USGS' AS fonte, _source_file, size(features) AS eventos
    FROM sismos.bronze.terremotos_raw
    WHERE CAST(ano AS INT) = 2025
    UNION ALL
    SELECT 'EMSC' AS fonte, _source_file, size(features) AS eventos
    FROM sismos.bronze.emsc_raw
    WHERE CAST(ano AS INT) = 2025
)
SELECT
    m.mes,
    COUNT_IF(d.fonte = 'USGS') AS arquivos_usgs,
    SUM(CASE WHEN d.fonte = 'USGS' THEN d.eventos END) AS eventos_usgs,
    COUNT_IF(d.fonte = 'EMSC') AS arquivos_emsc,
    SUM(CASE WHEN d.fonte = 'EMSC' THEN d.eventos END) AS eventos_emsc
FROM meses m
LEFT JOIN documentos d
    ON m.mes = CAST(regexp_extract(d._source_file, 'mes=([0-9]+)', 1) AS INT)
GROUP BY m.mes
ORDER BY m.mes;
```

Cada catálogo tem cobertura, critérios de inclusão e revisões próprios. Os totais com o mesmo ano e a mesma magnitude mínima podem divergir. A reconciliação de completude é feita entre cada catálogo e sua própria Bronze.

Execute o histórico após a primeira e a segunda carga do EMSC. Registre a saída de zero linhas novas e compare os dois históricos para confirmar que a reexecução não acrescentou uma escrita com registros.

```sql
DESCRIBE HISTORY sismos.bronze.emsc_raw;
```

Fontes dos dados e requisitos da Aula 2. [USGS](https://earthquake.usgs.gov/fdsnws/event/1/) · [EMSC SeismicPortal, CC BY 4.0](https://seismicportal.eu/fdsn-wsevent.html) · [Guia e desafio da Aula 2](https://ckoliveiraa.github.io/lakehouse-sismico/aula-2.html)
