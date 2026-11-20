# Databricks notebook source
SOURCES = {
    "usgs": ("terremotos", "terremotos_raw"),
    "emsc": ("emsc", "emsc_raw"),
}


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

dbutils.widgets.dropdown("fonte", "usgs", list(SOURCES))
load_bronze(dbutils.widgets.get("fonte"))
