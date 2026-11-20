# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Carga incremental na Bronze
# MAGIC Aula 2 · Landing → tabelas Delta
# MAGIC Execute depois que a extração da fonte tiver conferido os 12 meses.
# MAGIC
# MAGIC ## 1. Mapear as fontes e tabelas
# MAGIC USGS grava em `sismos.bronze.terremotos_raw` e EMSC em `sismos.bronze.emsc_raw`.

# COMMAND ----------

SOURCES = {
    "usgs": ("terremotos", "terremotos_raw"),
    "emsc": ("emsc", "emsc_raw"),
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Preparar a carga com Auto Loader
# MAGIC Cada arquivo mensal vira uma linha. O array `features` é preservado, e cada fonte usa o próprio checkpoint.

# COMMAND ----------

def load_bronze(source):
    folder, table = SOURCES[source]
    landing = f"/Volumes/sismos/bronze/landing/{folder}"
    checkpoint = f"/Volumes/sismos/bronze/checkpoints/{table}"
    target = f"sismos.bronze.{table}"
    before = spark.table(target).count() if spark.catalog.tableExists(target) else 0

    documents = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{checkpoint}/_schema")
        .option("cloudFiles.partitionColumns", "ano")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("multiLine", "true")
        .option("mode", "FAILFAST")
        .load(landing)
        .selectExpr("*", "_metadata.file_path AS _source_file", "current_timestamp() AS _ingested_at")
    )
    query = (
        documents.writeStream.format("delta")
        .outputMode("append")
        .option("checkpointLocation", checkpoint)
        .trigger(availableNow=True)
        .toTable(target)
    )
    query.awaitTermination()
    print(f"{target}: {spark.table(target).count() - before} linhas novas")


# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Selecionar a fonte
# MAGIC Execute a célula de parâmetros e escolha a fonte em **Mostrar parâmetros**.

# COMMAND ----------

dbutils.widgets.dropdown("fonte", "usgs", list(SOURCES))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Executar e conferir a carga
# MAGIC Na primeira carga de 2025, espere 12 linhas novas. Para testar a reexecução, rode esta mesma célula novamente com a mesma fonte. O resultado esperado é 0 linhas novas.

# COMMAND ----------

load_bronze(dbutils.widgets.get("fonte"))
