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
# MAGIC ## 2. Reconciliação mensal com a extração
# MAGIC
# MAGIC As contagens de referência são da extração de 20/11/2026. Para cada fonte e mês, a Bronze deve ter um arquivo e a contagem esperada de eventos. O resumo abaixo deve mostrar 12 meses aprovados e zero divergências por fonte.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH referencia AS (
# MAGIC   SELECT * FROM VALUES
# MAGIC     (1, 2258, 5961), (2, 2186, 7482), (3, 2238, 6140),
# MAGIC     (4, 2141, 6258), (5, 2022, 6195), (6, 2010, 5658),
# MAGIC     (7, 4181, 7007), (8, 3082, 7350), (9, 2340, 6474),
# MAGIC     (10, 2016, 6913), (11, 1948, 6398), (12, 2890, 7656)
# MAGIC   AS r(mes, usgs, emsc)
# MAGIC ),
# MAGIC esperado AS (
# MAGIC   SELECT 'USGS' AS fonte, mes, usgs AS eventos FROM referencia
# MAGIC   UNION ALL
# MAGIC   SELECT 'EMSC', mes, emsc FROM referencia
# MAGIC ),
# MAGIC documentos AS (
# MAGIC   SELECT 'USGS' AS fonte, _source_file, size(features) AS eventos
# MAGIC   FROM sismos.bronze.terremotos_raw WHERE CAST(ano AS INT) = 2025
# MAGIC   UNION ALL
# MAGIC   SELECT 'EMSC', _source_file, size(features)
# MAGIC   FROM sismos.bronze.emsc_raw WHERE CAST(ano AS INT) = 2025
# MAGIC ),
# MAGIC bronze AS (
# MAGIC   SELECT fonte,
# MAGIC          TRY_CAST(regexp_extract(_source_file, 'mes=([0-9]+)', 1) AS INT) AS mes,
# MAGIC          COUNT(*) AS arquivos,
# MAGIC          SUM(eventos) AS eventos
# MAGIC   FROM documentos
# MAGIC   GROUP BY 1, 2
# MAGIC )
# MAGIC SELECT COALESCE(e.fonte, b.fonte) AS fonte,
# MAGIC        COALESCE(e.mes, b.mes) AS mes,
# MAGIC        COALESCE(b.arquivos, 0) AS arquivos_bronze,
# MAGIC        e.eventos AS eventos_extracao,
# MAGIC        b.eventos AS eventos_bronze,
# MAGIC        CASE WHEN e.eventos = b.eventos AND b.arquivos = 1
# MAGIC             THEN 'OK' ELSE 'REVISAR' END AS status
# MAGIC FROM esperado e
# MAGIC FULL OUTER JOIN bronze b ON e.fonte = b.fonte AND e.mes = b.mes
# MAGIC ORDER BY fonte, mes;

# COMMAND ----------

from pyspark.sql import functions as F

display(
    _sqldf.groupBy("fonte")
    .agg(
        F.count("*").alias("meses_verificados"),
        F.sum(F.when(F.col("status") == "OK", 1).otherwise(0)).alias("meses_ok"),
        F.sum(F.when(F.col("status") == "REVISAR", 1).otherwise(0)).alias("divergencias"),
    )
    .orderBy("fonte")
)

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

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Reexecução da Bronze do EMSC
# MAGIC
# MAGIC Execute este teste manualmente após a primeira carga, mantendo os arquivos de origem e o checkpoint `checkpoints/emsc_raw`. Os resultados acima podem ser consultados sem reexecutar a carga.
# MAGIC
# MAGIC Em uma célula separada, execute `%run ./02_bronze_autoloader $fonte="emsc"`. O resultado esperado é `sismos.bronze.emsc_raw: 0 linhas novas`. Depois, execute novamente a consulta da seção 3 para verificar se a versão Delta permaneceu a mesma.
# MAGIC
# MAGIC Na execução de 20/11/2026, a tabela permaneceu na versão 2. [Evidências da execução](https://github.com/ckoliveiraa/lakehouse-sismico/issues/3#evid%C3%AAncias-da-execu%C3%A7%C3%A3o).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Evidências da execução
# MAGIC
# MAGIC ### 1. Contagens mensais de USGS e EMSC
# MAGIC
# MAGIC ![Contagem mensal de eventos para USGS e EMSC](https://github.com/user-attachments/assets/d940db15-1ba4-417f-a448-9b9298d2cd70)
# MAGIC
# MAGIC ### 2. Reconciliação mensal com 24 verificações aprovadas
# MAGIC
# MAGIC ![Doze meses aprovados por fonte e zero divergências](https://github.com/user-attachments/assets/9bf1820b-323d-4383-bcbf-5a079c6cdaca)
# MAGIC
# MAGIC ### 3. Histórico Delta de `sismos.bronze.emsc_raw`
# MAGIC
# MAGIC ![Histórico Delta com as versões 0, 1 e 2 e microlotes de 10 e 2 linhas](https://github.com/user-attachments/assets/d8d8ddb6-79a7-44e2-9bb9-22c34eaaa6c4)
# MAGIC
# MAGIC ### 4. Reexecução do EMSC com zero linhas novas
# MAGIC
# MAGIC ![Saída da reexecução do EMSC com zero linhas novas](https://github.com/user-attachments/assets/e105153d-a81d-46f8-b608-5c88307adb3e)
