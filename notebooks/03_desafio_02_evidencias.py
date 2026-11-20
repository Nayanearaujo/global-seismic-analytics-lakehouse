# Databricks notebook source
# MAGIC %md
# MAGIC # Desafio 2 · USGS e EMSC na Bronze
# MAGIC Eventos de janeiro a dezembro de 2025, com magnitude mínima de 2,5.
# MAGIC
# MAGIC ## Diferenças de contrato entre USGS e EMSC
# MAGIC
# MAGIC `extract_year(source, year)` e `load_bronze(source)` reaproveitam o fluxo para os dois catálogos.
# MAGIC
# MAGIC | Aspecto | USGS | EMSC | Como o pipeline trata |
# MAGIC |---|---|---|---|
# MAGIC | Formato | `geojson` | `json` | A configuração da fonte define o formato de `/count` e `/query`. |
# MAGIC | Contagem e limite | `count` e `maxAllowed` | `count` | Confere a quantidade recebida com `/count` e verifica `maxAllowed` quando informado. |
# MAGIC | Janela mensal | Horários em UTC | Mesmo recorte | Cada consulta usa o primeiro instante e o último milissegundo do mês, com magnitude ≥ 2,5. |
# MAGIC | Campos de revisão e local | `updated`, `place` | `lastupdate`, `flynn_region` | A Bronze preserva o array `features` de cada fonte para tratamento na Silver. |
# MAGIC | Checkpoint | `checkpoints/terremotos_raw` | `checkpoints/emsc_raw` | Cada fluxo mantém seu próprio progresso e caminho de schema. |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Contagem mensal lado a lado
# MAGIC Cada arquivo mensal ocupa uma linha na Bronze. A contagem de eventos vem do tamanho de `features`.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH meses AS (
# MAGIC   SELECT explode(sequence(1, 12)) AS mes
# MAGIC ),
# MAGIC documentos AS (
# MAGIC   SELECT 'USGS' AS fonte, _source_file, size(features) AS eventos
# MAGIC   FROM sismos.bronze.terremotos_raw
# MAGIC   WHERE CAST(ano AS INT) = 2025
# MAGIC   UNION ALL
# MAGIC   SELECT 'EMSC' AS fonte, _source_file, size(features) AS eventos
# MAGIC   FROM sismos.bronze.emsc_raw
# MAGIC   WHERE CAST(ano AS INT) = 2025
# MAGIC )
# MAGIC SELECT lpad(CAST(m.mes AS STRING), 2, '0') AS mes,
# MAGIC        COUNT_IF(d.fonte = 'USGS') AS arquivos_usgs,
# MAGIC        SUM(CASE WHEN d.fonte = 'USGS' THEN d.eventos END) AS eventos_usgs,
# MAGIC        COUNT_IF(d.fonte = 'EMSC') AS arquivos_emsc,
# MAGIC        SUM(CASE WHEN d.fonte = 'EMSC' THEN d.eventos END) AS eventos_emsc
# MAGIC FROM meses m
# MAGIC LEFT JOIN documentos d
# MAGIC   ON m.mes = TRY_CAST(regexp_extract(d._source_file, 'mes=([0-9]+)', 1) AS INT)
# MAGIC GROUP BY m.mes
# MAGIC ORDER BY m.mes;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Reconciliação com a extração
# MAGIC Compare os totais observados na Bronze com os totais da extração conferida pelo `/count` de cada fonte em 20/11/2026.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH conferencias AS (
# MAGIC   SELECT 'USGS' AS fonte, COUNT(*) AS arquivos,
# MAGIC          SUM(size(features)) AS eventos_bronze, 29312 AS eventos_extracao
# MAGIC   FROM sismos.bronze.terremotos_raw WHERE CAST(ano AS INT) = 2025
# MAGIC   UNION ALL
# MAGIC   SELECT 'EMSC', COUNT(*), SUM(size(features)), 79492
# MAGIC   FROM sismos.bronze.emsc_raw WHERE CAST(ano AS INT) = 2025
# MAGIC )
# MAGIC SELECT fonte, arquivos, eventos_extracao, eventos_bronze,
# MAGIC        eventos_bronze - eventos_extracao AS diferenca,
# MAGIC        CASE WHEN arquivos = 12 AND eventos_bronze = eventos_extracao
# MAGIC             THEN 'OK' ELSE 'REVISAR' END AS status
# MAGIC FROM conferencias
# MAGIC ORDER BY fonte DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Histórico Delta do EMSC
# MAGIC No teste de 20/11/2026, a primeira carga gravou 12 linhas. A segunda, com o mesmo checkpoint, registrou 0 linhas novas. Após a reexecução, a última versão observada foi a 2.

# COMMAND ----------

from pyspark.sql import functions as F

history = spark.sql("DESCRIBE HISTORY sismos.bronze.emsc_raw")
display(
    history.select(
        F.col("version").alias("versao"),
        F.col("timestamp").alias("horario"),
        F.col("operation").alias("operacao"),
        F.col("operationMetrics")["numOutputRows"].cast("long").alias("linhas_gravadas"),
    ).orderBy("versao")
)
