# Databricks notebook source
# MAGIC %md
# MAGIC # Teste de conectividade com o USGS
# MAGIC Consulta o total de eventos das últimas 24 horas, com magnitude mínima de 2,5.

# COMMAND ----------

from datetime import datetime, timedelta, timezone

import requests

COUNT_URL = "https://earthquake.usgs.gov/fdsnws/event/1/count"

end = datetime.now(timezone.utc)
start = end - timedelta(days=1)
params = {
    "format": "text",
    "starttime": start.isoformat(timespec="seconds"),
    "endtime": end.isoformat(timespec="seconds"),
    "minmagnitude": 2.5,
}

response = requests.get(COUNT_URL, params=params, timeout=60)
response.raise_for_status()
total = int(response.text)

print(f"Conectividade confirmada (HTTP {response.status_code})")
print(f"Eventos com magnitude ≥ 2,5 nas últimas 24 horas: {total}")
