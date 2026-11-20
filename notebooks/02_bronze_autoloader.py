# Databricks notebook source
LANDING = "/Volumes/sismos/bronze/landing/terremotos"
CHECKPOINT = "/Volumes/sismos/bronze/checkpoints/terremotos_raw"
TARGET = "sismos.bronze.terremotos_raw"

documents = (
    spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", f"{CHECKPOINT}/schema")
    .option("cloudFiles.partitionColumns", "ano,mes")
    .option("multiLine", "true")
    .option("mode", "FAILFAST")
    .load(LANDING)
    .selectExpr("*", "_metadata.file_path AS _file_path", "current_timestamp() AS _ingestion_time")
)

query = (
    documents.writeStream.format("delta")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT)
    .trigger(availableNow=True)
    .toTable(TARGET)
)
query.awaitTermination()
