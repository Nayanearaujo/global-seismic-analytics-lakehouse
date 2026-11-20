# Parte 1 — Ingestão histórica do USGS e camada Bronze

A Aula 2 apresentou a API do USGS, o particionamento mensal da landing e a ingestão com Auto Loader. No projeto, o notebook de extração também confere a contagem da fonte e sinaliza meses que falharam. A Bronze preserva o array `features` para o `explode` na Silver.

## Execução

1. Crie o catálogo `sismos`, o schema `bronze` e os volumes `landing` e `checkpoints` com o SQL de setup da Aula 1.
2. Execute `notebooks/01_extract_usgs_landing.py`. Para cada mês de 2025, o notebook consulta `/count` e `/query` com os mesmos filtros, incluindo `minmagnitude=1.0` e `eventtype=earthquake`. O primeiro instante e o último milissegundo do mês são explícitos em UTC, pois os dois limites do USGS são inclusivos. A extração usa janelas mensais. Se uma janela exceder 20.000 eventos, ela falha e requer subdivisão ou paginação.
3. Execute `notebooks/02_bronze_autoloader.py` após o sucesso da extração. O Auto Loader processa os arquivos disponíveis, grava os documentos em `sismos.bronze.terremotos_raw` e encerra. Reutilize o checkpoint nas próximas execuções. A landing histórica preserva os arquivos existentes. Se a fonte revisar um mês já publicado, trate a revisão antes de reprocessá-lo.

[Documentação da API do USGS](https://earthquake.usgs.gov/fdsnws/event/1/)

## Reconciliação da Bronze

A extração confere o total retornado por `/count` com o tamanho de `features` e com `metadata.count` antes de salvar cada arquivo. Na Bronze, a consulta abaixo compara a quantidade ingerida com esse total registrado no GeoJSON e mostra meses ausentes ou repetidos. A carga esperada tem 12 meses com status `OK`.

```sql
WITH meses AS (
    SELECT explode(sequence(1, 12)) AS mes
),
bronze AS (
    SELECT
        CAST(mes AS INT) AS mes,
        COUNT(*) AS documentos,
        SUM(size(features)) AS eventos,
        SUM(CAST(metadata.count AS BIGINT)) AS eventos_usgs
    FROM sismos.bronze.terremotos_raw
    WHERE CAST(ano AS INT) = 2025
    GROUP BY CAST(mes AS INT)
)
SELECT
    meses.mes,
    COALESCE(bronze.documentos, 0) AS documentos,
    bronze.eventos,
    bronze.eventos_usgs,
    CASE
        WHEN bronze.documentos = 1 AND bronze.eventos = bronze.eventos_usgs THEN 'OK'
        ELSE 'REVISAR'
    END AS status
FROM meses
LEFT JOIN bronze USING (mes)
ORDER BY meses.mes;
```

Depois de conferir os 12 meses, calcule o total carregado.

```sql
SELECT SUM(size(features)) AS total_eventos
FROM sismos.bronze.terremotos_raw
WHERE CAST(ano AS INT) = 2025;
```
