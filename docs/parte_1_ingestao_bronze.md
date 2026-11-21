# Aula 2: USGS e EMSC na Bronze

O ano de 2025 é extraído em 12 janelas mensais UTC com magnitude mínima de 2,5. As duas fontes passam pelas mesmas funções e preservam o array `features` para a Silver.

| Fonte | Formato da API | Landing | Tabela Bronze e nome do checkpoint |
|---|---|---|---|
| USGS | `geojson` | `terremotos/ano=2025/mes=MM.geojson` | `terremotos_raw` |
| EMSC | `json` | `emsc/ano=2025/mes=MM.geojson` | `emsc_raw` |

1. No Databricks, crie o catálogo `sismos`, o schema `bronze` e os volumes `landing` e `checkpoints` executando a parte 2 do [SQL de setup](../notebooks/00_setup_and_delta_fundamentals.sql).
2. Execute `01_extract_usgs_landing.py` para cada fonte pelo widget `fonte`, com `ano=2025`. O notebook compara o `/count` com o número de eventos do `/query` em cada mês usando os mesmos filtros e encerra com erro se algum mês falhar. As janelas terminam no último milissegundo do mês para respeitar o limite inclusivo documentado pelo USGS. O código preserva os arquivos existentes e sinaliza revisões que alterem o conteúdo já publicado.
3. Execute `02_bronze_autoloader.py` para cada fonte. Cada execução processa os arquivos disponíveis, grava uma linha por documento e termina. Rode a Bronze do EMSC pela segunda vez com o mesmo checkpoint. A saída esperada é `0 linhas novas`.
4. Se o Databricks bloquear o USGS, o `landing_2025.zip` do professor pode ser extraído no volume `landing`, mantendo o caminho `terremotos/ano=2025/mes=MM.geojson`. Se o domínio do EMSC retornar `ConnectionError`, avise no grupo da turma conforme o guia.

## Consulta de contagem mensal

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
    ON m.mes = TRY_CAST(regexp_extract(d._source_file, 'mes=([0-9]+)', 1) AS INT)
GROUP BY m.mes
ORDER BY m.mes;
```

Cada catálogo tem cobertura, critérios de inclusão e revisões próprios. Os totais com o mesmo ano e a mesma magnitude mínima podem divergir. A reconciliação de completude é feita entre cada catálogo e sua própria Bronze.

## Reexecução e histórico Delta

Consulte o histórico após a primeira e a segunda carga do EMSC. Com os mesmos arquivos e o mesmo checkpoint, a reexecução deve retornar zero linhas novas e manter a versão Delta.

```sql
DESCRIBE HISTORY sismos.bronze.emsc_raw;
```

## Evidências da execução de 20/11/2026

O notebook de evidências compara a Bronze com as contagens da extração por fonte e mês. As **24 verificações** passaram, cada uma com um arquivo e a contagem esperada. Os totais foram **29.312 eventos no USGS** e **79.492 no EMSC**. Na reexecução do EMSC, a carga retornou **0 linhas novas** e a tabela permaneceu na **versão 2**.

[Notebook de evidências](../notebooks/03_desafio_02_evidencias.py) · [Entrega do Desafio 2](https://github.com/ckoliveiraa/lakehouse-sismico/issues/3)

### 1. Contagens mensais de USGS e EMSC

![Contagem mensal de eventos para USGS e EMSC](https://github.com/user-attachments/assets/d940db15-1ba4-417f-a448-9b9298d2cd70)

### 2. Reconciliação mensal com 24 verificações aprovadas

![Doze meses aprovados por fonte e zero divergências](https://github.com/user-attachments/assets/9bf1820b-323d-4383-bcbf-5a079c6cdaca)

### 3. Histórico Delta de `sismos.bronze.emsc_raw`

![Histórico Delta com as versões 0, 1 e 2 e microlotes de 10 e 2 linhas](https://github.com/user-attachments/assets/d8d8ddb6-79a7-44e2-9bb9-22c34eaaa6c4)

### 4. Reexecução do EMSC com zero linhas novas

![Saída da reexecução do EMSC com zero linhas novas](https://github.com/user-attachments/assets/e105153d-a81d-46f8-b608-5c88307adb3e)

## Fontes

[USGS](https://earthquake.usgs.gov/fdsnws/event/1/) · [EMSC SeismicPortal, CC BY 4.0](https://seismicportal.eu/fdsn-wsevent.html) · [Guia e desafio da Aula 2](https://ckoliveiraa.github.io/lakehouse-sismico/aula-2.html)
